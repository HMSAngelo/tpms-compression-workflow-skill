---
name: tpms-ntopology-headless
description: Run an editable nTopology TPMS notebook with nTop Automate and verify the linear mesh handoff to HyperMesh.
---

# nTopology headless TPMS handoff

1. Check the installed nTop Automate runtime using the local executable's version and help options. The historical reference used 5.9.2. Use a configured license reference and keep credentials out of logs and the case package.
2. Use an authorized editable notebook with the required TPMS geometry. Work on a copy. Verify which inputs it exposes, the unit convention, and where it exports the mesh. The package has no notebook or general notebook authoring API.
3. For Automation inputs, use the executable's documented template option to inspect the input schema. Use the installed version's syntax to pass the input JSON and write the output JSON in the new case directory. See the [workflow reference](../../workflow.md#ntopology-native-solid-and-linear-mesh) for the tested invocation and mesh recipe. Leave `--trustnotebook` unset.
4. If the notebook uses a hardcoded export path, retarget the copy before running. The [5.9.2 container helper](../../../scripts/container_592.py) is version-specific and requires a compatible donor. Verify the copy and its output path with a small run before relying on it.
5. Check for a fresh specimen-only INP, nonzero node and `C3D4` element counts, expected dimensions and preserved units. Record native solid volume and exported mesh volume separately. Pass the verified linear specimen mesh to the [HyperMesh workflow](../hypermesh-evidence-meshing/SKILL.md#ntopology-tpms-mesh-for-abaqusexplicit).
