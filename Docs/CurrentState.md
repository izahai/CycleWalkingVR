# Project Milestones — Procedural Stair-Climbing Locomotion

## Ultimate Goal

**Fully procedural, code-computed stair-climbing animation** for the Y Bot character in VR — with zero dependency on Mixamo stair animations. Every movement (foot lift, foot plant, pelvis rise, weight shift, balance) is computed mathematically from raycasts, pedal cadence, and biomechanical constraints.

The character must walk up stairs with **natural foot-to-foot orchestration**: the left foot lands precisely on a stair tread, weight transfers to it, the right foot lifts and lands on the next tread, all while the pelvis rises in a smooth, biologically plausible trajectory. No sliding. No clipping. No snapping.

---

## Architecture (Four Independent Layers)

```
Input Layer           Movement Layer        Animation Layer         IK Layer
───────────           ──────────────        ────────────────        ────────
Pedals (UDP)    →    BikeLocomotion    →    Blend Tree         →   Foot IK
                     CharacterController     Idle ↔ Walk             Pelvis IK
                                        ↓    Stair Detect            Spine IK
                                        ↓    Step Orchestrator
```

The IK Layer never knows where the movement came from. This separation lets us develop animation quality independently of hardware integration.

---

## What We Have Done

### ✅ M1: Prototype Foundation
- XR project setup (URP, OpenXR, XR Interaction Toolkit 3.3.1)
- Mixamo Y Bot imported as Humanoid with full `mixamorig:` skeleton
- `WalkingAnimator.controller` with 1D Blend Tree (Idle ↔ Walk)
- `AvatarFollow.cs`: headset-driven avatar positioning with dynamic raycast-based Y height
- `BikeLocomotion.cs`: pedal-angle-driven CharacterController movement via UDP
- `UdpReceiver.cs`: background-thread UDP listener (port 9000)

### ✅ M2: Animation Rigging IK Infrastructure
- `Assets/Editor/YBotIKSetup.cs` — **Tools > YBot > Setup IK Rig** one-click setup
- `Y Bot IK.prefab`: `RigBuilder`, `FootRig`/`Rig`, `TwoBoneIKConstraint` × 2
- Leg chains: LeftUpLeg→LeftLeg→LeftFoot and RightUpLeg→RightLeg→RightFoot
- `LeftTarget` / `RightTarget` / `LeftHint` / `RightHint` transforms
- `WalkingAnimator.controller`: **IK Pass enabled**
- `BoneRenderer` for skeleton debug visualization

### ✅ M3: Project Focus Defined
- `IK_Scene.unity` designated as the only active scene
- `CLAUDE.md` updated; `BasicScene`, `PolarCycle.cs` marked as legacy
- `Docs/CurrentState.md` created

### ✅ M4: Single-Foot IK Test Lift — The "Spacebar Demo"
- `FootRaycastResult.cs` — shared data struct (`hit`, `point`, `normal`, `distance`, `hitTransform`)
- `FootRaycaster.cs` — per-foot raycast data provider + forward probe for stair detection
  - Auto-finds `mixamorig:LeftFoot` / `RightFoot` bones
  - Debug rays: green (left), red (right), cyan (forward probe)
  - `[DefaultExecutionOrder(-1)]` — guaranteed to run before FootIKDriver
- `FootIKDriver.cs` — per-foot IK actuator
  - Auto-finds `LeftTarget` / `RightTarget` by path + `TwoBoneIKConstraint` components
  - Starts with IK weight=0 (animation plays freely — avoids T-pose folding)
  - `maintainTargetRotationOffset = true` (preserves animation foot rotation)
  - Y-velocity swing/stance detection per foot
  - Smooth weight blending via `Mathf.MoveTowards`
  - **Spacebar test lift**: positions hint in front of foot, arcs target up to stair height
  - OnGUI debug overlay showing L/R IK weights
- `AvatarFollow.cs`: added optional `pedalSource` + `followPedalXZ` for simulated pedal testing

**Verified:** At Idle, feet look normal. Spacebar lifts right foot with knee bending forward onto the stair tread.

