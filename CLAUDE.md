# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python Backend
* Run Python tracker stream simulation with local mock data:
  ```bash
  python Backend/main2.py
  # Once started:
  # > start  - to begin streaming mock positions
  # > quit   - to exit
  ```
* Run tracker visualization client:
  ```bash
  python Backend/udp_client_vis.py
  ```
* Run other backend scripts:
  ```bash
  python Backend/main_vive.py
  python Backend/2d_visualize.py
  ```

### Unity Client (Standard Unity workflows)
* Unity projects in this repository are managed using the Unity Editor (specifically under `Client/CycleWalking`).
* To open the project: open the folder `Client/CycleWalking` in Unity Hub.
* **Primary scene (the only scene we care about):** `Client/CycleWalking/Assets/Scenes/IK_Scene.unity` (IK and Avatar Tracking)
  * All other scenes — `BasicScene.unity`, `SampleScene.unity`, `Demo URP.unity`, and any Hands Demo scenes — are legacy/irrelevant and should be **ignored** unless the user explicitly mentions them.

---

## High-Level Architecture & Code Structure

The repository is divided into two primary subsystems: a Python **Backend** (acting as a data source / sensor processor) and a C# Unity **Client** (handling VR locomotion and animations).

```
 ┌────────────────────────┐                  ┌─────────────────────────┐
 │     Python Backend     │                  │      Unity Client       │
 │                        │                  │                         │
 │ 1. Tracker Source      │                  │ 1. UdpReceiver          │
 │    (JSON or Vive)      │                  │    (Listens on port)    │
 │           │            │                  │            │            │
 │           ▼            │                  │            ▼            │
 │ 2. TrackerRunner (tick)│  UDP Broadcast   │ 2. BikeLocomotion       │
 │           │            │ ───────────────> │    (Speed from angle)   │
 │           ▼            │    Port 9000     │    (Calculates speed)   │
 │ 3. TrackerUdpBroadcaster                  │            │            │
 │    (Fit circle, calc   │                  │            ▼            │
 │     angle & send)      │                  │ 3. CharacterController  │
 └────────────────────────┘                  │    & Animator updates   │
                                             └─────────────────────────┘
```

### 1. Data Flow & Communication
* **Protocol**: UDP JSON packets broadcasted over port `9000` (IP: `127.0.0.1` or `255.255.255.255`).
* **Packet Schemes**:
  * **Coordinate stream** (`"type": "pos"`): `{"x": float, "y": float, "z": float, "ts": float}`
  * **Angle/velocity stream**: `{"angle_deg": float, "angular_velocity": float, "ts": float}`
  * **Calibration metadata**: Circles (`"type": "circle"`) and reference lines (`"type": "refline"`).

### 2. Python Backend (`/Backend`)
* **`tracker_source/`**: Abstractions (`abc_tracker.py`) for reading spatial data from JSON recordings (`json_tracker.py`) or hardware trackers (`vive_tracker.py`).
* **`models/broadcaster.py`**:
  * Consumes positions, calibrates circular crank trajectories in 3D using `best_fit_3d_circle`, and projects coordinates into angles.
  * Calculates delta times, angular speed differences, and sends formatted JSON payloads over UDP.
* **`utils/polar_utils.py`**: Math and fitting operations (SVD-based 3D circle fitting, centroids, YZ projection visualizations using Pygame).

### 3. Unity VR Client (`/Client/CycleWalking`)
* **`UdpReceiver.cs`**: Runs a background thread listening for network packets, decoding incoming JSON strings into `AnglePacket` objects in a thread-safe lock-based cache.
* **`BikeLocomotion.cs`**:
  * Handles VR player locomotion by scaling raw angular change over time into movement speed.
  * Dynamically re-centers the VR Rig (`CharacterController`) to sync physical bounds with headset movement while maintaining gravity constraints.
* **`AvatarFollow.cs`**:
  * Performs raycasting from the VR headset to detect step/terrain heights dynamically, updating target pelvis heights for procedural walking animations.
  * The primary script for IK-driven character follow (used in `IK_Scene`).

### Focus: Only IK_Scene matters
* **`Client/CycleWalking/Assets/Scenes/IK_Scene.unity`** is the only active scene for development.
* Scene setup: `AppCode` GameObject with `BikeLocomotion` + `UdpReceiver` + `AvatarFollow` scripts, plus `XR Origin (XR Rig)` and `Y Bot` character with Animation Rigging IK.
* **`PolarCycle.cs` (UdpCyclingLocomotion)** is associated with `BasicScene.unity` — ignore this file unless explicitly referenced.

---

## Code Quality & Implementation Patterns

* **Unity Best Practices**: Perform coordinate adjustments and character positioning in `FixedUpdate` rather than standard `Update` for physical correctness. Keep networking off the main thread (managed via `UdpReceiver` thread pool or standalone background threads) and thread-safe lock objects.
* **Python Patterns**: Utilize strict typing/abstractions for different tracker sources, and handle resource cleanup gracefully (e.g., closing UDP sockets and terminating threads via `finally` blocks).
