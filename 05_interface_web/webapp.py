from flask import Flask, render_template
import sqlite3
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "02_stockage"))
from stockage import init_bd

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parents[1]
BDD = BASE_DIR / "data" / "monitoring.db"

def get_conn():
    return sqlite3.connect(BDD)

def recuperer_dernieres_mesures():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT machine, sonde, donnees, timestamp
        FROM mesures
        WHERE machine IS NOT NULL
        ORDER BY id DESC
    """)
    lignes = c.fetchall()
    conn.close()
    dernieres = {}
    for machine, sonde, donnees, timestamp in lignes:
        if machine not in dernieres:
            dernieres[machine] = {}
        if sonde not in dernieres[machine]:
            dernieres[machine][sonde] = {
                "timestamp": timestamp,
                "donnees": donnees
            }
    return dernieres

def recuperer_derniere_alerte():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT titre, lien, date_publication, date_recuperation
        FROM alertes_cert
        ORDER BY id DESC
        LIMIT 1
    """)
    ligne = c.fetchone()
    conn.close()
    if ligne:
        return {
            "titre": ligne[0],
            "lien": ligne[1],
            "date_publication": ligne[2],
            "date_recuperation": ligne[3]
        }
    return None

@app.route("/")
def index():
    mesures = recuperer_dernieres_mesures()
    alerte = recuperer_derniere_alerte()
    return render_template("index.html", mesures=mesures, alerte=alerte)

if __name__ == "__main__":
    init_bd()
    app.run(host="0.0.0.0", port=5000, debug=True)
