using UnityEngine;
using System.Linq;

/// <summary>
/// Pure data provider — casts rays from each foot bone downward each frame
/// and stores the results publicly. No IK or Animation Rigging awareness.
///
/// FootIKDriver (and later StepStateMachine, PelvisController) reads
/// the .leftFoot / .rightFoot / .forwardProbe properties each frame.
/// </summary>
[DefaultExecutionOrder(-1)]
public class FootRaycaster : MonoBehaviour
{
    [Header("Bone References (auto-found if empty)")]
    [SerializeField] private Transform leftFootBone;
    [SerializeField] private Transform rightFootBone;

    [Header("Raycasting")]
    [SerializeField] private LayerMask groundLayer;
    [SerializeField] private float footRayLength = 2f;
    [SerializeField] private float forwardProbeDistance = 0.35f;
    [SerializeField] private float forwardProbeLength = 3f;

    [Header("Gizmos")]
    [SerializeField] private bool showDebugRays = true;

    // ─── Private backing fields (struct, must be read/write) ──────────
    private FootRaycastResult _left;
    private FootRaycastResult _right;
    private FootRaycastResult _probe;

    // ─── Public read-only results ────────────────────────────────────
    public FootRaycastResult leftFoot      => _left;
    public FootRaycastResult rightFoot     => _right;
    public FootRaycastResult forwardProbe  => _probe;

    // ─── Lifecycle ───────────────────────────────────────────────────

    private void Awake()
    {
        if (leftFootBone == null)
            leftFootBone = FindBone("mixamorig:LeftFoot");
        if (rightFootBone == null)
            rightFootBone = FindBone("mixamorig:RightFoot");

        if (leftFootBone == null || rightFootBone == null)
            Debug.LogError("[FootRaycaster] Could not find foot bones. " +
                "Assign them in the Inspector or ensure 'mixamorig:' bone naming.");
    }

    private void Update()
    {
        RaycastFoot(leftFootBone,  ref _left,  Color.green);
        RaycastFoot(rightFootBone, ref _right, Color.red);
        RaycastForwardProbe();
    }

    // ─── Foot raycast ────────────────────────────────────────────────

    private void RaycastFoot(Transform footBone, ref FootRaycastResult result, Color debugColor)
    {
        if (footBone == null)
        {
            result = default;
            return;
        }

        // Cast from slightly above the foot bone so the ray always starts
        // above the surface — even when the animated foot position clips
        // slightly into the ground.
        Vector3 origin = footBone.position + Vector3.up * 0.15f;

        if (Physics.Raycast(origin, Vector3.down, out RaycastHit hit, footRayLength, groundLayer))
        {
            result.hit          = true;
            result.point        = hit.point;
            result.normal       = hit.normal;
            result.distance     = hit.distance;
            result.hitTransform = hit.transform;

            if (showDebugRays)
            {
                Debug.DrawLine(origin, hit.point, debugColor);
                DrawCross(hit.point, debugColor, 0.04f);
            }
        }
        else
        {
            result.hit = false;

            if (showDebugRays)
                Debug.DrawRay(origin, Vector3.down * footRayLength, Color.gray);
        }
    }

    // ─── Forward-probe raycast ───────────────────────────────────────

    private void RaycastForwardProbe()
    {
        Vector3 origin = transform.position + Vector3.up * 1.0f
                         + transform.forward * forwardProbeDistance;

        if (Physics.Raycast(origin, Vector3.down, out RaycastHit hit, forwardProbeLength, groundLayer))
        {
            _probe.hit          = true;
            _probe.point        = hit.point;
            _probe.normal       = hit.normal;
            _probe.distance     = hit.distance;
            _probe.hitTransform = hit.transform;

            if (showDebugRays)
            {
                Debug.DrawLine(origin, hit.point, Color.cyan);
                DrawCross(hit.point, Color.cyan, 0.05f);
            }
        }
        else
        {
            _probe.hit = false;

            if (showDebugRays)
                Debug.DrawRay(origin, Vector3.down * forwardProbeLength, Color.gray * 0.5f);
        }
    }

    // ─── Helpers ─────────────────────────────────────────────────────

    private Transform FindBone(string boneName)
    {
        return GetComponentsInChildren<Transform>()
            .FirstOrDefault(t => t.name == boneName);
    }

    private static void DrawCross(Vector3 pos, Color color, float size)
    {
        Debug.DrawLine(pos + Vector3.left   * size, pos + Vector3.right  * size, color);
        Debug.DrawLine(pos + Vector3.forward * size, pos + Vector3.back   * size, color);
        Debug.DrawLine(pos + Vector3.up     * size, pos + Vector3.down   * size, color);
    }
}
