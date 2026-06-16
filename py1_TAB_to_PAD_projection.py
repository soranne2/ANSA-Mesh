# -*- coding: utf-8 -*-
from ansa import base, constants

DECK = constants.LSDYNA

TAB_PROP_NAME = "NEGATIVE TAP_CU_MID"
PAD_PROP_NAMES = ["PAD", "PAD_CELL_SIDE_INT"]

TOL = 1.0e-6


def norm_name(s):
    if s is None:
        return ""
    return str(s).strip().replace('"', '').replace("'", "")


def get_entity_name(ent):
    # ANSA card name이 버전/Deck마다 Name, TITLE, HEADING 등 다를 수 있어서 다 시도
    for key in ["Name", "NAME", "TITLE", "Title", "HEADING"]:
        try:
            vals = base.GetEntityCardValues(DECK, ent, [key])
            if vals and vals.get(key):
                return norm_name(vals.get(key))
        except:
            pass
    return ""


def get_shell_property(shell):
    # LS-DYNA shell card에서 property/section 참조 필드가 PID인 경우가 많음
    for key in ["PID", "PID1", "SECTION", "SECID"]:
        try:
            vals = base.GetEntityCardValues(DECK, shell, [key])
            prop = vals.get(key)
            if prop:
                return prop
        except:
            pass
    return None


def collect_shells_by_property_name(target_prop_name):
    target = norm_name(target_prop_name)
    all_shells = base.CollectEntities(DECK, None, "SHELL")

    matched_shells = []

    for shell in all_shells:
        prop = get_shell_property(shell)
        if prop is None:
            continue

        pname = get_entity_name(prop)

        if pname == target:
            matched_shells.append(shell)

    return matched_shells


def get_nodes_from_shells(shells):
    node_dict = {}

    for shell in shells:
        nodes = base.CollectEntities(DECK, shell, "NODE", recursive=True)
        for n in nodes:
            node_dict[n._id] = n

    return list(node_dict.values())


def get_node_xyz(node):
    vals = base.GetEntityCardValues(DECK, node, ["X1", "X2", "X3"])
    return vals["X1"], vals["X2"], vals["X3"]


def collect_pad_surfaces_by_property_names(prop_names):
    target_names = [norm_name(n) for n in prop_names]

    all_faces = []
    for etype in ["FACE", "SURF"]:
        try:
            ents = base.CollectEntities(DECK, None, etype)
            if ents:
                all_faces.extend(ents)
        except:
            pass

    matched_faces = []

    for face in all_faces:
        prop = get_shell_property(face)

        # geometry face는 shell처럼 PID가 없을 수도 있음
        if prop is None:
            for key in ["PID", "PROPERTY", "PART"]:
                try:
                    vals = base.GetEntityCardValues(DECK, face, [key])
                    prop = vals.get(key)
                    if prop:
                        break
                except:
                    pass

        if prop is None:
            continue

        pname = get_entity_name(prop)

        if pname in target_names:
            matched_faces.append(face)

    return matched_faces


def create_hot_point(x, y, z):
    # hot point field name도 버전에 따라 X/Y/Z 또는 X1/X2/X3가 갈릴 수 있음
    try:
        return base.CreateEntity(DECK, "HOT POINT", {
            "X": x,
            "Y": y,
            "Z": z
        })
    except:
        return base.CreateEntity(DECK, "HOT POINT", {
            "X1": x,
            "X2": y,
            "X3": z
        })


def project_hot_point_to_faces(hp, faces):
    try:
        base.ProjectEntities(DECK, [hp], faces)
        return True
    except Exception as e:
        print("[WARN] ProjectEntities failed:", e)

    try:
        base.ProjectEntity(DECK, hp, faces)
        return True
    except Exception as e:
        print("[WARN] ProjectEntity failed:", e)

    return False


def main():
    tab_shells = collect_shells_by_property_name(TAB_PROP_NAME)

    if not tab_shells:
        print("[ERROR] No shell elements found with property name:", TAB_PROP_NAME)
        print("[CHECK] Property name may be slightly different. Check blank, underscore, or TAP/TAB typo.")
        return

    tab_nodes = get_nodes_from_shells(tab_shells)

    pad_faces = collect_pad_surfaces_by_property_names(PAD_PROP_NAMES)

    if not pad_faces:
        print("[ERROR] No PAD faces found with property names:", PAD_PROP_NAMES)
        return

    print("[INFO] Matched tab shells:", len(tab_shells))
    print("[INFO] Unique tab nodes:", len(tab_nodes))
    print("[INFO] Matched PAD faces:", len(pad_faces))

    used = set()
    created = []

    for node in tab_nodes:
        x, y, z = get_node_xyz(node)

        key = (
            round(x / TOL),
            round(y / TOL),
            round(z / TOL)
        )

        if key in used:
            continue

        used.add(key)

        hp = create_hot_point(x, y, z)

        if hp is None:
            print("[WARN] Failed to create hot point:", x, y, z)
            continue

        ok = project_hot_point_to_faces(hp, pad_faces)

        if ok:
            created.append(hp)
        else:
            print("[WARN] Projection failed:", x, y, z)

    print("[DONE] Created projected hot points:", len(created))


if __name__ == "__main__":
    main()