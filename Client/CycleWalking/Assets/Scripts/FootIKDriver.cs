using UnityEngine;
using UnityEngine.Animations.Rigging;
using System.Linq;
using System.Collections;

/// <summary>
/// Consumes FootRaycaster data each frame. Detects swing vs stance per foot
/// via foot-bone Y-velocity, blends per-foot IK weight, and moves the
/// LeftTarget / RightTarget transforms to the raycast hit positions.
///
/// Execute in Update() so TwoBoneIKConstraint overrides happen in LateUpdate
/// (via RigBuilder's playable graph).
///
/// M4 uses a simple Y-velocity heuristic for swing detection.
/// M5 will replace this with a proper StepStateMachine.
/// </summary>
public class FootIKDriver : MonoBehaviour
{
    [Header("Dependencies")]
    [SerializeField] private FootRaycaster footRaycaster;

    [Header("IK Targets (auto-found if empty)")]
    [SerializeField] private Transform leftTarget;
    [SerializeField] private Transform rightTarget;
    [SerializeField] private Transform leftHint;
    [SerializeField] private Transform rightHint;

    [Header("Settings")]
    [SerializeField] private float snapSpeed = 15f;
    [SerializeField] private float weightBlendSpeed = 8f;
    [SerializeField] private float swingVelocityThreshold = 0.25f;

    [Header("Debug")]
    [SerializeField] private bool showWeights = true;

    [Header("Test — Single-Foot Lift (Space)")]
    [SerializeField] private KeyCode liftKey = KeyCode.Space;
    [SerializeField] private float liftDuration = 0.5f;
    [SerializeField] private float liftHeightOffset = 0.15f;
    [SerializeField] private bool testRightFoot = true;

    // ─── Private state ───────────────────────────────────────────────

    private TwoBoneIKConstraint leftConstraint;
    private TwoBoneIKConstraint rightConstraint;

    private Transform leftFootBone;
    private Transform rightFootBone;

    // Per-foot IK weights (0 = animation, 1 = snapped to terrain)
    private float leftCurrentWeight;
    private float rightCurrentWeight;
    private float leftTargetWeight;
    private float rightTargetWeight;

    // Y-velocity tracking per foot
    private float leftLastY;
    private float rightLastY;

    // Test lift state
    private bool isLifting;
    private Vector3 liftStartPos;
    private Vector3 liftEndPos;
    private float liftStartTime;
    private Transform liftTarget;      // which target we're moving (right or left)

    // ─── Lifecycle ───────────────────────────────────────────────────

    private void Awake()
    {
        // Auto-find IK constraint owners and targets
        Transform leftMover  = transform.Find("FootRig/LeftFootMover");
        Transform rightMover = transform.Find("FootRig/RightFootMover");

        if (leftMover != null)
        {
            if (leftTarget == null)
                leftTarget = leftMover.Find("LeftTarget");
            leftConstraint = leftMover.GetComponent<TwoBoneIKConstraint>();
        }

        if (rightMover != null)
        {
            if (rightTarget == null)
                rightTarget = rightMover.Find("RightTarget");
            rightConstraint = rightMover.GetComponent<TwoBoneIKConstraint>();
        }

        // Auto-find hint transforms (root children)
        if (leftHint == null)
            leftHint = FindHint("LeftHint");
        if (rightHint == null)
            rightHint = FindHint("RightHint");

        // Foot bones for Y-velocity detection
        leftFootBone  = FindBone("mixamorig:LeftFoot");
        rightFootBone = FindBone("mixamorig:RightFoot");

        // Log warnings for missing references
        if (leftConstraint == null) Debug.LogError("[FootIKDriver] LeftFootMover/TwoBoneIKConstraint not found");
        if (rightConstraint == null) Debug.LogError("[FootIKDriver] RightFootMover/TwoBoneIKConstraint not found");
        if (leftTarget == null) Debug.LogWarning("[FootIKDriver] LeftTarget not found");
        if (rightTarget == null) Debug.LogWarning("[FootIKDriver] RightTarget not found");

        // ── Start with IK disabled — animation plays freely ──
        // Awake() runs BEFORE the Animator evaluates, so snapping targets
        // to foot bone positions would capture T-pose positions, not the
        // Idle animation pose.  Instead, start at weight=0 and let the
        // ProcessFoot() blend ramp up naturally as raycast hits arrive.
        leftCurrentWeight  = 0f;
        rightCurrentWeight = 0f;
        leftTargetWeight   = 0f;
        rightTargetWeight  = 0f;
        if (leftConstraint != null)
        {
            leftConstraint.weight = 0f;
            leftConstraint.data.maintainTargetRotationOffset = true;
        }
        if (rightConstraint != null)
        {
            rightConstraint.weight = 0f;
            rightConstraint.data.maintainTargetRotationOffset = true;
        }

        // Initialise Y-tracking so first-frame delta is zero
        if (leftFootBone != null)  leftLastY  = leftFootBone.position.y;
        if (rightFootBone != null) rightLastY = rightFootBone.position.y;
    }

