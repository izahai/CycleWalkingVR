# Project Milestones — Procedural Stair-Climbing Locomotion

## Ultimate Goal

**Fully procedural, code-computed stair-climbing animation** for the Y Bot character in VR — with zero dependency on Mixamo stair animations. Every movement (foot lift, foot plant, pelvis rise, weight shift, balance) is computed mathematically from raycasts, pedal cadence, and biomechanical constraints.

The character must walk up stairs with **natural foot-to-foot orchestration**: the left foot lands precisely on a stair tread, weight transfers to it, the right foot lifts and lands on the next tread, all while the pelvis rises in a smooth, biologically plausible trajectory. No sliding. No clipping. No snapping.

---

## Architecture (Four Independent Layers)

```
Input Layer           Movement Layer        Animation Layer         IK Layer
───────────           ──────────────        ────────────────        ────────
Joystick (test)  →    Desired Speed    →    Blend Tree         →   Head IK
Pedals (UDP)          Desired Direction     Idle ↔ Walk             Hand IK
                                         ↓   Stair Detect           Foot IK
                                         ↓   Gait Select            Pelvis IK
                                         ↓   Step Orchestrator      Spine IK
```

The IK Layer never knows where the movement came from. This separation lets us develop animation quality independently of hardware integration.

---

## What We Have Done

### ✅ M1: Prototype Foundation (Complete)
- XR project setup (URP, OpenXR, XR Interaction Toolkit 3.3.1)
- Mixamo Y Bot imported as Humanoid with full `mixamorig:` skeleton
- `WalkingAnimator.controller` with 1D Blend Tree (Idle ↔ Walk)
- `AvatarFollow.cs`: headset-driven avatar positioning with dynamic raycast-based Y height
- `BikeLocomotion.cs`: pedal-angle-driven CharacterController movement via UDP
- `UdpReceiver.cs`: background-thread UDP listener (port 9000)

### ✅ M2: Animation Rigging IK Infrastructure (Complete)
- `Assets/Editor/YBotIKSetup.cs` — **Tools > YBot > Setup IK Rig** one-click setup
- `Y Bot Unpack.prefab` modified: `RigBuilder`, `FootRig`/`Rig`, `TwoBoneIKConstraint` × 2
- Leg chains wired: LeftUpLeg→LeftLeg→LeftFoot and RightUpLeg→RightLeg→RightFoot
- `LeftTarget` / `RightTarget` transforms positioned at neutral foot positions for runtime override
- `LeftHint` / `RightHint` transforms for knee-bend direction control
- `WalkingAnimator.controller`: **IK Pass enabled**, **Slope float parameter added**
- `BoneRenderer` component added for skeleton debug visualization
- Documentation: `Docs/IK_Rig_Setup.md`

### ✅ M3: Project Focus Defined (Complete)
- `IK_Scene.unity` designated as the only active scene
- `CLAUDE.md` updated to reflect IK_Scene focus; `BasicScene`, `PolarCycle.cs` marked as legacy
- `Docs/CurrentState.md` created (this file)

---

## Future Milestones

> **Key principle:** Walking up stairs is not about one foot moving. It is the **orchestration between two feet**, with **pelvis position and center of mass** driving the natural feel. Every milestone below must account for two-foot coordination and pelvic compensation.

---

### 🔲 M4: Single-Foot IK Lift onto First Stair (NEXT — MVP)

**Success criteria:** Run the game. The character approaches a single stair step. The right foot lifts, swings forward, and lands precisely on the stair tread — positioned by raycast hit point. The left foot remains on the ground. The pelvis rises slightly to accommodate the higher right foot. No popping. No penetration.

**What to build:**

1. **`FootPlacementDriver.cs`** — a new MonoBehaviour that:
   - Finds `LeftTarget` / `RightTarget` / `LeftHint` / `RightHint` by path from the Y Bot root
   - Casts two raycasts downward each frame: one from the **current animated foot position offset slightly forward**, one from **ahead of the character** (predictive)
   - **Determines which foot is in "swing phase" vs "stance phase"** by detecting the Y-velocity of the animated foot bone (when the Mixamo animation lifts the foot, `footTransform.position.y` rises; when it plants, it plateaus). This is the **no-Mixamo-stair-animation** approach — we read the Walk cycle's foot states and override the landing positions.
   - During swing phase: IK weight → 0 (let the Walk animation swing the leg naturally)
   - During stance phase: IK weight → 1 (snap foot to raycast hit point)
   - Handles the **first stair step** case: when the forward raycast detects a step higher than the current ground, set that as the upcoming foot target

