# Project Title: A Simulation Framework for GPS-Denied Drone Navigation and Precision Landing Using Visual Landmark Recognition

### **1. Introduction**

The proliferation of autonomous unmanned aerial vehicles (UAVs), or drones, has opened up new possibilities in fields ranging from logistics and agriculture to search and rescue. However, the reliability of these systems is often critically dependent on the availability and accuracy of the Global Positioning System (GPS). In many real-world scenarios—such as urban canyons, indoor environments, or situations involving signal jamming—GPS can be unreliable or entirely unavailable. This limitation presents a significant challenge to true autonomy.

This project addresses the problem of GPS-denied navigation by developing a simulation framework for a drone that can navigate a pre-planned route and execute a precision landing by relying on what it "sees" rather than on absolute positioning data. It leverages computer vision techniques to visually recognize waypoints, mimicking a human's ability to correlate a map with the real world. The system is designed in two phases: Phase 1 focuses on the core challenge of precision landing via visual confirmation, while Phase 2 integrates this capability into a long-range navigation mission.

The entire system is built using a technology stack of Python, OpenCV for computer vision processing, Pygame for the simulation engine and visualization, and a Flask-based web interface for user-friendly mission planning.

### **2. System Architecture**

The project is logically divided into two main subsystems: the **Route Planner** and the **Simulation Engine**.

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Web-Based Route │      │  Asset Generation  │      │  Simulation      │
│  Planner (Flask) │────►│  Pipeline (ArcGIS) │────►│  Engine (Pygame) │
└──────────────────┘      └──────────────────┘      └──────────────────┘
                                                          │
                                                          ▼
          ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
          │   Vision System │    │ Navigation      │    │   Drone         │
          │   (OpenCV)      │◄──►│   System        │◄──►│   Physics       │
          └─────────────────┘    └─────────────────┘    └─────────────────┘
