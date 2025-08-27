from flask import Flask, request, jsonify, send_from_directory, render_template
import json
import subprocess
import os
import sys
import shutil
from geopy.distance import distance as geopy_distance
from geopy.point import Point
import requests
from generate_snapshots import generate_snapshots

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def script():
    return send_from_directory('.', 'script.js')

@app.route('/run_simulation', methods=['POST'])
def run_simulation():
    waypoints = request.json
    
    if not waypoints or len(waypoints) < 2:
        return jsonify({"message": "Route requires at least a start and a destination."}), 400

    with open('route.json', 'w') as f:
        json.dump(waypoints, f, indent=4)

    # --- Generate Ground Truth Map ---
    print("\n--- Generating Satellite Ground Truth Map ---")
    drone_feed_path = os.path.join("assets", "drone_feed.png")
    # Ensure the assets directory exists before writing the image
    os.makedirs(os.path.dirname(drone_feed_path), exist_ok=True)
    try:
        buffer = 0.001
        route_min_lat = min(wp['lat'] for wp in waypoints) - buffer
        route_max_lat = max(wp['lat'] for wp in waypoints) + buffer
        route_min_lon = min(wp['lon'] for wp in waypoints) - buffer
        route_max_lon = max(wp['lon'] for wp in waypoints) + buffer

        route_bbox = f"{route_min_lon},{route_min_lat},{route_max_lon},{route_max_lat}"
        width = 1500
        height = int(width * (route_max_lat - route_min_lat) / (route_max_lon - route_min_lon))

        params = {
            'bbox': route_bbox, 'bboxSR': 4326, 'size': f'{width},{height}',
            'imageSR': 4326, 'format': 'png', 'transparent': 'false', 'f': 'image'
        }
        IMAGERY_URL = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
        response = requests.get(IMAGERY_URL, params=params, timeout=30)
        response.raise_for_status()

        with open(drone_feed_path, 'wb') as f:
            f.write(response.content)
        print(f" -> Saved satellite ground truth map to {drone_feed_path}")

        map_meta = {'bbox': [route_min_lon, route_min_lat, route_max_lon, route_max_lat]}
        with open('map_meta.json', 'w') as f:
            json.dump(map_meta, f)
        print(" -> Saved map metadata to map_meta.json")

    except requests.exceptions.RequestException as e:
        print(f"\n--- Ground Truth Map Generation Failed ---")
        print(f"Could not fetch satellite map: {e}")
        return jsonify({"message": f"Failed to generate ground truth map: {e}"}), 500

    # --- Generate Satellite Snapshots ---
    generate_snapshots()

    # --- VERIFY ASSET GENERATION ---
    print("\n--- Verifying Required Assets ---")
    satellite_snapshot_dir = os.path.join("assets", "waypoint_snapshots")
    expected_snapshots = len(waypoints) - 1
    
    # Check for ground truth map
    if not os.path.exists(drone_feed_path) or os.path.getsize(drone_feed_path) == 0:
        error_msg = "Verification Failed: Ground truth map (drone_feed.png) was not created. The selected route may be invalid."
        print(f"ERROR: {error_msg}")
        return jsonify({"message": error_msg}), 500

    # Check for waypoint snapshots
    if not os.path.exists(satellite_snapshot_dir) or len(os.listdir(satellite_snapshot_dir)) != expected_snapshots:
        error_msg = f"Verification Failed: Expected {expected_snapshots} waypoint snapshots, but found {len(os.listdir(satellite_snapshot_dir))}. Try a different route."
        print(f"ERROR: {error_msg}")
        return jsonify({"message": error_msg}), 500
    
    print(" -> Asset verification successful.")

    # --- Launch Simulation ---
    print("\n--- Launching Simulation ---")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        simulation_main_path = os.path.join(script_dir, "simulation_main.py")
        subprocess.run([sys.executable, simulation_main_path], cwd=script_dir, check=True)
        return jsonify({"message": "Simulation started successfully!"})
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"Error launching simulation: {e}")
        return jsonify({"message": f"Failed to start simulation: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)