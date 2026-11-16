"""Audit HyperMesh square rigid plates and substitute them into the solved HPS deck."""
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

CASE = Path(__file__).resolve().parent
BASE = Path(r"C:\SIMULIA\temp\HPS180_Native_Redo_20261107")
OUT = Path(r"C:\SIMULIA\temp\HPS180_QuadPlatens_RP_20261109")
MESH = CASE / "platens_hm.inp"


def read_platens(path):
    nodes = {}
    elements = {"BOTTOM": {}, "TOP": {}}
    ref_sets = {"BOTTOM": [], "TOP": []}
    section = None
    for raw in path.read_text().splitlines():
        row = raw.strip().upper()
        if not row or row.startswith("**"):
            continue
        if row.startswith("*"):
            if row == "*NODE":
                section = nodes
                continue
            rp_set = re.fullmatch(r"\*NSET,\s*NSET=(BOTTOM|TOP)_RP", row)
            if rp_set:
                section = ref_sets[rp_set[1]]
                continue
            match = re.fullmatch(r"\*ELEMENT,TYPE=R3D4,ELSET=(BOTTOM|TOP)", row)
            if not match:
                raise ValueError(f"Unexpected HyperMesh export keyword: {row}")
            section = elements[match[1]]
            continue
        if isinstance(section, list):
            section.extend(int(v) for v in row.split(",") if v.strip())
            continue
        tag, *values = row.split(",")
        label = int(tag)
        if label in section:
            raise ValueError(f"Duplicate label: {label}")
        section[label] = tuple(map(float if section is nodes else int, values))
    return nodes, elements, ref_sets


def audit(nodes, elements, target_z):
    groups = {}
    for name, sign in (("BOTTOM", 1), ("TOP", -1)):
        grid = elements[name]
        used = {node for conn in grid.values() for node in conn}
        coords = {nodes[node] for node in used}
        cells = set()
        if len(grid) != 400 or len(used) != 441 or len(coords) != 441:
            raise ValueError(f"{name}: unexpected mesh size or duplicate node coordinates")
        for conn in grid.values():
            q = [nodes[n] for n in conn]
            if len(set(conn)) != 4 or any(abs(p[2] - target_z[name]) > 1e-8 for p in q):
                raise ValueError(f"{name}: degenerate or off-plane facet")
            for i, p in enumerate(q):
                if not math.isclose(math.dist(p, q[(i + 1) % 4]), 2.5, abs_tol=1e-8):
                    raise ValueError(f"{name}: expected 2.5 mm square edges")
            ux, uy = (q[1][i] - q[0][i] for i in (0, 1))
            vx, vy = (q[3][i] - q[0][i] for i in (0, 1))
            if not math.isclose(sign * (ux * vy - uy * vx), 6.25, abs_tol=1e-8):
                raise ValueError(f"{name}: invalid square or normal orientation")
            index = tuple((min(p[axis] for p in q) + 25) / 2.5 for axis in (0, 1))
            cell = tuple(round(i) for i in index)
            if any(abs(i - j) > 1e-8 for i, j in zip(index, cell)):
                raise ValueError(f"{name}: facet does not align to the regular grid")
            cells.add(cell)
        if cells != {(i, j) for i in range(20) for j in range(20)}:
            raise ValueError(f"{name}: plate has holes, overlap or wrong footprint")
        groups[name] = used
    if groups["TOP"] & groups["BOTTOM"]:
        raise ValueError("Plate nodes must be separate")
    if set(elements["TOP"]) & set(elements["BOTTOM"]):
        raise ValueError("Plate element IDs must be separate")
    return groups


def sha256(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    reference = Path(r"C:\HPS180_Native_Redo_20261107\results")
    baseline = json.loads((reference / "case.json").read_text())
    mesh = json.loads((reference / "second_order_audit.json").read_text())
    for filename, expected in baseline["solver_inputs_sha256"].items():
        if sha256(BASE / filename) != expected:
            raise ValueError(f"Reference input changed: {filename}")
    target_z = dict(zip(("BOTTOM", "TOP"), baseline["initial_plate_faces_z_mm"]))
    nodes, elements, ref_sets = read_platens(MESH)
    groups = audit(nodes, elements, target_z)
    used = sorted(groups["BOTTOM"] | groups["TOP"])
    rp_source = {}
    for name, rp_set in ref_sets.items():
        if len(rp_set) != 1 or rp_set[0] in used:
            raise ValueError(f"{name}: expected one independent HyperMesh reference node")
        rp_source[name] = rp_set[0]
        if math.dist(nodes[rp_set[0]], (0, 0, target_z[name])) > 1e-8:
            raise ValueError(f"{name}: reference node must be at the platen center")
    if len(set(rp_source.values())) != 2 or set(nodes) != set(used) | set(rp_source.values()):
        raise ValueError("Expected only mesh nodes and two unique reference nodes")
    node_offset, elem_offset = mesh["max_node_label"], mesh["max_element_label"]
    node_map = {old: node_offset + i for i, old in enumerate(used, 1)}
    rps = {"BOTTOM": node_offset + len(used) + 1, "TOP": node_offset + len(used) + 2}
    OUT.mkdir()
    shutil.copyfile(BASE / "specimen.inp", OUT / "specimen.inp")
    with (OUT / "platens.inp").open("x") as f:
        f.write("** HyperMesh R3D4 platens; only mesh nodes; IDs offset past specimen\n*Node\n")
        for key in used:
            x, y, z = nodes[key]
            f.write(f"{node_map[key]},{x:.15g},{y:.15g},{z:.15g}\n")
        for name, rp in rps.items():
            x, y, z = nodes[rp_source[name]]
            f.write(f"{rp},{x:.15g},{y:.15g},{z:.15g}\n")
        for name, grid in elements.items():
            f.write(f"*Element,type=R3D4,elset={name}\n")
            for eid, conn in grid.items():
                f.write(f"{elem_offset + eid}," + ",".join(str(node_map[n]) for n in conn) + "\n")
        for name, rp in rps.items():
            f.write(f"*Nset,nset={name}_RP\n{rp}\n*Rigid Body,ref node={rp},elset={name}\n")
    deck = (BASE / "HPS180_Native.inp").read_text()
    before, rest = deck.split("*Include, input=specimen.inp\n", 1)
    material, after = rest.split("*Material,name=SS316L\n", 1)[1].split("*Surface Interaction", 1)
    material, _ = material.split("*Solid Section,elset=BOTTOM", 1)
    (OUT / "HPS180_QuadPlatens.inp").write_text(
        before + "*Include, input=specimen.inp\n*Include, input=platens.inp\n"
        + "*Material,name=SS316L\n" + material + "*Surface Interaction" + after, encoding="ascii")
    report = {
        "geometry": "zero retained geometry entities", "side_mm": 50, "square_edge_mm": 2.5,
        "element_type": "R3D4", "elements_per_plate": 400, "mesh_nodes_per_plate": 441,
        "plate_z_mm": target_z, "hypermesh_reference_nodes": rp_source,
        "abaqus_reference_nodes": rps, "hypermesh_export_sha256": sha256(MESH),
        "assembled_inputs_sha256": {p.name: sha256(p) for p in sorted(OUT.glob("*.inp"))},
    }
    (CASE / "mesh_audit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
