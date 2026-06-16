# -*- coding: utf-8 -*-
from ansa import base, constants

DECK = constants.LSDYNA  # 필요하면 ABAQUS 등으로 변경

TAB_PROP_NAME = "NEGATIVE TAP_CU_MID"
PAD_PROP_NAMES = ["PAD", "PAD_CELL_SIDE_INT"]

TOL = 1.0e-6


def get_prop_by_name(prop_name):
    props = base.CollectEntities(DECK, None, "PROPERTY")
    for prop in props:
        vals = base.GetEntityCardValues(DECK, prop, ["Name"])
        if vals.get("Name") == prop_name:
            return prop
    return None


def get_shell_nodes_from_prop(prop):
    shells = base.CollectEntities(DECK, prop, "SHELL", recursive=True)
    node_dict = {}

    for shell in shells:
        nodes = base.CollectEntities(DECK, shell, "NODE", recursive=True)
        for n in nodes:
            node_dict[n._id] = n

    return list(node_dict.values())


def get_node_xyz(node):
    vals = base.GetEntityCardValues(DECK, node, ["X1", "X2", "X3"])
    return vals["X1"], vals["X2"], vals["X3"]


def collect_pad_surfaces(prop_names):
    surfaces = []

    for name in prop_names:
        prop = get_prop_by_name(name)
        if prop is None:
            print("[WARN] Property not found:", name)
            continue

        # ANSA geometry surface entity name은 모델/버전에 따라 FACE 또는 SURF일 수 있음
        surfs = base.CollectEntities(DECK, prop, "FACE", recursive=True)
        if not surfs:
            surfs = base.CollectEntities(DECK, prop, "SURF", recursive=True)

        surfaces.extend(surfs)

    return surfaces


def create_hot_point(x, y, z):
    hp = base.CreateEntity(DECK, "HOT POINT", {
        "X": x,
        "Y": y,
        "Z": z
    })
    return hp


def project_hot_point_to_surfaces(hp, target_surfaces):
    """
    ANSA 버전에 따라 projection 함수명이 다를 수 있음.
    아래 함수가 안 먹으면 ANSA Script Editor에서
    Help > Python API > Project 관련 함수명 확인 필요.
    """

    try:
        # 일부 버전에서 사용 가능한 형태
        base.ProjectEntities(DECK, [hp], target_surfaces)
        return True

    except Exception as e:
        print("[WARN] ProjectEntities failed:", e)

    try:
        # 다른 버전에서 사용 가능한 형태일 수 있음
        base.ProjectEntity(DECK, hp, target_surfaces)
        return True

    except Exception as e:
        print("[WARN] ProjectEntity failed:", e)

    return False


def main():
    tab_prop = get_prop_by_name(TAB_PROP_NAME)
    if tab_prop is None:
        print("[ERROR] Tab property not found:", TAB_PROP_NAME)
        return

    pad_surfaces = collect_pad_surfaces(PAD_PROP_NAMES)
    if not pad_surfaces:
        print("[ERROR] PAD target surfaces not found.")
        return

    tab_nodes = get_shell_nodes_from_prop(tab_prop)
    print("[INFO] Tab node count:", len(tab_nodes))
    print("[INFO] Target PAD surface count:", len(pad_surfaces))

    # 같은 위치 node 중복 방지
    used_xyz = set()
    created_hps = []

    for node in tab_nodes:
        x, y, z = get_node_xyz(node)

        key = (
            round(x / TOL),
            round(y / TOL),
            round(z / TOL)
        )

        if key in used_xyz:
            continue

        used_xyz.add(key)

        hp = create_hot_point(x, y, z)
        if hp is None:
            print("[WARN] Failed to create hot point at:", x, y, z)
            continue

        ok = project_hot_point_to_surfaces(hp, pad_surfaces)

        if ok:
            created_hps.append(hp)
        else:
            print("[WARN] Projection failed. Hot point remains at original node position:", x, y, z)

    print("[DONE] Created projected hot points:", len(created_hps))


if __name__ == "__main__":
    main()