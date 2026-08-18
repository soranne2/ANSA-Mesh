# -*- coding: utf-8 -*-
"""ANSA 2025.1 - Property / Part 이름 전체 덤프"""
from ansa import base

deck = base.CurrentDeck()
print("=" * 70)
print("CurrentDeck =", deck)

TYPES = [
    "__PROPERTIES__",
    "__PARTS__",
    "ANSAPART",
    "PART",
    "PSHELL",
    "PSOLID",
    "PROPERTY",
    "SECTION_SHELL",
    "SECTION_SOLID",
    "SECTION",
    "SET",
]

def names_of(ent):
    out = {}
    out["_name"] = getattr(ent, "_name", None)
    out["_id"] = getattr(ent, "_id", None)
    try:
        out["type"] = base.GetEntityType(deck, ent)
    except Exception:
        out["type"] = "?"
    for key in ("Name", "NAME", "Title", "TITLE", "PID", "SID", "Comment"):
        try:
            v = base.GetEntityCardValues(deck, ent, [key])
            if v and v.get(key) not in (None, ""):
                out[key] = v.get(key)
        except Exception:
            pass
        try:
            v = ent.get_entity_values(deck, [key])
            if v and v.get(key) not in (None, ""):
                out["gev_" + key] = v.get(key)
        except Exception:
            pass
    return out

for typ in TYPES:
    try:
        ents = base.CollectEntities(deck, None, typ) or []
    except Exception as e:
        print("\n[{}] COLLECT FAIL: {}".format(typ, e))
        continue
    print("\n[{}] count={}".format(typ, len(ents)))
    for i, e in enumerate(ents[:80]):
        print("  {:3d} {}".format(i + 1, names_of(e)))
    if len(ents) > 80:
        print("  ... +{} more".format(len(ents) - 80))

print("\n" + "=" * 70)
print("위 출력에서 Name / Title / _name 중 실제 값을 TARGET에 넣으세요.")