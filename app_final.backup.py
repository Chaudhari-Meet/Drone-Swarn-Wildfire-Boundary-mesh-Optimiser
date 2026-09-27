from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import zipfile
import csv
from datetime import datetime
from PIL import Image
import numpy as np
import cv2
import sys

# Import backend algorithms - with fallback to built-in functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from Algorithms.Mesh_Generation import generate_mesh
except:
    generate_mesh = None
try:
    from Algorithms.Drone_Allocation import allocate_drones
except:
    allocate_drones = None
try:
    from Algorithms.Path_Planning import nearest_neighbor_path, two_opt_optimization, calculate_path_distance
except:
    nearest_neighbor_path = None
    two_opt_optimization = None
    calculate_path_distance = None
try:
    from Algorithms.Area_Calculation import calculate_area as calc_area_algo
except:
    calc_area_algo = None

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = 'uploads'
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

session_data = {
    'file_uploaded': False,
    'filename': None,
    'file_type': None,
    'boundary': [],
    'area': 0,
    'mesh': [],
    'drones': {},
    'paths': {},
    'extraction_info': {}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    """Handle file upload - EXTRACT ACTUAL DATA FROM FILE"""
    global session_data
    
    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'msg': 'No file provided'}), 400
    
    # CLEAR ALL PREVIOUS DATA
    session_data = {
        'file_uploaded': False,
        'filename': None,
        'file_type': None,
        'boundary': [],
        'area': 0,
        'mesh': [],
        'drones': {},
        'paths': {},
        'extraction_info': {},
        'upload_time': datetime.now().isoformat()
    }
    
    filename = file.filename
    unique_filename = f"{int(datetime.now().timestamp())}_{filename}"
    filepath = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # EXTRACT BOUNDARY FROM UPLOADED FILE
        boundary, extraction_info = extract_boundary_from_file(filepath, file_ext)
        
        if not boundary:
            return jsonify({
                'status': 'error',
                'msg': f'Could not extract wildfire boundary from {filename}',
                'details': extraction_info
            }), 400
        
        # CALCULATE AREA FROM EXTRACTED BOUNDARY
        area = calculate_area(boundary)
        
        # STORE CURRENT UPLOAD DATA
        session_data.update({
            'file_uploaded': True,
            'filename': filename,
            'file_type': file_ext,
            'size_kb': round(file_size / 1024, 2),
            'boundary': boundary,
            'area': area,
            'extraction_info': extraction_info,
            'boundary_points': len(boundary),
            'timestamp': datetime.now().timestamp()
        })
        
        print(f"\n[UPLOAD SUCCESS]")
        print(f"  File: {filename}")
        print(f"  Boundary Points: {len(boundary)}")
        print(f"  Calculated Area: {area:.2f}")
        print(f"  Method: {extraction_info.get('method', 'unknown')}\n")
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'boundary_points': len(boundary),
            'area': area,
            'extraction_method': extraction_info.get('method', ''),
            'file_size_kb': session_data['size_kb']
        }), 200
        
    except Exception as e:
        print(f"[UPLOAD ERROR] {str(e)}")
        return jsonify({
            'status': 'error',
            'msg': f'Upload failed: {str(e)}'
        }), 500

def extract_boundary_from_file(filepath, file_ext):
    """
    PHASE 1: Extract actual boundary coordinates from uploaded file
    DO NOT generate fake data
    """
    print(f"[EXTRACT] Processing {filepath} with extension {file_ext}")
    
    # Image file
    if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']:
        return extract_from_image(filepath)
    
    # JSON file - check for GeoJSON or coordinate arrays
    elif file_ext == '.json':
        return extract_from_json(filepath)
    
    # CSV file - extract coordinate rows
    elif file_ext == '.csv':
        return extract_from_csv(filepath)
    
    # GeoJSON
    elif file_ext == '.geojson':
        return extract_from_geojson(filepath)
    
    # KML
    elif file_ext == '.kml':
        return extract_from_kml(filepath)
    
    # Text/GPX
    elif file_ext in ['.txt', '.gpx']:
        return extract_from_text(filepath)
    
    # ZIP - extract from contents
    elif file_ext == '.zip':
        return extract_from_zip(filepath)
    
    else:
        return [], {'method': 'unsupported_format', 'error': f'Format {file_ext} not supported'}

