# -*- coding: utf-8 -*-
"""
ANSA 2025.1
지정 Property 이름 파트의 Mid-surface Shell Mesh
Target length = 5

실행: Script Editor > Run
또는: ansa64.bat -nogui -i model.ansa -exec mid_shell_mesh_l5.py
"""

from ansa import base
from ansa import constants
from ansa import mesh
from ansa import session

# =============================================================================
# 사용자 설정
# =============================================================================
TARGET_PROPERTY_NAMES = [
    "HOOD_OUTER",
    "FENDER_LH",
    "DOOR_INR_RH",
    # "PANEL*",          # 와일드카드(*) 가능
]

TARGET_LENGTH = 5.0
MIN_LENGTH = 2.5          # 보통 target * 0.5
MAX_LENGTH = 7.5          # 보통 target * 1.5
GROWTH_RATE = 1.2

# "exact" | "wildcard" | "contains"
NAME_MATCH = "wildcard"

# "skin"  : 박육/시트메탈 mid-surface (일반)
# "offset": 이미 한쪽 스킨만 있을 때 두께 절반 offset
# "auto"  : VOLUME 있으면 skin, 없으면 offset 없이 바로 mesh
MID_METHOD = "auto"

# True면 기존 SHELL을 지우고 다시  inter
REMESH_EXISTING = True

# =============================================================================


def _norm(name):
    return (name or "").strip()


def _match(name, patterns, mode):
    n = _norm(name).upper()
    if not n:
        return False
    for raw in patterns:
        p = _norm(raw).upper()
        if not p:
            continue
        if mode == "exact" and n == p:
            return True
        if mode == "contains" and p in n:
            return True
        if mode == "wildcard":
            if p.endswith("*") and n.startswith(p[:-1]):
                return True
            if p.startswith("*") and n.endswith(p[1:]):
                return True
            if p.startswith("*") and p.endswith("*") and p[1:-1] in n:
                return True
            if n == p:
                return True
    return False


def _ent_name(ent, deck):
    try:
        vals = ent.get_entity_values(deck, ["Name"])
        if vals and vals.get("Name"):
            return vals["Name"]
    except Exception:
        pass
    return getattr(ent, "_name", "") or ""


def _collect_properties(deck):
    props = []
    for typ in ("PROPERTY", "PSHELL", "PSOLID", "SECTION_SHELL", "SECTION_SOLID"):
        try:
            found = base.CollectEntities(deck, None, typ) or []
            props.extend(found)
        except Exception:
            continue
    # id 기준 중복 제거
    uniq, seen = [], set()
    for p in props:
        key = getattr(p, "_id", id(p))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def _collect_parts(deck):
    parts = []
    for typ in ("ANSAPART", "PART"):
        try:
            found = base.CollectEntities(deck, None, typ) or []
            parts.extend(found)
        except Exception:
            continue
    uniq, seen = [], set()
    for p in parts:
        key = getattr(p, "_id", id(p))
        if key not in seen:
            seen.add(key)
            uniq.append(p)
    return uniq


def collect_targets(deck, names, mode):
    """Property 이름에 매칭되는 property / part / face 수집."""
    matched_props = []
    for prop in _collect_properties(deck):
        if _match(_ent_name(prop, deck), names, mode):
            matched_props.append(prop)

    matched_parts = []
    for part in _collect_parts(deck):
        pname = _ent_name(part, deck)
        if _match(pname, names, mode):
            matched_parts.append(part)
            continue
        # part가 가진 property 이름으로도 매칭
        try:
            part_props = base.CollectEntities(deck, part, "PROPERTY") or []
            if any(_match(_ent_name(pp, deck), names, mode) for pp in part_props):
                matched_parts.append(part)
        except Exception:
            pass

    faces = []
    volumes = []
    containers = matched_props + matched_parts
    if not containers:
        return matched_props, matched_parts, [], []

    for cont in containers:
        try:
            faces.extend(base.CollectEntities(deck, cont, "FACE", recursive=True) or [])
        except Exception:
            try:
                faces.extend(base.CollectEntities(deck, cont, "FACE") or [])
            except Exception:
                pass
        for vtyp in ("VOLUME", "SOLID"):
            try:
                volumes.extend(base.CollectEntities(deck, cont, vtyp, recursive=True) or [])
            except Exception:
                try:
                    volumes.extend(base.CollectEntities(deck, cont, vtyp) or [])
                except Exception:
                    pass

    def _dedup(ents):
        out, seen = [], set()
        for e in ents:
            key = getattr(e, "_id", id(e))
            if key not in seen:
                seen.add(key)
                out.append(e)
        return out

    return matched_props, matched_parts, _dedup(faces), _dedup(volumes)


def delete_existing_shells(deck, containers):
    if not REMESH_EXISTING:
        return 0
    shells = []
    for cont in containers:
        try:
            shells.extend(base.CollectEntities(deck, cont, "SHELL", recursive=True) or [])
        except Exception:
            try:
                shells.extend(base.CollectEntities(deck, cont, "SHELL") or [])
            except Exception:
                pass
    if shells:
        try:
            base.DeleteEntity(shells)
        except Exception:
            for s in shells:
                try:
                    base.DeleteEntity(s)
                except Exception:
                    pass
    return len(shells)


