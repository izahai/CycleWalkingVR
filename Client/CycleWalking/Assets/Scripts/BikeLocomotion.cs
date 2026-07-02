using UnityEngine;

public class BikeLocomotion : MonoBehaviour
{
    [Header("Dependencies")]
    [SerializeField] private CharacterController controller;
    [SerializeField] private UdpReceiver udpReceiver;
    [SerializeField] private Transform cameraTransform;

    [Header("Movement Settings")]
    public float speedScale = 0.01f;   
    public float maxSpeed = 10.0f;
    public float acceleration = 5.0f;  

    private float currentSpeed;
    private float verticalVelocity; // Correctly tracks gravity over time
    
    private float lastAngle;
    private float lastTime;
    private bool isInitialized;

    void Start()
    {
        if (controller == null) Debug.LogError("[BikeLocomotion] Missing CharacterController!");
        if (udpReceiver == null) Debug.LogError("[BikeLocomotion] Missing UdpReceiver!");
        if (cameraTransform == null) Debug.LogError("[BikeLocomotion] Missing Camera Transform!");
    }

    void FixedUpdate()
    {
        if (controller == null) return;

        // 1. Sync the VR headset position with the controller FIRST in the physics loop
        if (cameraTransform != null)
        {
            UpdateCharacterControllerPosition();
        }

        if (udpReceiver == null) return;

        // 2. Fetch data from the network module
        if (!udpReceiver.TryGetLatestPacket(out AnglePacket packet)) 
            return; 

        // 3. Initialize tracking on the very first packet
        if (!isInitialized)
        {
            lastAngle = packet.angle_deg;
            lastTime = packet.ts;
            isInitialized = true;
            return;
        }

        // 4. Calculate delta time from the packet sender
        float dt = packet.ts - lastTime;
        if (dt <= 0.0001f) return;

        // 5. Calculate angular speed and target velocity
        float dAngle = Mathf.DeltaAngle(lastAngle, packet.angle_deg);
        float angularVelocity = Mathf.Abs(dAngle / dt);
        float targetSpeed = Mathf.Clamp(angularVelocity * speedScale, 0f, maxSpeed);

        lastAngle = packet.angle_deg;
        lastTime = packet.ts;

        // 6. Smooth acceleration
        currentSpeed = Mathf.MoveTowards(currentSpeed, targetSpeed, acceleration * Time.fixedDeltaTime);
        
        // 7. Determine direction based on camera view
        Vector3 forward = transform.forward;
        if (cameraTransform != null)
        {
            forward = Vector3.ProjectOnPlane(cameraTransform.forward, Vector3.up).normalized;
        }

        // 8. Handle GRAVITY correctly
        if (controller.isGrounded)
        {
            verticalVelocity = -1.0f; // Solid grounding force
        }
        else
        {
            verticalVelocity += Physics.gravity.y * Time.fixedDeltaTime; // Real-world acceleration
        }

        // 9. Combine movements into a synchronized displacement vector
        Vector3 moveDirection = (forward * currentSpeed * Time.fixedDeltaTime) + (Vector3.up * verticalVelocity * Time.fixedDeltaTime);

        // Final physics movement execution
        controller.Move(moveDirection);
    }

    /// <summary>
    /// Re-centers the XR Rig root inside FixedUpdate to maintain solid collision states.
    /// </summary>
    private void UpdateCharacterControllerPosition()
    {
        Vector3 cameraLocalPos = controller.transform.InverseTransformPoint(cameraTransform.position);
        Vector3 centerOffset = new Vector3(cameraLocalPos.x, 0, cameraLocalPos.z);

        // Move the physical CharacterController by the offset
        controller.Move(controller.transform.TransformDirection(centerOffset));

        // Push the camera tracking space back by the exact same amount so the camera doesn't jump
        if (cameraTransform.parent != null)
        {
            cameraTransform.parent.position -= controller.transform.TransformDirection(centerOffset);
        }

        // Dynamic capsule height adjustment based on player height
        controller.height = Mathf.Max(cameraLocalPos.y, 1.0f);
        controller.center = new Vector3(0, controller.height / 2f + controller.skinWidth, 0);
    }
    
    public float GetCurrentSpeed() => currentSpeed;
}