---

## Future Milestones

> **Key principle:** Walking up stairs is not about one foot moving. It is the **orchestration between two feet**, with **pelvis position and center of mass** driving the natural feel. Every milestone below builds incrementally on the previous and is small enough to test in a single Unity Play session.

Each milestone has:
- **Context**: what new capability we're adding (and why)
- **Success test**: exact steps to run in Unity, what to observe, and what "correct" looks like
- **What to build**: files to create/modify

---

### 🔲 M5: Walk + IK Coexistence

**Context:** Currently we've only tested IK at Idle and with the spacebar lift. The Walk animation continuously moves the foot bones — we need to verify the IK constraint doesn't fold or twist feet when the animation is playing at speed.

**Success test:**
1. Start the bike simulator (`python Backend/main2.py`, then `start`) to make the character walk
2. Observe the Y Bot's feet during walking on flat ground
3. **PASS:** Feet look natural throughout the walk cycle — no folding, no twisting, no abnormal knee bending. The OnGUI debug overlay shows both L and R weight values changing (they won't necessarily oscillate cleanly yet — that's M6).
4. **PASS:** Feet contact the ground properly (no floating above or penetrating below).
5. **FAIL:** Any foot folding, knee backward bending, or foot twisting at any point in the walk cycle.

**What to build:** No code changes expected — this is a verification milestone. If issues are found, fix them here before proceeding.

---

### 🔲 M6: Swing/Stance Weight Blending Validation

**Context:** The Y-velocity heuristic (`velocityY > threshold → swing → weight=0`) should cause each foot's IK weight to oscillate in sync with the walk cycle. We need to verify this rhythm is correct before relying on it for automatic stair stepping.

**Success test:**
1. Start bike simulator, character walks on flat ground
2. Watch the OnGUI debug overlay (L: and R: weight values near the character)
3. **PASS:** When the left foot lifts off the ground (visually), the L weight drops toward 0. When it plants, L weight rises toward 1. Same for R.
4. **PASS:** Weight transitions are smooth (not instant 0↔1 jumps) — `weightBlendSpeed` should produce visible ramping.
5. **FAIL:** Weights stay at 0 always, stay at 1 always, or don't correlate with visible foot movement.

**What to build:** May need to tune `swingVelocityThreshold` and `weightBlendSpeed` in the Inspector. If the Y-velocity heuristic proves unreliable during walking, add a position-based heuristic (foot-bone Y relative to ankle Y) as fallback. No new files.

---

### 🔲 M7: Forward-Probe Stair Detection

**Context:** The forward probe ray (from `FootRaycaster`) casts ahead of the character to detect upcoming stair steps. Before we can auto-step, we need to verify the probe reliably detects stair treads at different distances.

