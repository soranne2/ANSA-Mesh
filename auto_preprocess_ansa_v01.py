# auto_preprocess_ansa_v01.py
# 목적:
# STP import → mesh → surface/set 생성 → Tie/Contact 생성 → solver deck export

import os
import json
import sys

from ansa import base
from ansa import constants
from ansa import mesh
from ansa import connections


# ============================================================
# 0. 기본 설정
# ============================================================

CONFIG_PATH = "auto_preprocess_config.json"

# Abaqus 기준
DECK = constants.ABAQUS
# LS-DYNA면:
# DECK = constants.LSDYNA


# ============================================================
# 1. 유틸
# ============================================================

def log(msg):
    print("[AUTO_PRE] " + str(msg))


def load_config(config_path):
    with open(config_path, "r") as f:
        return json.load(f)


def find_entities_by_name(deck, entity_type, name_keyword):
    """
    예:
    entity_type = "PART", "SHELL", "SOLID", "FACE", "SET", "SURFACE"
    name_keyword 포함된 entity 찾기
    """
    entities = base.CollectEntities(deck, None, entity_type)
    result = []

    for ent in entities:
        try:
            name = base.GetEntityCardValues(deck, ent, ["Name"]).get("Name", "")
        except:
            name = ""

        if name_keyword.upper() in str(name).upper():
            result.append(ent)

    return result


def get_part_name(part):
    try:
        vals = base.GetEntityCardValues(DECK, part, ["Name"])
        return vals.get("Name", "")
    except:
        return ""


# ============================================================
# 2. CAD Import
# ============================================================

def import_cad(stp_path):
    log("Import CAD: {}".format(stp_path))

    if not os.path.exists(stp_path):
        raise FileNotFoundError(stp_path)

    # ANSA 버전에 따라 ImportCode 함수/옵션명이 다를 수 있음
    # 필요 시 ANSA Script Editor에서 recording 후 이 부분만 교체
    base.InputCAD(stp_path)

    log("CAD import done")


# ============================================================
# 3. Geometry cleanup / defeature placeholder
# ============================================================

def geometry_cleanup(config):
    log("Geometry cleanup start")

    # 여기는 처음엔 수동/반자동으로 두는 걸 추천
    # 예:
    # - 작은 face 제거
    # - free edge check
    # - topology cleanup
    # - hole 제거
    # - fillet 제거

    # ANSA 버전에 따라 함수명이 다를 수 있으므로 wrapper로 유지
    # base.CheckAndFixGeometry(...)
    # base.Topology(...)
    # base.DeleteEntity(...)

    log("Geometry cleanup skipped in v0.1")


# ============================================================
# 4. Mesh
# ============================================================

def apply_mesh_parameters(config):
    mesh_size = config.get("mesh", {}).get("target_size", 5.0)
    min_size = config.get("mesh", {}).get("min_size", 2.0)
    max_size = config.get("mesh", {}).get("max_size", 8.0)

    log("Apply mesh parameters")
    log("target={}, min={}, max={}".format(mesh_size, min_size, max_size))

    # 실제 ANSA mesh parameter 함수는 사내 버전에서 recording으로 확인 추천
    # 예시 구조만 유지
    # mesh.SetMeshParams(...)
    # mesh.SetPerimetersLength(...)
    # mesh.SetShellMeshParams(...)


def auto_mesh(config):
    log("Auto mesh start")

    apply_mesh_parameters(config)

    # 대상 part를 이름 기반으로 찾기
    mesh_rules = config.get("mesh_rules", [])

    for rule in mesh_rules:
        part_keyword = rule.get("part_keyword")
        mesh_type = rule.get("mesh_type", "shell")

        parts = find_entities_by_name(DECK, "PART", part_keyword)

        log("Mesh rule: {} / {} / found {}".format(
            part_keyword, mesh_type, len(parts)
        ))

        for part in parts:
            # 여기서 part에 속한 faces/surfaces/elements를 가져와 mesh 적용
            # 실제 함수명은 ANSA 버전별 확인 필요
            #
            # if mesh_type == "shell":
            #     mesh.CreateShellMesh(part, ...)
            # elif mesh_type == "tetra":
            #     mesh.CreateTetraMesh(part, ...)
            pass

    log("Auto mesh done / placeholder")


# ============================================================
# 5. Surface / Set 생성
# ============================================================

