from fastapi import FastAPI
from pytrends.request import TrendReq
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime
import pandas as pd
import time  # ✅ ajout pour limiter les requêtes trop rapides

pd.set_option('future.no_silent_downcasting', True)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "OK", "message": "API d'analyse comportementale opérationnelle"}

@app.get("/generate")
from fastapi.responses import JSONResponse

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

    all_data = []
    sentiments = []
    sector_summaries = {}

    for sector, keywords in SECTORS.items():
        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='FR', gprop='')
        data = pytrends.interest_over_time()
        if 'isPartial' in data.columns:
            data = data.drop(columns='isPartial')

        sector_data = []
        deltas = []

        for keyword in keywords:
            if keyword in data.columns:
                trend = data[keyword]
                avg = round(trend.mean(), 1)
                pct_change = round(((trend.iloc[-1] - trend.iloc[0]) / max(trend.iloc[0], 1)) * 100, 1)
                deltas.append(pct_change)

                impact = "Hausse" if pct_change > 10 else "Baisse" if pct_change < -10 else "Stable"

                sector_data.append({
                    "mot_clé": keyword,
                    "score_moyen": avg,
                    "variation_%": pct_change,
                    "interprétation": impact
                })

        sentiment = sum(deltas) / len(deltas) if deltas else 0
        sentiments.append(sentiment)

        summary = {
            "tendance": "positive" if sentiment > 10 else "négative" if sentiment < -10 else "stable",
            "variation_moyenne": round(sentiment, 1)
        }

        sector_summaries[sector] = summary

        all_data.append({
            "secteur": sector,
            "données": sector_data,
            "résumé": summary
        })

    global_sentiment = sum(sentiments) / len(sentiments)
    global_summary = {
        "tendance_globale": "positive" if global_sentiment > 10 else "négative" if global_sentiment < -10 else "stable",
        "variation_moyenne": round(global_sentiment, 1)
    }

    return JSONResponse(content={
        "analyse": all_data,
        "résumés_sectoriels": sector_summaries,
        "résumé_global": global_summary
    })
    return {"status": "ok", "fichier": filename}
