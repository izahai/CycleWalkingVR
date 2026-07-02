using UnityEngine;
using UnityEditor;
using UnityEngine.Animations.Rigging;
using UnityEditor.Animations;
using System.Linq;

public static class YBotIKSetup
{
    // -------- Asset paths (relative to project root) --------
    private const string PrefabPath  = "Assets/Prefabs/Y Bot Unpack.prefab";
    private const string AnimControllerPath = "Assets/Mixamo/Controllers/WalkingAnimator.controller";

    // -------- Skeleton naming --------
    private const string BonePrefix = "mixamorig:";

    [MenuItem("Tools/YBot/Setup IK Rig", false, 100)]
    public static void SetupIKRig()
    {
        // ---------------------------------------------------------------
        // 1. Load and modify the WalkingAnimator controller
        // ---------------------------------------------------------------
        var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(AnimControllerPath);
        if (controller == null)
        {
            EditorUtility.DisplayDialog("Error",
                $"Could not find AnimatorController at:\n{AnimControllerPath}", "OK");
            return;
        }
        ModifyAnimatorController(controller);

        // ---------------------------------------------------------------
        // 2. Load and modify the Y Bot Unpack prefab
        // ---------------------------------------------------------------
        GameObject root = PrefabUtility.LoadPrefabContents(PrefabPath);
        if (root == null)
        {
            EditorUtility.DisplayDialog("Error",
                $"Could not load prefab at:\n{PrefabPath}", "OK");
            return;
        }

        bool modified = false;
        try
        {
            // ---------------------------------------------------------------
            // 2a. Check if IK Rig already exists → prompt to overwrite
            // ---------------------------------------------------------------
            var existingRigBuilder = root.GetComponent<RigBuilder>();
            if (existingRigBuilder != null)
            {
                var existingFootRig = root.transform.Find("FootRig");
                if (existingFootRig != null && existingFootRig.GetComponent<Rig>() != null)
                {
                    if (!EditorUtility.DisplayDialog("IK Rig Already Exists",
                        "Y Bot Unpack.prefab already has a FootRig with Rig component.\n" +
                        "Do you want to overwrite it (destroy old and create fresh)?",
                        "Overwrite", "Cancel"))
                    {
                        return; // user cancelled
                    }
                    // Destroy old hierarchy
                    Object.DestroyImmediate(existingFootRig.gameObject);
                    Object.DestroyImmediate(existingRigBuilder);
                    modified = true;
                }
            }

            // ---------------------------------------------------------------
            // 2b. Add RigBuilder on root
            // ---------------------------------------------------------------
            var rigBuilder = root.AddComponent<RigBuilder>();
            Undo.RegisterCreatedObjectUndo(rigBuilder, "Add RigBuilder");
            modified = true;

            // ---------------------------------------------------------------
            // 2c. Create FootRig child with Rig component
            // ---------------------------------------------------------------
            var footRigGO = new GameObject("FootRig");
            footRigGO.transform.SetParent(root.transform);
            footRigGO.transform.localPosition = Vector3.zero;
            footRigGO.transform.localRotation = Quaternion.identity;
            var rig = footRigGO.AddComponent<Rig>();
            rig.weight = 1f;
            Undo.RegisterCreatedObjectUndo(footRigGO, "Create FootRig");
            modified = true;

            // ---------------------------------------------------------------
            // 2d. Create LeftFootMover / RightFootMover (IK constraint owners)
            // ---------------------------------------------------------------
            var leftMoverGO  = CreateChild(footRigGO.transform, "LeftFootMover");
            var rightMoverGO = CreateChild(footRigGO.transform, "RightFootMover");
            Undo.RegisterCreatedObjectUndo(leftMoverGO,  "Create LeftFootMover");
            Undo.RegisterCreatedObjectUndo(rightMoverGO, "Create RightFootMover");
            modified = true;

            // ---------------------------------------------------------------
            // 2e. Create LeftTarget / RightTarget (IK position targets)
            // ---------------------------------------------------------------
            var leftTargetGO  = CreateChild(leftMoverGO.transform,  "LeftTarget");
            var rightTargetGO = CreateChild(rightMoverGO.transform, "RightTarget");
            Undo.RegisterCreatedObjectUndo(leftTargetGO,  "Create LeftTarget");
            Undo.RegisterCreatedObjectUndo(rightTargetGO, "Create RightTarget");
            modified = true;

            // ---------------------------------------------------------------
            // 2f. Create LeftHint / RightHint (IK knee-hint transforms)
            // ---------------------------------------------------------------
            var leftHintGO  = CreateChild(root.transform, "LeftHint");
            var rightHintGO = CreateChild(root.transform, "RightHint");
            Undo.RegisterCreatedObjectUndo(leftHintGO,  "Create LeftHint");
            Undo.RegisterCreatedObjectUndo(rightHintGO, "Create RightHint");
            modified = true;

            // ---------------------------------------------------------------
            // 2g. Find skeleton bones by name
            // ---------------------------------------------------------------
            var leftUpLeg  = FindBone(root, BonePrefix + "LeftUpLeg");
            var leftLeg    = FindBone(root, BonePrefix + "LeftLeg");
            var leftFoot   = FindBone(root, BonePrefix + "LeftFoot");
            var rightUpLeg = FindBone(root, BonePrefix + "RightUpLeg");
            var rightLeg   = FindBone(root, BonePrefix + "RightLeg");
            var rightFoot  = FindBone(root, BonePrefix + "RightFoot");

            if (!ValidateBones(leftUpLeg, leftLeg, leftFoot, rightUpLeg, rightLeg, rightFoot))
                return; // bones missing — dialog already shown

            // ---------------------------------------------------------------
            // 2h. Position targets at foot world positions (neutral IK pose)
            // ---------------------------------------------------------------
            leftTargetGO.transform.position  = leftFoot.position;
            rightTargetGO.transform.position = rightFoot.position;

            // Hints: behind foot, slightly below, so knee bends forward
            Vector3 hintLocal = new Vector3(0f, -0.05f, -0.1f);
            leftHintGO.transform.position  = leftFoot.position  + leftFoot.TransformDirection(hintLocal);
            rightHintGO.transform.position = rightFoot.position + rightFoot.TransformDirection(hintLocal);
            leftHintGO.transform.rotation  = leftFoot.rotation;
            rightHintGO.transform.rotation = rightFoot.rotation;

            // ---------------------------------------------------------------
            // 2i. Add TwoBoneIKConstraints and wire bones / targets / hints
            // ---------------------------------------------------------------
            AddTwoBoneIKConstraint(leftMoverGO,  leftUpLeg,  leftLeg,  leftFoot,
                                   leftTargetGO.transform,  leftHintGO.transform);
            AddTwoBoneIKConstraint(rightMoverGO, rightUpLeg, rightLeg, rightFoot,
                                   rightTargetGO.transform, rightHintGO.transform);

            // ---------------------------------------------------------------
            // 2j. Wire RigBuilder → FootRig Rig layer
            // ---------------------------------------------------------------
            var rigBuilderSO = new SerializedObject(rigBuilder);
            var layersProp = rigBuilderSO.FindProperty("m_RigLayers");
            layersProp.arraySize++;

            var newLayer = layersProp.GetArrayElementAtIndex(layersProp.arraySize - 1);
            newLayer.FindPropertyRelative("m_Rig").objectReferenceValue = rig;
            newLayer.FindPropertyRelative("m_Active").boolValue = true;
            rigBuilderSO.ApplyModifiedProperties();

            // ---------------------------------------------------------------
            // 2k. (Optional) Add BoneRenderer for debugging
            // ---------------------------------------------------------------
            var existingBoneRenderer = root.GetComponent<BoneRenderer>();
            if (existingBoneRenderer == null)
            {
                var hips = FindBone(root, BonePrefix + "Hips");
                if (hips != null)
                {
                    var allBones = hips.GetComponentsInChildren<Transform>(true);
                    var boneRenderer = root.AddComponent<BoneRenderer>();
                    boneRenderer.transforms = allBones;
                    Undo.RegisterCreatedObjectUndo(boneRenderer, "Add BoneRenderer");
                    modified = true;
                }
            }

            // ---------------------------------------------------------------
            // 2l. Assign WalkingAnimator controller to Animator component
            // ---------------------------------------------------------------
            var animator = root.GetComponent<Animator>();
            if (animator != null)
            {
                SerializedObject animatorSO = new SerializedObject(animator);
                var controllerProp = animatorSO.FindProperty("m_Controller");
                if (controllerProp.objectReferenceValue == null)
                {
                    controllerProp.objectReferenceValue = controller;
                    animatorSO.ApplyModifiedProperties();
                    modified = true;
                }
            }
        }
        finally
        {
            // Save changes to the prefab asset on disk
            if (modified)
            {
                PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
                AssetDatabase.Refresh();
                Debug.Log("[YBotIKSetup] IK Rig successfully added to Y Bot Unpack.prefab");
            }
            PrefabUtility.UnloadPrefabContents(root);
        }

        EditorUtility.DisplayDialog("IK Setup Complete",
            "IK Rig has been added to Y Bot Unpack.prefab.\n\n" +
            "The WalkingAnimator.controller now has IK Pass enabled\n" +
            "and a 'Slope' float parameter.\n\n" +
            "Next: Drag the updated prefab into your scene,\n" +
            "add a CharacterController and your locomotion script.",
            "OK");
    }

