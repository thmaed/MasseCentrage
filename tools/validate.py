#!/usr/bin/env python3
"""Contrôle des fiches d'avions du dépôt (même esprit que le contrôle de l'app, en plus léger).

Usage : python3 tools/validate.py
Code de sortie 1 si une fiche est invalide. L'app refait elle-même son contrôle complet avant d'appliquer
quoi que ce soit : ce script sert à repérer une erreur AVANT qu'elle n'arrive sur les téléphones.
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FAMILIES = {"da40", "da40ng", "ps28", "pa19", "a22", "xl8", "dr400", "c152", "c172", "pa28", "aquila", "p2008", "da20"}
REQUIRED = ["id", "model", "family", "registration", "armUnit", "empty", "crew", "passenger", "baggage",
            "fuel", "envelope", "perf", "speedUnit", "speeds", "livery"]
GRIDS = ["takeoffRoll", "takeoff50", "landingRoll", "landing50"]

errors = []

def err(path, msg):
    errors.append(f"{path} : {msg}")

def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)

def grid_state(g):
    """'blank' (tout à 0), 'complete' (2 masses × 3 températures × 3 altitudes, toutes > 0) ou 'partial'."""
    if not (isinstance(g, list) and len(g) == 2 and all(isinstance(m, list) and len(m) == 3 and all(isinstance(t, list) and len(t) == 3 for t in m) for m in g)):
        return "bad"
    cells = [c for m in g for t in m for c in t]
    if not all(num(c) for c in cells):
        return "bad"
    if all(c == 0 for c in cells):
        return "blank"
    return "complete" if all(c > 0 for c in cells) else "partial"

def check_aircraft(path, a, name):
    for k in REQUIRED:
        if k not in a:
            err(path, f"champ « {k} » manquant")
    if errors and any(e.startswith(path) for e in errors):
        return
    if a["family"] not in FAMILIES:
        err(path, f"famille inconnue « {a['family']} »")
    reg = str(a["registration"]).strip()
    if not reg:
        err(path, "immatriculation vide")
    if name != reg + ".json":
        err(path, f"le fichier doit s'appeler {reg}.json")
    if a["id"] != reg:
        err(path, f"id « {a['id']} » différent de l'immatriculation « {reg} » (l'id ne doit jamais changer)")
    if not str(a["model"]).strip():
        err(path, "modèle vide")
    e = a["empty"]
    if not (num(e.get("mass")) and e["mass"] > 0): err(path, "pesée : masse à vide > 0 requise")
    if not (num(e.get("arm")) and e["arm"] != 0): err(path, "pesée : bras à vide requis")
    if not (num(e.get("maxMass")) and num(e.get("mass")) and e["maxMass"] > e["mass"]): err(path, "masse maximale > masse à vide requise")
    env = a["envelope"]
    # Chaque point est une paire [bras, masse].
    if not (isinstance(env, list) and len(env) >= 3 and all(isinstance(p, list) and len(p) == 2 and num(p[0]) and num(p[1]) and p[1] > 0 for p in env)):
        err(path, "enveloppe : au moins 3 points [bras, masse > 0]")
    elif len({p[0] for p in env}) < 2 or len({p[1] for p in env}) < 2:
        err(path, "enveloppe : doit couvrir une plage de bras et de masses")
    f = a["fuel"]
    if not (num(f.get("density")) and f["density"] > 0): err(path, "carburant : densité > 0 requise")
    caps = [f.get(s, {}).get("capacity") for s in ("left", "right")]
    if not all(num(c) and c >= 0 for c in caps) or sum(caps) <= 0: err(path, "carburant : capacité des réservoirs requise")
    perf = a["perf"]
    states = [grid_state(perf.get(g)) for g in GRIDS]
    if "bad" in states: err(path, "performances : tableaux mal formés (2 masses × 3 températures × 3 altitudes)")
    elif set(states) != {"blank"}:
        if set(states) != {"complete"}: err(path, "performances : tableaux commencés mais incomplets (tout vide ou tout rempli)")
        if not (num(perf.get("minMass")) and num(perf.get("maxMass")) and perf["maxMass"] > perf["minMass"]):
            err(path, "performances : la 2e masse doit dépasser la 1re")
    for k, s in a["speeds"].items():
        if not (isinstance(s, dict) and num(s.get("value")) and s["value"] >= 0): err(path, f"vitesse {k} invalide")

seen_ids, seen_regs = {}, {}
clubs = 0
for folder in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, folder)
    if not os.path.isdir(d) or folder.startswith((".", "_")) or folder == "tools":
        continue
    meta_path = os.path.join(d, "club.json")
    if not os.path.exists(meta_path):
        err(folder, "dossier de club sans club.json")
        continue
    clubs += 1
    try:
        meta = json.load(open(meta_path))
        if not str(meta.get("name", "")).strip(): err(f"{folder}/club.json", "« name » requis")
        defaults = meta.get("defaults")
        if defaults is not None:
            ok = isinstance(defaults, dict) and set(defaults) <= {"departure", "arrival"} and all(isinstance(v, str) and re.fullmatch(r"[A-Za-z0-9-]{2,8}", v) for v in defaults.values())
            if not ok:
                err(f"{folder}/club.json", "« defaults » : { \"departure\": \"LFLP\", \"arrival\": \"LFLP\" } attendu (codes OACI)")
        order = meta.get("order")
        if order is not None and not (isinstance(order, list) and all(isinstance(x, str) for x in order)):
            err(f"{folder}/club.json", "« order » : liste d'immatriculations attendue")
    except Exception as ex:
        err(f"{folder}/club.json", f"JSON illisible ({ex})")
    for name in sorted(os.listdir(d)):
        if name == "club.json" or not name.endswith(".json"):
            continue
        path = f"{folder}/{name}"
        try:
            a = json.load(open(os.path.join(d, name)))
        except Exception as ex:
            err(path, f"JSON illisible ({ex})")
            continue
        if not isinstance(a, dict):
            err(path, "une fiche est un objet JSON")
            continue
        n0 = len(errors)
        check_aircraft(path, a, name)
        if len(errors) == n0:
            for table, key in ((seen_ids, ("id", a["id"])), (seen_regs, ("reg", a["registration"].lower()))):
                full = (folder, key)
                if full in table: err(path, f"{key[0]} en double avec {table[full]}")
                table[full] = path

for folder in sorted(os.listdir(ROOT)):
    meta_path = os.path.join(ROOT, folder, "club.json")
    if os.path.isfile(meta_path) and not folder.startswith((".", "_")):
        try:
            order = json.load(open(meta_path)).get("order") or []
        except Exception:
            continue
        known = {key[1] for (f, key) in seen_regs if f == folder}        # immatriculations (minuscules) du dossier
        for reg in order:
            if reg.lower() not in known:
                errors.append(f"{folder}/club.json : « order » cite {reg}, qui n'a pas de fiche")

if clubs == 0:
    errors.append("aucun dossier de club")
if errors:
    print(f"{len(errors)} problème(s) :")
    for e in errors:
        print("  ✗", e)
    sys.exit(1)
print(f"OK — {clubs} club(s), {len(seen_ids)} fiche(s) valides")