    private void Update()
    {
        if (footRaycaster == null) return;

        float dt = Time.deltaTime;
        if (dt < 0.0001f) return;

        // ── Test lift trigger ──
        if (!isLifting && Input.GetKeyDown(liftKey))
        {
            TriggerLift();
        }

        // ── Animate test lift ──
        if (isLifting)
        {
            float elapsed = Time.time - liftStartTime;
            float t = Mathf.Clamp01(elapsed / liftDuration);
            // Bell-curve arc: rises fastest in the middle
            float height = Mathf.Sin(t * Mathf.PI) * liftHeightOffset;
            Vector3 pos = Vector3.Lerp(liftStartPos, liftEndPos, t);
            pos.y += height;
            if (liftTarget != null)
                liftTarget.position = pos;

            if (t >= 1f)
            {
                isLifting = false;
                // Force the weight to stay at 1 so the foot stays planted on the step
                if (liftTarget == rightTarget && rightConstraint != null)
                    rightConstraint.weight = 1f;
                else if (liftTarget == leftTarget && leftConstraint != null)
                    leftConstraint.weight = 1f;
            }
            // While lifting, keep IK weight at 1 so the constraint pulls the foot
            return; // skip normal foot processing during test lift
        }

        // Process each foot independently
        ProcessFoot(
            footRaycaster.leftFoot,  leftFootBone,
            leftTarget,  leftConstraint,
            ref leftCurrentWeight,  ref leftTargetWeight,
            ref leftLastY,  dt);

        ProcessFoot(
            footRaycaster.rightFoot,  rightFootBone,
            rightTarget,  rightConstraint,
            ref rightCurrentWeight,  ref rightTargetWeight,
            ref rightLastY,  dt);

        // Handle forward-probe stair step for upcoming foot
        HandleForwardProbe();
    }

    // ─── Test lift trigger ───────────────────────────────────────────

    private void TriggerLift()
    {
        if (!footRaycaster.forwardProbe.hit)
        {
            Debug.Log("[FootIKDriver] No forward probe hit — position the character closer to the stairs.");
            return;
        }

        // Determine which foot to lift (right by default)
        liftTarget = testRightFoot ? rightTarget : leftTarget;
        if (liftTarget == null) return;

        liftStartPos = liftTarget.position;

        // ── Position the hint for natural knee-forward bending ──
        // The prefab hints are behind the character (Z negative), which
        // causes the TwoBoneIK solver to bend the knee backward.  We
        // override the hint here so the knee bends in the character's
        // forward direction during the lift.
        if (testRightFoot && rightHint != null && rightFootBone != null)
        {
            rightHint.position = rightFootBone.position
                                 + transform.forward * 0.15f
                                 + Vector3.down * 0.05f;
        }
        else if (!testRightFoot && leftHint != null && leftFootBone != null)
        {
            leftHint.position = leftFootBone.position
                                + transform.forward * 0.15f
                                + Vector3.down * 0.05f;
        }

        // Lift to stair HEIGHT at the foot's OWN XZ position.
        // This avoids the IK solver trying to reach a target far from
        // the foot's current horizontal position, which causes leg folding.
        liftEndPos = liftStartPos;
        liftEndPos.y = footRaycaster.forwardProbe.point.y;

        liftStartTime = Time.time;
        isLifting = true;

        // Set IK weight to 1 on the lifting foot
        if (testRightFoot && rightConstraint != null)
        {
            rightCurrentWeight = 1f;
            rightConstraint.weight = 1f;
        }
        else if (!testRightFoot && leftConstraint != null)
        {
            leftCurrentWeight = 1f;
            leftConstraint.weight = 1f;
        }

        Debug.Log($"[FootIKDriver] Lifting foot from y={liftStartPos.y:F3} to y={liftEndPos.y:F3}");
    }

    // ─── Per-foot processing ─────────────────────────────────────────

