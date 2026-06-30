using UnityEngine;

[RequireComponent(typeof(Animator))]
public class AvatarFollow : MonoBehaviour
{
    [Header("Tracking")]
    [SerializeField] private Transform headset;

    [Header("Movement")]
    [SerializeField] private float floorHeight = 0f;
    [SerializeField] private float positionSmooth = 10f;
    [SerializeField] private float rotationSmooth = 10f;

    [Header("Animation")]
    [SerializeField] private float maxWalkSpeed = 1.5f;
    [SerializeField] private float animationDamping = 0.1f;

    [Tooltip("Animator playback speed while idle.")]
    [SerializeField] private float idleAnimatorSpeed = 1f;

    [Tooltip("Animator playback speed at full walking.")]
    [SerializeField] private float walkAnimatorSpeed = 2f;

    private Animator animator;
    private Vector3 lastHeadPos;

    private void Start()
    {
        animator = GetComponent<Animator>();
        lastHeadPos = headset.position;
    }

    private void Update()
    {
        // Follow player
        Vector3 targetPos = headset.position;
        targetPos.y = floorHeight;

        transform.position = Vector3.Lerp(
            transform.position,
            targetPos,
            positionSmooth * Time.deltaTime);

        // Rotate with headset yaw
        Vector3 forward = headset.forward;
        forward.y = 0f;

        if (forward.sqrMagnitude > 0.001f)
        {
            Quaternion targetRotation = Quaternion.LookRotation(forward);

            transform.rotation = Quaternion.Slerp(
                transform.rotation,
                targetRotation,
                rotationSmooth * Time.deltaTime);
        }

        // Calculate movement speed
        Vector3 delta = headset.position - lastHeadPos;
        delta.y = 0f;

        float worldSpeed = delta.magnitude / Mathf.Max(Time.deltaTime, 0.0001f);
        float normalizedSpeed = Mathf.Clamp01(worldSpeed / maxWalkSpeed);

        animator.SetFloat(
            "Speed",
            normalizedSpeed,
            animationDamping,
            Time.deltaTime);

        // Control animation playback speed
        animator.speed = Mathf.Lerp(
            idleAnimatorSpeed,
            walkAnimatorSpeed,
            normalizedSpeed);

        lastHeadPos = headset.position;
    }
}