    // ======================================================================
    // Helper methods
    // ======================================================================

    /// <summary>Create a child GameObject with zero local position/rotation.</summary>
    private static GameObject CreateChild(Transform parent, string name)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent);
        go.transform.localPosition = Vector3.zero;
        go.transform.localRotation = Quaternion.identity;
        return go;
    }

    /// <summary>Find a Transform by name anywhere in the hierarchy.</summary>
    private static Transform FindBone(GameObject root, string boneName)
    {
        return root.GetComponentsInChildren<Transform>()
            .FirstOrDefault(t => t.name == boneName);
    }

    /// <summary>Show dialog if any bones are null; return true if all present.</summary>
    private static bool ValidateBones(params Transform[] bones)
    {
        var missing = string.Join(" ",
            bones.Where(b => b == null)
                 .Select((_, i) => new[] { "LeftUpLeg", "LeftLeg", "LeftFoot",
                                           "RightUpLeg", "RightLeg", "RightFoot" }[i]));
        if (missing.Length > 0)
        {
            EditorUtility.DisplayDialog("Bones Not Found",
                $"Could not find these bones in the prefab hierarchy:\n{missing}\n\n" +
                "The prefab may not be a Mixamo-rigged character with 'mixamorig:' bone prefix.",
                "OK");
            return false;
        }
        return true;
    }

    /// <summary>
    /// Adds a TwoBoneIKConstraint to <paramref name="owner"/> and wires all
    /// fields via SerializedObject (required because TwoBoneIKConstraintData
    /// is a struct that copies by value).
    /// </summary>
    private static void AddTwoBoneIKConstraint(
        GameObject owner,
        Transform rootBone, Transform midBone, Transform tipBone,
        Transform target, Transform hint)
    {
        var constraint = owner.AddComponent<TwoBoneIKConstraint>();

        SerializedObject so = new SerializedObject(constraint);
        so.FindProperty("m_Data.m_Root").objectReferenceValue     = rootBone;
        so.FindProperty("m_Data.m_Mid").objectReferenceValue      = midBone;
        so.FindProperty("m_Data.m_Tip").objectReferenceValue      = tipBone;
        so.FindProperty("m_Data.m_Target").objectReferenceValue   = target;
        so.FindProperty("m_Data.m_Hint").objectReferenceValue     = hint;
        so.FindProperty("m_Data.m_TargetPositionWeight").floatValue = 1f;
        so.FindProperty("m_Data.m_TargetRotationWeight").floatValue  = 1f;
        so.FindProperty("m_Data.m_HintWeight").floatValue            = 1f;
        so.ApplyModifiedProperties();
    }

    /// <summary>
    /// Enables IK Pass on the Base Layer and adds a "Slope" float parameter
    /// if neither has been done yet.
    /// </summary>
    private static void ModifyAnimatorController(AnimatorController controller)
    {
        bool changed = false;

        // --- Enable IK Pass on Base Layer ---
        var layers = controller.layers;
        if (layers.Length > 0)
        {
            var baseLayer = layers[0];
            if (!baseLayer.iKPass)
            {
                baseLayer.iKPass = true;
                layers[0] = baseLayer;
                controller.layers = layers;
                changed = true;
                Debug.Log("[YBotIKSetup] Enabled IK pass on WalkingAnimator Base Layer");
            }
        }

        // --- Add "Slope" float parameter if missing ---
        if (controller.parameters.All(p => p.name != "Slope"))
        {
            controller.AddParameter("Slope", AnimatorControllerParameterType.Float);
            changed = true;
            Debug.Log("[YBotIKSetup] Added 'Slope' Float parameter to WalkingAnimator");
        }

        if (changed)
        {
            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssetIfDirty(controller);
        }
    }
}
