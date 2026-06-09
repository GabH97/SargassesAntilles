import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import datetime
import os
import urllib.request
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- 0. INJECTION DU STYLE CSS POUR MOBILE ---
st.markdown("""
<style>
    /* Typographie globale optimisée pour l'écosystème Apple/Mobile */
    html, body, [class*="st-"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    
    /* Titre principal de l'application (H1) */
    h1 {
        font-size: 32px !important;
        font-weight: 800 !important;
        line-height: 1.2 !important;
        padding-bottom: 5px !important;
    }
    
    /* Sous-titres de section (ex: Prévisions Météo France) (H2) */
    h2 {
        font-size: 24px !important;
        font-weight: 700 !important;
        margin-top: 30px !important;
        padding-bottom: 10px !important;
        border-bottom: 2px solid #f0f2f6 !important;
    }
    
    /* Titres de paragraphes (ex: Prévisions pour les 4 prochains jours) (H3, H4) */
    h3, h4 {
        font-size: 20px !important;
        font-weight: 600 !important;
        margin-top: 15px !important;
        margin-bottom: 10px !important;
    }
    
    /* Texte normal de lecture, paragraphes et listes */
    p, li, .stMarkdown {
        font-size: 16px !important;
        line-height: 1.6 !important;
        color: #2c3e50 !important;
    }

    /* Amélioration du bouton pour les doigts sur écran tactile (pouce) */
    .stButton>button {
        width: 100% !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 12px !important;
        border-radius: 8px !important;
        margin-bottom: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Sargasses - Arc Antillais")
st.write("Suivi satellitaire (USF Marine Optics)")

# --- 1. CONFIGURATION ---
aujourd_hui = datetime.date.today()
year = aujourd_hui.year
end_day = aujourd_hui.timetuple().tm_yday
num_days_history = 20 

crop_box = (1, 450, 710, 1150)
mois_fr = ["janvier", "fév
