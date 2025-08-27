# Autonomous Drone Navigation & Landing Simulation

## Project Overview

This project implements a **Phase 1 & Phase 2** autonomous drone system capable of navigating between waypoints using visual odometry and performing precision landing on designated landmarks without GPS. The system demonstrates advanced computer vision techniques for autonomous navigation in GPS-denied environments.

## 🎯 Phase 1: Precision Landing Prototype

**Objective**: Demonstrate precise landing capability using computer vision and visual servoing.

**Features**:
- **Enhanced ORB Feature Detection**: 2000+ features with FLANN matching for robust landmark recognition
- **Real-time Visual Servoing**: Continuous position correction during landing approach
- **Confidence-based Detection**: Adaptive thresholding for reliable landmark tracking
- **Precision Control**: Sub-pixel accuracy for landing positioning

**Technology Stack**:
- OpenCV ORB detector with enhanced parameters
- FLANN-based feature matching for performance
- RANSAC homography estimation for robust bounding box detection
- Real-time confidence scoring and adaptive thresholds

## 🚁 Phase 2: Long-Range Visual Navigation

**Objective**: Navigate between distant waypoints using visual odometry and offline map correlation.

**Features**:
- **Waypoint Navigation**: Pre-planned route following with visual waypoints
- **Enhanced Visual Odometry**: Feature-based movement estimation between frames
- **Position Drift Correction**: RANSAC-based homography for robust movement estimation
- **Seamless Mode Switching**: Automatic transition from navigation to landing mode

**Technology Stack**:
- Multi-layer navigation state machine
- FLANN-based visual odometry with confidence scoring
- Homography-based movement estimation
- Adaptive velocity control based on mission phase

## 🛠️ Enhanced Drone Physics

**Realistic Flight Characteristics**:
- Adaptive velocity control (0.5 - 5.0 pixels/frame)
- Altitude-dependent speed adjustment
- Battery simulation with realistic drain rates
- Emergency landing procedures
- Position and altitude tolerance controls

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- OpenCV 4.5+
- Pygame 2.0+
- NumPy 1.20+

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd drone_simulation

# Install dependencies
pip install -r requirements.txt

# Run tests to verify systems
python test_enhanced_systems.py

# Launch simulation
python simulation_main.py
```

### Controls
- **R**: Reset simulation
- **ESC**: Quit simulation
- **Automatic**: The drone navigates autonomously

## 📊 Simulation Interface

**Left Panel**: Real-time camera feed from drone's perspective
**Right Panel**: Processed vision data with feature matching and bounding boxes
**Bottom Panel**: Comprehensive status information including:
- Current state (Navigation/Landing/Completed)
- Position and altitude
- Velocity and battery status
- Waypoint progress
- Visual odometry data
- Real-time commands

**Performance Metrics**:
- FPS counter
- Elapsed time
- Frame count
- Visual odometry samples

## 🔧 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vision System │    │ Navigation      │    │   Drone        │
│   (Phase 1)     │◄──►│   System        │◄──►│   Physics      │
│                 │    │   (Phase 2)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Simulation Engine                            │
│              (State Machine + Rendering)                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🎮 Simulation Modes

### Navigation Mode (Phase 2)
1. **Waypoint Following**: Navigate between predefined waypoints
2. **Visual Odometry**: Track movement using feature matching
3. **Landmark Detection**: Continuously scan for landing target
4. **Mode Transition**: Switch to landing when landmark detected

### Landing Mode (Phase 1)
1. **Target Acquisition**: Lock onto detected landmark
2. **Visual Servoing**: Real-time position correction
3. **Precision Approach**: Gradual descent with continuous adjustment
4. **Touchdown**: Final positioning and landing

## 📈 Performance Features

- **60 FPS Simulation**: Smooth real-time operation
- **Adaptive Processing**: Performance-based feature detection
- **Memory Management**: Efficient visual odometry data handling
- **Error Recovery**: Robust handling of landmark loss scenarios

## 🔬 Technical Specifications

**Vision System**:
- ORB features: 2000+ per frame
- Matching confidence: 0.6+ threshold
- Processing time: <16ms per frame
- Feature tracking: 20+ matches displayed

**Navigation System**:
- Waypoint threshold: 25 pixels
- Visual odometry confidence: 0.3+ threshold
- Movement estimation: RANSAC-based homography
- State transitions: Automatic mode switching

**Drone Physics**:
- Velocity range: 0.5 - 5.0 pixels/frame
- Altitude range: 5 - 150 pixels
- Battery life: 100% to 0% simulation
- Landing precision: ±3 pixels

## 🚧 Future Enhancements (Phase 3)

- Hardware integration with real drone platforms
- Advanced SLAM algorithms for mapping
- Machine learning-based landmark recognition
- Multi-drone coordination systems
- Extended range navigation capabilities

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

This project demonstrates advanced computer vision and autonomous navigation concepts. Contributions are welcome for:
- Algorithm improvements
- Performance optimizations
- Additional simulation features
- Documentation enhancements

---

**Status**: Phase 1 & 2 Complete ✅  
**Last Updated**: August 15, 2025  
**Version**: 2.0.0
