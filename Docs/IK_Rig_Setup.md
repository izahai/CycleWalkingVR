# Animation Rigging IK Setup — Y Bot

## Overview

This document describes the **Animation Rigging IK Setup** tool for the Y Bot character. The tool is an Editor script that automatically configures Unity's **Animation Rigging** package (`com.unity.animation.rigging`, v1.4.1) on the `Y Bot Unpack.prefab`, enabling procedural foot IK for stair-climbing and terrain-adaptive locomotion.

The tool was created as **Phase 3 (IK Foot Placement)** of the broader stair-climbing implementation plan, following Phase 1 (Avatar Smooth Follow) and Phase 2 (Procedural Stair Detection via raycasting).

---

## Motivation

The project's locomotion system — driven by UDP angle packets from a cycling pedal sensor — moves a `CharacterController` across the scene. However, the Y Bot's feet remain locked to the animation blend tree (Idle ↔ Walk). To climb stairs procedurally without Mixamo animations, the feet must be **computationally positioned** onto each stair tread. This requires:

1. **A Rig Builder graph** that runs after the Animator and overrides foot bone positions.
2. **Two-Bone IK Constraints** for each leg to solve the hip→knee→foot chain toward a target.
3. **Target transforms** that a runtime script can move each frame based on raycast hits.

The Editor tool configures all three automatically.

---

## Tool: `Tools > YBot > Setup IK Rig`

### Location

| Asset | Path |
|-------|------|
| Editor script | `Assets/Editor/YBotIKSetup.cs` |

### What It Modifies

#### 1. `WalkingAnimator.controller` (`Assets/Mixamo/Controllers/`)

| Setting | Before | After |
|---------|--------|-------|
| **IK Pass** (Base Layer) | Disabled | **Enabled** — the Animator will invoke `OnAnimatorIK` on any MonoBehaviour with the method |
| **Parameters** | `Speed` (Float) | `Speed` + **`Slope`** (Float) — so `PolarCycle.cs` / `UdpCyclingLocomotion` can drive stair-state without errors |

#### 2. `Y Bot Unpack.prefab` (`Assets/Prefabs/`)

Before running the tool, the prefab has only:
- `Transform`
- `Animator` (no controller assigned)

After running, the prefab hierarchy becomes:

```
Y Bot Unpack
├── Transform
├── Animator  (WalkingAnimator.controller now assigned)
├── RigBuilder  ← NEW
├── BoneRenderer  ← NEW (optional, debug visualization of skeleton)
│
├── FootRig  ← NEW
│   └── Rig  (weight = 1.0)
│   │
│   ├── LeftFootMover  ← NEW
│   │   ├── Transform  (localPosition = (0,0,0))
│   │   ├── TwoBoneIKConstraint  ← NEW
│   │   │   ├── Root:  mixamorig:LeftUpLeg
│   │   │   ├── Mid:   mixamorig:LeftLeg
│   │   │   ├── Tip:   mixamorig:LeftFoot
│   │   │   ├── Target: LeftTarget
│   │   │   ├── Hint:  LeftHint
│   │   │   ├── Target Position Weight: 1.0
│   │   │   ├── Target Rotation Weight: 1.0
│   │   │   └── Hint Weight: 1.0
│   │   └── LeftTarget  ← NEW (positioned at LeftFoot.worldPosition)
│   │
│   └── RightFootMover  ← NEW
│       ├── Transform  (localPosition = (0,0,0))
│       ├── TwoBoneIKConstraint  ← NEW
│       │   ├── Root:  mixamorig:RightUpLeg
│       │   ├── Mid:   mixamorig:RightLeg
│       │   ├── Tip:   mixamorig:RightFoot
│       │   ├── Target: RightTarget
│       │   ├── Hint:  RightHint
│       │   ├── Target Position Weight: 1.0
│       │   ├── Target Rotation Weight: 1.0
│       │   └── Hint Weight: 1.0
│       └── RightTarget  ← NEW (positioned at RightFoot.worldPosition)
│
├── LeftHint  ← NEW (behind/below LeftFoot — controls knee bend direction)
└── RightHint  ← NEW (behind/below RightFoot — controls knee bend direction)
```

---

## How the IK Rig Works at Runtime

### Execution Order

```
Update()  ──→  Animator  ──→  RigBuilder  ──→  Render
   │                          (LateUpdate)
   │
   └── Your script moves
       LeftTarget / RightTarget
       based on raycast hits
```

The `RigBuilder` executes **after** the Animator in the playable graph (typically in `LateUpdate`). This means:

- The Animator plays the Walk/Idle animation, producing a default pose.
- The `TwoBoneIKConstraint`s then **override** the foot bone positions to match the target transforms.

