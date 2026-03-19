import requests
import json
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

STAND_FILE = "vorige_stand.json"
url = "https://www.gppoule.nl/topscores/17283/"

# Data ophalen
soup = BeautifulSoup(requests.get(url).text, "html.parser")

spelers = []
for rij in soup.select("a[href*='voorspellinginzien']"):
    tekst = [t for t in rij.get_text(separator="|").split("|") if t.strip()]
    if len(tekst) >= 3:
        spelers.append((tekst[0].strip(), tekst[1].strip(), tekst[2].strip()))

# Vorige stand laden (als die er is)
vorige = {}
if os.path.exists(STAND_FILE):
    with open(STAND_FILE, "r") as f:
        vorige = json.load(f)  # {"naam": plek, ...}

# Huidige stand opslaan voor volgende keer
huidige = {naam: int(plek) for plek, naam, _ in spelers}
with open(STAND_FILE, "w") as f:
    json.dump(huidige, f)

# Rijen bouwen met pijltjes
rijen = ""
kleuren = ["#FFD700", "#C0C0C0", "#CD7F32"]
for i, (plek, naam, punten) in enumerate(spelers):
    kleur = kleuren[i] if i < 3 else "white"
    
    # Positieverandering berekenen
    if naam in vorige:
        verschil = vorige[naam] - int(plek)  # positief = omhoog
        if verschil > 0:
            pijltje = f'<span style="color:#00cc44; font-size:0.75em; margin-left:10px">▲{verschil}</span>'
        elif verschil < 0:
            pijltje = f'<span style="color:#ff4444; font-size:0.75em; margin-left:10px">▼{abs(verschil)}</span>'
        else:
            pijltje = f'<span style="color:#888; font-size:0.75em; margin-left:10px">—</span>'
    else:
        pijltje = f'<span style="color:#888; font-size:0.75em; margin-left:10px">nieuw</span>'

    rijen += f'<tr style="color:{kleur}"><td>{plek}{pijltje}</td><td>{naam}</td><td>{punten} pts</td></tr>'

# HTML bouwen
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #1a1a2e;
    color: white;
    font-family: Arial, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60px;
  }}
  h1 {{ color: #ffd100; font-size: 3.5em; margin-bottom: 30px; }}
  table {{ width: 900px; border-collapse: collapse; font-size: 2em; }}
  td {{ padding: 16px 24px; border-bottom: 1px solid #333; }}
  td:last-child {{ text-align: right; font-weight: bold; }}
</style>
</head>
<body>
  <h1>🏎️ colorFabb F1 Poule</h1>
  <table>{rijen}</table>
</body>
</html>"""

# Screenshot maken, hoogte past zich aan de tabel aan
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 1920})
    page.set_content(html)
    # Echte hoogte van de pagina meten
    hoogte = page.evaluate("document.body.scrollHeight")
    page.set_viewport_size({"width": 1080, "height": hoogte})
    page.screenshot(path="stand.png", full_page=False)
    browser.close()

print("Klaar! stand.png aangemaakt.")
