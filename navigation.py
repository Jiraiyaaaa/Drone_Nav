# navigation.py - Geographic Navigation System

import math
from typing import List, Tuple, Optional, Dict
from geopy.distance import geodesic


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the initial bearing (in degrees) from point 1 to point 2.
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dLon = lon2_rad - lon1_rad

    y = math.sin(dLon) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dLon))

    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)

    return (bearing_deg + 360) % 360 # Normalize to 0-360


class NavigationSystem:
    def __init__(self, waypoints: List[Dict[str, any]]):
        """
        Initialize the navigation system with a list of geographic waypoints.
        Each waypoint is a dict with 'name', 'lat', 'lon'.
        """
        self.waypoints = waypoints
        self.current_waypoint_idx = 1
        self.reached_destination = False if len(self.waypoints) > 1 else True
        self.waypoint_threshold = 5  # meters
        self.distance_to_wp = None
        self.bearing_to_wp = None
        
        if self.waypoints:
            print(f"Navigation system initialized with {len(self.waypoints)} waypoints.")
        else:
            print("Navigation system initialized with no waypoints.")

    def update(self, current_lat: float, current_lon: float):
        """Update navigation logic, called each frame."""
        if self.reached_destination or not self.waypoints:
            self.distance_to_wp = None
            self.bearing_to_wp = None
            return

        target_wp = self.waypoints[self.current_waypoint_idx]
        target_pos = (target_wp['lat'], target_wp['lon'])
        current_pos = (current_lat, current_lon)

        self.distance_to_wp = geodesic(current_pos, target_pos).meters
        self.bearing_to_wp = calculate_bearing(current_lat, current_lon, target_pos[0], target_pos[1])

    def advance_waypoint(self):
        if not self.reached_destination:
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.waypoints):
                self.reached_destination = True
                print("Final waypoint reached.")
            else:
                waypoint_name = self.waypoints[self.current_waypoint_idx]['name']
                print(f"Advanced to next waypoint: {waypoint_name}")
        else:
            self.reached_destination = True
            print("Reached final waypoint!")

    def set_new_route(self, new_waypoints: List[Dict[str, any]]):
        """Sets a new route for the drone, resetting the navigation state."""
        self.waypoints = new_waypoints
        self.current_waypoint_idx = 0
        self.reached_destination = False
        print(f"New route set with {len(self.waypoints)} waypoints.")

    def get_current_waypoint_index(self) -> int:
        return self.current_waypoint_idx

    def is_final_waypoint(self):
        """Check if the current waypoint is the last one on the route."""
        return self.current_waypoint_idx == len(self.waypoints) - 1

    def reset(self):
        """Reset the navigation state."""
        self.current_waypoint_idx = 0
        self.reached_destination = False
        self.visited_waypoints = set()
        print("Navigation system has been reset.")
