import json
import os
import requests
import cv2
import numpy as np
from geopy.distance import distance as geopy_distance
from geopy.point import Point

def generate_snapshots():
    """Loads route from route.json and fetches satellite snapshots for each waypoint."""
    print("--- Generating Waypoint Snapshots ---")

    try:
        with open('route.json', 'r') as f:
            waypoints = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not load or parse route.json: {e}")
        return

    if not waypoints or len(waypoints) < 2:
        print("Warning: Route requires at least two points (a start and a destination). No snapshots to generate.")
        return

    print("\n--- Acquiring True Color Satellite Imagery via REST API ---")
    try:
        satellite_snapshot_dir = os.path.join("assets", "waypoint_snapshots")
        os.makedirs(satellite_snapshot_dir, exist_ok=True)

        for f in os.listdir(satellite_snapshot_dir):
            os.remove(os.path.join(satellite_snapshot_dir, f))
        print(f"Cleared existing snapshots in {satellite_snapshot_dir}")

        IMAGERY_URL = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"

        print(f"\nINFO: The first waypoint is the drone's start position and does not require a snapshot.")
        print(f"      Generating snapshots for the remaining {len(waypoints) - 1} destination waypoints...")

        for i, wp in enumerate(waypoints[1:], start=1):
            lat, lon, name = wp['lat'], wp['lon'], wp['name']
            print(f"Fetching satellite image for waypoint {i}: {name}")

            center_point = Point(latitude=lat, longitude=lon)
            dist_m = 50
            north = geopy_distance(meters=dist_m).destination(center_point, 0)
            east = geopy_distance(meters=dist_m).destination(center_point, 90)
            south = geopy_distance(meters=dist_m).destination(center_point, 180)
            west = geopy_distance(meters=dist_m).destination(center_point, 270)
            
            bbox = f"{west.longitude},{south.latitude},{east.longitude},{north.latitude}"

            params = {
                'bbox': bbox,
                'bboxSR': 4326,
                'size': '500,500',
                'imageSR': 4326,
                'format': 'png',
                'transparent': 'false',
                'f': 'image'
            }

            response = requests.get(IMAGERY_URL, params=params)
            response.raise_for_status()

            # --- Image Validation ---
            try:
                image_array = np.frombuffer(response.content, np.uint8)
                img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                if img is None:
                    raise ValueError("OpenCV could not decode the image. It might be invalid or corrupted.")
                
                h, w, _ = img.shape
                if h < 100 or w < 100:
                    raise ValueError(f"Image is too small ({w}x{h}). It might be an error image from the API.")

            except Exception as e:
                print(f" !! Validation failed for waypoint {i} ({name}): {e}")
                print(f" !! The downloaded content might be an error message instead of a map image.")
                print(f" !! Skipping this snapshot.")
                continue
            # --- End Validation ---

            snapshot_filename = os.path.join(satellite_snapshot_dir, f"waypoint_{i-1}_{name.replace(' ', '_')}.png")
            with open(snapshot_filename, 'wb') as f:
                f.write(response.content)
            print(f" -> Saved satellite snapshot to {snapshot_filename}")

        num_generated = len(os.listdir(satellite_snapshot_dir))
        print(f"\n--- Snapshot generation complete! ---")
        print(f" -> Generated {num_generated} snapshots for {len(waypoints)} total waypoints.")

    except requests.exceptions.RequestException as e:
        print(f"\n--- ArcGIS Satellite Imagery Failed ---")
        print(f"Could not fetch satellite images: {e}")
        print("Please check your internet connection.")

if __name__ == '__main__':
    generate_snapshots()
