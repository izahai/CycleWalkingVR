using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class UdpReceiver : MonoBehaviour
{
    [Header("Network Settings")]
    public int listenPort = 9000;

    private UdpClient client;
    private Thread recvThread;
    
    private AnglePacket latestPacket;
    private bool hasNewPacket;
    private readonly object packetLock = new object();

    void Start()
    {
        try
        {
            client = new UdpClient(listenPort);
            recvThread = new Thread(ReceiveLoop) { IsBackground = true };
            recvThread.Start();
            Debug.Log($"[UDP] Listening on port {listenPort}");
        }
        catch (Exception e)
        {
            Debug.LogError($"[UDP] Failed to start listening: {e.Message}");
        }
    }

    private void ReceiveLoop()
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
                    Debug.Log($"[UDP RX] Received {data.Length} bytes from {ep} | Raw JSON: {json} | Parsed -> Angle: {packet.angle_deg}°, TS: {packet.ts}");
                    lock (packetLock)
                    {
                        latestPacket = packet;
                        hasNewPacket = true;
                    }
                }
            }
            catch
            {
                // Thread abort or socket close handled gracefully
                break; 
            }
        }
    }

    // Public API for other scripts to scale and pull data cleanly
    public bool TryGetLatestPacket(out AnglePacket packet)
    {
        lock (packetLock)
        {
            packet = latestPacket;
            if (hasNewPacket)
            {
                hasNewPacket = false; // Consume the packet flag
                return true;
            }
            return packet != null; // Return true if we have at least cached data
        }
    }

    void OnDestroy()
    {
        client?.Close();
        recvThread?.Abort();
    }
}