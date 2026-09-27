from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import csv
import zipfile
from datetime import datetime
import math

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Global storage for current session
current_session = {
    'filename': None,
    'file_type': None,
    'boundary': None,
    'area': None,
    'extraction_info': None
}

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload - JSON and GeoJSON only"""
    global current_session
    
    print("\n[DEBUG] Upload request received")
    print(f"[DEBUG] Request files: {list(request.files.keys())}")
    
    file = request.files.get('file')
    if not file or file.filename == '':
        print("[DEBUG] No file in request")
        return jsonify({'status': 'error', 'msg': 'No file selected'}), 400
    
    # CLEAR previous session
    current_session = {
        'filename': None,
        'file_type': None,
        'boundary': None,
        'area': None,
        'extraction_info': None
    }
    
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    # ONLY ALLOW JSON AND GEOJSON
    if ext not in ['.json', '.geojson']:
        print(f"[ERROR] Unsupported format: {ext}")
        return jsonify({
            'status': 'error',
            'msg': f'Unsupported format: {ext}',
            'details': {'error': f'Unsupported format: {ext}', 'method': 'unsupported'}
        }), 400
    
    # Save file
    filepath = os.path.join(UPLOAD_DIR, f"{int(datetime.now().timestamp())}_{filename}")
    file.save(filepath)
    
    print(f"\n[UPLOAD] File: {filename}, Type: {ext}")
    
    # Extract boundary (only JSON now)
    boundary, info = extract_json(filepath)
    
    if not boundary:
        print(f"[ERROR] {info.get('error', 'Unknown error')}")
        return jsonify({
            'status': 'error',
            'msg': f"Could not extract data: {info.get('error', 'Unknown format')}",
            'details': info
        }), 400
    
    # Calculate area
    area = shoelace_area(boundary)
    
    # Store in session
    current_session = {
        'filename': filename,
        'file_type': ext,
        'boundary': boundary,
        'area': area,
        'extraction_info': info,
        'timestamp': datetime.now().isoformat(),
        'file_size': os.path.getsize(filepath),
        'boundary_points': len(boundary)
    }
    
    print(f"[SUCCESS] Extracted {len(boundary)} points, Area: {area:.2f}")
    print(f"[INFO] Method: {info.get('method', 'unknown')}\n")
    
    return jsonify({
        'status': 'success',
        'filename': filename,
        'points': len(boundary),
        'area': area,
        'method': info.get('method', '')
    }), 200

@app.route('/api/get-data')
def get_data():
    """Get current session data"""
    if not current_session['boundary']:
        return jsonify({'status': 'error', 'msg': 'No data'}), 400
    
    return jsonify({
        'status': 'success',
        'data': current_session
    }), 200

@app.route('/api/generate-mesh', methods=['POST'])
def generate_mesh_api():
    """Generate mesh nodes inside boundary"""
    if not current_session.get('boundary'):
        return jsonify({'status': 'error', 'msg': 'No boundary data'}), 400
    
    try:
        import time
        
        data = request.get_json() or {}
        spacing_input = float(data.get('spacing', 15))
        
        boundary = current_session['boundary']
        
        # Get bounding box
        xs = [p[0] for p in boundary]
        ys = [p[1] for p in boundary]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        width = max_x - min_x
        height = max_y - min_y
        
        print(f"[MESH DEBUG] Boundary: min=({min_x}, {min_y}), max=({max_x}, {max_y})")
        print(f"[MESH DEBUG] Size: {width} x {height}")
        print(f"[MESH DEBUG] User spacing input: {spacing_input}")
        
        # Check if coordinates are geographic (lat/lon)
        is_geographic = (all(-180 <= x <= 180 for x in xs) and 
                        all(-90 <= y <= 90 for y in ys))
        
        # === START TIMING ===
        start_time = time.time()
        
        if is_geographic:
            # For geographic coordinates, convert spacing from meters to degrees
            # User enters spacing in meters, we convert to degree spacing
            avg_lat = sum(ys) / len(ys)
            meters_per_deg_lat = 111320
            meters_per_deg_lon = 111320 * math.cos(math.radians(avg_lat))
            
            # Convert user's meter spacing to degree spacing
            spacing_deg_x = spacing_input / meters_per_deg_lon
            spacing_deg_y = spacing_input / meters_per_deg_lat
            
            print(f"[MESH DEBUG] Geographic mode: {spacing_input}m = {spacing_deg_x:.8f}° lon, {spacing_deg_y:.8f}° lat")
            
            # Generate grid points
            mesh = []
            x = min_x
            while x <= max_x:
                y = min_y
                while y <= max_y:
                    if point_in_polygon(x, y, boundary):
                        mesh.append([x, y])
                    y += spacing_deg_y
                x += spacing_deg_x
            
            spacing_used = spacing_input  # Display in meters
        else:
            # Cartesian coordinates - use spacing directly
            spacing = spacing_input
            
            mesh = []
            x = min_x
            while x <= max_x:
                y = min_y
                while y <= max_y:
                    if point_in_polygon(x, y, boundary):
                        mesh.append([x, y])
                    y += spacing
                x += spacing
            
            spacing_used = spacing
        
        # === END TIMING ===
        mesh_generation_time = time.time() - start_time
        
        current_session['mesh'] = mesh
        current_session['mesh_spacing'] = spacing_used
        current_session['mesh_generation_time'] = mesh_generation_time
        
        print(f"[MESH] Generated {len(mesh)} nodes with spacing {spacing_used}")
        print(f"[MESH] Generation time: {mesh_generation_time*1000:.2f} ms")
        print(f"[MESH] Complexity: O(n) where n={len(mesh)}")
        
        return jsonify({
            'status': 'success',
            'mesh': mesh,
            'count': len(mesh),
            'spacing_used': spacing_used,
            'is_geographic': is_geographic,
            'generation_time_ms': mesh_generation_time * 1000
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Mesh generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@app.route('/api/allocate-drones', methods=['POST'])
def allocate_drones_api():
    """Allocate mesh nodes to drones"""
    if not current_session.get('mesh'):
        return jsonify({'status': 'error', 'msg': 'Generate mesh first'}), 400
    
    try:
        data = request.get_json() or {}
        num_drones = int(data.get('num_drones', 4))
        
        mesh = current_session['mesh']
        
        # Divide mesh nodes among drones
        nodes_per_drone = len(mesh) // num_drones
        allocation = {}
        
        for i in range(num_drones):
            start_idx = i * nodes_per_drone
            if i == num_drones - 1:
                # Last drone gets remaining nodes
                allocation[i] = mesh[start_idx:]
            else:
                allocation[i] = mesh[start_idx:start_idx + nodes_per_drone]
        
        current_session['drone_allocation'] = allocation
        current_session['num_drones'] = num_drones
        
        print(f"[DRONES] Allocated {num_drones} drones")
        for i, nodes in allocation.items():
            print(f"  Drone {i}: {len(nodes)} nodes")
        
        return jsonify({
            'status': 'success',
            'allocation': {str(k): v for k, v in allocation.items()},
            'num_drones': num_drones
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Drone allocation: {str(e)}")
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@app.route('/api/plan-paths', methods=['POST'])
def plan_paths_api():
    """Plan optimized paths for each drone with baseline comparison"""
    if not current_session.get('drone_allocation'):
        return jsonify({'status': 'error', 'msg': 'Allocate drones first'}), 400
    
    try:
        import time
        
        allocation = current_session['drone_allocation']
        
        # Optimized paths (Nearest Neighbor)
        paths_optimized = {}
        distances_optimized = {}
        times_optimized = {}
        
        # Baseline paths (Sequential)
        paths_baseline = {}
        distances_baseline = {}
        times_baseline = {}
        
        # Area coverage
        areas = {}
        
        for drone_id, nodes in allocation.items():
            if len(nodes) == 0:
                continue
            
            # === OPTIMIZED PATH (Nearest Neighbor) ===
            start_time = time.time()
            path_opt = nearest_neighbor_tsp(nodes)
            time_opt = time.time() - start_time
            dist_opt = calculate_path_distance(path_opt)
            
            paths_optimized[drone_id] = path_opt
            distances_optimized[drone_id] = dist_opt
            times_optimized[drone_id] = time_opt
            
            # === BASELINE PATH (Sequential) ===
            start_time = time.time()
            path_seq = list(nodes)  # Sequential order as generated
            time_seq = time.time() - start_time
            dist_seq = calculate_path_distance(path_seq)
            
            paths_baseline[drone_id] = path_seq
            distances_baseline[drone_id] = dist_seq
            times_baseline[drone_id] = time_seq
            
            # === AREA COVERAGE ===
            if len(path_opt) >= 3:
                area = shoelace_area(path_opt)
            else:
                area = 0
            areas[drone_id] = area
            
            # === PERFORMANCE METRICS ===
            reduction_pct = ((dist_seq - dist_opt) / dist_seq * 100) if dist_seq > 0 else 0
            
            print(f"[PATH] Drone {drone_id}:")
            print(f"  Nodes: {len(nodes)}")
            print(f"  Sequential: {dist_seq:.2f} m (time: {time_seq*1000:.2f} ms)")
            print(f"  Optimized:  {dist_opt:.2f} m (time: {time_opt*1000:.2f} ms)")
            print(f"  Reduction:  {reduction_pct:.2f}%")
            print(f"  Area:       {area:.2f} m²")
        
        # Store all results
        current_session['drone_paths_optimized'] = paths_optimized
        current_session['drone_paths_baseline'] = paths_baseline
        current_session['drone_distances_optimized'] = distances_optimized
        current_session['drone_distances_baseline'] = distances_baseline
        current_session['drone_times_optimized'] = times_optimized
        current_session['drone_times_baseline'] = times_baseline
        current_session['drone_areas'] = areas
        
        # Calculate totals
        total_dist_opt = sum(distances_optimized.values())
        total_dist_seq = sum(distances_baseline.values())
        total_reduction = ((total_dist_seq - total_dist_opt) / total_dist_seq * 100) if total_dist_seq > 0 else 0
        
        print(f"\n[TOTAL] Sequential: {total_dist_seq:.2f} m")
        print(f"[TOTAL] Optimized:  {total_dist_opt:.2f} m")
        print(f"[TOTAL] Reduction:  {total_reduction:.2f}%\n")
        
        return jsonify({
            'status': 'success',
            'paths_optimized': {str(k): v for k, v in paths_optimized.items()},
            'paths_baseline': {str(k): v for k, v in paths_baseline.items()},
            'distances_optimized': {str(k): v for k, v in distances_optimized.items()},
            'distances_baseline': {str(k): v for k, v in distances_baseline.items()},
            'times_optimized': {str(k): v for k, v in times_optimized.items()},
            'times_baseline': {str(k): v for k, v in times_baseline.items()},
            'areas': {str(k): v for k, v in areas.items()},
            'total_distance_optimized': total_dist_opt,
            'total_distance_baseline': total_dist_seq,
            'total_reduction_percent': total_reduction
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Path planning: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'msg': str(e)}), 500

def point_in_polygon(x, y, polygon):
    """Check if point is inside polygon using ray casting"""
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def nearest_neighbor_tsp(nodes):
    """Nearest neighbor algorithm for TSP"""
    if len(nodes) == 0:
        return []
    
    path = [nodes[0]]
    remaining = list(nodes[1:])
    
    while remaining:
        current = path[-1]
        # Find nearest unvisited node
        nearest = min(remaining, key=lambda p: distance(current, p))
        path.append(nearest)
        remaining.remove(nearest)
    
    return path

def distance(p1, p2):
    """Euclidean distance between two points"""
    # Check if coordinates are geographic (lat/lon)
    if (-180 <= p1[0] <= 180 and -90 <= p1[1] <= 90 and
        -180 <= p2[0] <= 180 and -90 <= p2[1] <= 90):
        # Use Haversine formula for geographic coordinates
        return haversine_distance(p1, p2)
    else:
        # Euclidean distance for Cartesian coordinates
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def haversine_distance(p1, p2):
    """Calculate distance between two lat/lon points in meters"""
    lon1, lat1 = p1[0], p1[1]
    lon2, lat2 = p2[0], p2[1]
    
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def calculate_path_distance(path):
    """Calculate total path distance"""
    if len(path) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(path) - 1):
        total += distance(path[i], path[i + 1])
    
    # Add return to start
    total += distance(path[-1], path[0])
    
    return total

def extract_from_file(filepath, ext):
    """Extract boundary from any supported file"""
    
    # JSON
    if ext == '.json':
        return extract_json(filepath)
    
    # CSV
    elif ext == '.csv':
        return extract_csv(filepath)
    
    # ZIP - try to find supported files inside
    elif ext == '.zip':
        return extract_zip(filepath)
    
    # Text
    elif ext == '.txt':
        return extract_text(filepath)
    
    else:
        return None, {'error': f'Unsupported format: {ext}', 'method': 'unsupported'}

def extract_json(filepath):
    """Extract coordinates from JSON"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check for GeoJSON FeatureCollection
        if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
            features = data.get('features', [])
            if features and 'geometry' in features[0]:
                geom = features[0]['geometry']
                
                # Handle Polygon
                if geom['type'] == 'Polygon':
                    coords = geom['coordinates'][0]
                    boundary = [[float(c[0]), float(c[1])] for c in coords]
                    return boundary, {'method': 'geojson_featurecollection_polygon', 'points': len(boundary)}
                
                # Handle MultiPolygon - take first polygon
                elif geom['type'] == 'MultiPolygon':
                    coords = geom['coordinates'][0][0]  # First polygon, outer ring
                    boundary = [[float(c[0]), float(c[1])] for c in coords]
                    return boundary, {'method': 'geojson_featurecollection_multipolygon', 'points': len(boundary)}
        
        # Check for GeoJSON Feature
        if isinstance(data, dict) and data.get('type') == 'Feature':
            geom = data.get('geometry', {})
            
            # Handle Polygon
            if geom.get('type') == 'Polygon':
                coords = geom['coordinates'][0]
                boundary = [[float(c[0]), float(c[1])] for c in coords]
                return boundary, {'method': 'geojson_feature_polygon', 'points': len(boundary)}
            
            # Handle MultiPolygon
            elif geom.get('type') == 'MultiPolygon':
                coords = geom['coordinates'][0][0]
                boundary = [[float(c[0]), float(c[1])] for c in coords]
                return boundary, {'method': 'geojson_feature_multipolygon', 'points': len(boundary)}
        
        # Look for 'boundary' key
        if 'boundary' in data and isinstance(data['boundary'], list):
            boundary = parse_coords(data['boundary'])
            if boundary:
                return boundary, {'method': 'json_boundary_key', 'points': len(boundary)}
        
        # Look for 'coordinates' key
        if 'coordinates' in data and isinstance(data['coordinates'], list):
            boundary = parse_coords(data['coordinates'])
            if boundary:
                return boundary, {'method': 'json_coordinates_key', 'points': len(boundary)}
        
        # Look for 'points' key
        if 'points' in data and isinstance(data['points'], list):
            boundary = parse_coords(data['points'])
            if boundary:
                return boundary, {'method': 'json_points_key', 'points': len(boundary)}
        
        # Try any list with numeric values
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 2:
                boundary = parse_coords(value)
                if boundary and len(boundary) >= 3:
                    return boundary, {'method': 'json_generic_list', 'key': key, 'points': len(boundary)}
        
        return None, {'error': 'No coordinate data found in JSON', 'method': 'json_no_coords'}
    
    except json.JSONDecodeError as e:
        return None, {'error': f'Invalid JSON: {str(e)}', 'method': 'json_parse_error'}
    except Exception as e:
        return None, {'error': str(e), 'method': 'json_error'}