def extract_from_json(filepath):
    """Extract coordinates from JSON - supports multiple schemas"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if GeoJSON
        if isinstance(data, dict) and 'type' in data:
            if data['type'] == 'FeatureCollection':
                return extract_geojson_featurecollection(data)
            elif data['type'] == 'Feature':
                return extract_geojson_feature(data)
        
        # Look for boundary/coordinates arrays
        boundary = []
        info_keys = []
        
        for key in data.keys():
            info_keys.append(key)
            if key.lower() in ['boundary', 'coordinates', 'points', 'polygon', 'fire_boundary', 'wildfire']:
                coords = data[key]
                boundary = parse_coordinate_array(coords)
                if boundary:
                    return boundary, {
                        'method': 'json_direct',
                        'key_used': key,
                        'points': len(boundary),
                        'json_structure': info_keys[:10]
                    }
        
        # If no named boundary found, return error
        return [], {
            'method': 'json_no_boundary',
            'error': 'No boundary/coordinates key found',
            'available_keys': info_keys
        }
        
    except json.JSONDecodeError as e:
        return [], {'method': 'json_parse_error', 'error': str(e)}
    except Exception as e:
        return [], {'method': 'json_error', 'error': str(e)}

def extract_geojson_feature(feature):
    """Extract geometry from GeoJSON Feature"""
    try:
        if 'geometry' not in feature:
            return [], {'method': 'geojson_no_geometry'}
        
        geom = feature['geometry']
        if geom['type'] == 'Polygon':
            coords = geom['coordinates'][0]  # Outer ring
            boundary = [[float(c[0]), float(c[1])] for c in coords]
            return boundary, {
                'method': 'geojson_polygon',
                'points': len(boundary)
            }
        elif geom['type'] == 'MultiPolygon':
            # Use first polygon
            coords = geom['coordinates'][0][0]
            boundary = [[float(c[0]), float(c[1])] for c in coords]
            return boundary, {
                'method': 'geojson_multipolygon_first',
                'points': len(boundary)
            }
        
        return [], {'method': 'geojson_unsupported_type', 'type': geom['type']}
        
    except Exception as e:
        return [], {'method': 'geojson_feature_error', 'error': str(e)}

def extract_geojson_featurecollection(data):
    """Extract first feature from GeoJSON FeatureCollection"""
    try:
        if 'features' not in data or len(data['features']) == 0:
            return [], {'method': 'geojson_no_features'}
        
        # Use first feature
        return extract_geojson_feature(data['features'][0])
        
    except Exception as e:
        return [], {'method': 'geojson_collection_error', 'error': str(e)}

def extract_from_csv(filepath):
    """Extract coordinates from CSV"""
    try:
        boundary = []
        headers = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # Read first line to detect headers
            first_line = f.readline().strip()
            f.seek(0)
            
            reader = csv.reader(f)
            headers = next(reader, [])
            
            # Find coordinate columns
            x_col, y_col = find_coordinate_columns(headers)
            
            if x_col is None or y_col is None:
                return [], {'method': 'csv_no_coordinates', 'headers': headers}
            
            # Read coordinates
            for row in reader:
                try:
                    if len(row) > max(x_col, y_col):
                        x = float(row[x_col].strip())
                        y = float(row[y_col].strip())
                        boundary.append([x, y])
                except (ValueError, IndexError):
                    continue
        
        if not boundary:
            return [], {'method': 'csv_parse_failed', 'headers': headers}
        
        return boundary, {
            'method': 'csv_extraction',
            'points': len(boundary),
            'x_column': headers[x_col] if x_col < len(headers) else 'unknown',
            'y_column': headers[y_col] if y_col < len(headers) else 'unknown'
        }
        
    except Exception as e:
        return [], {'method': 'csv_error', 'error': str(e)}

def find_coordinate_columns(headers):
    """Find x and y coordinate columns in CSV headers"""
    headers_lower = [h.lower().strip() for h in headers]
    
    x_keywords = ['x', 'lon', 'longitude', 'long', 'lng']
    y_keywords = ['y', 'lat', 'latitude']
    
    x_col = None
    y_col = None
    
    for i, h in enumerate(headers_lower):
        if h in x_keywords and x_col is None:
            x_col = i
        if h in y_keywords and y_col is None:
            y_col = i
    
    # If not found by name, use first two numeric columns
    if x_col is None and y_col is None:
        numeric_cols = []
        for i, h in enumerate(headers_lower):
            try:
                float(h)
                numeric_cols.append(i)
            except:
                pass
        
        if len(numeric_cols) >= 2:
            x_col, y_col = numeric_cols[0], numeric_cols[1]
    
    return x_col, y_col

def extract_from_geojson(filepath):
    """Extract from GeoJSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get('type') == 'FeatureCollection':
            return extract_geojson_featurecollection(data)
        elif data.get('type') == 'Feature':
            return extract_geojson_feature(data)
        
        return [], {'method': 'geojson_invalid_type'}
        
    except Exception as e:
        return [], {'method': 'geojson_error', 'error': str(e)}

