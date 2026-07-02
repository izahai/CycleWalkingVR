Your current script is a solid foundation—it moves the avatar to the correct 2D plane and accurately handles the movement blend based on headset velocity.

To bridge the gap between this script and precise stair climbing, **your immediate next MVP milestone is to replace that hardcoded `floorHeight = 0f` with dynamic raycasting.** Before you even touch IK rigging, your code must dynamically discover where the stairs are. Here is exactly what to modify in Unity next.

---

## Step 1: Upgrading the Code to "See" the Stairs

Instead of clamping the avatar to a flat `floorHeight`, we will shoot a raycast downward from the headset's position to find the current step's height, and a raycast slightly forward to predict the next step's height.

Replace your current script with this updated MVP version:

```csharp
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class AvatarFollow : MonoBehaviour
{
    [Header("Tracking")]
    [SerializeField] private Transform headset;

    [Header("Movement & Terrain")]
    [SerializeField] private LayerMask groundLayer; // Set this to your Stairs/Floor layer
    [SerializeField] private float positionSmooth = 10f;
    [SerializeField] private float rotationSmooth = 5f; // Lowered slightly to prevent snappy VR rotation
    [SerializeField] private float stepLookAhead = 0.25f; // Distance ahead to check for the next step

    [Header("Animation")]
    [SerializeField] private float maxWalkSpeed = 1.5f;
    [SerializeField] private float animationDamping = 0.1f;
    [SerializeField] private float idleAnimatorSpeed = 1f;
    [SerializeField] private float walkAnimatorSpeed = 1.5f;

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
        // 1. Calculate Ground and Stair Height dynamically
        CalculateTargetHeights();

        // 2. Follow player XZ position, but use dynamic Y from Raycast
        Vector3 targetPos = headset.position;
        targetPos.y = targetPelvisHeight; 

        transform.position = Vector3.Lerp(
            transform.position,
            targetPos,
            positionSmooth * Time.deltaTime);

        // 3. Smooth Body Rotation (Yaw only)
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

        // 4. Calculate movement speed for Blend Tree
        Vector3 delta = headset.position - lastHeadPos;
        delta.y = 0f;

        float worldSpeed = delta.magnitude / Mathf.Max(Time.deltaTime, 0.0001f);
        float normalizedSpeed = Mathf.Clamp01(worldSpeed / maxWalkSpeed);

        animator.SetFloat("Speed", normalizedSpeed, animationDamping, Time.deltaTime);
        animator.speed = Mathf.Lerp(idleAnimatorSpeed, walkAnimatorSpeed, normalizedSpeed);

        lastHeadPos = headset.position;
    }

    private void CalculateTargetHeights()
    {
        // Raycast straight down from the headset's horizontal position
        Vector3 downRayOrigin = new Vector3(headset.position.x, headset.position.y + 1f, headset.position.z);
        
        if (Physics.Raycast(downRayOrigin, Vector3.down, out RaycastHit hit, 5f, groundLayer))
        {
            // This is the floor/step directly beneath the user
            targetPelvisHeight = hit.point.y;
        }

        // OPTIONAL VISUALIZATION: Predict the next step height ahead of the user
        Vector3 forwardDirection = headset.forward;
        forwardDirection.y = 0f;
        forwardDirection.Normalize();

        Vector3 aheadRayOrigin = downRayOrigin + (forwardDirection * stepLookAhead);
        Debug.DrawRay(aheadRayOrigin, Vector3.down * 3f, Color.red);
        Debug.DrawRay(downRayOrigin, Vector3.down * 3f, Color.green);
    }
}

```

---

## Step 2: What to setup in Unity Editor right now

1. **Assign a Layer:** Select all of your 3D stair assets in the inspector. Change their **Layer** to a new layer named `Ground` or `Stairs`.
2. **Update the Component:** On your avatar's `AvatarFollow` component, set the **Ground Layer** dropdown mask to match that `Ground/Stairs` layer you just made.
3. **Press Play and Watch:** Walk up your stairs in VR or move the headset object manually in the scene view.
* Look at the Scene tab. You will see green and red debug lines tracking the floor.
* The avatar's whole body should now automatically smoothly glide upward onto the steps because `targetPelvisHeight` updates dynamically.



---

## What this achieves for your MVP

By finishing this step, you have solved **Phase 2 (Procedural Detection)** and the pelvis movement portion of **Phase 3**. Your avatar no longer clips through the stairs horizontally; instead, the whole body smoothly ascends the incline.

Because the pelvis now lifts naturally to the correct $Y$ height, your next step will simply be installing Unity's **Animation Rigging** package to snap the feet down to those exact green/red raycast hit positions so they don't slide.