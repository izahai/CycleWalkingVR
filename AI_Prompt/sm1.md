Here's a summary of everything we've built so far. You're essentially creating a **minimal VR avatar prototype** before adding full-body IK.

---

# Current Architecture

```text
XR Origin (XR Rig)
├── Camera Offset
│   ├── Main Camera (HMD)
│   ├── Left Controller
│   └── Right Controller
│
└── Locomotion
```

Separately:

```text
Y Bot
├── Animator
├── AvatarFollow
└── Mesh
```

The avatar is **not** parented to the camera or controllers.

---

# What we learned

### ❌ Don't parent Y Bot to the Main Camera

Although the Main Camera moves with your headset, parenting the avatar to it causes:

* body rotates when you look around
* body crouches when you crouch
* body leans with your head

This is not how VR avatars work.

---

### Why XR Origin wasn't working

You discovered that

* XR Origin transform does **not** change
* Main Camera transform **does** change

So the prototype follows the headset instead.

Later, once locomotion is finalized, the avatar will follow the player rig instead.

---

# AvatarFollow script

Current responsibilities:

* Follow headset position on XZ
* Keep feet on the floor (fixed Y)
* Rotate toward headset yaw
* Compute movement speed
* Drive Animator Speed parameter
* Adjust animator playback speed

This is a temporary solution before IK.

---

# Animator setup

Created

```text
Player.controller
```

Inside it:

```text
Entry
   │
   ▼
Blend Tree
```

---

## Blend Tree

Parameter

```text
Speed (float)
```

Motions

```text
Idle
Threshold = 0

Walk
Threshold = 1
```

The script updates

```csharp
animator.SetFloat("Speed", normalizedSpeed);
```

Unity blends automatically.

---

# Animation Import

Animations are imported as

```text
Humanoid
```

using

```text
Copy From Other Avatar
```

where

```text
Source Avatar
```

is the Y Bot avatar.

This allows Mixamo animations to work correctly.

---

# Floating feet issue

We determined this is **not** an IK problem.

Possible causes:

* root transform offset
* idle animation root settings
* model pivot

IK is **not** needed yet.

---

# Animator speed

Instead of hardcoding

```csharp
animator.speed = 2f;
```

we exposed Inspector variables:

```text
Idle Animator Speed

Walk Animator Speed
```

Now they can be tuned live.

---

# Current prototype

Current pipeline:

```text
Headset moves
        │
        ▼
AvatarFollow
        │
        ▼
Move avatar
        │
        ▼
Compute speed
        │
        ▼
Animator Speed parameter
        │
        ▼
Blend Tree
        │
        ▼
Idle ↔ Walk
```

---

# What is NOT implemented yet

No IK

```text
Head
Left Hand
Right Hand
Feet
```

are still driven only by the animation.

---

No hand tracking

Controllers are not connected to the avatar.

---

No body tracking

The avatar simply follows the headset.

---

No foot planting

Feet will slide slightly because movement and animation aren't fully synchronized.

---

# Next milestones

### Phase 1 ✅ (Current)

* XR locomotion works
* Avatar follows player
* Idle animation
* Walk animation
* Blend Tree
* Speed parameter
* Adjustable animation speed

---

### Phase 2

Instead of using

```text
headset.position
```

to determine movement speed,

use the **left joystick movement vector** from the XR locomotion system.

Benefits:

* Looking around doesn't trigger walking.
* Walking animation matches player intent.
* Closer to VRChat behavior.

---

### Phase 3

Implement **full-body IK**:

* Head target → Main Camera
* Left hand target → Left Controller
* Right hand target → Right Controller

The IK solver drives the spine, arms, and legs.

---

### Phase 4

Replace the simple follow logic with a true avatar root:

```text
XR Origin
        │
        ▼
Player Root
        │
        ▼
IK Solver
        │
        ▼
Y Bot
```

The avatar root follows the player's locomotion, while IK aligns the body with the headset and controllers.

---

## Current Goal

At this point, you have a solid prototype that proves the basic animation pipeline. The next meaningful improvement is to **replace headset-based speed detection with joystick-based locomotion**, so the walk animation is driven by player input rather than physical head movement. That will make the behavior much closer to games like VRChat before you start integrating full-body IK.