2. **IK weight blending per foot** — each foot has independent IK activation:
   ```
   Left foot in swing  → LeftTwoBoneIK.weight  = 0.0
   Left foot in stance → LeftTwoBoneIK.weight  = 1.0
   Right foot in swing → RightTwoBoneIK.weight = 0.0
   Right foot in stance → RightTwoBoneIK.weight = 1.0
   ```

3. **Scene setup in `IK_Scene.unity`:**
   - Place one `LongStair` or a single-step Cube in front of the Y Bot
   - Set the step's Layer to `Ground` (or a layer included in the `groundLayer` mask)
   - Attach `FootPlacementDriver.cs` to Y Bot alongside the existing `AvatarFollow`

**Deliverable:** Video showing the right foot lifting onto a single stair step while the left foot stays grounded.

---

### 🔲 M5: Two-Foot Step Orchestration

**Success criteria:** The character walks up 2-3 consecutive stairs. Left foot steps up. Weight shifts. Right foot steps up to the next tread. No sliding — each foot plants exactly once per step. The rhythm is natural: swing-plant-swing-plant.

**What to build:**

1. **Step state machine per foot:**
   ```
   SWING  → foot lifts, IK off, animate freely
   PLANT  → foot lands, IK on, snap to raycast hit
   STANCE → foot holds position, body moves forward over planted foot
   ```

2. **Weight-transfer detection:** When one foot plants on a higher step, compute the pelvis target height as the **weighted average of left and right foot heights** (favoring the stance foot during its support phase).

3. **Step detection refinement** — don't just use foot Y-velocity. Add a **step-trigger zone**: when the animated foot's XZ position crosses ahead of a certain threshold (e.g., `stepLookAhead` from `AvatarFollow`), and the animation is in its "foot down" phase, fire the IK snap.

4. **Prevent double-plant:** Once a foot has planted on a stair tread, lock its target position until the animation enters a new swing phase. This prevents the foot from vibrating between heights.

**Deliverable:** Video showing two feet alternating naturally across 3 stair steps.

---

### 🔲 M6: Pelvis & Center of Mass — Natural Body Rise ⭐

**Success criteria:** The character's pelvis rises smoothly as it climbs. When both feet are on different step heights, the pelvis tilts and translates naturally — not snapping, but moving with inertia and biological weight shift. The upper body leans slightly forward (as humans do when climbing stairs). The center of mass projection stays within the support polygon of the planted foot/feet.

**What to build:**

1. **Pelvis height tracking** — the pelvis Y should follow the **weighted blend** of left and right foot target heights:
   ```csharp
   float targetPelvisY = (leftFootTarget.y * leftWeight + rightFootTarget.y * rightWeight)
                        + basePelvisOffset;
   ```
   Where `leftWeight` / `rightWeight` reflect which foot is in stance (1.0 when planted, tapering during swing).

2. **Pelvis tilt** — when one foot is higher than the other (mid-stride on stairs), tilt the pelvis bone slightly around the Z-axis to reflect the natural hip drop. Use `Mathf.SmoothDamp` for all transitions.

3. **Center of Mass projection** — compute the CoM as a point between the hips and spine. Raycast downward from CoM. Ensure it falls within the **convex hull of planted feet**. If it drifts outside, apply a corrective hip shift.

4. **Forward lean** — blend the upper spine rotation toward `Quaternion.Euler(-5f, 0, 0)` as slope increases, ramping from 0° on flat to ~8-10° on steep stairs.

5. **Integrate with `AvatarFollow.cs`** — replace the current headset-based `targetPelvisHeight` with the computed pelvis height from foot targets. The headset still drives XZ position and yaw rotation.

**Deliverable:** Video showing the Y Bot's body rising naturally — hips, spine, and subtle forward lean — across a staircase. No stiff bolt-upright posture.

---

### 🔲 M7: Smooth Foot Roll & Rotation

**Success criteria:** When a foot lands on a stair tread, it rotates to match the surface normal (flat stairs → flat foot; sloped surface → foot angled). The foot "rolls" from heel-strike to toe-off during the stance phase.

**What to build:**

1. **Foot rotation from surface normal** — set `LeftTarget` / `RightTarget` rotation to match `Quaternion.FromToRotation(Vector3.up, hit.normal)` during the plant phase. Blend smoothly.

2. **Heel-to-toe roll** — during the stance phase, interpolate the target position from the heel contact point to the ball-of-foot contact point as the character moves forward. This creates the natural roll-through feeling.

