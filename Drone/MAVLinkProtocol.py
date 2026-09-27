"""
MAVLink Protocol Layer - Real drone communication interface.

Handles:
- MAVLink message creation and parsing
- Drone command interface (arm, disarm, takeoff, land, goto)
- Telemetry message handlers (heartbeat, GPS, altitude, battery)
- Connection management and message queuing
"""

import struct
import time
import threading
import queue
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple
from enum import IntEnum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MAVMessageType(IntEnum):
    """MAVLink message type identifiers."""
    HEARTBEAT = 0
    SYS_STATUS = 1
    SYSTEM_TIME = 2
    PARAM_VALUE = 22
    GPS_RAW_INT = 24
    ATTITUDE = 30
    GLOBAL_POSITION_INT = 33
    LOCAL_POSITION_NED = 32
    BATTERY_STATUS = 147
    EXTENDED_SYS_STATE = 245


class MAVCommandType(IntEnum):
    """MAVLink command types for drone control."""
    DO_SET_MODE = 176
    DO_ARM_DISARM = 400
    NAV_TAKEOFF = 22
    NAV_LAND = 21
    NAV_WAYPOINT = 16
    DO_SET_ROI = 201


class DroneMode(IntEnum):
    """Drone flight modes."""
    STABILIZE = 0
    ACRO = 1
    ALT_HOLD = 2
    AUTO = 3
    GUIDED = 4
    LOITER = 5
    RTB = 6  # Return To Base


class DroneState(IntEnum):
    """Drone operational states."""
    DISARMED = 0
    ARMED = 1
    FLYING = 2
    LANDING = 3
    IDLE = 4


@dataclass
class GPSData:
    """GPS position and accuracy information."""
    latitude: float
    longitude: float
    altitude_msl: float  # Altitude above mean sea level (meters)
    altitude_agl: float  # Altitude above ground level (meters)
    horizontal_accuracy: float  # in meters
    vertical_accuracy: float  # in meters
    hdop: float  # Horizontal dilution of precision
    num_satellites: int
    timestamp: datetime


@dataclass
class AttitudeData:
    """Drone attitude (roll, pitch, yaw)."""
    roll: float  # radians
    pitch: float  # radians
    yaw: float  # radians
    roll_rate: float  # rad/s
    pitch_rate: float  # rad/s
    yaw_rate: float  # rad/s
    timestamp: datetime


@dataclass
class BatteryData:
    """Battery status information."""
    voltage: float  # volts
    current: float  # amperes
    charge_remaining: float  # 0-100 percentage
    time_remaining: float  # seconds
    cell_count: int
    battery_function: int  # 0=all, 1=flight
    battery_type: int  # 0=lipo, 1=life, 2=lion
    timestamp: datetime


@dataclass
class TelemetryPacket:
    """Complete telemetry packet from drone."""
    drone_id: int
    mode: DroneMode
    armed: bool
    system_status: int  # 0=inactive, 1=active, etc.
    gps: Optional[GPSData] = None
    attitude: Optional[AttitudeData] = None
    battery: Optional[BatteryData] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MAVLinkMessage:
    """MAVLink message wrapper."""

    def __init__(self, msg_type: int, system_id: int = 1, component_id: int = 1,
                 sequence: int = 0, payload: bytes = b''):
        self.msg_type = msg_type
        self.system_id = system_id
        self.component_id = component_id
        self.sequence = sequence
        self.payload = payload

    def encode(self) -> bytes:
        """Encode message to MAVLink binary format."""
        # MAVLink frame format:
        # byte 0: frame start marker (0xFE)
        # byte 1: payload length
        # byte 2: packet sequence
        # byte 3: system ID
        # byte 4: component ID
        # byte 5: message ID
        # bytes 6+: payload
        # last 2 bytes: CRC

        payload_len = len(self.payload)
        header = bytes([
            0xFE,  # start marker
            payload_len,
            self.sequence,
            self.system_id,
            self.component_id,
            self.msg_type
        ])

        # Simple CRC (in practice, would use proper MAVLink CRC)
        frame = header + self.payload
        crc = self._calculate_crc(frame)

        return frame + struct.pack('<H', crc)

    @staticmethod
    def _calculate_crc(data: bytes) -> int:
        """Simple CRC calculation (placeholder for real implementation)."""
        crc = 0
        for byte in data:
            crc = ((crc << 8) ^ byte) & 0xFFFF
        return crc

    @classmethod
    def decode(cls, data: bytes) -> Optional['MAVLinkMessage']:
        """Decode MAVLink binary message."""
        if len(data) < 8 or data[0] != 0xFE:
            return None

        try:
            payload_len = data[1]
            if len(data) < payload_len + 8:
                return None

            sequence = data[2]
            system_id = data[3]
            component_id = data[4]
            msg_type = data[5]
            payload = data[6:6 + payload_len]

            return cls(msg_type, system_id, component_id, sequence, payload)
        except Exception as e:
            logger.error(f"Error decoding MAVLink message: {e}")
            return None