def extract_csv(filepath):
    """Extract coordinates from CSV"""
    try:
        boundary = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            
            # Find x, y columns
            x_idx, y_idx = find_xy_columns(headers)
            
            if x_idx is None or y_idx is None:
                # Try first two columns as x, y
                x_idx, y_idx = 0, 1
            
            for row in reader:
                try:
                    if len(row) > max(x_idx, y_idx):
                        x = float(row[x_idx].strip())
                        y = float(row[y_idx].strip())
                        boundary.append([x, y])
                except (ValueError, IndexError):
                    continue
        
        if not boundary or len(boundary) < 3:
            return None, {'error': 'Insufficient coordinates in CSV', 'method': 'csv_no_coords'}
        
        return boundary, {
            'method': 'csv_extraction',
            'points': len(boundary),
            'x_column': headers[x_idx] if x_idx < len(headers) else 'column_0',
            'y_column': headers[y_idx] if y_idx < len(headers) else 'column_1'
        }
    
    except Exception as e:
        return None, {'error': str(e), 'method': 'csv_error'}

def extract_text(filepath):
    """Extract coordinates from text file"""
    try:
        boundary = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Split by comma or space
                parts = line.replace(',', ' ').split()
                try:
                    if len(parts) >= 2:
                        x = float(parts[0])
                        y = float(parts[1])
                        boundary.append([x, y])
                except ValueError:
                    continue
        
        if not boundary or len(boundary) < 3:
            return None, {'error': 'Insufficient coordinates in text file', 'method': 'text_no_coords'}
        
        return boundary, {'method': 'text_extraction', 'points': len(boundary)}
    
    except Exception as e:
        return None, {'error': str(e), 'method': 'text_error'}