    private void ProcessFoot(
        FootRaycastResult raycast,
        Transform footBone,
        Transform target,
        TwoBoneIKConstraint constraint,
        ref float currentWeight,
        ref float targetWeight,
        ref float lastY,
        float dt)
    {
        if (constraint == null || footBone == null) return;

        // ── 1. Compute foot Y-velocity ──
        float currentY = footBone.position.y;
        float velocityY = (currentY - lastY) / dt;
        lastY = currentY;

        // ── 2. Detect swing vs stance ──
        bool isSwing = velocityY > swingVelocityThreshold;

        // ── 3. Set target weight ──
        // During swing: weight → 0 (let animation swing freely)
        // During stance: weight → 1 (snap foot to terrain)
        targetWeight = isSwing ? 0f : 1f;

        // ── 4. Move target ──
        if (raycast.hit && !isSwing)
        {
            // Foot is planted on terrain — snap to hit point
            target.position = Vector3.Lerp(
                target.position,
                raycast.point,
                snapSpeed * dt);
        }
        else if (!isSwing && footBone != null)
        {
            // Foot is planted but no terrain hit yet (first few frames) —
            // follow the animated foot bone position instead of leaving
            // the target at the prefab offset.  Prevents a brief "foot
            // lift" as IK weight blends from 0→1.
            target.position = Vector3.Lerp(
                target.position,
                footBone.position,
                snapSpeed * dt);
        }

        // ── 5. Smooth-blend the IK weight ──
        currentWeight = Mathf.MoveTowards(
            currentWeight,
            targetWeight,
            weightBlendSpeed * dt);

        constraint.weight = currentWeight;
    }

    // ─── Forward-probe stair detection ───────────────────────────────

    private void HandleForwardProbe()
    {
        if (!footRaycaster.forwardProbe.hit) return;

        // Check if the forward probe detected a step higher than the current
        // foot positions (meaning stairs ahead).
        FootRaycastResult probe = footRaycaster.forwardProbe;
        float leftFootHeight  = leftTarget  != null ? leftTarget.position.y  : transform.position.y;
        float rightFootHeight = rightTarget != null ? rightTarget.position.y : transform.position.y;
        float probeHeight     = probe.point.y;

        if (probeHeight > Mathf.Max(leftFootHeight, rightFootHeight) + 0.1f)
        {
            // A stair step is detected ahead.
            // When a foot transitions from swing to stance, the forward-probe
            // height influences its target Y. This is handled automatically:
            // the foot raycast (from bone position) will hit the step when the
            // animated foot is over it during descent.

            if (showWeights)
            {
                Debug.DrawLine(
                    probe.point,
                    probe.point + Vector3.up * 0.15f,
                    Color.yellow);
            }
        }
    }

    // ─── Helpers ─────────────────────────────────────────────────────

    private Transform FindBone(string boneName)
    {
        return GetComponentsInChildren<Transform>()
            .FirstOrDefault(t => t.name == boneName);
    }

    private static Transform FindHint(Transform root, string hintName)
    {
        for (int i = 0; i < root.childCount; i++)
        {
            Transform child = root.GetChild(i);
            if (child.name == hintName) return child;
        }
        return null;
    }

    private Transform FindHint(string hintName)
    {
        return FindHint(transform, hintName);
    }

    // ─── OnGUI debug overlay ─────────────────────────────────────────

    private void OnGUI()
    {
        if (!showWeights || leftConstraint == null || rightConstraint == null) return;

        GUIStyle style = new GUIStyle(GUI.skin.label);
        style.fontSize = 14;
        style.fontStyle = FontStyle.Bold;

        Vector3 worldPos = transform.position + Vector3.up * 2f;
        Vector3 screenPos = Camera.main != null
            ? Camera.main.WorldToScreenPoint(worldPos)
            : Vector3.zero;

        if (screenPos.z > 0)
        {
            screenPos.y = Screen.height - screenPos.y;

            GUI.color = leftCurrentWeight > 0.5f ? Color.green : Color.white;
            GUI.Label(new Rect(screenPos.x - 80, screenPos.y - 30, 80, 24),
                $"L: {leftCurrentWeight:F2}", style);

            GUI.color = rightCurrentWeight > 0.5f ? Color.green : Color.white;
            GUI.Label(new Rect(screenPos.x + 10, screenPos.y - 30, 80, 24),
                $"R: {rightCurrentWeight:F2}", style);

            if (isLifting)
            {
                GUI.color = Color.yellow;
                GUI.Label(new Rect(screenPos.x - 40, screenPos.y - 55, 120, 24),
                    "LIFTING", style);
            }

            GUI.color = Color.white;
        }
    }
}