```

**2.1. Route Planning & Asset Generation**
The user initiates a mission through a web-based interface powered by Flask and Leaflet.js. The user graphically defines a series of waypoints on an interactive map. Upon mission launch, the system executes an automated asset generation pipeline:
1.  **Ground-Truth Map:** It sends a request to the ArcGIS Image Server REST API to download a single, high-resolution satellite map covering the entire mission area. This map serves as the foundational "world" for the simulation.
2.  **Waypoint Snapshots:** For each destination waypoint, it downloads a separate, highly-detailed 500x500 pixel snapshot of a 100x100 meter area centered on the waypoint's coordinates. These snapshots are the reference "photos" the drone will use for visual verification.

**2.2. Simulation Engine**
The core of the project is a Pygame application that orchestrates the simulation, comprised of several key modules:
*   **Drone Physics (`drone.py`):** Manages the drone's state machine (e.g., `TAKING_OFF`, `NAVIGATING`, `SEARCHING`, `LANDING`), physical properties (position, altitude, heading, battery), and behavioral logic, such as executing a spiral search pattern.
*   **Environment (`environment.py`):** Generates the drone's live camera feed by cropping and scaling the high-resolution ground-truth map based on the drone's current simulated position and altitude. This creates a realistic top-down visual feed.
*   **Navigation System (`navigation.py`):** Provides basic guidance by calculating the bearing and distance from the drone's current simulated coordinates to the next target waypoint. It acts as an idealized, non-visual guidance system.
*   **Vision System (`vision_system.py`):** The intelligence of the project. It is responsible for the visual verification process that allows the drone to operate without relying on GPS for confirmation.

### **3. Methodology**

The project's methodology integrates geospatial data processing, simulated physics, and state-of-the-art computer vision algorithms.

**3.1. Mission Planning**
The process begins with the user defining a route in the `index.html` interface. A JavaScript front-end captures the latitude and longitude of each point, uses the Nominatim API for reverse-geocoding to get place names, and sends the complete route to the Flask back-end.

**3.2. Visual Verification: The Core of GPS-Denied Navigation**
When the drone's navigation system guides it to the vicinity of a waypoint, it enters a `HOVERING` state and initiates a visual verification protocol. This process is a classic implementation of **feature-based image matching**.

1.  **Feature Detection and Description (ORB):** The system does not compare the live feed and the snapshot pixel-for-pixel. Instead, it uses the **ORB (Oriented FAST and Rotated BRIEF)** algorithm from the OpenCV library. ORB is an efficient and robust feature detector that identifies thousands of unique points of interest (keypoints) in an image, such as corners and distinct patterns. For each keypoint, it generates a numerical "descriptor" that represents its unique characteristics. This is performed on both the live camera feed and the target waypoint snapshot. ORB is chosen for its high speed and its invariance to rotation and scale, making it ideal for this task.

2.  **Feature Matching (FLANN):** With two sets of feature descriptors in hand, the system uses the **FLANN (Fast Library for Approximate Nearest Neighbors)** based matcher. For every feature in the target snapshot, FLANN efficiently finds the most similar-looking feature in the live camera feed.

3.  **Match Filtering (Lowe's Ratio Test):** To ensure high-quality matches, the results from FLANN are filtered using the ratio test. A match is considered valid only if it is significantly better than the second-best alternative. This discards ambiguous matches and dramatically increases the reliability of the verification.

4.  **Confidence Scoring & Decision:** The system calculates a confidence score based on the number of high-quality matches found.
    *   If this score exceeds a predefined threshold (`0.25`), the waypoint is considered visually confirmed. The drone has achieved a "visual handshake" and proceeds to the next waypoint.
    *   If the score is too low, the verification fails. The drone concludes it is not in the correct location and transitions to a `SEARCHING` state, flying in an expanding spiral to find the target.

### **4. Detailed File & Component Description**

*   **`app.py`**: A Flask web server that acts as the primary entry point. It serves the web UI, receives the user-defined route, orchestrates the asset generation pipeline (calling `generate_snapshots.py`), verifies that assets were created, and launches the main simulation as a subprocess.
*   **`generate_snapshots.py`**: A utility script that takes the `route.json` file, calculates a 100x100m bounding box around each destination waypoint, and downloads a 500x500px satellite image from the ArcGIS REST API for each one.
*   **`index.html`, `style.css`, `script.js`**: The frontend code for the web-based route planner, using Leaflet.js to provide an interactive map.
*   **`simulation_main.py`**: The main simulation file. It initializes Pygame, loads all assets (maps, snapshots), creates instances of the Drone, NavigationSystem, and VisionSystem, and contains the main loop that updates and renders the simulation state every frame.
*   **`drone.py`**: Defines the `Drone` class. It contains the `DroneState` enum and all logic for the drone's movement, physics, state transitions, and battery simulation.
*   **`environment.py`**: Defines the `Environment` class. Its primary role is to generate the drone's camera view by cropping the main ground-truth map, effectively simulating the drone's camera.
*   **`navigation.py`**: Defines the `NavigationSystem` class, which manages the list of waypoints and provides the drone with the bearing and distance to its next target.
*   **`vision_system.py`**: Defines the `VisionSystem` class. It encapsulates all computer vision logic, including initializing the ORB detector, preprocessing snapshots to extract features, and the `match_waypoint` method that performs the core verification logic.
*   **`requirements.txt`**: Lists all Python package dependencies for the project.
*   **`route.json`**: A data file that acts as the interface between the route planner and the simulation engine, storing the list of waypoints for the current mission.
*   **`map_meta.json`**: Stores the geographic bounding box of the main ground-truth map, used by the `Environment` to correctly map coordinates to pixels.
*   **`drone.png`**: The icon image used to represent the drone in the simulation.

### **5. References**

*   **ORB Algorithm:** Rublee, E., Rabaud, V., Konolige, K., & Bradski, G. (2011). *ORB: An efficient alternative to SIFT or SURF*. In IEEE International Conference on Computer Vision (ICCV).
*   **Lowe's Ratio Test:** Lowe, D. G. (2004). *Distinctive Image Features from Scale-Invariant Keypoints*. International Journal of Computer Vision, 60(2), 91-110. (The ratio test is a key component of the SIFT algorithm, but is widely used for all descriptor-based matching).
*   **OpenCV:** Bradski, G. (2000). *The OpenCV Library*. Dr. Dobb's Journal of Software Tools.
*   **ArcGIS Image Server REST API:** The service used for acquiring satellite imagery.
*   **Pygame, Flask, Leaflet.js, Geopy, Nominatim:** Key libraries and services used for building the application and handling geospatial data.