def extract_from_kml(filepath):
    """Extract from KML file (basic support)"""
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Find Polygon/LineString elements
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        for polygon in root.findall('.//kml:Polygon', ns):
            coords_elem = polygon.find('.//kml:LinearRing/kml:coordinates', ns)
            if coords_elem is not None and coords_elem.text:
                boundary = parse_kml_coordinates(coords_elem.text)
                if boundary:
                    return boundary, {'method': 'kml_polygon', 'points': len(boundary)}
        
        return [], {'method': 'kml_no_polygon_found'}
        
    except Exception as e:
        return [], {'method': 'kml_error', 'error': str(e)}

def parse_kml_coordinates(coord_string):
    """Parse KML coordinate string"""
    boundary = []
    for coord in coord_string.strip().split():
        parts = coord.strip().split(',')
        if len(parts) >= 2:
            try:
                x = float(parts[0])
                y = float(parts[1])
                boundary.append([x, y])
            except ValueError:
                continue
    return boundary

def extract_from_text(filepath):
    """Extract coordinates from text/GPX file"""
    try:
        boundary = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Try GPX format first
        if '<gpx' in content.lower():
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
            
            for trkpt in root.findall('.//gpx:trkpt', ns):
                lat = trkpt.get('lat')
                lon = trkpt.get('lon')
                if lat and lon:
                    boundary.append([float(lon), float(lat)])
        
        # Parse as coordinate pairs
        if not boundary:
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Try to parse as coordinates
                coords = line.replace(',', ' ').split()
                try:
                    if len(coords) >= 2:
                        x = float(coords[0])
                        y = float(coords[1])
                        boundary.append([x, y])
                except:
                    continue
        
        if not boundary:
            return [], {'method': 'text_no_coordinates'}
        
        return boundary, {
            'method': 'text_coordinates',
            'points': len(boundary),
            'lines_parsed': len(boundary)
        }
        
    except Exception as e:
        return [], {'method': 'text_error', 'error': str(e)}

def extract_from_image(filepath):
    """Extract wildfire boundary from image using edge detection"""
    try:
        img = cv2.imread(filepath)
        if img is None:
            return [], {'method': 'image_cannot_read'}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return [], {'method': 'image_no_contours'}
        
        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        
        # Approximate to reduce points
        epsilon = 0.02 * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)
        
        boundary = [[float(p[0][0]), float(p[0][1])] for p in approx]
        
        return boundary, {
            'method': 'image_edge_detection',
            'image_size': f'{img.shape[1]}x{img.shape[0]}',
            'points': len(boundary),
            'area_px': cv2.contourArea(largest)
        }
        
    except Exception as e:
        return [], {'method': 'image_error', 'error': str(e)}