class DroneCommandInterface:
    """Interface for sending commands to drone via MAVLink."""

    def __init__(self, drone_id: int, system_id: int = 1):
        self.drone_id = drone_id
        self.system_id = system_id
        self.sequence = 0
        self.command_queue: queue.Queue = queue.Queue()

    def _next_sequence(self) -> int:
        """Get next message sequence number."""
        self.sequence = (self.sequence + 1) % 256
        return self.sequence

    def _create_command_message(self, command: MAVCommandType, params: List[float]) -> MAVLinkMessage:
        """Create MAVLink command message."""
        # Command Long format: target_system, target_component, command, confirmation,
        # param1-7
        payload = struct.pack('<BBBBB', self.system_id, 1, int(command) & 0xFF, 0, 0)
        payload += struct.pack('<7f', *[float(p) if i < len(params) else 0.0 for i, p in enumerate(params)][:7])

        msg = MAVLinkMessage(76, self.system_id, 1, self._next_sequence(), payload)
        return msg

    def arm(self) -> MAVLinkMessage:
        """Create ARM command."""
        logger.info(f"Drone {self.drone_id}: Creating ARM command")
        params = [1, 0, 0, 0, 0, 0, 0]  # param1=1 to arm
        return self._create_command_message(MAVCommandType.DO_ARM_DISARM, params)

    def disarm(self) -> MAVLinkMessage:
        """Create DISARM command."""
        logger.info(f"Drone {self.drone_id}: Creating DISARM command")
        params = [0, 0, 0, 0, 0, 0, 0]  # param1=0 to disarm
        return self._create_command_message(MAVCommandType.DO_ARM_DISARM, params)

    def takeoff(self, altitude: float) -> MAVLinkMessage:
        """Create TAKEOFF command."""
        logger.info(f"Drone {self.drone_id}: Creating TAKEOFF command (altitude={altitude}m)")
        params = [0, 0, 0, 0, 0, 0, altitude]
        return self._create_command_message(MAVCommandType.NAV_TAKEOFF, params)

    def land(self) -> MAVLinkMessage:
        """Create LAND command."""
        logger.info(f"Drone {self.drone_id}: Creating LAND command")
        params = [0, 0, 0, 0, 0, 0, 0]
        return self._create_command_message(MAVCommandType.NAV_LAND, params)

    def goto(self, latitude: float, longitude: float, altitude: float) -> MAVLinkMessage:
        """Create GOTO (waypoint) command."""
        logger.info(f"Drone {self.drone_id}: Creating GOTO command ({latitude:.6f}, {longitude:.6f}, {altitude}m)")
        params = [0, 0, 0, 0, latitude, longitude, altitude]
        return self._create_command_message(MAVCommandType.NAV_WAYPOINT, params)

    def set_mode(self, mode: DroneMode) -> MAVLinkMessage:
        """Create SET_MODE command."""
        logger.info(f"Drone {self.drone_id}: Creating SET_MODE command (mode={mode.name})")
        params = [0, int(mode), 0, 0, 0, 0, 0]
        return self._create_command_message(MAVCommandType.DO_SET_MODE, params)

    def set_roi(self, latitude: float, longitude: float, altitude: float) -> MAVLinkMessage:
        """Create SET_ROI (set region of interest) command."""
        logger.info(f"Drone {self.drone_id}: Creating SET_ROI command ({latitude:.6f}, {longitude:.6f}, {altitude}m)")
        params = [0, 0, 0, 0, latitude, longitude, altitude]
        return self._create_command_message(MAVCommandType.DO_SET_ROI, params)

    def enqueue_command(self, command_msg: MAVLinkMessage):
        """Queue command for transmission."""
        self.command_queue.put(command_msg)
        logger.debug(f"Drone {self.drone_id}: Command queued")

    def get_pending_commands(self) -> List[MAVLinkMessage]:
        """Get all pending commands."""
        commands = []
        while not self.command_queue.empty():
            try:
                commands.append(self.command_queue.get_nowait())
            except queue.Empty:
                break
        return commands


