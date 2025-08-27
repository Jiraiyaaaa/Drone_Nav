# environment.py - Dynamic, Tile-Based Environment (Offline)

import pygame
import math
import os
import json
from typing import Tuple, List
from geo_utils import deg2num, num2deg, get_parent_tile

class Environment:
    def __init__(self, waypoints, ground_truth_map):
        """
        Initialize the tile-based environment for offline use.
        """
        self.waypoints = waypoints
        self.map_meta = self._load_map_meta()
        self.tile_size = 256
        self.map_surface = ground_truth_map # Use the pre-rendered satellite map
        self.map_rect = self.map_surface.get_rect()

    def _load_map_meta(self):
        try:
            with open('map_meta.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Warning: map_meta.json not found or invalid. Using default values.")
            # Fallback values if meta file is missing
            return {
                'bbox': [-1.0, 51.0, 0.0, 52.0] # Default bbox
            }

    def get_camera_view(self, drone_lat: float, drone_lon: float, zoom: int, altitude: float, camera_size: Tuple[int, int]) -> pygame.Surface:
        """
        Generate the camera view by cropping the pre-rendered ground truth map.
        The view is scaled based on the drone's altitude.
        """
        cam_width, cam_height = camera_size
        
        # Determine the crop area on the full map based on drone's lat/lon
        center_x, center_y = self.latlon_to_screen(drone_lat, drone_lon)

        # Dynamic zoom based on altitude for takeoff and landing.
        # The idea is to change the size of the area we crop from the main map.
        # A smaller crop area scaled up to the camera size gives a zoom-in effect.
        # A larger crop area scaled down gives a zoom-out effect.

        # Define cruise altitude and max zoom level.
        cruise_altitude = 100.0
        max_zoom_factor = 10.0 # At altitude 0, the view is 10x zoomed in.

        if altitude >= cruise_altitude:
            # At or above cruise altitude, maintain a standard view.
            scale_factor = 1.0
        else:
            # From ground to cruise altitude, interpolate the zoom factor.
            # As altitude increases, zoom factor decreases from max_zoom_factor to 1.0.
            zoom_progress = altitude / cruise_altitude
            scale_factor = max_zoom_factor - (zoom_progress * (max_zoom_factor - 1.0))
        
        # A larger scale_factor means a smaller crop area (zoom in).
        crop_width = cam_width / scale_factor
        crop_height = cam_height / scale_factor

        # Define the source rectangle for the crop
        crop_rect = pygame.Rect(
            center_x - crop_width / 2,
            center_y - crop_height / 2,
            crop_width,
            crop_height
        )

        # Clip the crop_rect to ensure it's entirely within the map's boundaries.
        # .clip() will adjust both position and size to fit.
        clipped_rect = crop_rect.clip(self.map_rect)

        # Create a subsurface from the main map using the safe, clipped rectangle.
        # Using a subsurface is efficient as it doesn't copy pixel data.
        cropped_surface = self.map_surface.subsurface(clipped_rect)

        # Scale the cropped view to fit the camera panel
        camera_view = pygame.transform.smoothscale(cropped_surface, camera_size)
        
        # Add vignette effect at low altitude
        if altitude < 60:
            vignette_alpha = int(150 * (1 - (altitude / 60)))
            vignette = pygame.Surface(camera_size, pygame.SRCALPHA)
            pygame.draw.rect(vignette, (0,0,0,vignette_alpha), vignette.get_rect())
            center_ellipse_rect = vignette.get_rect().inflate(-vignette.get_width()*0.2, -vignette.get_height()*0.2)
            pygame.draw.ellipse(vignette, (0,0,0,0), center_ellipse_rect)
            camera_view.blit(vignette,(0,0))

        return camera_view

    def latlon_to_screen(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        Convert latitude and longitude to screen coordinates on the ground truth map.
        """
        # Bounding box of the map in lat/lon
        min_lon, min_lat, max_lon, max_lat = self.map_meta['bbox']

        # Map dimensions in pixels
        map_width, map_height = self.map_surface.get_size()

        # Handle potential division by zero if bbox is a point
        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat
        if lon_range == 0 or lat_range == 0:
            return map_width // 2, map_height // 2

        # Simple linear interpolation
        screen_x = ((lon - min_lon) / lon_range) * map_width
        # For latitude, the mapping is inverted (higher lat is lower y)
        screen_y = ((max_lat - lat) / lat_range) * map_height

        return int(screen_x), int(screen_y)

    def get_map_surface(self):
        return self.map_surface

    def screen_to_latlon(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """
        Convert screen coordinates on the ground truth map to latitude and longitude.
        """
        min_lon, min_lat, max_lon, max_lat = self.map_meta['bbox']
        map_width, map_height = self.map_surface.get_size()

        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat

        if map_width == 0 or map_height == 0:
            return 0.0, 0.0

        # Inverse of the linear interpolation in latlon_to_screen
        lon_percent = screen_x / map_width
        lat_percent = screen_y / map_height

        lon = min_lon + (lon_percent * lon_range)
        lat = max_lat - (lat_percent * lat_range) # Inverted mapping for latitude

        return lat, lon