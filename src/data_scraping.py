
import requests
import csv
import time
import pandas as pd

"""
#URL pour récupérer les IDs des teams de ligue 1 :
url = "https://fbrapi.com/team-season-stats"

params = {
    "league_id": "13",        # Remplace par l’ID de la ligue (ex: Ligue 1)
    "season_id": "2024-2025"
}

headers = {
    "X-API-Key": api_key
}

resp = requests.get(url, params=params, headers=headers)

team_dict = {}  # Dictionnaire final

if resp.status_code != 200:
    print("Erreur lors de la récupération des équipes :", resp.text)
else:
    data = resp.json().get("data", [])
    team_ids = []

    print("\nListe des équipes de Ligue 1 :")
    for team in data:
        meta = team.get("meta_data", {})
        team_id = meta.get("team_id")
        team_name = meta.get("team_name")

        if team_id and team_name:
            team_dict[team_name] = team_id
            print(f"- {team_name} ({team_id})")

    print("\nDictionnaire final (team_name -> team_id) :")
    print(team_dict)

with open("team_dict.csv", "w", newline='', encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["team_name", "team_id"])
    for name, id_ in team_dict.items():
        writer.writerow([name, id_])
"""
# Générer la clé
response = requests.post('https://fbrapi.com/generate_api_key')
api_key = response.json()['api_key']
print("API Key:", api_key)

headers = {
    "X-API-Key": api_key
}

team_dict = {}
with open("team_dict.csv", "r", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        team_dict[row["team_name"]] = row["team_id"]

url_players = "https://fbrapi.com/player-season-stats"

all_players = []

def fetch_with_retries(team_name, team_id, max_retries=3):
    """Essaie plusieurs fois de récupérer les données du joueur pour une équipe."""
    params = {
        "team_id": team_id,
        "league_id": "9",
        "season_id": "2024-2025"
    }
    for attempt in range(1, max_retries + 1):
        resp = requests.get(url_players, params=params, headers=headers)
        if resp.status_code == 200:
            players = resp.json().get("players", [])
            return players
        else:
            print(f" → tentative {attempt} : erreur {resp.status_code} pour l'équipe {team_name}")
            # Si ce n’est pas la dernière tentative, attendre un peu avant de réessayer
            # On peut utiliser un back-off linéaire / exponentiel
            wait = 6 + (attempt - 1) * 3  # par exemple 6s, puis 9s, puis 12s
            print(f"   Attente de {wait} secondes avant retry…")
            time.sleep(wait)
    # Après toutes les tentatives, on abandonne
    print(f"Erreur persistante pour l'équipe {team_name}. On saute.")
    return []

# Boucle équipes
for team_name, team_id in team_dict.items():
    print(f"In the loop : team {team_name} / {team_id}")
    players = fetch_with_retries(team_name, team_id, max_retries=3)
    for p in players:
        flat_player = {
            "equipe": team_name,
            **p.get("meta_data", {}),
            **p.get("stats", {}).get("stats", {}),
            **p.get("stats", {}).get("shooting", {}),
            **p.get("stats", {}).get("passing", {}),
            **p.get("stats", {}).get("passing_types", {}),
            **p.get("stats", {}).get("gca", {}),
            **p.get("stats", {}).get("defense", {}),
            **p.get("stats", {}).get("possession", {}),
            **p.get("stats", {}).get("playingtime", {}),
            **p.get("stats", {}).get("misc", {})
        }
        all_players.append(flat_player)

    # Toujours respecter le délai minimum entre deux appels initiaux
    time.sleep(6)

if not all_players:
    print("❌ Aucun joueur récupéré. Trop d’erreurs peut‑être.")
else:
    print(f"✅ {len(all_players)} joueurs récupérés.")
    df = pd.DataFrame(all_players)
    df.to_csv("joueurs_ligue1_2024_2025.csv", index=False, encoding="utf-8")
    print("✅ Export CSV terminé.")