def extract_midsurface(faces, volumes, method):
    """
    ANSA 2025.1 Middle Mesh.
    Skin = 박육 솔리드에서 mid-surface 추출 후 shell 준비.
    함수 시그니처가 사이트마다 조금 다를 수 있어 여러 이름을 순차 시도.
    """
    ents = volumes if volumes else faces
    if not ents:
        return False, "no geometry"

    use_skin = (method == "skin") or (method == "auto" and bool(volumes))
    if not use_skin:
        return True, "skip mid-surface (already surface / auto)"

    candidates = [
        # ANSA 22~25 Middle Mesh Generate (Skin)
        lambda: mesh.GenerateMiddleMesh(ents, algorithm="Skin", target_length=TARGET_LENGTH),
        lambda: mesh.GenerateMiddleMesh(ents, "Skin", TARGET_LENGTH),
        lambda: mesh.MiddleMeshGenerate(ents, algorithm="Skin"),
        lambda: mesh.Skin(ents),
        lambda: mesh.Offset(ents, "MID", copy="on", connect="on"),
        lambda: mesh.Offset(faces, 0, copy="on"),
    ]

    last_err = None
    for fn in candidates:
        try:
            fn()
            return True, fn.__code__.co_names if hasattr(fn, "__code__") else "ok"
        except AttributeError as e:
            last_err = e
            continue
        except TypeError as e:
            last_err = e
            continue
        except Exception as e:
            # 함수는 있는데 인자만 다른 경우 → 다음 후보
            last_err = e
            continue

    return False, "mid-surface API call failed: {}".format(last_err)


def set_length_and_mesh(faces):
    if not faces:
        return False, "no faces to mesh"

    # 1) FACE에 target length 부여
    param_sets = [
        {
            "TARGET_LENGTH": str(TARGET_LENGTH),
            "MIN_LENGTH": str(MIN_LENGTH),
            "MAX_LENGTH": str(MAX_LENGTH),
        },
        {
            "TARGETLGTH": str(TARGET_LENGTH),
            "MINLGTH": str(MIN_LENGTH),
            "MAXLGTH": str(MAX_LENGTH),
        },
    ]
    applied = False
    for keys in param_sets:
        try:
            for f in faces:
                f.set_entity_values(base.CurrentDeck(), keys)
            applied = True
            break
        except Exception:
            try:
                mesh.ApplyMeshParams(faces, keys)
                applied = True
                break
            except Exception:
                continue

    # 2) Shell mesh 생성
    mesh_fns = [
        lambda: mesh.SurfMesh(faces, target_length=TARGET_LENGTH),
        lambda: mesh.SurfMesh(faces, length=TARGET_LENGTH),
        lambda: mesh.CreateShellMesh(faces),
        lambda: mesh.CreateMesh(faces),
        lambda: mesh.Reconstruct(faces),
        lambda: mesh.ReconstructShells(faces),
    ]
    last_err = None
    for fn in mesh_fns:
        try:
            fn()
            return True, "meshed (params_applied={})".format(applied)
        except Exception as e:
            last_err = e
            continue
    return False, "mesh API call failed: {}".format(last_err)


def report(deck, props, parts, faces):
    shells = []
    for cont in (props + parts):
        try:
            shells.extend(base.CollectEntities(deck, cont, "SHELL", recursive=True) or [])
        except Exception:
            pass
    print("=" * 60)
    print("[Mid-surface Shell Mesh] done")
    print("  properties : {}".format(len(props)))
    for p in props:
        print("    - {}".format(_ent_name(p, deck)))
    print("  parts      : {}".format(len(parts)))
    for p in parts:
        print("    - {}".format(_ent_name(p, deck)))
    print("  faces      : {}".format(len(faces)))
    print("  shells     : {}".format(len(shells)))
    print("  length     : {}".format(TARGET_LENGTH))
    print("=" * 60)


def main():
    deck = base.CurrentDeck()
    print("[INFO] deck =", deck)
    print("[INFO] target names =", TARGET_PROPERTY_NAMES)
    print("[INFO] length =", TARGET_LENGTH)

    props, parts, faces, volumes = collect_targets(
        deck, TARGET_PROPERTY_NAMES, NAME_MATCH
    )
    if not props and not parts:
        print("[ERROR] 매칭된 Property/Part 없음. TARGET_PROPERTY_NAMES 확인.")
        print("        현재 PROPERTY 목록:")
        for p in _collect_properties(deck)[:50]:
            print("          ", _ent_name(p, deck))
        return

    print("[INFO] matched props={}, parts={}, faces={}, volumes={}".format(
        len(props), len(parts), len(faces), len(volumes)
    ))

    n_del = delete_existing_shells(deck, props + parts)
    if n_del:
        print("[INFO] deleted existing shells:", n_del)

    ok, msg = extract_midsurface(faces, volumes, MID_METHOD)
    print("[MID ]", ok, msg)
    if not ok:
        print("[WARN] mid-surface 실패. 이미 surface면 그대로 mesh 진행.")

    # mid-surface 후 FACE가 새로 생겼을 수 있어 재수집
    _, _, faces2, _ = collect_targets(deck, TARGET_PROPERTY_NAMES, NAME_MATCH)
    mesh_faces = faces2 or faces

    ok, msg = set_length_and_mesh(mesh_faces)
    print("[MESH]", ok, msg)

    try:
        base.RedrawAll()
    except Exception:
        pass

    report(deck, props, parts, mesh_faces)


# ANSA 버튼으로도 실행 가능하게
try:
    @session.defbutton("Mesh", "MidShell_L5")
    def _btn():
        main()
except Exception:
    pass


if __name__ == "__main__":
    main()