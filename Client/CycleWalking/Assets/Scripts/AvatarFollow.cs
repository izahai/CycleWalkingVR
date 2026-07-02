using UnityEngine;

[RequireComponent(typeof(Animator))]
public class AvatarFollow : MonoBehaviour
{
    [Header("Tracking")]
    [SerializeField] private Transform headset;

    [Header("Movement & Terrain")]
    [SerializeField] private LayerMask groundLayer;
    [SerializeField] private float positionSmooth = 10f;
    [SerializeField] private float rotationSmooth = 5f;
    [SerializeField] private float stepLookAhead = 0.25f;

    [Header("Animation")]
    [SerializeField] private float maxWalkSpeed = 1.5f;
    [SerializeField] private float animationDamping = 0.1f;
    [SerializeField] private float idleAnimatorSpeed = 1f;
    [SerializeField] private float walkAnimatorSpeed = 1.5f;

    [Header("Pedal Source (optional)")]
    [SerializeField] private BikeLocomotion pedalSource;
    [SerializeField] private bool followPedalXZ;

    private Animator animator;
    private Vector3 lastHeadPos;
    private float targetPelvisHeight;

    private void Start()
    {
        animator = GetComponent<Animator>();
        lastHeadPos = headset.position;
    }

    private void Update()
    {
        CalculateTargetHeights();

        // ─── Position ────────────────────────────────────────────────
        if (pedalSource != null && followPedalXZ)
        {
            // Pedal mode: keep body XZ where the CharacterController is,
            // only adjust Y from raycast
            Vector3 targetPos = transform.position;
            targetPos.y = targetPelvisHeight;
            transform.position = Vector3.Lerp(
                transform.position, targetPos, positionSmooth * Time.deltaTime);
        }
        else
        {
            // Headset mode: follow headset XZ, use raycast Y
            Vector3 targetPos = headset.position;
            targetPos.y = targetPelvisHeight;
            transform.position = Vector3.Lerp(
                transform.position, targetPos, positionSmooth * Time.deltaTime);
        }

        // ─── Rotation (always from headset yaw) ──────────────────────
        Vector3 forward = headset.forward;
        forward.y = 0f;

        if (forward.sqrMagnitude > 0.001f)
        {
            Quaternion targetRotation = Quaternion.LookRotation(forward);
            transform.rotation = Quaternion.Slerp(
                transform.rotation, targetRotation, rotationSmooth * Time.deltaTime);
        }

        // ─── Animation Speed ─────────────────────────────────────────
        float worldSpeed;
        if (pedalSource != null)
        {
            worldSpeed = pedalSource.GetCurrentSpeed();
        }
        else
        {
            // Use headset velocity
            Vector3 delta = headset.position - lastHeadPos;
            delta.y = 0f;
            worldSpeed = delta.magnitude / Mathf.Max(Time.deltaTime, 0.0001f);
        }

        float normalizedSpeed = Mathf.Clamp01(worldSpeed / maxWalkSpeed);
        animator.SetFloat("Speed", normalizedSpeed, animationDamping, Time.deltaTime);
        animator.speed = Mathf.Lerp(idleAnimatorSpeed, walkAnimatorSpeed, normalizedSpeed);

        lastHeadPos = headset.position;
    }

    private void CalculateTargetHeights()
    {
        Vector3 downRayOrigin = new Vector3(headset.position.x, headset.position.y + 1f, headset.position.z);

        if (Physics.Raycast(downRayOrigin, Vector3.down, out RaycastHit hit, 5f, groundLayer))
        {
            targetPelvisHeight = hit.point.y;
        }

        // Forward probe debug ray (the actual stair detection is now in FootRaycaster)
        Vector3 forwardDirection = headset.forward;
        forwardDirection.y = 0f;
        forwardDirection.Normalize();

        Vector3 aheadRayOrigin = downRayOrigin + (forwardDirection * stepLookAhead);
        Debug.DrawRay(aheadRayOrigin, Vector3.down * 3f, Color.red);
        Debug.DrawRay(downRayOrigin, Vector3.down * 3f, Color.green);
    }
}