def extract_from_zip(filepath):
    """Extract from supported files inside ZIP"""
    try:
        boundary = []
        with zipfile.ZipFile(filepath, 'r') as z:
            for filename in z.namelist():
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.json', '.csv', '.txt', '.geojson', '.kml']:
                    temp_path = os.path.join(UPLOAD_DIR, filename)
                    with z.open(filename) as zf:
                        with open(temp_path, 'wb') as out:
                            out.write(zf.read())
                    
                    b, info = extract_boundary_from_file(temp_path, ext)
                    if b and len(b) > len(boundary):
                        boundary = b
                        info['source_file'] = filename
                        return boundary, info
        
        return [], {'method': 'zip_no_supported_files'}
        
    except Exception as e:
        return [], {'method': 'zip_error', 'error': str(e)}

def parse_coordinate_array(data):
    """Parse various coordinate array formats"""
    if not isinstance(data, list):
        return []
    
    boundary = []
    for item in data:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            try:
                boundary.append([float(item[0]), float(item[1])])
            except:
                continue
        elif isinstance(item, dict) and ('x' in item or 'lat' in item):
            try:
                x = item.get('x') or item.get('lon') or item.get('longitude', 0)
                y = item.get('y') or item.get('lat') or item.get('latitude', 0)
                boundary.append([float(x), float(y)])
            except:
                continue
    
    return boundary

def calculate_area(boundary):
    """PHASE 2: Calculate area from EXTRACTED boundary using Shoelace formula"""
    if not boundary or len(boundary) < 3:
        return 0.0
    
    # Convert to tuple format
    boundary_tuples = [(float(p[0] if isinstance(p, (list, tuple)) else p.get('x', 0)), 
                       float(p[1] if isinstance(p, (list, tuple)) else p.get('y', 0))) 
                      for p in boundary]
    
    try:
        # Use backend algorithm if available
        if calc_area_algo:
            area = calc_area_algo(boundary_tuples)
            return abs(area)
    except:
        pass
    
    # Fallback to Shoelace
    area = 0.0
    n = len(boundary_tuples)
    for i in range(n):
        j = (i + 1) % n
        area += boundary_tuples[i][0] * boundary_tuples[j][1]
        area -= boundary_tuples[j][0] * boundary_tuples[i][1]
    return abs(area) / 2

def generate_mesh_fallback(boundary, spacing=10):
    """Fallback mesh generation"""
    xs = [p[0] for p in boundary]
    ys = [p[1] for p in boundary]
    minX, maxX = min(xs), max(xs)
    minY, maxY = min(ys), max(ys)
    
    mesh = []
    x = minX
    while x <= maxX:
        y = minY
        while y <= maxY:
            if point_in_polygon(x, y, boundary):
                mesh.append((x, y))
            y += spacing
        x += spacing
    return mesh

def point_in_polygon(x, y, polygon):
    """Check if point is inside polygon"""
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, len(polygon) + 1):
        p2x, p2y = polygon[i % len(polygon)]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def allocate_drones_fallback(mesh, num_drones=4):
    """Fallback drone allocation"""
    if not mesh or len(mesh) == 0:
        return {}
    
    allocation = {}
    nodes_per_drone = len(mesh) // num_drones
    
    for i in range(num_drones):
        start = i * nodes_per_drone
        end = start + nodes_per_drone if i < num_drones - 1 else len(mesh)
        allocation[str(i)] = [list(n) for n in mesh[start:end]]
    
    return allocation

def nearest_neighbor_fallback(nodes):
    """Fallback nearest neighbor path planning"""
    if not nodes or len(nodes) == 0:
        return []
    
    path = [nodes[0]]
    remaining = list(nodes[1:])
    
    while remaining:
        current = path[-1]
        nearest = min(remaining, key=lambda p: (p[0]-current[0])**2 + (p[1]-current[1])**2)
        path.append(nearest)
        remaining.remove(nearest)
    
    return path

def calculate_distance_fallback(path):
    """Fallback distance calculation"""
    if not path or len(path) < 2:
        return 0.0
    
    total = 0.0
    for i in range(len(path) - 1):
        p1, p2 = path[i], path[i+1]
        total += ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
    return total

@app.route('/api/get-data')
def get_data():
    """Return current session data"""
    if not session_data.get('file_uploaded'):
        return jsonify({
            'status': 'error',
            'msg': 'No wildfire data uploaded',
            'data': None
        }), 400
    
    return jsonify({
        'status': 'success',
        'data': session_data
    }), 200

