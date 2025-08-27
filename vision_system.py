import cv2
import numpy as np
import pygame
from typing import Dict, Any

class VisionSystem:
    def __init__(self, satellite_snapshots):
        self.satellite_snapshots = satellite_snapshots
        self.orb = cv2.ORB_create(nfeatures=2000)
        
        # Use FLANN-based matcher for better performance
        FLANN_INDEX_LSH = 6
        index_params = dict(algorithm=FLANN_INDEX_LSH, table_number=6, key_size=12, multi_probe_level=1)
        search_params = dict(checks=50)
        self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        self.waypoint_features = self._preprocess_snapshots()
        self.confidence_threshold = 0.25 # Requires a 25% match

    def _preprocess_snapshots(self):
        features = []
        for snapshot_bgr in self.satellite_snapshots:
            # The snapshots are already loaded as NumPy arrays (BGR format by cv2)
            snapshot_gray = cv2.cvtColor(snapshot_bgr, cv2.COLOR_BGR2GRAY)
            
            kp, des = self.orb.detectAndCompute(snapshot_gray, None)
            features.append({'kp': kp, 'des': des, 'img': snapshot_gray})
        print(f"Preprocessed features for {len(features)} waypoint snapshots.")
        return features

    def match_waypoint(self, camera_np, waypoint_index):
        """
        Match the drone's camera feed against a specific waypoint snapshot.

        Returns:
            (match_successful, confidence, processed_image_surface)
        """
        if waypoint_index >= len(self.waypoint_features):
            return False, 0.0, None

        # 1. Get pre-processed features for the target waypoint
        target_features = self.waypoint_features[waypoint_index]
        kp_target, des_target = target_features['kp'], target_features['des']

        if des_target is None:
            return False, 0.0, None

        # 2. Process the live camera feed
        # The input `camera_np` is already a BGR numpy array from simulation_main
        camera_gray = cv2.cvtColor(camera_np, cv2.COLOR_BGR2GRAY)
        kp_camera, des_camera = self.orb.detectAndCompute(camera_gray, None)

        if des_camera is None:
            return False, 0.0, None

        # 3. Match features using KNN and apply Lowe's ratio test
        matches = self.matcher.knnMatch(des_target, des_camera, k=2)

        good_matches = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

        # 4. Calculate confidence
        # 4. Calculate confidence based on the number of good matches
        num_good_matches = len(good_matches)
        total_target_kp = len(kp_target)
        confidence = (num_good_matches / 100) if total_target_kp > 0 else 0.0 # Normalize against a baseline of 100 good matches

        match_successful = confidence >= self.confidence_threshold

        # 5. Create visualization
        match_visualization = self._draw_matches(target_features['img'], kp_target, camera_gray, kp_camera, good_matches, match_successful)
        
        # Convert back to Pygame surface
        match_visualization_rgb = cv2.cvtColor(match_visualization, cv2.COLOR_BGR2RGB)
        processed_surface = pygame.surfarray.make_surface(match_visualization_rgb.transpose([1, 0, 2]))

        return match_successful, confidence, processed_surface

    def _draw_matches(self, img1, kp1, img2, kp2, matches, success):
        """Draws the feature matches for visualization."""
        h, w = img1.shape
        vis = np.zeros((h, w * 2, 3), np.uint8)
        vis[:h, :w, 0] = img1
        vis[:h, :w, 1] = img1
        vis[:h, :w, 2] = img1
        vis[:h, w:, 0] = img2
        vis[:h, w:, 1] = img2
        vis[:h, w:, 2] = img2

        for m in matches:
            pt1 = (int(kp1[m.queryIdx].pt[0]), int(kp1[m.queryIdx].pt[1]))
            pt2 = (int(kp2[m.trainIdx].pt[0] + w), int(kp2[m.trainIdx].pt[1]))
            color = (0, 255, 0) if success else (0, 0, 255)
            cv2.line(vis, pt1, pt2, color, 1)

        return vis