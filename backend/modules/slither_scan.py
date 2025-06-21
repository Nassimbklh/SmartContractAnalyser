#%%
import datetime
import json
import os
import re
import subprocess
from collections import defaultdict
from typing import Any, Dict, Tuple

#%%
#file_path = '../data/val/ReentrancyVulnerable2.sol'

#%%
def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

#%%
def extract_solc_version(sol_path: str) -> str:
    """
    Lit le fichier Solidity et renvoie la version indiquée par pragma solidity,
    par exemple "0.8.20" pour "pragma solidity ^0.8.20;" ou "pragma solidity 0.7.6;".
    """
    pragma_re = re.compile(r"pragma\s+solidity\s+(?:\^)?(?P<ver>\d+\.\d+\.\d+)")
    with open(sol_path, "r", encoding="utf-8") as f:
        for line in f:
            m = pragma_re.search(line)
            if m:
                return m.group("ver")
    raise ValueError(f"Aucune pragma solidity trouvée dans {sol_path}")

#%%
def ensure_solc_version(version: str) -> None:
    """
    Vérifie si `version` est installée avec solc-select, l'installe si besoin, puis l'active.
    """
    # Vérifier la présence de solc-select
    try:
        subprocess.run(
            ["solc-select", "--help"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise EnvironmentError("solc-select non trouvé : installe-le via pip install solc-select")

    # Lister les versions installées
    out = subprocess.check_output(["solc-select", "versions"], text=True)
    installed = {line.strip().lstrip("* ") for line in out.splitlines() if line.strip()}

    # Installer si nécessaire
    pattern = re.compile(re.escape(version) + r' \(current, set by .*\)')
    if any(pattern.match(item) for item in installed):
        print(f"▶ solc {version} déjà sélectionné")
    elif version in installed:
        # Activer la version
        print(f"▶ Activation de solc {version}")
        subprocess.run(["solc-select", "use", version], check=True)
    elif version not in installed:
        print(f"▶ Installation de solc {version}…")
        subprocess.run(["solc-select", "install", version], check=True)

#%%
def run_slither(sol_path: str, out_json: str, solc_version: str, project_root: str = "audits_smart_contracts") -> str:
    """
    Appelle extract_solc_version + ensure_solc_version avant d'exécuter Slither
    avec l'option --fail-on.
    """
    # 1) Préparer le bon compilateur
    ensure_solc_version(solc_version)

    # 2) Construire et lancer Slither
    if os.path.exists(out_json):
        os.remove(out_json)

    cmd_json = [
        "slither",
        sol_path,
        "--json",
        out_json,
        "--ignore-compile"
    ]
    print("▶ slither", " ".join(cmd_json[1:]))
    result_json = subprocess.run(cmd_json)

    cmd_txt = [
        "slither",
        sol_path,
        "--ignore-compile"
    ]
    print("▶ slither", " ".join(cmd_txt[1:]))
    out_txt = out_json[:-5] + ".txt"
    result_txt = subprocess.run(cmd_txt, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    pattern = rf"--allow-paths \.,.*?{re.escape(project_root)}[\\/]"
    result = re.sub(pattern, "--allow-paths .," + project_root.split(os.sep)[-1] + os.sep, result_txt.stdout)

    # écriture (mode 'w' écrase si existant)
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write(result)

    # 3) Tolérer 0 ou 255 (issues détectées), sinon erreur
    if result_json.returncode not in {0, 255}:
        raise subprocess.CalledProcessError(result_json.returncode, cmd_json)
    if result_txt.returncode not in {0, 255}:
        raise subprocess.CalledProcessError(result_txt.returncode, cmd_txt)

    return result
#%%
def parse_detectors(slither_data: Dict[str, Any]) -> Tuple[Dict[str, int], list[str]]:
    """Return (severity_counts, highlights) extracted from Slither JSON."""
    detectors = slither_data.get("results", {}).get("detectors", [])
    severity_counts: Dict[str, int] = defaultdict(int)
    highlights: list[str] = []

    for item in detectors:
        impact = item.get("impact", "Unknown")
        confidence = item.get("confidence", "Unknown")
        title = item.get("check", "Unnamed check")
        description = item.get("description", "").strip()
        severity_counts[impact] += 1

        if impact.lower() in {"critical", "high", "medium"}:
            highlights.append(f"[{impact}/{confidence}] {title}: {description}")

    return severity_counts, highlights

#%%
def slither_analyze(sol_path: str,
                     dest_dir: str = "../data/slither") -> str:
    """
    Run Slither on *sol_path* using the correct solc version from pragma,
    install/activate it if needed, and create raw + summary reports inside *dest_dir*.
    """
    # 1) Check input file
    if not os.path.isfile(sol_path):
        raise FileNotFoundError(sol_path)

    # 2) Prepare output directory
    os.makedirs(dest_dir, exist_ok=True)

    # 3) Determine output paths
    base = os.path.splitext(os.path.basename(sol_path))[0]
    ts = timestamp()
    json_path = os.path.join(dest_dir, f"{base}.json")#f"{base}_{ts}.json")

    # 4) Extract and set up correct solc version
    solc_version = extract_solc_version(sol_path)
    print(f"▶ Detected pragma solidity {solc_version}")

    # 5) Run Slither with the chosen fail-on policy
    print(f"▶ Launching Slither analysis on {sol_path}…")
    slither_result = run_slither(sol_path, json_path, solc_version)

    return slither_result
#%%
#print(slither_analyze(file_path))