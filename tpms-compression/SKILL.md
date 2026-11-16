---
name: tpms-compression
description: Plan, build, check, run, and report Windows TPMS compression tests between rigid plates using optional SolidWorks CAD, native nTopology modeling, HyperMesh second-order tetrahedra, and Abaqus/Explicit. Use for natural-language TPMS compression cases, 无界面 TPMS 压缩, command-line handoffs, job status, and checkpoint recovery. Covers multiple TPMS families; does not assume HPS geometry or load settings.
---

# TPMS compression

Use the pipeline **SolidWorks (only when needed) → nTopology → HyperMesh → Abaqus/Explicit**. Use PowerShell, Python, Tcl, vendor batch programs, and native noninteractive APIs. Do not use desktop automation or drive a GUI. Read [the workflow reference](references/workflow.md) before invoking adapters. Use its version matrix and verified HPS example to identify reusable steps and case-specific gaps.

For each stage, open the bundled [nTopology Automate guide](references/dependencies/ntopology/SKILL.md), [HyperMesh evidence meshing skill](references/dependencies/hypermesh-evidence-meshing/SKILL.md), or [Abaqus general scripting skill](references/dependencies/abaqus/general/SKILL.md). Use a separately installed `solidworks-automation` skill only if external CAD is required. Use the project workflow to select the solver and verify the handoffs. The HyperMesh UI guide and Abaqus/Standard static templates serve separate requests.

1. Determine whether the request is to prepare, datacheck, solve, check status, pause, or resume. A request to continue building or checking the workflow does not resume a paused simulation. For job control, read the recovery section before acting.
2. Turn the request and its source files into a case record. Include geometry, mesh, material, rigid plates, contact, loading, outputs, and runtime. Record units and the source for each consequential value. Preserve explicitly supplied settings. If a value can be inferred from an authorized source, identify the inference; do not invent missing material data, physical loads, or acceptance limits. Complete independent steps even if one input blocks analysis.
3. Run each required tool with fresh, case-specific output paths. Keep new artifacts under a dedicated C-drive case directory outside Codex; put Abaqus work and scratch under a new per-job directory in `C:\SIMULIA\temp`. Record the exact input and output paths, versions, commands, logs, and handoff counts. Verify that outputs were produced from the intended inputs before passing them on.
4. Author and mesh the specimen in nTopology. Export a linear mesh, then elevate the order in HyperMesh and verify the `C3D10M` connectivity and quality. Use temporary zero-thickness platen surfaces in HyperMesh to map regular square grids. Delete the geometry, create a separate reference node at each plate center, and export the `R3D4` meshes with their reference-node sets. In Abaqus, bind the imported reference nodes to their rigid bodies and define constraints and contact. Run native datacheck on that exact deck in datacheck or solve mode. Submit when solve is requested and the deck passes.
5. Report the highest verified stage. For a solve, verify solver completion and requested stroke, and deliver the ODB, loaded-plate force–displacement data, and energy and mass-scaling checks appropriate to the case. Label partial results and numerical or physical limitations explicitly.

## Dependency update checks

At the start of a workflow, inventory the installed versions and provenance of this skill and the SolidWorks, nTopology adapter, HyperMesh, and Abaqus skills actually needed. When a dependency has a verifiable upstream, compare its installed revision and local modifications with the current upstream; otherwise record that no upstream/version is known and do not claim it is current. Assess compatibility with the installed software and preserve local fixes before updating. Record the check date, source, revision, differences, outcome, and any unverified dependencies in the case record. Do not silently replace locally modified instructions or execute unreviewed upstream code.

