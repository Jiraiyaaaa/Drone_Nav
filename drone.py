# drone.py - Enhanced Drone Physics and Control with Geographic Coordinates

import pygame
import math
from typing import Tuple, Optional
from geopy.distance import geodesic
from geopy.point import Point
from enum import Enum, auto
from navigation import calculate_bearing
import time

class DroneState(Enum):
    IDLE = 0
    TAKING_OFF = 1
    NAVIGATING = 2
    HOVERING = 3
    SEARCHING = 4
    MATCH_FOUND = 5
    RETURN_HOME = 6
    LANDING = 7
    LANDED = 8

class Drone:
    def __init__(self, start_pos_lat_lon: Tuple[float, float], start_alt: float):
        """
        Initialize the drone's state with geographic coordinates.
        
        Args:
            start_pos_lat_lon: Tuple of (latitude, longitude) starting position.
            start_alt: Starting altitude in meters.
        """
        self.start_pos_lat_lon = start_pos_lat_lon # Home position
        self.lat, self.lon = start_pos_lat_lon
        self.z = 0  # Start at ground level
        self.cruise_altitude = start_alt # The target altitude for navigation

        # Movement parameters
        self.velocity = 15.0  # m/s
        self.search_velocity = 5.0 # m/s, slower speed for precise search
        self.ascent_speed = 5.0  # m/s
        self.descent_speed = 1.5  # m/s
        self.landing_altitude = 10  # Altitude to trigger final landing stage

        # Flight characteristics
        self.heading = 0  # Bearing in degrees
        self.battery = 100.0
        self.battery_drain_rate = 0.01  # Per second

        # State machine for drone behavior
        self.state = DroneState.TAKING_OFF
        self.hover_start_time = None
        self.match_found_time = None

        # Search state parameters
        self.search_start_time = 0
        self.max_search_radius = 20.0  # meters
        self.search_angle = 0
        self.search_center_lat = 0
        self.search_center_lon = 0
        self.total_search_time = 0 # Total time spent in search for a single waypoint

        print(f"Drone initialized at: (Lat: {self.lat:.4f}, Lon: {self.lon:.4f}). State: {self.state.name}")

    def set_bearing(self, bearing: float):
        """
        Set the drone's heading/bearing.
        Args:
            bearing: The new heading in degrees.
        """
        self.heading = bearing

    def update(self, dt: float, nav_system):
        """Main update method for the drone, called each frame."""
        if self.state == DroneState.LANDED:
            return

        # --- State Logic ---
        if self.state == DroneState.TAKING_OFF:
            self.altitude += self.ascent_speed * dt
            if self.altitude >= self.cruise_altitude:
                self.altitude = self.cruise_altitude
                self.state = DroneState.NAVIGATING
                print(f"Cruise altitude reached. State changed to: {self.state.name}")
        
        elif self.state == DroneState.NAVIGATING:
            if nav_system.reached_destination:
                # This case should be handled after a successful match of the last waypoint.
                # The drone will transition to RETURN_HOME in the MATCH_FOUND state.
                pass
            else:
                if nav_system.bearing_to_wp is not None:
                    self.heading = nav_system.bearing_to_wp
                distance_to_wp = nav_system.distance_to_wp

                # Braking logic: slow down when close to the waypoint
                braking_distance = 30 # meters
                if distance_to_wp < braking_distance:
                    # Scale velocity linearly from max speed down to a minimum speed
                    min_velocity = 3.0
                    speed_ratio = max(0, distance_to_wp / braking_distance)
                    current_velocity = min_velocity + (self.velocity - min_velocity) * speed_ratio
                else:
                    current_velocity = self.velocity

                distance_this_frame = current_velocity * dt
                distance_moved = min(distance_this_frame, distance_to_wp) if distance_to_wp is not None else distance_this_frame

                if distance_moved > 0:
                    start_point = Point(self.lat, self.lon)
                    destination = geodesic(meters=distance_moved).destination(start_point, self.heading)
                    self.lat, self.lon = destination.latitude, destination.longitude

                if nav_system.distance_to_wp is not None and nav_system.distance_to_wp < nav_system.waypoint_threshold:
                    self.state = DroneState.HOVERING
                    print(f"Arrived at waypoint {nav_system.get_current_waypoint_index()}. State changed to: HOVERING")

        elif self.state == DroneState.HOVERING:
            # Hover for a short duration to stabilize for image matching
            if time.time() - self.hover_start_time > 2: # Hover for 2 seconds
                # The simulation_main loop will attempt a match and change the state.
                # If it doesn't, we'll be stuck here. This is intentional.
                pass

        elif self.state == DroneState.SEARCHING:
            self.total_search_time += dt # Increment total search time

            # Execute a spiral search pattern
            if self.search_start_time == 0: # Initialize search
                self.search_start_time = time.time()
                self.search_radius = 5 # Start with a 5m radius
                self.search_angle = 0
                self.search_center_lat, self.search_center_lon = self.lat, self.lon

            # Spiral out over time
            time_in_search = time.time() - self.search_start_time
            if self.search_radius < self.max_search_radius:
                self.search_radius += 1 * dt # Expand radius at 1 m/s
            self.search_angle += 60 * dt # Rotate at 60 deg/s

            # Calculate new position on the spiral
            search_center_point = Point(self.search_center_lat, self.search_center_lon)
            destination = geodesic(meters=self.search_radius).destination(search_center_point, self.search_angle)
            
            # Create a mini-navigation goal to the next point on the spiral
            target_lat, target_lon = destination.latitude, destination.longitude
            bearing_to_target = calculate_bearing(self.lat, self.lon, target_lat, target_lon)
            self.heading = bearing_to_target

            distance_this_frame = self.search_velocity * dt
            start_point = Point(self.lat, self.lon)
            new_pos = geodesic(meters=distance_this_frame).destination(start_point, self.heading)
            self.lat, self.lon = new_pos.latitude, new_pos.longitude

            # After a few seconds, return to HOVERING to re-attempt the match
            if time_in_search > 5:
                print("Search segment complete. Returning to HOVERING to re-attempt match.")
                self.state = DroneState.HOVERING
                self.hover_start_time = time.time()
                self.search_start_time = 0 # Reset timer for the next search segment
                return

            # Failsafe: if searching for too long, abort and return to home base
            if self.total_search_time > 30: # Max 30 seconds of total searching for a single waypoint
                print("!! SEARCH FAILED: Could not find waypoint after extensive search.")
                print("!! Aborting mission and returning to start point.")
                self.state = DroneState.RETURN_HOME
                # The navigation system is configured to handle the return journey
                home_waypoint = {'name': 'Home', 'lat': self.start_pos_lat_lon[0], 'lon': self.start_pos_lat_lon[1]}
                nav_system.set_new_route([home_waypoint])
                self.total_search_time = 0 # Reset search timer

        elif self.state == DroneState.MATCH_FOUND:
            # Briefly pause to signify a successful match, then continue
            if time.time() - self.match_found_time > 1: # Pause for 1 second
                if nav_system.is_final_waypoint():
                    print("Final waypoint confirmed. Initiating landing.")
                    self.initiate_landing()
                else:
                    nav_system.advance_waypoint()
                    self.state = DroneState.NAVIGATING

        elif self.state == DroneState.RETURN_HOME:
            if nav_system.reached_destination:
                self.initiate_landing()
            else:
                # Standard navigation logic, but towards home
                if nav_system.bearing_to_wp is not None:
                    self.heading = nav_system.bearing_to_wp
                distance_to_wp = nav_system.distance_to_wp
                distance_this_frame = self.velocity * dt
                distance_moved = min(distance_this_frame, distance_to_wp) if distance_to_wp is not None else distance_this_frame

                if distance_moved > 0:
                    start_point = Point(self.lat, self.lon)
                    destination = geodesic(meters=distance_moved).destination(start_point, self.heading)
                    self.lat, self.lon = destination.latitude, destination.longitude

        elif self.state == DroneState.LANDING:
            self.altitude -= self.descent_speed * dt
            if self.altitude <= 0.1:
                self.altitude = 0
                self.state = DroneState.LANDED
                self.velocity = 0
                print("DRONE HAS LANDED SUCCESSFULLY!")

        # --- Physics & Battery ---
        self.altitude = max(0, self.altitude)
        self.battery = max(0, self.battery - (self.battery_drain_rate * dt))
            
    def get_battery_status(self):
        """Return the current battery level and status."""
        if self.battery > 50:
            return self.battery, "OK"
        elif self.battery > 20:
            return self.battery, "LOW"
        else:
            return self.battery, "CRITICAL"
            
    @property
    def altitude(self):
        return self.z

    @altitude.setter
    def altitude(self, value):
        self.z = value

    def get_position(self) -> Tuple[float, float]:
        """Return the current position as a tuple (lat, lon)."""
        return (self.lat, self.lon)
        
    def get_status(self) -> dict:
        """Get comprehensive drone status."""
        battery_level, battery_status = self.get_battery_status()
        
        return {
            "position": (self.lat, self.lon, self.z),
            "heading": self.heading,
            "velocity": self.velocity,
            "battery": battery_level,
            "battery_status": battery_status,
            "state": self.state,
        }
    
    def initiate_landing(self):
        """Begin the landing sequence."""
        if self.state != DroneState.LANDING:
            self.state = DroneState.LANDING
            print(f"Landing sequence initiated. State changed to: {self.state.name}")

    def confirm_match(self):
        self.state = DroneState.MATCH_FOUND
        self.match_found_time = time.time()
        self.search_start_time = 0 # Reset search parameters
        self.total_search_time = 0 # Reset total search time

    def reset_position(self, new_pos_lat_lon: Tuple[float, float], new_alt: float):
        """Reset drone position (for testing)."""
        self.lat, self.lon = new_pos_lat_lon
        self.z = 0 # Start at ground
        self.cruise_altitude = new_alt
        self.state = "TAKING_OFF" # Reset to initial state
        self.velocity = 15.0
        self.battery = 100.0
        print(f"Drone position reset to: (Lat: {self.lat:.4f}, Lon: {self.lon:.4f}), Alt: {self.z}m")

    def draw(self, surface: pygame.Surface):
        """Draw the drone on the screen."""
        # In the new system, the drone is always at the center of the camera view.
        screen_width, screen_height = surface.get_size()
        center_x, center_y = screen_width // 2, screen_height // 2
        
        # Draw drone body
        pygame.draw.circle(surface, (255, 255, 0), (center_x, center_y), 8)
        
        # Draw heading indicator (0=N, 90=E, 180=S, 270=W)
        # Pygame's y-axis is inverted, and 0 degrees is to the right.
        # We need to convert from bearing (0=N) to pygame angle (0=E).
        # Angle in Pygame = -Bearing + 90
        pygame_angle_rad = math.radians(-self.heading + 90)
        
        line_end_x = center_x + 12 * math.cos(pygame_angle_rad)
        line_end_y = center_y - 12 * math.sin(pygame_angle_rad)
        pygame.draw.line(surface, (255, 0, 0), (center_x, center_y), (int(line_end_x), int(line_end_y)), 3)