3. **Stair edge detection** — raycast detects when the foot is near the edge of a stair tread. Add a small forward offset to prevent the heel from hanging off.

---

### 🔲 M8: Stair Descent (Downward)

**Success criteria:** The character walks down stairs with the same quality as up. Foot reaches down to lower tread. Pelvis lowers smoothly. No "falling" or sudden drops.

**What to build:**

1. **Descending detection** — when forward raycast finds a step *lower* than current foot height, the system switches to descent mode.

2. **Downward step reach** — the foot target searches further below during descent. IK chain stretches to reach down (handled naturally by TwoBoneIK).

3. **Pelvis descent compensation** — descend the pelvis smoothly before the foot reaches the lower step, so the character doesn't "drop" onto the descending foot.

---

### 🔲 M9: Variable Step Heights & Mixed Terrain

**Success criteria:** The system handles stairs of varying heights (4cm to 25cm), sloped ramps, and transitions between flat ground and stairs. The gait adapts — small steps = subtle foot lift, large steps = exaggerated lift.

**What to build:**

1. **Dynamic step height** — adjust swing height based on detected stair height. Bigger step → lift foot higher during swing (move IK target position + hint upward during swing phase).

2. **Flat-to-stair transition** — detect the moment the forward raycast first hits a stair riser. Smoothly transition from flat-walk IK offset to stair-climb IK offset.

3. **Ramp handling** — when surface normal is sloped but continuous (no discrete step), keep IK weight at 1 and slide the target along the slope.

---

### 🔲 M10: Pedal-Cadence Synchronization

**Success criteria:** The step tempo matches the pedaling cadence. Faster pedaling → faster step cycle → faster stair ascent. Slower pedaling → deliberate steps. The walk animation playback speed is derived from pedal RPM.

**What to build:**

1. **Cadence-to-step-frequency mapping** — map `UdpReceiver` angle packet rate to `Animator.speed` and step-orchestrator timing parameters.

2. **Synchronization verification** — ensure foot plant events align with pedal crank position (e.g., right pedal down ≈ right foot plant).

3. **Replace joystick input** — remove any joystick-based speed from the locomotion pipeline; speed comes only from pedal cadence.

---

### 🔲 M11: Full Polish & Research Evaluation

**Success criteria:** The entire system feels natural. No visual glitches. Foot IK blending is seamless. Pelvis motion is smooth. Ready for research data collection and user studies.

**What to do:**

1. **Edge case hardening** — very steep stairs, very shallow stairs, sudden stops, backward walking, turning on stairs.

2. **Performance profiling** — ensure IK and raycasting run within budget for VR (90fps target).

3. **Research metrics pipeline** — capture: pedal cadence, avatar speed, foot placement accuracy, pelvis trajectory, CoM deviation, step timing, packet latency.

---

## Quick Reference: Key File Locations

| File | Purpose |
|------|---------|
| `Assets/Editor/YBotIKSetup.cs` | One-click IK Rig setup tool |
| `Assets/Scripts/AvatarFollow.cs` | Headset-driven avatar follow + raycast pelvis height |
| `Assets/Scripts/BikeLocomotion.cs` | Pedal-angle → CharacterController locomotion |
| `Assets/Scripts/UdpReceiver.cs` | UDP receive thread (port 9000) |
| `Assets/Scripts/AnglePacket.cs` | UDP packet data struct |
| `Assets/Prefabs/Y Bot Unpack.prefab` | Character prefab (has IK Rig) |
| `Assets/Mixamo/Controllers/WalkingAnimator.controller` | Blend tree (Idle↔Walk), IK Pass enabled |
| `Assets/Scenes/IK_Scene.unity` | **Only active development scene** |
| `Docs/IK_Rig_Setup.md` | IK Rig documentation |
| `Docs/CurrentState.md` | This milestone tracker |

---

## Status Summary

| Milestone | Status |
|-----------|--------|
| M1 — Prototype Foundation | ✅ Complete |
| M2 — IK Rig Infrastructure | ✅ Complete |
| M3 — Project Focus Defined | ✅ Complete |
| M4 — Single-Foot IK Lift | 🔲 Next |
| M5 — Two-Foot Orchestration | 🔲 Planned |
| M6 — Pelvis & Center of Mass | 🔲 Planned |
| M7 — Foot Roll & Rotation | 🔲 Planned |
| M8 — Stair Descent | 🔲 Planned |
| M9 — Variable Step Heights | 🔲 Planned |
| M10 — Pedal Synchronization | 🔲 Planned |
| M11 — Polish & Evaluation | 🔲 Planned |