def create_surface_from_part_keyword(surface_name, part_keyword):
    """
    part 이름 기준으로 surface 생성하는 placeholder.
    실제로는 shell element face 또는 geometry face를 모아서 Surface entity 생성.
    """
    log("Create surface: {} from part keyword {}".format(
        surface_name, part_keyword
    ))

    parts = find_entities_by_name(DECK, "PART", part_keyword)

    if not parts:
        log("WARNING: no part found for {}".format(part_keyword))
        return None

    # 실제 구현 방향:
    # 1) part 하위 shell/solid element collect
    # 2) 외곽 face 추출
    # 3) surface entity 생성
    #
    # elems = []
    # for part in parts:
    #     elems += base.CollectEntities(DECK, part, "SHELL")
    #
    # surface = base.CreateEntity(DECK, "SURFACE", {"Name": surface_name})
    # base.AddToSet(surface, elems)

    surface = None

    return surface


def create_surfaces(config):
    log("Create surfaces start")

    surface_map = {}

    for rule in config.get("surface_rules", []):
        surface_name = rule["surface_name"]
        part_keyword = rule["part_keyword"]

        surf = create_surface_from_part_keyword(surface_name, part_keyword)
        surface_map[surface_name] = surf

    log("Create surfaces done")
    return surface_map


# ============================================================
# 6. Tie / Contact 생성
# ============================================================

def create_tie_contact(name, master_surface, slave_surface, rule):
    log("Create TIE: {}".format(name))

    # Abaqus 기준 Tie 생성 placeholder
    # 실제 ANSA entity card 이름은 버전/Deck 설정에 따라 확인 필요
    #
    # tie = base.CreateEntity(DECK, "TIE", {
    #     "Name": name,
    #     "Master": master_surface,
    #     "Slave": slave_surface,
    #     "Position Tolerance": rule.get("tolerance", 0.5)
    # })
    #
    # return tie

    return None


def create_general_contact(name, surface_a, surface_b, rule):
    log("Create CONTACT: {}".format(name))

    # Abaqus contact pair 또는 LS-DYNA contact 생성 placeholder
    #
    # contact = base.CreateEntity(DECK, "CONTACT PAIR", {...})
    #
    # friction = rule.get("friction", 0.2)
    # search_distance = rule.get("search_distance", 0.5)

    return None


def create_contacts(config, surface_map):
    log("Create contacts start")

    for rule in config.get("tie_rules", []):
        name = rule["name"]
        master_name = rule["master_surface"]
        slave_name = rule["slave_surface"]

        master = surface_map.get(master_name)
        slave = surface_map.get(slave_name)

        if master is None or slave is None:
            log("WARNING: Tie skipped. Missing surface: {}".format(name))
            continue

        create_tie_contact(name, master, slave, rule)

    for rule in config.get("contact_rules", []):
        name = rule["name"]
        surf_a_name = rule["surface_a"]
        surf_b_name = rule["surface_b"]

        surf_a = surface_map.get(surf_a_name)
        surf_b = surface_map.get(surf_b_name)

        if surf_a is None or surf_b is None:
            log("WARNING: Contact skipped. Missing surface: {}".format(name))
            continue

        create_general_contact(name, surf_a, surf_b, rule)

    log("Create contacts done")


# ============================================================
# 7. Quality check
# ============================================================

def quality_check(config):
    log("Quality check start")

    # 예:
    # - min length
    # - max length
    # - aspect ratio
    # - skew
    # - warpage
    # - jacobian
    #
    # failed = mesh.CheckElements(...)
    # report 저장

    log("Quality check placeholder")


# ============================================================
# 8. Export
# ============================================================

def export_solver_deck(output_path):
    log("Export solver deck: {}".format(output_path))

    # ANSA 버전별 Export 함수 확인 필요
    # base.OutputAbaqus(output_path)
    # base.OutputLSDyna(output_path)
    #
    # 또는:
    # base.Output(DECK, output_path)

    log("Export placeholder")


# ============================================================
# 9. Main
# ============================================================

def main():
    config = load_config(CONFIG_PATH)

    stp_path = config["input_stp"]
    output_path = config["output_solver_deck"]

    import_cad(stp_path)
    geometry_cleanup(config)
    auto_mesh(config)

    surface_map = create_surfaces(config)
    create_contacts(config, surface_map)

    quality_check(config)
    export_solver_deck(output_path)

    log("All process done")


if __name__ == "__main__":
    main()