def extract_zip(filepath):
    """Extract from files inside ZIP"""
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            for filename in z.namelist():
                ext = os.path.splitext(filename)[1].lower()
                
                if ext in ['.json', '.csv', '.txt']:
                    # Extract to temp
                    temp_path = os.path.join(UPLOAD_DIR, filename)
                    with z.open(filename) as zf:
                        with open(temp_path, 'wb') as out:
                            out.write(zf.read())
                    
                    # Try to extract
                    boundary, info = extract_from_file(temp_path, ext)
                    if boundary:
                        info['source'] = f'extracted from {filename}'
                        return boundary, info
        
        return None, {'error': 'No supported files in ZIP', 'method': 'zip_no_supported'}
    
    except Exception as e:
        return None, {'error': str(e), 'method': 'zip_error'}

def parse_coords(data):
    """Parse various coordinate formats"""
    coords = []
    
    for item in data:
        try:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                x = float(item[0])
                y = float(item[1])
                coords.append([x, y])
            elif isinstance(item, dict):
                x = item.get('x') or item.get('lon') or item.get('longitude')
                y = item.get('y') or item.get('lat') or item.get('latitude')
                if x is not None and y is not None:
                    coords.append([float(x), float(y)])
        except (ValueError, TypeError, KeyError):
            continue
    
    return coords if coords else None