@app.route('/api/generate-mesh', methods=['POST'])
def api_generate_mesh():
    """PHASE 4: Generate mesh from CURRENT boundary"""
    if not session_data.get('file_uploaded') or not session_data.get('boundary'):
        return jsonify({'status': 'error', 'msg': 'No boundary data'}), 400
    
    try:
        spacing = request.json.get('spacing', 10)
        boundary_tuples = [(float(p[0] if isinstance(p, (list, tuple)) else p.get('x', 0)), 
                           float(p[1] if isinstance(p, (list, tuple)) else p.get('y', 0))) 
                          for p in session_data['boundary']]
        
        # Use backend or fallback
        if generate_mesh:
            mesh = generate_mesh(boundary_tuples, spacing=spacing)
        else:
            mesh = generate_mesh_fallback(boundary_tuples, spacing=spacing)
        
        session_data['mesh'] = [[float(m[0]), float(m[1])] for m in mesh]
        
        print(f"[MESH] Generated {len(mesh)} nodes with spacing {spacing}")
        
        return jsonify({
            'status': 'success',
            'mesh_nodes': len(mesh),
            'mesh': [[float(m[0]), float(m[1])] for m in mesh]
        }), 200
        
    except Exception as e:
        print(f"[MESH ERROR] {str(e)}")
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@app.route('/api/allocate-drones', methods=['POST'])
def api_allocate_drones():
    """PHASE 5: Allocate drones to mesh nodes"""
    if not session_data.get('mesh'):
        return jsonify({'status': 'error', 'msg': 'Generate mesh first'}), 400
    
    try:
        num_drones = request.json.get('num_drones', 4)
        mesh_tuples = [(float(p[0]), float(p[1])) for p in session_data['mesh']]
        
        # Use backend or fallback
        if allocate_drones:
            allocation = allocate_drones(mesh_tuples, num_drones=num_drones)
        else:
            allocation = allocate_drones_fallback(mesh_tuples, num_drones=num_drones)
        
        session_data['drones'] = allocation
        
        print(f"[DRONES] Allocated {len(allocation)} drones")
        
        return jsonify({
            'status': 'success',
            'drones': len(allocation),
            'allocation': allocation
        }), 200
        
    except Exception as e:
        print(f"[DRONES ERROR] {str(e)}")
        return jsonify({'status': 'error', 'msg': str(e)}), 500

@app.route('/api/plan-paths', methods=['POST'])
def api_plan_paths():
    """PHASE 6: Plan optimized paths for each drone"""
    if not session_data.get('drones'):
        return jsonify({'status': 'error', 'msg': 'Allocate drones first'}), 400
    
    try:
        paths = {}
        distances = {}
        
        for drone_id, nodes in session_data['drones'].items():
            if len(nodes) == 0:
                continue
            
            # Convert to tuples for path planning
            node_tuples = [(n[0], n[1]) for n in nodes]
            
            # Generate nearest neighbor path
            if nearest_neighbor_path:
                path = nearest_neighbor_path(node_tuples)
            else:
                path = nearest_neighbor_fallback(node_tuples)
            
            # Optimize if available
            if two_opt_optimization:
                optimized_path = two_opt_optimization(path)
            else:
                optimized_path = path
            
            # Calculate distance
            if calculate_path_distance:
                distance = calculate_path_distance(optimized_path)
            else:
                distance = calculate_distance_fallback(optimized_path)
            
            paths[str(drone_id)] = [[float(p[0]), float(p[1])] for p in optimized_path]
            distances[str(drone_id)] = distance
            
            print(f"[PATH] Drone {drone_id}: {len(optimized_path)} nodes, distance {distance:.2f}")
        
        session_data['paths'] = paths
        session_data['distances'] = distances
        
        return jsonify({
            'status': 'success',
            'paths': paths,
            'distances': distances,
            'total_distance': sum(distances.values())
        }), 200
        
    except Exception as e:
        print(f"[PATH ERROR] {str(e)}")
        return jsonify({'status': 'error', 'msg': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