class TelemetryHandler:
    """Handles incoming telemetry messages from drone."""

    def __init__(self, drone_id: int):
        self.drone_id = drone_id
        self.gps_data: Optional[GPSData] = None
        self.attitude_data: Optional[AttitudeData] = None
        self.battery_data: Optional[BatteryData] = None
        self.mode: DroneMode = DroneMode.STABILIZE
        self.armed: bool = False
        self.system_status: int = 0
        self.last_heartbeat: float = time.time()
        self.is_connected: bool = False

    def handle_heartbeat(self, payload: bytes):
        """Handle HEARTBEAT message."""
        if len(payload) < 9:
            return

        mode = payload[4]
        armed_status = payload[5]

        self.mode = DroneMode(mode)
        self.armed = bool(armed_status)
        self.last_heartbeat = time.time()
        self.is_connected = True

        logger.debug(f"Drone {self.drone_id}: Heartbeat - mode={self.mode.name}, armed={self.armed}")

    def handle_gps_raw(self, payload: bytes):
        """Handle GPS_RAW_INT message."""
        if len(payload) < 30:
            return

        try:
            lat_raw, lon_raw, alt_msl, hdop, vdop, vel, cog, sat_count = struct.unpack(
                '<iiIHHHHB',
                payload[8:32]
            )

            self.gps_data = GPSData(
                latitude=lat_raw / 1e7,
                longitude=lon_raw / 1e7,
                altitude_msl=alt_msl / 1000.0,
                altitude_agl=alt_msl / 1000.0,  # Placeholder
                horizontal_accuracy=hdop / 100.0,
                vertical_accuracy=vdop / 100.0,
                hdop=hdop / 100.0,
                num_satellites=sat_count,
                timestamp=datetime.now()
            )

            logger.debug(f"Drone {self.drone_id}: GPS - lat={self.gps_data.latitude:.6f}, "
                        f"lon={self.gps_data.longitude:.6f}, alt={self.gps_data.altitude_msl:.1f}m")
        except Exception as e:
            logger.error(f"Error parsing GPS data: {e}")

    def handle_attitude(self, payload: bytes):
        """Handle ATTITUDE message."""
        if len(payload) < 28:
            return

        try:
            time_boot, roll, pitch, yaw, roll_rate, pitch_rate, yaw_rate = struct.unpack(
                '<Iffffff',
                payload[:28]
            )

            self.attitude_data = AttitudeData(
                roll=roll,
                pitch=pitch,
                yaw=yaw,
                roll_rate=roll_rate,
                pitch_rate=pitch_rate,
                yaw_rate=yaw_rate,
                timestamp=datetime.now()
            )

            logger.debug(f"Drone {self.drone_id}: Attitude - roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}")
        except Exception as e:
            logger.error(f"Error parsing attitude data: {e}")

    def handle_battery_status(self, payload: bytes):
        """Handle BATTERY_STATUS message."""
        if len(payload) < 20:
            return

        try:
            battery_id, battery_function, battery_type, temperature, voltages = struct.unpack(
                '<BBBBH',
                payload[:7]
            )

            # Parse cell voltages (up to 10 cells)
            cell_count = min(10, (len(payload) - 7) // 2)
            cell_voltages = []
            for i in range(cell_count):
                offset = 7 + i * 2
                voltage = struct.unpack('<H', payload[offset:offset + 2])[0] / 1000.0
                cell_voltages.append(voltage)

            current = struct.unpack('<i', payload[15:19])[0] / 100.0
            charge_remaining = payload[19]

            total_voltage = sum(cell_voltages) if cell_voltages else voltages / 1000.0

            self.battery_data = BatteryData(
                voltage=total_voltage,
                current=current,
                charge_remaining=charge_remaining,
                time_remaining=0,  # Would calculate based on consumption
                cell_count=cell_count,
                battery_function=battery_function,
                battery_type=battery_type,
                timestamp=datetime.now()
            )

            logger.debug(f"Drone {self.drone_id}: Battery - {self.battery_data.voltage:.2f}V, "
                        f"{self.battery_data.charge_remaining:.0f}%, {self.battery_data.current:.1f}A")
        except Exception as e:
            logger.error(f"Error parsing battery data: {e}")

    def get_telemetry_packet(self) -> TelemetryPacket:
        """Get current telemetry as a packet."""
        return TelemetryPacket(
            drone_id=self.drone_id,
            mode=self.mode,
            armed=self.armed,
            system_status=self.system_status,
            gps=self.gps_data,
            attitude=self.attitude_data,
            battery=self.battery_data,
            timestamp=datetime.now()
        )


class MAVLinkConnection:
    """MAVLink connection manager for a single drone."""

    def __init__(self, drone_id: int, system_id: int = 1, connection_timeout: float = 10.0):
        self.drone_id = drone_id
        self.system_id = system_id
        self.connection_timeout = connection_timeout

        self.cmd_interface = DroneCommandInterface(drone_id, system_id)
        self.telemetry = TelemetryHandler(drone_id)

        self.message_handlers: Dict[int, Callable] = {
            MAVMessageType.HEARTBEAT: self.telemetry.handle_heartbeat,
            MAVMessageType.GPS_RAW_INT: self.telemetry.handle_gps_raw,
            MAVMessageType.ATTITUDE: self.telemetry.handle_attitude,
            MAVMessageType.BATTERY_STATUS: self.telemetry.handle_battery_status,
        }

        self.receive_queue: queue.Queue = queue.Queue()
        self.is_running = False
        self.message_thread: Optional[threading.Thread] = None

    def connect(self) -> bool:
        """Establish connection (in real implementation, would connect to serial/network port)."""
        logger.info(f"Connecting to drone {self.drone_id}...")
        self.is_running = True
        self.message_thread = threading.Thread(target=self._message_processor, daemon=True)
        self.message_thread.start()
        logger.info(f"Drone {self.drone_id} connection established")
        return True

    def disconnect(self):
        """Close connection."""
        logger.info(f"Disconnecting from drone {self.drone_id}...")
        self.is_running = False
        if self.message_thread:
            self.message_thread.join(timeout=2.0)
        logger.info(f"Drone {self.drone_id} disconnected")

    def send_message(self, msg: MAVLinkMessage) -> bool:
        """Send MAVLink message to drone."""
        if not self.telemetry.is_connected:
            logger.warning(f"Drone {self.drone_id} not connected, cannot send message")
            return False

        try:
            # In real implementation, would send through serial/network port
            encoded = msg.encode()
            logger.debug(f"Drone {self.drone_id}: Sent {len(encoded)} bytes")
            return True
        except Exception as e:
            logger.error(f"Error sending message to drone {self.drone_id}: {e}")
            return False

    def receive_message(self, timeout: float = 0.1) -> Optional[MAVLinkMessage]:
        """Receive MAVLink message from drone."""
        try:
            return self.receive_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def process_incoming_data(self, data: bytes):
        """Process incoming raw data from drone."""
        msg = MAVLinkMessage.decode(data)
        if msg:
            self.receive_queue.put(msg)
            self._handle_message(msg)

    def _handle_message(self, msg: MAVLinkMessage):
        """Route message to appropriate handler."""
        if msg.msg_type in self.message_handlers:
            try:
                self.message_handlers[msg.msg_type](msg.payload)
            except Exception as e:
                logger.error(f"Error handling message type {msg.msg_type}: {e}")

    def _message_processor(self):
        """Process incoming messages (runs in background thread)."""
        while self.is_running:
            # In real implementation, would read from serial port
            # Simulate heartbeat
            if time.time() - self.telemetry.last_heartbeat > 1.0:
                self.telemetry.is_connected = True
                self.telemetry.last_heartbeat = time.time()

            time.sleep(0.1)

    def is_connected(self) -> bool:
        """Check if drone is connected."""
        return self.telemetry.is_connected and (time.time() - self.telemetry.last_heartbeat) < self.connection_timeout

    def get_status(self) -> Dict:
        """Get drone status."""
        packet = self.telemetry.get_telemetry_packet()
        return {
            'drone_id': self.drone_id,
            'connected': self.is_connected(),
            'armed': packet.armed,
            'mode': packet.mode.name,
            'gps': {
                'lat': packet.gps.latitude if packet.gps else None,
                'lon': packet.gps.longitude if packet.gps else None,
                'altitude': packet.gps.altitude_msl if packet.gps else None,
            } if packet.gps else None,
            'battery': {
                'voltage': packet.battery.voltage if packet.battery else None,
                'current': packet.battery.current if packet.battery else None,
                'charge': packet.battery.charge_remaining if packet.battery else None,
            } if packet.battery else None,
            'attitude': {
                'roll': packet.attitude.roll if packet.attitude else None,
                'pitch': packet.attitude.pitch if packet.attitude else None,
                'yaw': packet.attitude.yaw if packet.attitude else None,
            } if packet.attitude else None,
        }
