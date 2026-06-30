Yes, I actually think that's the right engineering approach, and it reduces risk significantly.

The key is to separate **locomotion control** from **animation quality**. Your research contribution is the pedal-driven locomotion, but if you try to solve hardware integration, networking, locomotion, animation, IK, and stair placement all at the same time, debugging becomes very difficult.

I'd structure it like this:

## Phase 1 – Animation Prototype (Joystick)

Ignore the pedals completely.

```
Joystick
      ↓
Desired Walking Speed
      ↓
Animation Controller
      ↓
Blend Tree
      ↓
IK
      ↓
Foot Placement
```

Your objective is to answer questions like:

* Does the stair-climbing animation look believable?
* Does the foot land exactly on each step?
* Does the pelvis move naturally?
* Does the body lean correctly when ascending?
* Does IK improve realism?

If something looks wrong, you immediately know it's an animation/IK problem, not a UDP or hardware problem.

---

## Phase 2 – Replace the Input

Once you're satisfied with the animation pipeline, swap only the input source:

```
Joystick Speed
        ↓
Animation Controller
```

becomes

```
Pedal Cadence
        ↓
Animation Controller
```

Everything downstream stays the same.

This is a sign of a good architecture: the animation system shouldn't care whether the speed came from a joystick, pedals, or even AI.

---

# I'd actually divide your project into four independent modules

```
Input Layer
──────────────
Joystick
Pedals (UDP)
Keyboard

        │

Movement Layer
──────────────
Desired speed
Desired direction

        │

Animation Layer
──────────────
Idle
Walk
Run
Stair Up
Stair Down

        │

IK Layer
──────────────
Head
Hands
Feet
Pelvis
```

Notice the IK layer never knows where the movement came from.

---

# The part I think deserves the most time

From what you've described, **the most difficult problem is not receiving UDP packets.**

It's this:

```
Stair Geometry
        │
        ▼
Where should the next foot land?
        │
        ▼
Move pelvis
        │
        ▼
Solve both legs
        │
        ▼
Maintain balance
```

That's where most VR locomotion projects struggle.

---

# I would even postpone full-body IK

Instead, I'd implement in this order:

### Milestone 1 ✅

Idle

Walk

Blend Tree

(Already done.)

---

### Milestone 2

Walk on flat ground

Joystick only

No stairs

No IK

Goal:

> Perfect walk cycle.

---

### Milestone 3

Create a proper stair-climbing animation.

Just animation.

No IK.

```
Idle

Walk

Climb Stairs
```

---

### Milestone 4 ⭐

Foot Placement

This is where research starts becoming interesting.

```
Raycast

↓

Detect stair height

↓

Place foot exactly on tread
```

The animation remains mostly unchanged.

IK simply adjusts the final pose.

---

### Milestone 5 ⭐⭐⭐

Pelvis compensation

When one foot climbs onto a higher step,

the hips should rise naturally.

This is the biggest difference between an amateur implementation and a convincing one.

---

### Milestone 6

Hand IK

Head IK

Spine IK

Now the body follows the HMD and controllers.

---

### Milestone 7

Replace joystick

↓

UDP pedal cadence

Done.

---

# One suggestion that could strengthen your research

If your goal is a publication or thesis, avoid making the contribution "pedals move the avatar." Instead, frame it around **adaptive locomotion driven by pedal cadence and terrain**.

For example:

```
Pedal RPM
        │
        ▼
Desired Velocity
        │
Terrain Analysis
        │
        ▼
Adaptive Gait Selection
        │
        ▼
Walk
Jog
Stair Up
Stair Down
```

In this design, the system doesn't just play a fixed climbing animation. It **selects and adjusts the gait** based on both the user's pedaling cadence and the environment. That opens the door to research questions about synchronization, realism, and user comfort that go beyond simply replacing a joystick with pedals.

I think you're making the right call by focusing on the animation and IK first. If the movement looks natural with a joystick, then replacing the joystick's speed signal with pedal cadence becomes a relatively small integration task rather than another source of uncertainty.