**Success test:**
1. Position the Y Bot ~0.5m in front of the first stair step (move in Scene view before Play, or walk up to it)
2. Press Play. Look at the cyan debug ray in the Scene view.
3. **PASS:** The cyan ray hits the stair tread surface. It should NOT hit the floor in front of the stair.
4. Move the character to different distances: 0.2m, 0.5m, 1.0m from the stair.
5. **PASS:** At 0.2–0.5m the probe hits the stair. At 1.0m it hits the floor (too far — that's expected).
6. **FAIL:** Probe never hits the stair even when close, or ray length/position is wrong.

**What to build:** May need to tune `forwardProbeDistance` and `forwardProbeLength` in the Inspector. The probe origin is `transform.position + up*1.0 + forward*distance`. Verify the origin isn't blocked by the character's own collider.

---

### 🔲 M8: Automatic Single-Foot Step-Up

**Context:** The spacebar demo (M4) proved the IK constraint can lift a foot to stair height. Now we make it automatic: when the character walks close enough to a stair that the forward probe detects it, AND the foot's own raycast hits the raised tread during stance, the foot target snaps to the stair surface.

**Success test:**
1. Start bike simulator. Character walks toward the stair.
2. Do NOT press spacebar. Let the character walk naturally.
3. **PASS:** When the character's leading foot reaches the stair, that foot lands on the stair surface (not on the floor below it). The IK snaps the foot up to the tread height.
4. **PASS:** The other foot remains on the lower ground — only one foot steps up.
5. **PASS:** The transition is smooth — no sudden pop or teleport.
6. **FAIL:** Foot stays on the lower ground despite being over the stair, or foot snaps up too early (before reaching the stair).

**What to build:** Modify `ProcessFoot()` in `FootIKDriver.cs`: when the foot raycast hits a surface whose Y is significantly higher than the current target Y AND the forward probe confirms a stair ahead, use the higher hit point. The key logic: `if (raycast.point.y > target.position.y + stepThreshold) → snap to stair`.

---

### 🔲 M9: Stance Lock — Target Freeze After Plant

**Context:** During stance, small animation jitter or raycast noise can cause the foot target to vibrate between slightly different positions. Once a foot plants on a surface (especially a stair tread), its target should lock until the next swing phase begins.

**Success test:**
1. Walk character onto the first stair step (M8 must pass first).
2. After the foot lands on the stair, watch carefully for any sliding or vibration.
3. **PASS:** The planted foot stays perfectly still on the stair tread. No micro-movements, no sliding, no oscillation.
4. **PASS:** When the walk cycle enters a new swing phase for that foot, the lock releases and the foot lifts normally.
5. **FAIL:** Foot drifts, slides, or vibrates while supposed to be planted.

**What to build:** Add `private bool leftLocked` / `rightLocked` and `private Vector3 leftLockPosition` / `rightLockPosition` to `FootIKDriver`. When swing→stance transition is detected (weight crosses a threshold upward), capture `lockPosition = target.position`. While locked, set `target.position = lockPosition` directly (bypass Lerp). Clear lock when stance→swing transition detected.

---

### 🔲 M10: Two-Step Alternating Sequence

**Context:** With one foot on the first stair (M8), the character's body is now closer to the second stair. The trailing foot needs to lift and land on the next tread. This is the first test of two-foot coordination.

**Success test:**
1. Walk character toward stairs. First foot steps onto stair 1 (automatic from M8).
2. Keep walking forward. The trailing foot should lift and land on stair 2.
3. **PASS:** Right foot on stair 1 → left foot lifts and lands on stair 2. Each foot plants exactly once per step. No foot lands on the same stair twice.
4. **PASS:** Stance lock (M9) works for both feet — each stays planted after landing.
5. **FAIL:** Trailing foot doesn't reach stair 2, lands on stair 1 instead, or both feet end up on the same stair.

**What to build:** This should mostly work if M8 and M9 are solid — the forward probe naturally detects the next stair after the first step. May need to advance the forward probe origin as the character climbs (use pelvis height, not `transform.position`). Add a per-foot `lastStepHeight` to track which stair each foot is on, preventing a foot from stepping to the same height twice.

---

### 🔲 M11: Three-Stair Continuous Walk

**Context:** Scale up from 2 stairs to 3+ — verify the alternating pattern holds and the system doesn't break down with sustained climbing.

**Success test:**
1. Walk character up 3 or more consecutive stairs.
2. **PASS:** Feet alternate naturally: R→stair1, L→stair2, R→stair3, L→stair4. Rhythm is consistent.
3. **PASS:** No missed steps (a foot fails to reach a stair), no double-plants (foot lands twice on same stair), no foot sliding.
4. **PASS:** The forward probe continues detecting next stairs as the character climbs.
5. **FAIL:** Any breakdown after stair 2 — missed detection, wrong height, foot snaps to wrong surface.

**What to build:** Likely no new code — this is a scaling verification of M8–M10. If forward probe fails after climbing (because probe origin doesn't rise with the character), adjust probe origin to use a rising reference point (e.g., pelvis bone height + offset instead of `transform.position`).

---

### 🔲 M12: Pelvis Height from Foot Average

**Context:** Currently `AvatarFollow` sets pelvis height from a headset raycast. But when one foot is on a higher stair and the other is on the ground, the pelvis should rise to a weighted average of the two foot heights — otherwise the hip stays low and the stepped-up leg looks unnaturally bent.

**Success test:**
1. After M8: one foot on stair, one on ground. Observe the pelvis/hip position.
2. **PASS:** The pelvis Y rises above its flat-ground height. The rise is proportional to the foot height difference — if the right foot is 15cm higher, the pelvis should be ~7-8cm higher (roughly half, since one foot is still low).
3. **PASS:** The rise is smooth (no snap). It uses `Mathf.SmoothDamp` or `MoveTowards`.
4. **FAIL:** Pelvis stays at flat-ground height, or pelvis rises too much (both feet look like they're floating).

**What to build:** Add `PelvisController.cs` — reads `FootRaycaster` foot hit points (or `FootIKDriver` target positions), computes `targetPelvisY = (leftY * leftWeight + rightY * rightWeight) / (leftWeight + rightWeight) + baseOffset`. Feed this into `AvatarFollow` as an optional `externalPelvisTarget` override. Modify `AvatarFollow.cs`: add `[SerializeField] private Transform externalPelvisTarget` — when set, use its Y instead of the headset raycast Y.

---

### 🔲 M13: Pelvis Tilt from Uneven Feet

**Context:** When one foot is higher than the other mid-stride, the pelvis should tilt (the hip on the higher-foot side rises, the other side drops). This is a subtle but important visual cue for natural stair climbing — without it, the character looks stiff.

**Success test:**
1. Walk character so one foot is on a stair and the other is still on the lower ground.
2. **PASS:** The pelvis/hip bone tilts slightly around the Z-axis (forward axis) — the side with the higher foot tilts up, the lower side tilts down. Tilt angle is proportional to the foot height difference.
3. **PASS:** Tilt transitions are smooth. When both feet are on the same level, tilt returns to zero.
4. **FAIL:** No visible tilt, or tilt in the wrong direction, or tilt is jerky.

**What to build:** Add to `PelvisController.cs`: compute `tiltAngle = Mathf.Atan2(rightY - leftY, hipWidth) * Mathf.Rad2Deg`. Apply via `pelvisBone.localRotation = Quaternion.Slerp(current, targetTilt, speed * dt)`. The pelvis bone is `mixamorig:Hips`. Tilt around the Z-axis (forward) to raise one hip and lower the other.

---

### 🔲 M14: Forward Lean on Stairs

**Context:** Humans lean slightly forward when climbing stairs — this shifts the center of mass forward over the leading foot. Without it, the character looks like it's being pulled up by an invisible string.

**Success test:**
1. Walk character up stairs.
2. **PASS:** The upper body (spine) leans forward ~5-8° when climbing. The lean ramps up as the character transitions from flat to stairs.
3. **PASS:** When back on flat ground, the lean returns to zero.
4. **FAIL:** No lean, too much lean (>15°), or lean activates on flat ground.

**What to build:** Add to `PelvisController.cs`: track the slope angle (difference between forward probe hit height and current foot height, divided by horizontal distance). Map slope to a target forward lean angle. Apply to the spine bone (`mixamorig:Spine` or `mixamorig:Spine1`) as a local X rotation. Smooth blend.

---

### 🔲 M15: Foot Rotation from Surface Normal

**Context:** Currently the foot target rotation is preserved from the animation (thanks to `maintainTargetRotationOffset`). But when the foot lands on a non-flat surface (sloped ramp, or eventually uneven terrain), the foot should rotate to match the surface. For flat stairs this is a no-op (normal = up), but we need the plumbing.

**Success test:**
1. Place a sloped surface (or use the Cube ramp in IK_Scene). Walk onto it.
2. **PASS:** The foot rotates to match the slope angle — the sole lies flat on the surface.
3. On flat stairs: foot stays flat (no unwanted rotation).
4. **FAIL:** Foot stays horizontal on a slope (penetrating the surface), or foot rotates incorrectly on flat ground.

**What to build:** In `FootIKDriver.ProcessFoot()`: when raycast hits and foot is in stance, set `target.rotation = Quaternion.Slerp(target.rotation, Quaternion.FromToRotation(Vector3.up, raycast.normal) * baseRotation, rotSpeed * dt)`. Store the animation-driven base rotation during swing so we can blend back to it.

---

### 🔲 M16: Heel-to-Toe Roll During Stance

**Context:** In natural walking, the foot doesn't plant flat instantly — it rolls from heel-strike to flat to toe-off. Simulating this roll adds significant visual quality to the foot planting.

**Success test:**
1. Walk character on flat ground. Watch a single stance phase for one foot.
2. **PASS:** When the foot first plants, the target is slightly behind the foot bone (heel position). As the body moves forward during stance, the target shifts toward the toe. At the end of stance, the target is near the ball of the foot.
3. **PASS:** The roll distance is small (~5-10cm total travel from heel to toe) and smooth.
4. **FAIL:** Foot target stays at a fixed position throughout stance (no roll), or roll travels too far.

**What to build:** Track `stanceProgress` per foot — 0.0 at plant, 1.0 at lift. Compute from animation normalized time or from the character's forward movement during stance. Interpolate target position from heel-offset to toe-offset based on progress. Offsets computed from the character's forward direction.

---

### 🔲 M17: Stair Descent Detection

**Context:** The forward probe currently looks for higher surfaces (stairs going up). For descent, it needs to detect when the ground ahead is LOWER than the current foot height — meaning stairs going down.

**Success test:**
1. Walk character toward a downward step (the opposite side of the stairs, or a separate test geometry).
2. **PASS:** When the forward probe hits a surface significantly LOWER than current foot height, the system recognizes "descent ahead." A debug indicator confirms this (different color probe ray, or console log).
3. **FAIL:** System treats descent like flat ground (foot doesn't reach down), or misidentifies descent as ascent.

**What to build:** Modify `HandleForwardProbe()`: add a `isDescent` flag when `probeHeight < currentFootHeight - threshold`. During descent stance, allow the foot target to go below the current floor level. The foot raycast naturally finds the lower surface.

---

### 🔲 M18: Full Descent Sequence — Downward Step & Pelvis Lowering

**Context:** When descending, the foot reaches down to a lower tread AND the pelvis lowers smoothly. Without pelvis lowering, the character "drops" onto the descending foot.

**Success test:**
1. Walk character down 3+ stairs.
2. **PASS:** The leading foot reaches down and lands on the lower tread — no snapping, smooth transition.
3. **PASS:** The pelvis lowers smoothly as the character descends — no sudden drops.
4. **PASS:** The alternating foot pattern works going down just like going up.
5. **FAIL:** Foot doesn't reach the lower tread, pelvis drops suddenly, or alternating pattern breaks.

**What to build:** Extend `PelvisController`: when descent is detected, blend the pelvis target Y downward before the foot reaches the lower step (anticipatory lowering). The `FootIKDriver` naturally handles the downward foot reach since the foot raycast will hit the lower surface.

---

### 🔲 M19: Variable Step Height Adaptation

**Context:** Real staircases may have different step heights. The system should adapt — small steps (5cm) get a subtle foot lift, large steps (20cm) get an exaggerated lift. The swing animation and hint position should scale with step height.

**Success test:**
1. Test with stairs of different heights: create a few test steps of 5cm, 10cm, 15cm, 20cm.
2. **PASS:** Swing height (how high the foot lifts above the tread) scales with step height. A 5cm step gets ~8cm lift. A 20cm step gets ~28cm lift.
3. **PASS:** The hint position scales too — higher hint for higher steps (so the knee lifts more).
4. **FAIL:** Same lift height regardless of step height (foot clips through tall steps, or lifts absurdly high for short steps).

**What to build:** In `FootIKDriver`, compute `stepHeight = forwardProbe.point.y - currentTarget.y`. Multiply `liftHeightOffset` by a factor based on `stepHeight`. Adjust hint position proportionally. The spacebar test lift already has lift height logic — extend it to the automatic path.

---

### 🔲 M20: Flat-to-Stair Transition Smoothness

**Context:** The first stair step is the hardest — the character transitions from flat-ground walking to stair-climbing. This boundary often has a visible "pop" as the IK suddenly starts targeting a higher surface. We need this transition to be as smooth as the subsequent stairs.

**Success test:**
1. Walk character from flat ground onto the first stair.
2. **PASS:** No visible pop, snap, or jerk at the moment the first foot steps up. The transition looks as natural as stair-2-to-stair-3.
3. **PASS:** The pelvis rise begins smoothly as the first foot approaches the stair (anticipatory rise, not reactive snap).
4. **FAIL:** First step looks qualitatively different/worse than later steps.

**What to build:** This is a tuning/polish milestone. Likely involves adjusting: forward probe detection distance (detect stair earlier), weight blend speed (slower at the transition), and pelvis anticipation (start rising before the foot plants). No new architecture — parameter tuning and small logic tweaks.

---

### 🔲 M21: Edge Cases — Sudden Stop, Turn, Backward Walk

**Context:** In VR, the user won't always walk straight up stairs at a constant speed. They might stop mid-staircase, turn around, or walk backward. The IK system must not break in these scenarios.

**Success test:**
1. **Stop mid-climb:** Walk onto stair 2 and stop (kill bike simulator). **PASS:** Feet stay planted where they are. No sliding. No weird leg poses.
2. **Turn on stairs:** Stand on a stair tread and rotate the character 180°. **PASS:** Feet stay planted on the stair during the turn. They don't slide off or lift.
3. **Backward walk on flat ground:** Walk backward. **PASS:** Feet still track the ground properly. No folding or penetration.
4. **FAIL:** Any foot breaking, sliding, or folding in these scenarios.

**What to build:** Add safety checks: when movement speed is near zero, lock both feet in stance (IK weight = 1, targets locked). During rotation, the targets are in world space so they naturally maintain their positions. For backward walking, the forward probe logic needs to handle negative velocity — disable stair detection when moving backward.

---

### 🔲 M22: Pedal Cadence to Step Speed

**Context:** The character's walk speed currently comes from pedal cadence (via `BikeLocomotion`). But the IK step timing should also respond to cadence — faster pedaling should mean faster step cycles. This milestone connects the pedal input to the animation playback speed.

**Success test:**
1. Start bike simulator at low speed (slow pedaling). **PASS:** Character walks slowly, steps are deliberate.
2. Increase pedal speed. **PASS:** Animation speed increases. Step cycle is faster. Feet still track terrain correctly at higher speed.
3. **PASS:** IK weight blending keeps up with the faster cycle — no lag where weight stays at 1 when foot has already lifted.
4. **FAIL:** IK can't keep up at high speeds, or animation looks choppy.

**What to build:** The `Animator.speed` is already driven by `BikeLocomotion` via `AvatarFollow` when `followPedalXZ` is on. Verify this chain works. May need to scale `weightBlendSpeed` with animation speed (faster animation → faster weight transitions).

---

### 🔲 M23: Pedal-Step Phase Alignment

**Context:** Ideally, the right pedal at the bottom of its crank cycle corresponds to the right foot being planted. This creates a natural cycling-walking rhythm. We don't need perfect synchronization, but the phase relationship should not drift wildly.

**Success test:**
1. Start bike simulator. Observe the relationship between pedal angle (visible in bike simulator log or debug display) and foot plant events (visible in the OnGUI weight overlay).
2. **PASS:** There is a consistent phase relationship — e.g., right foot always plants around the same point in the pedal cycle. Or at minimum, the step frequency matches the pedal cadence frequency (they don't drift apart).
3. **FAIL:** Step frequency and pedal cadence are completely unrelated, or the phase drifts continuously.

**What to build:** This may not require code changes — just verification. If alignment is needed, add a phase-offset parameter that shifts when the step state machine triggers relative to the pedal angle. This is a research-polish milestone; functional correctness matters more than perfect alignment.

---

### 🔲 M24: Full Staircase End-to-End

**Context:** The ultimate integration test — walk up a full staircase (8+ stairs), turn around, walk down. Everything must work together: ascent, descent, alternating feet, pelvis compensation, foot rotation, variable heights, and edge-case handling.

**Success test:**
1. Walk up 8+ stairs. **PASS:** Smooth, natural climbing throughout. No glitches at any step.
2. Turn around at the top. **PASS:** Feet stay planted during turn.
3. Walk down all 8 stairs. **PASS:** Smooth descent with proper foot reach and pelvis lowering.
4. **PASS:** Zero console errors. No foot sliding, clipping, or folding at any point.
5. **FAIL:** Any visual glitch, missed step, or IK breakdown anywhere in the sequence.

**What to build:** This is a verification milestone. Fix any issues discovered. Likely involves tuning parameters across all systems for end-to-end consistency.

---

### 🔲 M25: Performance & Data Collection Readiness

**Context:** For VR research, we need 90fps performance and the ability to capture metrics: pedal cadence, avatar speed, foot placement accuracy, pelvis trajectory, CoM deviation, step timing, and packet latency.

**Success test:**
1. Run the full staircase test (M24) with the Unity Profiler open. **PASS:** Frame time stays under 11ms (90fps). No GC spikes from IK/raycasting.
2. Enable metric logging. **PASS:** A CSV or JSON log file is written with per-frame data: timestamp, pedal angle, avatar position, left/right foot target Y, pelvis Y, IK weights, forward probe hit Y.
3. **FAIL:** Frame drops below 90fps, or logging causes performance degradation.

**What to build:**
- `MetricsLogger.cs`: collects per-frame data into a ring buffer, writes to `Application.persistentDataPath` on application quit.
- Profile and optimize: reduce raycast count if needed, use `NonAlloc` raycast variants, simplify `OnGUI` if it causes allocations.

---

## Quick Reference: Key File Locations

| File | Purpose |
|------|---------|
| `Assets/Editor/YBotIKSetup.cs` | One-click IK Rig setup tool |
| `Assets/Scripts/FootRaycaster.cs` | Per-foot raycast data provider (M4) |
| `Assets/Scripts/FootIKDriver.cs` | IK target positioning + weight blending (M4) |
| `Assets/Scripts/FootRaycastResult.cs` | Shared foot raycast data struct (M4) |
| `Assets/Scripts/AvatarFollow.cs` | Headset-driven avatar follow + raycast pelvis height |
| `Assets/Scripts/BikeLocomotion.cs` | Pedal-angle → CharacterController locomotion |
| `Assets/Scripts/UdpReceiver.cs` | UDP receive thread (port 9000) |
| `Assets/Scripts/AnglePacket.cs` | UDP packet data struct |
| `Assets/Prefabs/Y Bot IK.prefab` | Character prefab (has IK Rig) |
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
| M4 — Single-Foot IK Test Lift | ✅ Complete |
| M5 — Walk + IK Coexistence | 🔲 Next — verify |
| M6 — Swing/Stance Weight Blending | 🔲 |
| M7 — Forward-Probe Stair Detection | 🔲 |
| M8 — Automatic Single-Foot Step-Up | 🔲 |
| M9 — Stance Lock | 🔲 |
| M10 — Two-Step Alternating | 🔲 |
| M11 — Three-Stair Continuous Walk | 🔲 |
| M12 — Pelvis Height from Foot Average | 🔲 |
| M13 — Pelvis Tilt from Uneven Feet | 🔲 |
| M14 — Forward Lean on Stairs | 🔲 |
| M15 — Foot Rotation from Surface Normal | 🔲 |
| M16 — Heel-to-Toe Roll | 🔲 |
| M17 — Stair Descent Detection | 🔲 |
| M18 — Full Descent Sequence | 🔲 |
| M19 — Variable Step Height Adaptation | 🔲 |
| M20 — Flat-to-Stair Transition | 🔲 |
| M21 — Edge Cases | 🔲 |
| M22 — Pedal Cadence to Step Speed | 🔲 |
| M23 — Pedal-Step Phase Alignment | 🔲 |
| M24 — Full Staircase End-to-End | 🔲 |
| M25 — Performance & Data Collection | 🔲 |
