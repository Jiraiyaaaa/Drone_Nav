import pygame
import sys
import json
from environment import Environment
from drone import Drone, DroneState
from navigation import NavigationSystem
from vision_system import VisionSystem
import os
import cv2

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
MAP_WIDTH, MAP_HEIGHT = 1200, 900
INFO_PANEL_WIDTH = SCREEN_WIDTH - MAP_WIDTH
ROUTE_FILE = 'route.json'
MAP_SNAPSHOT_FILE = 'map_snapshot.png'

# --- Load Route from File ---
def load_route():
    try:
        with open(ROUTE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# --- Initialization ---
WAYPOINTS = load_route()
if not WAYPOINTS:
    print("Error: Could not load route.json. Please plan a route first.")
    sys.exit()

# --- Constants and Screen Setup ---
SCREEN_WIDTH = 1600  # Increased width for a better layout
SCREEN_HEIGHT = 900
DRONE_VIEW_WIDTH = 1100
INFO_PANEL_WIDTH = SCREEN_WIDTH - DRONE_VIEW_WIDTH  # 500px

# Info panel sections
ROUTE_OVERVIEW_HEIGHT = 350
WAYPOINT_VIEW_HEIGHT = 250
STATUS_PANEL_HEIGHT = SCREEN_HEIGHT - ROUTE_OVERVIEW_HEIGHT - WAYPOINT_VIEW_HEIGHT

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Drone Simulation")

font_small = pygame.font.SysFont('Arial', 16)
font_large = pygame.font.SysFont('Arial', 22, bold=True)

# --- Load Route and Environment ---
print("Loading route and environment...")
with open('route.json', 'r') as f:
    waypoints = json.load(f)
    start_pos = (waypoints[0]['lat'], waypoints[0]['lon'])

# Load the new satellite ground truth map
ground_truth_map_path = os.path.join("assets", "drone_feed.png")
if os.path.exists(ground_truth_map_path):
    print(f"Loading ground truth map from {ground_truth_map_path}")
    ground_truth_map = pygame.image.load(ground_truth_map_path).convert()
else:
    print(f"Error: Ground truth map not found at {ground_truth_map_path}")
    # As a fallback, create a black surface
    ground_truth_map = pygame.Surface((1500, 1000))
    ground_truth_map.fill((0, 0, 0))

# Load satellite waypoint snapshots for the vision system
satellite_snapshot_dir = os.path.join("assets", "waypoint_snapshots")
satellite_snapshots = []
if os.path.exists(satellite_snapshot_dir):
    snapshot_files = sorted(os.listdir(satellite_snapshot_dir))
    for filename in snapshot_files:
        if filename.endswith(".png"):
            try:
                img = cv2.imread(os.path.join(satellite_snapshot_dir, filename))
                satellite_snapshots.append(img)
            except Exception as e:
                print(f"Could not load satellite snapshot {filename}: {e}")
print(f"Loaded {len(satellite_snapshots)} satellite waypoint snapshots for CV.")

# Also load snapshots as Pygame surfaces for UI display
ui_satellite_snapshots = []
if os.path.exists(satellite_snapshot_dir):
    snapshot_files = sorted(os.listdir(satellite_snapshot_dir))
    for filename in snapshot_files:
        if filename.endswith(".png"):
            try:
                img_path = os.path.join(satellite_snapshot_dir, filename)
                ui_img = pygame.image.load(img_path).convert()
                ui_satellite_snapshots.append(ui_img)
            except Exception as e:
                print(f"Could not load UI snapshot {filename}: {e}")

env = Environment(waypoints, ground_truth_map)
map_surface = env.get_map_surface() # This now just returns the loaded map
map_rect = map_surface.get_rect()

screen_width, screen_height = 1600, 900 # Increased width for new panels
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Drone Simulation - Visual Navigation")

font_small = pygame.font.SysFont("Arial", 16)
font_large = pygame.font.SysFont("Arial", 22, bold=True)

# Load and resize the drone icon before the main loop
drone_icon = pygame.image.load('drone.png').convert_alpha() # Use convert_alpha for transparency
drone_icon = pygame.transform.scale(drone_icon, (50, 50)) # Resize to a suitable size

clock = pygame.time.Clock()

# --- Objects ---
drone = Drone(start_pos_lat_lon=start_pos, start_alt=10.0)
nav_system = NavigationSystem(waypoints)
vision_system = VisionSystem(satellite_snapshots)

# Create scaled-down version of the overview map
route_overview_map = pygame.transform.smoothscale(ground_truth_map, (INFO_PANEL_WIDTH, ROUTE_OVERVIEW_HEIGHT))

def draw_status_text(screen, font_small, font_large, drone, nav_system, panel_pos):
    x_offset, y_offset = panel_pos[0] + 15, panel_pos[1] + 15
    line_height = 28

    # Drone State
    state_text = f"{drone.state.name}"
    state_surface = font_large.render(state_text, True, (255, 255, 0))
    screen.blit(state_surface, (x_offset, y_offset))
    y_offset += 40

    # Position and Altitude
    lat, lon, alt = drone.lat, drone.lon, drone.altitude
    pos_text = f"Lat: {lat:.5f}, Lon: {lon:.5f}"
    screen.blit(font_small.render(pos_text, True, (255, 255, 255)), (x_offset, y_offset))
    y_offset += line_height
    screen.blit(font_small.render(f"Altitude: {alt:.1f} m", True, (255, 255, 255)), (x_offset, y_offset))
    y_offset += line_height
    screen.blit(font_small.render(f"Heading: {drone.heading:.1f}", True, (255, 255, 255)), (x_offset, y_offset))
    y_offset += line_height

    # Navigation Info
    dist_to_wp = nav_system.distance_to_wp
    if dist_to_wp is not None:
        dist_text = f"Dist to WP: {dist_to_wp:.1f} m"
        screen.blit(font_small.render(dist_text, True, (255, 255, 255)), (x_offset, y_offset))
        y_offset += line_height

    # Match Confidence
    confidence_text = f"Match Confidence: {last_match_confidence:.2f}"
    screen.blit(font_small.render(confidence_text, True, (255, 255, 255)), (x_offset, y_offset))
    y_offset += line_height

    # Navigation
    y_offset += 10
    screen.blit(font_large.render("NAVIGATION", True, (255, 255, 255)), (x_offset, y_offset))
    y_offset += 30
    screen.blit(font_small.render(f"Next Waypoint: {nav_system.get_current_waypoint_index()}", True, (255, 255, 255)), (x_offset, y_offset))
    if nav_system.distance_to_wp is not None and nav_system.bearing_to_wp is not None:
        screen.blit(font_small.render(f"Distance: {nav_system.distance_to_wp:.1f} m | Bearing: {nav_system.bearing_to_wp:.1f}", True, (255, 255, 255)), (x_offset, y_offset + line_height))

def draw_route_on_overview(screen, env, nav_system, waypoints, drone, panel_x_offset, map_rect):
    # Draw route line and waypoints on overview
    if drone.state == DroneState.RETURN_HOME:
        home_pos = drone.start_pos_lat_lon
        home_x, home_y = env.latlon_to_screen(home_pos[0], home_pos[1])
        overview_home_x = int((home_x / map_rect.width) * INFO_PANEL_WIDTH) + panel_x_offset
        overview_home_y = int((home_y / map_rect.height) * ROUTE_OVERVIEW_HEIGHT)
        
        drone_ov_x, drone_ov_y = env.latlon_to_screen(drone.lat, drone.lon)
        drone_overview_x = int((drone_ov_x / map_rect.width) * INFO_PANEL_WIDTH) + panel_x_offset
        drone_overview_y = int((drone_ov_y / map_rect.height) * ROUTE_OVERVIEW_HEIGHT)

        pygame.draw.line(screen, (0, 255, 255), (drone_overview_x, drone_overview_y), (overview_home_x, overview_home_y), 3)
    else:
        route_points = []
        for wp in waypoints:
            wp_x, wp_y = env.latlon_to_screen(wp['lat'], wp['lon'])
            overview_x = int((wp_x / map_rect.width) * INFO_PANEL_WIDTH) + panel_x_offset
            overview_y = int((wp_y / map_rect.height) * ROUTE_OVERVIEW_HEIGHT)
            route_points.append((overview_x, overview_y))

        if len(route_points) > 1:
            pygame.draw.lines(screen, (255, 255, 0), False, route_points, 2)

        for i, point in enumerate(route_points):
            wp_color = (0, 255, 0) if i < nav_system.get_current_waypoint_index() else (255, 0, 0)
            pygame.draw.circle(screen, wp_color, point, 5)

    # Draw drone on overview
    drone_ov_x, drone_ov_y = env.latlon_to_screen(drone.lat, drone.lon)
    drone_overview_x = int((drone_ov_x / map_rect.width) * INFO_PANEL_WIDTH) + panel_x_offset
    drone_overview_y = int((drone_ov_y / map_rect.height) * ROUTE_OVERVIEW_HEIGHT)
    pygame.draw.circle(screen, (0, 255, 255), (drone_overview_x, drone_overview_y), 6)

# --- State for Vision System ---
match_attempted = False
last_match_confidence = 0.0

# Timer for periodic matching during search
last_search_match_time = 0
SEARCH_MATCH_INTERVAL = 0.5  # seconds

# --- Main Loop ---
running = True
while running:
    dt = clock.tick(30) / 1000.0 # Delta time in seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Update Simulation State ---
    nav_system.update(drone.lat, drone.lon)
    drone.update(dt, nav_system)

    # --- Drawing --- #
    screen.fill((20, 20, 30)) # Dark blue-grey background

    # 1. Main View: Top-down map centered on the drone
    # Calculate the top-left corner of the map section to blit
    drone_map_x, drone_map_y = env.latlon_to_screen(drone.lat, drone.lon)
    view_x = drone_map_x - DRONE_VIEW_WIDTH / 2
    view_y = drone_map_y - SCREEN_HEIGHT / 2

    # Blit the relevant part of the full map
    screen.blit(map_surface, (0, 0), (view_x, view_y, DRONE_VIEW_WIDTH, SCREEN_HEIGHT))

    # Draw the route on the main view, relative to the drone's position
    if drone.state != DroneState.RETURN_HOME:
        route_points = []
        for wp in waypoints:
            wp_x, wp_y = env.latlon_to_screen(wp['lat'], wp['lon'])
            view_wp_x = wp_x - view_x
            view_wp_y = wp_y - view_y
            route_points.append((view_wp_x, view_wp_y))

        if len(route_points) > 1:
            pygame.draw.lines(screen, (255, 255, 0), False, route_points, 3)

        for i, point in enumerate(route_points):
            wp_color = (0, 255, 0) if i < nav_system.get_current_waypoint_index() else (255, 0, 0)
            pygame.draw.circle(screen, wp_color, point, 8)
            pygame.draw.circle(screen, (255, 255, 255), point, 8, 1)

    # Draw drone icon in the center of the view
    rotated_drone = pygame.transform.rotate(drone_icon, -drone.heading)
    drone_rect = rotated_drone.get_rect(center=(DRONE_VIEW_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(rotated_drone, drone_rect.topleft)

    # --- Vision System Logic (uses a snapshot from the map as camera feed) ---
    # Always get the drone's camera view for UI display
    snapshot_size = 500
    crop_rect = pygame.Rect(0, 0, snapshot_size, snapshot_size)
    crop_rect.center = (DRONE_VIEW_WIDTH // 2, SCREEN_HEIGHT // 2)
    live_drone_view_surface = screen.subsurface(crop_rect).copy()

    # We can attempt a match if hovering, or periodically if searching
    current_time = pygame.time.get_ticks() / 1000.0
    should_attempt_match = False

    if drone.state == DroneState.HOVERING and not match_attempted:
        should_attempt_match = True
        match_attempted = True # Prevent re-matching in the same hover state
    elif drone.state == DroneState.SEARCHING:
        if current_time - last_search_match_time > SEARCH_MATCH_INTERVAL:
            should_attempt_match = True
            last_search_match_time = current_time

    if should_attempt_match:
        if drone.state == DroneState.HOVERING:
             print("Attempting to match waypoint...")

        current_waypoint_idx = nav_system.get_current_waypoint_index()
        view_np = pygame.surfarray.array3d(live_drone_view_surface)
        view_np = cv2.transpose(view_np)
        view_np = cv2.cvtColor(view_np, cv2.COLOR_RGB2BGR)

        snapshot_idx_to_match = current_waypoint_idx - 1
        match_successful, confidence, _ = vision_system.match_waypoint(view_np, snapshot_idx_to_match)
        last_match_confidence = confidence

        if match_successful:
            print(f"Match found during {drone.state.name}! Confidence: {confidence:.2f}")
            drone.confirm_match()
        elif drone.state == DroneState.HOVERING:
            print(f"Match failed. Confidence: {confidence:.2f}. Initiating search.")
            drone.state = DroneState.SEARCHING

    if drone.state != DroneState.HOVERING:
        match_attempted = False

    # --- Info Panel Drawing (Right Side) ---
    info_panel_x = DRONE_VIEW_WIDTH
    
    # A. Route Overview Panel
    screen.blit(route_overview_map, (info_panel_x, 0))
    draw_route_on_overview(screen, env, nav_system, waypoints, drone, info_panel_x, map_rect)

    # B. Waypoint Snapshot Panel
    waypoint_panel_y = ROUTE_OVERVIEW_HEIGHT
    pygame.draw.rect(screen, (30, 30, 40), (info_panel_x, waypoint_panel_y, INFO_PANEL_WIDTH, WAYPOINT_VIEW_HEIGHT))
    
    # Split the panel into two for side-by-side view
    half_panel_width = INFO_PANEL_WIDTH // 2
    img_size = (half_panel_width - 15, WAYPOINT_VIEW_HEIGHT - 40)

    # Draw Target Waypoint Snapshot
    target_wp_idx = nav_system.get_current_waypoint_index() - 1
    if 0 <= target_wp_idx < len(ui_satellite_snapshots):
        snapshot_img = ui_satellite_snapshots[target_wp_idx]
        scaled_snapshot = pygame.transform.smoothscale(snapshot_img, img_size)
        screen.blit(scaled_snapshot, (info_panel_x + 10, waypoint_panel_y + 30))
        screen.blit(font_small.render("Target Waypoint", True, (255,255,255)), (info_panel_x + 10, waypoint_panel_y + 5))

    # Draw Live Drone Camera View
    scaled_live_view = pygame.transform.smoothscale(live_drone_view_surface, img_size)
    screen.blit(scaled_live_view, (info_panel_x + half_panel_width + 5, waypoint_panel_y + 30))
    screen.blit(font_small.render("Live Drone View", True, (255,255,255)), (info_panel_x + half_panel_width + 5, waypoint_panel_y + 5))
        
    # C. Status Info Panel
    status_panel_y = ROUTE_OVERVIEW_HEIGHT + WAYPOINT_VIEW_HEIGHT
    pygame.draw.rect(screen, (10, 10, 20), (info_panel_x, status_panel_y, INFO_PANEL_WIDTH, STATUS_PANEL_HEIGHT))
    draw_status_text(screen, font_small, font_large, drone, nav_system, (info_panel_x, status_panel_y))

    pygame.display.flip()

# --- Cleanup ---
pygame.quit()
sys.exit()