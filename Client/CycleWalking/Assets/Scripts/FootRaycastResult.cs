using UnityEngine;

/// <summary>
/// Data produced by FootRaycaster each frame, consumed by FootIKDriver
/// (and later by PelvisController, StepStateMachine, etc.).
///
/// Pure data — no IK or Animation Rigging awareness.
/// </summary>
[System.Serializable]
public struct FootRaycastResult
{
    /// <summary>Whether the raycast hit anything on the ground layer.</summary>
    public bool hit;

    /// <summary>World-space hit point (where the foot should land).</summary>
    public Vector3 point;

    /// <summary>Surface normal at the hit point.</summary>
    public Vector3 normal;

    /// <summary>Distance from ray origin to hit point.</summary>
    public float distance;

    /// <summary>The terrain/stair object that was hit.</summary>
    public Transform hitTransform;
}