### Runtime Script Pattern

To drive the IK at runtime, you need a MonoBehaviour that finds the targets and moves them:

```csharp
public class FootIKDriver : MonoBehaviour
{
    private Transform leftTarget;
    private Transform rightTarget;

    void Start()
    {
        // Find targets by path from the root
        leftTarget  = transform.Find("FootRig/LeftFootMover/LeftTarget");
        rightTarget = transform.Find("FootRig/RightFootMover/RightTarget");
    }

    void Update()   // <-- runs BEFORE RigBuilder
    {
        // 1. Raycast downward from each foot's world position
        // 2. Set leftTarget.position / rightTarget.position to hit point
        // 3. Optionally set rotation to match ground normal
    }
}
```

### Hint Transforms (Knee Direction)

The `LeftHint` and `RightHint` transforms control which direction the knee bends. They are placed slightly behind and below the foot so the knee bends forward naturally. If the character uses a different facing direction, adjust the hint position:

```csharp
// Place hint behind the foot (in foot-local space)
hint.localPosition = new Vector3(0f, -0.05f, -0.1f);
```

---

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Prefab editing via `PrefabUtility.LoadPrefabContents`** | Only reliable way to modify a `.prefab` asset file without scene-side reference corruption. Edits happen in a temporary scene, then saved back. |
| **`SerializedObject` for `TwoBoneIKConstraint` wiring** | `TwoBoneIKConstraintData` is a struct. Direct assignment (`constraint.data.root = ...`) copies by value and won't serialize. Using `SerializedObject.FindProperty("m_Data.m_Root")` writes the backing field correctly. |
| **Bone discovery by name** | The `mixamorig:` prefix is consistent across all Mixamo characters. `GetComponentsInChildren<Transform>` with name matching is the most robust approach — no fragile fileID dependencies. |
| **Target initial position = foot world position** | Placing targets at the foot's world position creates a neutral pose (no offset). A runtime script pushes them down onto terrain each frame. |
| **Hints as root children (not FootMover children)** | Keeps hints easy to find at runtime, avoids confusion with the FootMover→Target parent chain. |

---

## Overwrite Protection

If the prefab already has a `RigBuilder` + `FootRig/Rig` setup (e.g. from a previous run or a manual configuration in `BasicScene.unity`), the tool shows a confirmation dialog:

> **"Y Bot Unpack.prefab already has a FootRig with Rig component. Do you want to overwrite it?"**

- **Overwrite**: Destroys the old FootRig + RigBuilder and creates a fresh setup.
- **Cancel**: Leaves the prefab unchanged.

---

## Verification Checklist

After running **Tools > YBot > Setup IK Rig**:

- [ ] **Prefab Inspector**: Select `Y Bot Unpack.prefab` in the Project window
  - [ ] `Animator` component has `WalkingAnimator.controller` assigned
  - [ ] `RigBuilder` component is present
  - [ ] `BoneRenderer` component is present (optional)
- [ ] **Prefab Hierarchy** expands to show:
  - [ ] `FootRig/LeftFootMover/LeftTarget` and `FootRig/RightFootMover/RightTarget`
  - [ ] `LeftHint` and `RightHint` as direct root children
  - [ ] `TwoBoneIKConstraint` fields: Root/Mid/Tip are wired to skeleton bones
- [ ] **Controller**: Open `WalkingAnimator.controller`
  - [ ] Parameters tab: `Speed` and `Slope` (both Float)
  - [ ] Layers tab: Base Layer has **IK Pass** checked
- [ ] **In-editor test**: Drag updated prefab into a scene
  - [ ] No console errors related to Animation Rigging
  - [ ] Select Y Bot → the RigBuilder component shows "FootRig" in its layers list with an active checkbox

---

## File Inventory

```
Client/CycleWalking/Assets/Editor/
└── YBotIKSetup.cs                    # The Editor tool script

Client/CycleWalking/Assets/Mixamo/Controllers/
└── WalkingAnimator.controller        # Modified: IK Pass + Slope param

Client/CycleWalking/Assets/Prefabs/
└── Y Bot Unpack.prefab               # Modified: full IK Rig hierarchy
```

---

## Next Steps

1. **Write a runtime foot-placement script** that finds `LeftTarget`/`RightTarget` by path and drives them with raycast data.
2. **Enable the `Slope` parameter** in the `WalkingAnimator.controller` blend tree (add stair-climbing animation states or procedural slope response).
3. **Integrate with `AvatarFollow.cs`** — the existing headset raycasting already gives `targetPelvisHeight` for body positioning; the foot targets should follow the same stair-detection logic.
