# Abaqus Agent Playbook — End-to-End Simulation Tasks

This playbook tells an AI agent (Claude Code, Codex, opencode, Gemini CLI, ...) how to
orchestrate a **complete Abaqus simulation task** using this repository's skills.
Follow it whenever the user asks to *run* an analysis, not just write a script.

> 中文说明：本文件是 agent 执行 Abaqus 仿真任务的「总流程」——澄清 → 生成 →
> 无头运行 → 日志诊断 → 迭代 → 验证 → 报告。所有细节在 general/reference 的
> 5 个执行文档中。

## 0. Read Order (progressive disclosure)

| Goal | Read |
|------|------|
| Understand the library | `CLAUDE.md` (or `AGENTS.md`) |
| Structure a full task | this file |
| Generate a model script | `abaqus_scriptcontrol_skills/general/SKILL.md` + `reference/*` |
| Run headlessly | `general/reference/headless_execution.md` |
| Fix failures | `general/reference/error_diagnosis.md` |
| Read results | `general/reference/postprocess_odb.md` |
| Prove correctness | `general/reference/verification.md` |
| Fortran subroutine needed? | `abaqus_subroutine_skills/SKILL.md` + `reference/` |

## 1. The Agent Execution Loop (mandatory)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INPUTS    resolve material, dimensions, load and solver  │
│              from the request and case sources             │
│ 2. GENERATE  model script per the Script Generation         │
│              Standard (10-section skeleton)                 │
│ 3. RUN       abaqus cae noGUI=model.py → abaqus job=...     │
│ 4. DIAGNOSE  parse .sta/.msg/.dat; map symptom → fix        │
│ 5. ITERATE   apply fix → re-run (max ~3 attempts, then      │
│              report to the user)                            │
│ 6. VERIFY    extract from .odb; compare with benchmarks;    │
│              energy balance; mesh convergence               │
│ 7. REPORT    summary table (model, results, verification,   │
│              warnings)                                      │
└─────────────────────────────────────────────────────────────┘
```

### Step 1 — Resolve inputs and execution mode

Read the request and case sources for material, dimensions, loading, solver, and whether the user asked for preparation, datacheck, solve or job control. Record values and their sources. Where an essential case value is missing, continue independent work and identify the dependent stage. Use numerical defaults only when explicitly appropriate, such as a labelled synthetic benchmark.

### Step 2 — Generate

- Follow the mandatory 10-section skeleton in `CLAUDE.md`
- Every dimension line has a unit comment: `length = 100.0  # mm`
- Use N-mm-MPa units ONLY (see the conversion table)
- Add `mdb.jobs[...].writeInput(consistencyChecking=OFF)` for inspectability

### Step 3 — Run headless

For an imported FE specimen, preserve its verified mesh. Generate the case deck using the selected launcher or an external writer. Run native datacheck before a solve and proceed only when the requested mode includes solve and that exact deck passed. Review [headless execution](general/reference/headless_execution.md) for terminal-state evidence.

```bash
abaqus cae noGUI=model_setup.py
# Inspect the native check files before submitting the solve.
abaqus job=Job-1-check input=Job-1.inp datacheck interactive
abaqus job=Job-1 input=Job-1.inp cpus=4 interactive
```

### Step 4 — Diagnose (symptom → fix)

| Symptom | Where | First action |
|---------|-------|--------------|
| cutbacks / too many attempts | `.sta`, `.msg` | see `error_diagnosis.md` table A |
| zero pivot / singular | `.msg` | check BCs & constraints |
| negative eigenvalue | `.msg` | rigid body mode or instability |
| distorted elements | `.msg` | refine mesh / element type |
| NaN | `.msg` | units or subroutine bug |
| aborted | `.log`, `.dat` | read error lines, fix, re-run |

### Step 5 — Verify (prove it, don't assume)

Run the checks from `verification.md`:
1. Analytical benchmark (cantilever/cylinder/1D conduction) within 1–5%
2. Review the applicable energy histories and use criteria appropriate to the analysis. For quasi-static Explicit work, assess kinetic and artificial energies and mass scaling over the relevant stroke.
3. Mesh convergence if time allows (3 mesh sizes)
4. Units sanity with `scripts/unit_converter.py`

### Step 6 — Report

```markdown
## Simulation Report
**Model**: [parts, materials, BCs, loads, mesh]
**Results**: max U = ..., max Mises = ..., max RF = ...
**Verification**: benchmark diff = 1.2% ✓ | energies ✓ | mesh converged ✓
**Warnings**: [list, with whether they matter]
**Files**: model_setup.py, Job-1.inp/.odb, load_deflection.csv
```

## 2. Subroutine Workflows (Python + Fortran together)

When a task needs a custom material / load / field:

1. Select the subroutine type from `abaqus_subroutine_skills/SKILL.md`
2. Copy the reference template → adapt parameters
3. Wire the Fortran into the Python script:
   `mdb.Job(..., userSubroutine='my_sub.f')`
4. Compile check: `abaqus make library=my_sub.f` (or run with `user=`)
5. Validate with a single-element test (see `verification.md` template 0)

## 3. Golden Rules

1. **Never invent Abaqus API** — copy from `reference/`; if unsure, check
   `docs/ERRATA.md` section 2 (unverified items) and state the uncertainty
2. **Never mix unit systems** — N-mm-MPa or nothing
3. **Never ship an unverified result** — run at least one benchmark comparison
4. **Always read the logs** — .sta/.msg/.dat are the ground truth
5. **Ask before big runs** — > 1M elements or > 1 hour: confirm with the user
6. **Chinese + English**: respond in the user's language; keep code comments English

## 4. Common Task Templates

| Task | Path |
|------|------|
| Static stress of a bracket | general + static + verification |
| Fatigue life of a welded joint | static (stress) + fatigue (S-N/ε-N) |
| Welding residual stress | thermal (DFLUX) + thermal stress + subroutine |
| Composite plate failure | composite (layup + Tsai-Wu/Hashin) |
| Crack propagation | xfem (XFEM or VCCT) |
| Custom constitutive model | subroutine (UMAT/VUMAT) + single-element test |

## 5. Environment Assumptions

- `abaqus` on PATH (sourced `abaqusvars.sh`/`.bat`)
- Match `abaqus cae noGUI=` and `abaqus python` scripts to the embedded runtime. Abaqus 2022/2023 use Python 2.7. Abaqus 2024 introduced Python 3.10. Use external Python 3 for standalone helpers.
- Fortran compiler per `abaqus_subroutine_skills/SKILL.md`
- Scratch space for large jobs; check `abaqus` license availability first
