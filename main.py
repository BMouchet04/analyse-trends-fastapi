from fastapi import FastAPI
from pytrends.request import TrendReq
from fastapi.responses import JSONResponse
from datetime import datetime
import pandas as pd
import time

pd.set_option('future.no_silent_downcasting', True)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "API d'analyse comportementale opérationnelle"}

@app.get("/generate")
def generate_report():
    pytrends = TrendReq(hl='fr-FR', tz=360)

    SECTORS = {
        "Beauté": ["coiffeur", "soin visage", "épilation", "vernis", "institut beauté"],
        "Restauration": ["restaurant", "livraison repas", "UberEats", "menu midi", "réservation resto"],
        "Voyage & mobilité": ["billets d'avion", "location voiture", "Airbnb", "réservation hôtel", "train"],
        "Retail / Luxe": ["acheter chaussures", "sac à main", "montre luxe", "boutique mode", "soldes"],
        "Technologie & abonnements": ["abonnement Netflix", "désabonnement", "Spotify", "Disney+", "Prime Video"]
    }

    data_tabulaire = []
    sentiments = []

    for secteur, mots_cles in SECTORS.items():
        try:
            pytrends.build_payload(mots_cles, cat=0, timeframe='now 7-d', geo='FR', gprop='')
            df = pytrends.interest_over_time()
        except Exception:
            continue

        if 'isPartial' in df.columns:
            df = df.drop(columns='isPartial')

        deltas = []

        for mot in mots_cles:
            if mot in df.columns:
                tendance = df[mot]
                moyenne = round(tendance.mean(), 1)
                variation = round(((tendance.iloc[-1] - tendance.iloc[0]) / max(tendance.iloc[0], 1)) * 100, 1)
                deltas.append(variation)

                interpretation = "Hausse" if variation > 10 else "Baisse" if variation < -10 else "Stable"

                data_tabulaire.append({
                    "secteur": secteur,
                    "mot_cle": mot,
                    "score_moyen": moyenne,
                    "variation_pourcent": variation,
                    "interpretation": interpretation
                })

        if deltas:
            sentiments.append(sum(deltas) / len(deltas))
        time.sleep(2)  # pour éviter un code 429

    tendance_globale = (
        "positive" if sum(sentiments)/len(sentiments) > 10 else
        "négative" if sum(sentiments)/len(sentiments) < -10 else
        "stable"
    )
    variation_moyenne_globale = round(sum(sentiments) / len(sentiments), 1) if sentiments else 0

    today = datetime.now().strftime("%Y-%m-%d")

    return JSONResponse(content={
        "date": today,
        "tableau": data_tabulaire,
        "résumé_global": {
            "tendance_globale": tendance_globale,
            "variation_moyenne": variation_moyenne_globale
        }
    })
