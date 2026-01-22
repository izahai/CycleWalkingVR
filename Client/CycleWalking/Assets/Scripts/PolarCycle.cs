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
    public float animationScale = 0.01f;   // deg/sec → units/sec
    public float maxSpeed = 10.0f;
    public float acceleration = 5.0f;  // units/sec^2

    [Header("Animation")]
    public Animator animator;
    public string speedParam = "WalkSpeed";

    [Header("Debug")]
    public bool logSpeed;
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

    // --- Angle tracking ---
    float lastAngle;
    float lastTime;
    bool hasLastSample;

    void Start()
    {
        client = new UdpClient(listenPort);
        recvThread = new Thread(ReceiveLoop);
        recvThread.IsBackground = true;
        recvThread.Start();
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

        if (logSpeed && Time.time >= nextLogTime)
        {
            Debug.Log($"Humanoid speed: {filteredSpeed:F3} units/sec");
            nextLogTime = Time.time + logInterval;
        }

        // --- Move avatar ---
        transform.position -=
            Vector3.forward * filteredSpeed * Time.fixedDeltaTime;

        // --- Drive animation ---
        if (animator != null)
            animator.SetFloat(speedParam, filteredSpeed*animationScale);
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
}
