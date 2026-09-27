"""
Main entry point for Drone Swarm Wildfire Response System.
Demonstrates the complete application with satellite data, drone simulation, and firefighter routing.
"""

import logging
import sys
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_logger, DEFAULT_MODE, FEATURES
from application import WildfireResponseSystem
from Visualization.EnhancedUI import run_interactive_ui


def main():
    """Main application entry point."""
    
    # Setup logging
    logger = get_logger("main")
    
    logger.info("="*70)
    logger.info("DRONE SWARM WILDFIRE RESPONSE & ROUTE OPTIMIZATION SYSTEM")
    logger.info("="*70)
    logger.info(f"Mode: {DEFAULT_MODE}")
    logger.info(f"Features enabled: {sum(1 for v in FEATURES.values() if v)} / {len(FEATURES)}")
    
    # Initialize system
    logger.info("\nInitializing system...")
    system = WildfireResponseSystem(mode=DEFAULT_MODE)
    
    # Run interactive UI with integrated application
    logger.info("\nLaunching interactive UI...")
    run_interactive_ui(system)


if __name__ == "__main__":
    main()


