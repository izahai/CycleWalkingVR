using System;

[Serializable]
public class AnglePacket
{
    public float angle_deg;   // Absolute crank angle
    public float ts;          // Sender timestamp (seconds)
}