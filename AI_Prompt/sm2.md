That changes the architecture significantly, and I actually think it's a better research direction. Your avatar is **not** trying to mimic VRChat. Instead, you're building a **VR locomotion research platform** where locomotion is driven by an external physical device (pedals) instead of a joystick.

The animation should therefore be synchronized with **physical pedaling cadence**, not controller input.

---

# Research Goal

Develop a **VR locomotion system driven by pedal cycling hardware** that provides natural locomotion and believable avatar animation, with a particular focus on realistic stair climbing.

The architecture becomes:

```text
Pedal Hardware
        │
        ▼
UDP Broadcast
        │
        ▼
Unity UDP Receiver
        │
        ▼
Locomotion Controller
        │
        ├──────────────► Move Player
        │
        ├──────────────► Avatar Animation
        │
        └──────────────► Research Metrics
```

Everything should originate from the pedal hardware.

---

# Current Progress

## ✅ XR Environment

* XR Origin configured
* Continuous locomotion available
* VR headset tracking working
* Controllers tracked correctly

---

## ✅ Avatar

* Imported Mixamo Y Bot
* Configured as Humanoid
* Animator attached
* AvatarFollow prototype created

Current implementation simply follows the headset as a temporary solution.

---

## ✅ Animation

Created

```
Player.controller
```

Using

```
Blend Tree
```

Parameter

```
Speed
```

Animations

```
Idle
Walk
```

Animation playback speed is adjustable.

---

## ✅ Basic Animation Synchronization

The animator currently computes speed from

```
Headset Position
```

This is **temporary**.

Ultimately it will use

```
Pedal Speed
```

instead.

---

# Updated Final Architecture

Instead of

```
Headset Movement
        │
        ▼
Animation Speed
```

the final architecture becomes

```
Pedal RPM
        │
        ▼
Normalize
        │
        ├────────► Player Velocity
        │
        ├────────► Blend Tree Speed
        │
        ├────────► Animator Playback Speed
        │
        └────────► Step Frequency
```

This keeps

* player movement
* animation
* locomotion

all synchronized from the same physical input.

---

# Recommended Milestones

## Milestone 1 — Stable Avatar Prototype ✅ (Almost Complete)

* XR project setup
* Humanoid avatar
* Blend Tree
* Idle ↔ Walk
* Avatar follows player
* Animation playback adjustable

Goal:

> Verify the complete animation pipeline before integrating hardware.

---

## Milestone 2 — UDP Hardware Integration

Receive

```
Pedal RPM
```

through UDP.

Expose values such as

```
RPM
Cadence
Direction
Resistance (optional)
```

Verify packet timing.

Goal:

Reliable communication between hardware and Unity.

---

## Milestone 3 — Pedal-Driven Locomotion

Replace

```
Headset speed
```

with

```
Pedal cadence
```

Pipeline:

```
UDP
    ↓
RPM
    ↓
Player velocity
    ↓
Character movement
```

No joystick required.

---

## Milestone 4 — Pedal-Driven Animation

Instead of

```csharp
Speed = headset velocity;
```

use

```text
Speed = normalized pedal cadence
```

Also drive

```
Animator.speed
```

from cadence.

Now the walking cycle matches the user's pedaling rhythm.

---

## Milestone 5 — Stair Climbing Prototype

Introduce

```
Terrain Slope
```

or

```
Stair Geometry
```

Map

```
Pedal cadence
+
Elevation
```

to

```
Walking animation
```

Eventually transition to

```
Walk
↔
Climb Stairs
```

using another Blend Tree or additional animation layer.

---

## Milestone 6 — Full-Body IK

Only after locomotion is stable.

Drive

```
Head
```

from

```
HMD
```

Drive

```
Hands
```

from

```
Controllers
```

Use IK to adjust

```
Spine
Hips
Feet
```

The animation now becomes procedural rather than purely authored.

---

## Milestone 7 — Procedural Foot Placement

This is essential for believable stairs.

Implement

```
Raycast
```

↓

```
Detect Stair Height
```

↓

```
Adjust Foot Target
```

↓

```
IK places foot
```

This prevents floating or penetrating steps.

---

## Milestone 8 — Research Evaluation

Collect synchronized data from the locomotion system:

* Pedal cadence (RPM)
* Avatar speed
* Head velocity
* Controller trajectories
* Stair ascent/descent times
* Packet latency and jitter
* User comfort measures (e.g., questionnaires)
* Presence/immersion ratings
* Motion sickness indicators

These measurements will let you quantitatively evaluate how well the pedal-driven locomotion maps to virtual movement and whether realistic animation improves the user experience.

---

# Final Target System

```text
Pedal Hardware
        │
        ▼
UDP Receiver
        │
        ▼
Cadence Filter / Normalization
        │
        ├────────► Player Locomotion
        │
        ├────────► Blend Tree Parameters
        │
        ├────────► Animator Playback Speed
        │
        ├────────► Stair Detection
        │                 │
        │                 ▼
        │           Stair Climb Blend
        │
        └────────► Full-Body IK
                          │
                          ▼
                   Head, Hands, Feet
```

One suggestion based on your research objective: avoid tightly coupling the UDP receiver to the avatar. A cleaner design is to separate the system into independent modules—**UDP Input → Locomotion Controller → Animation Controller → IK Controller**. That way, you can later swap the pedal hardware for another input device or compare multiple locomotion methods in your experiments without rewriting the animation or IK systems. This modular structure will also make your research implementation easier to extend and evaluate.
