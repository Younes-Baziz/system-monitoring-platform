import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
COLLECTE_DIR = BASE_DIR / "01_collecte"
CONFIG_MACHINES = BASE_DIR / "config" / "machines.json"

sys.path.insert(0, str(BASE_DIR / "02_stockage"))
from stockage import init_bd, sauvegarder_mesure


def charger_machines():
    """Charge la liste des machines distantes à superviser depuis le fichier de config.
    Retourne une liste vide si le fichier n'existe pas (aucune machine distante configurée)."""
    if not CONFIG_MACHINES.exists():
        print(f"Aucun fichier {CONFIG_MACHINES} trouvé, aucune machine distante configurée.")
        return []

    with open(CONFIG_MACHINES, "r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd):
    """Exécute une commande locale et retourne sa sortie."""
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=10
    )

    if r.returncode == 0:
        return r.stdout.strip()

    print(f"Erreur locale pour [{cmd}] : {r.stderr.strip()}")
    return None


def ssh(host, user, port, cmd):
    """Exécute une commande sur une machine distante via SSH."""
    r = subprocess.run(
        [
            "ssh",
            "-p", str(port),
            "-o", "ConnectTimeout=5",
            f"{user}@{host}",
            cmd
        ],
        capture_output=True,
        text=True,
        timeout=10
    )

    if r.returncode == 0:
        return r.stdout.strip()

    print(f"Erreur SSH pour [{cmd}] sur {host} : {r.stderr.strip()}")
    return None


def collect_local():
    """Collecte les informations de la machine locale avec les sondes du projet."""
    commandes = {
        "bash": ["bash", str(COLLECTE_DIR / "sonde_bash.sh")],
        "processus": ["bash", str(COLLECTE_DIR / "sonde_processus.sh")],
        "python": ["python3", str(COLLECTE_DIR / "sonde_bash.py")]
    }

    for sonde, cmd in commandes.items():
        sortie = run(cmd)

        if sortie:
            try:
                data = json.loads(sortie)
                sauvegarder_mesure("local", sonde, data)
                print(f"{sonde} sauvegardée pour local")
            except json.JSONDecodeError:
                print(f"Sortie invalide pour {sonde}")


def collect_remote(machine):
    """Récupère les informations système d'une machine distante via SSH.
    Si la machine est injoignable, on l'ignore et on continue avec les autres
    (une VM down ne doit pas bloquer la supervision du reste du parc)."""
    host = machine["host"]
    user = machine["user"]
    port = machine.get("port", 22)
    alias = machine.get("alias", host)

    print(f"Connexion SSH vers {user}@{host}:{port} ({alias})")

    data = {
        "hostname": ssh(host, user, port, "hostname"),
        "uptime": ssh(host, user, port, "uptime"),
        "memory": ssh(host, user, port, "free -m | grep '^Mem:'"),
        "disk": ssh(host, user, port, "df -h / | awk 'NR==2 {print $5}'"),
        "processus": ssh(host, user, port, "ps -e --no-headers | wc -l")
    }

    if all(value is not None for value in data.values()):
        sauvegarder_mesure(alias, "distance", data)
        print(f"Données distantes sauvegardées pour {alias}")
    else:
        print(f"Machine {alias} ignorée : informations incomplètes ou injoignable")


if __name__ == "__main__":
    print("=== GESTION DU PARC ===")
    init_bd()

    collect_local()

    machines = charger_machines()
    if not machines:
        print("Aucune machine distante configurée (voir config/machines.json).")

    for machine in machines:
        collect_remote(machine)

    print("Fin.")
