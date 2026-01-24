using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class UdpCyclingLocomotion : MonoBehaviour
{
    [Serializable]
    class AnglePacket
    {
        public float angle_deg;   // absolute crank angle
        public float ts;          // sender timestamp (seconds)
    }

    [Header("UDP")]
    public int listenPort = 9000;

    [Header("Locomotion")]
    public float speedScale = 0.01f;   // deg/sec → units/sec
    public float maxSpeed = 10.0f;
    public float acceleration = 5.0f;  // units/sec^2

    [Header("Slope Detection")]
    public float slopeRayLength = 1.2f;
    public LayerMask groundMask = ~0; // default: everything
    public float slopeAnimScale = 1.5f;

    [Header("Animation")]
    public Animator animator;
    private string speedParam = "Speed";
    private string slopeParam = "Slope";


    [Header("Debug")]
    public bool logSpeed = true;
    public float logInterval = 0.5f;

    // --- Networking ---
    UdpClient client;
    Thread recvThread;

    AnglePacket latestPacket;
    bool hasPacket;
    readonly object packetLock = new object();

    // --- Motion ---
    float filteredSpeed;
    float nextLogTime;
    float slopeState;   // 0 = flat, 1 = uphill
    float slopeVelocity;

    // --- Angle tracking ---
    float lastAngle;
    float lastTime;
    bool hasLastSample;

    // --- Animation ---
    CharacterController controller;

    // --- Exposed Var ---
    public float CurrentSpeed => filteredSpeed;
    public bool IsGrounded => controller.isGrounded;
    public bool IsMoving => filteredSpeed > 0.1f;



    void Start()
    {
        client = new UdpClient(listenPort);
        recvThread = new Thread(ReceiveLoop);
        recvThread.IsBackground = true;
        recvThread.Start();

        controller = GetComponent<CharacterController>();

    }

    void ReceiveLoop()
    {
        IPEndPoint ep = new IPEndPoint(IPAddress.Any, listenPort);

        while (true)
        {
            try
            {
                byte[] data = client.Receive(ref ep);
                string json = Encoding.UTF8.GetString(data);
                AnglePacket packet = JsonUtility.FromJson<AnglePacket>(json);

                if (packet != null)
                {
                    lock (packetLock)
                    {
                        latestPacket = packet;
                        hasPacket = true;
                    }
                }
            }
            catch
            {
                // Ignore malformed packets / shutdown races
            }
        }
    }

    void FixedUpdate()
    {
        AnglePacket packet;

        lock (packetLock)
        {
            if (!hasPacket)
                return;

            packet = latestPacket;
        }

        // --- Initialize on first sample ---
        if (!hasLastSample)
        {
            lastAngle = packet.angle_deg;
            lastTime = packet.ts;
            hasLastSample = true;
            return;
        }

        float dt = packet.ts - lastTime;
        if (dt <= 0.0001f)
            return;

        // --- Compute angular velocity (deg/sec) ---
        float dAngle = Mathf.DeltaAngle(lastAngle, packet.angle_deg);
        float angularVelocity = Mathf.Abs(dAngle / dt);

        lastAngle = packet.angle_deg;
        lastTime = packet.ts;

        // --- Convert to locomotion speed ---
        float targetSpeed = Mathf.Clamp(
            angularVelocity * speedScale,
            0f,
            maxSpeed
        );

        // --- Physically stable acceleration ---
        filteredSpeed = Mathf.MoveTowards(
            filteredSpeed,
            targetSpeed,
            acceleration * Time.fixedDeltaTime
        );

        // --- Move avatar ---
        Vector3 move = transform.forward * filteredSpeed * Time.fixedDeltaTime;
        controller.Move(move);

        // --- Drive walking animation ---
        if (animator != null)
            animator.SetFloat(
                speedParam,
                filteredSpeed,
                0.1f,                // damping time
                Time.fixedDeltaTime
            );

        // --- Drive walking up animation ---
        float slope = ComputeSlope();
        animator.SetFloat(
            slopeParam,
            slope,
            0.1f,
            Time.fixedDeltaTime
        );

        if (logSpeed && Time.time >= nextLogTime)
        {
            //Debug.Log($"Humanoid speed: {filteredSpeed:F3} units/sec");
            //Debug.Log($"Humanoid slope: {slope:F3}");
            nextLogTime = Time.time + logInterval;
        }
    }

    void OnDestroy()
    {
        try
        {
            recvThread?.Abort();
        }
        catch { }

        client?.Close();
    }

    float ComputeSlope()
    {
        bool isGrounded = controller.isGrounded;
        bool isMovingForward = filteredSpeed > 0.1f;

        float target = 0f;

        if (isGrounded && isMovingForward)
        {
            // 1) Normal-based slope
            float normalSlope = 0f;
            Ray ray = new Ray(transform.position + Vector3.up * 0.2f, Vector3.down);
            if (Physics.Raycast(ray, out RaycastHit hit, slopeRayLength, groundMask))
            {
                float angle = Vector3.Angle(hit.normal, Vector3.up);
                normalSlope = Mathf.InverseLerp(5f, 35f, angle);
            }

            // 2) Step-based vertical intent (not raw velocity)
            float verticalIntent = controller.velocity.y > 0.05f ? 1f : 0f;

            target = Mathf.Max(normalSlope, verticalIntent);
        }

        // 3) Smooth with critically damped motion
        slopeState = Mathf.SmoothDamp(
            slopeState,
            target,
            ref slopeVelocity,
            0.5f   // smoothing time (tune this)
        );

        return slopeState * slopeAnimScale;
    }
}