def find_xy_columns(headers):
    """Find X and Y column indices"""
    headers_lower = [h.lower().strip() for h in headers]
    
    x_keywords = ['x', 'lon', 'longitude']
    y_keywords = ['y', 'lat', 'latitude']
    
    x_idx = None
    y_idx = None
    
    for i, h in enumerate(headers_lower):
        if h in x_keywords and x_idx is None:
            x_idx = i
        if h in y_keywords and y_idx is None:
            y_idx = i
    
    return x_idx, y_idx

def shoelace_area(boundary):
    """Calculate area using Shoelace formula"""
    if not boundary or len(boundary) < 3:
        return 0.0
    
    # Check if coordinates are geographic (lat/lon)
    xs = [p[0] for p in boundary]
    ys = [p[1] for p in boundary]
    
    # If coordinates are in range -180 to 180 and -90 to 90, likely lat/lon
    is_geographic = (all(-180 <= x <= 180 for x in xs) and 
                     all(-90 <= y <= 90 for y in ys))
    
    if is_geographic:
        # Convert to approximate meters using Haversine for small areas
        # Use average latitude for projection
        avg_lat = sum(ys) / len(ys)
        
        # Meters per degree at this latitude
        meters_per_deg_lat = 111320  # approximately constant
        meters_per_deg_lon = 111320 * math.cos(math.radians(avg_lat))
        
        # Convert to local meters
        boundary_meters = []
        for p in boundary:
            x_m = (p[0] - xs[0]) * meters_per_deg_lon
            y_m = (p[1] - ys[0]) * meters_per_deg_lat
            boundary_meters.append([x_m, y_m])
        
        # Calculate area in square meters
        area_m2 = 0.0
        n = len(boundary_meters)
        for i in range(n):
            j = (i + 1) % n
            area_m2 += boundary_meters[i][0] * boundary_meters[j][1]
            area_m2 -= boundary_meters[j][0] * boundary_meters[i][1]
        
        area_m2 = abs(area_m2) / 2.0
        
        # Return area in square meters
        return area_m2
    else:
        # Use raw Shoelace for Cartesian coordinates
        area = 0.0
        n = len(boundary)
        for i in range(n):
            j = (i + 1) % n
            area += boundary[i][0] * boundary[j][1]
            area -= boundary[j][0] * boundary[i][1]
        
        return abs(area) / 2.0

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Wildfire Drone Response System - Backend")
    print("="*60)
    print(f"Server running on http://localhost:5000")
    print(f"Network access: http://192.168.1.11:5000")
    print("="*60 + "\n")
    
    # Get port from environment (for cloud deployment) or use 5000
    import os
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=False)
