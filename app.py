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
mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
}

font_filename = "Roboto-Bold.ttf"
if not os.path.exists(font_filename):
    try:
        url_font = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
        urllib.request.urlretrieve(url_font, font_filename)
    except:
        pass 

# --- 2. GÉNÉRATION DE L'ANIMATION SATELLITE ---
if st.button("Générer la mise à jour (Patientez ~15 sec)"):
    barre_progression = st.progress(0)
    texte_statut = st.empty()
    
    legende_img = None
    if os.path.exists("legende.png"):
        legende_img = Image.open("legende.png").convert("RGBA")

    frames = []
    
    for i in range(num_days_history):
        day = end_day - num_days_history + 1 + i
        
        if day <= 0:
            day_corrige = 365 + day
            year_corrige = year - 1
        else:
            day_corrige = day
            year_corrige = year
            
        day_str = f"{day_corrige:03d}"
        
        start_day = day_corrige - 6
        if start_day <= 0:
            start_day = 365 + start_day
            start_year = year_corrige - 1
        else:
            start_year = year_corrige
            
        start_day_str = f"{start_day:03d}"
        
        url = f"https://optics.marine.usf.edu/subscription/multi_sensor_fusion/C_ATLANTIC/{year_corrige}/comp/{day_str}/c{start_year}{start_day_str}{year_corrige}{day_str}.1KM.C_ATLANTIC.7DAY.L3D.FAD.png"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img_cropped = img.crop(crop_box).convert("RGBA")
                
                if legende_img:
                    x_paste = img_cropped.width - legende_img.width - 10
                    y_paste = img_cropped.height - legende_img.height - 10
                    img_cropped.paste(legende_img, (x_paste, y_paste), legende_img)

                img_cropped = img_cropped.convert("RGB")
                draw = ImageDraw.Draw(img_cropped)
                
                try:
                    font_date = ImageFont.truetype(font_filename, 30) 
                    font_source = ImageFont.truetype(font_filename, 25) 
                except:
                    font_date = ImageFont.load_default()
                    font_source = ImageFont.load_default()

                date_obj = datetime.datetime.strptime(f"{year_corrige}-{day_str}", "%Y-%j")
                texte_date = f"{date_obj.day} {mois_fr[date_obj.month - 1]} {date_obj.year}"

                bbox_jour = draw.textbbox((15, 15), texte_date, font=font_date)
                draw.rectangle([bbox_jour[0]-10, bbox_jour[1]-10, bbox_jour[2]+10, bbox_jour[3]+10], fill=(0, 0, 0))
                draw.text((15, 15), texte_date, font=font_date, fill=(255, 255, 255))

                texte_source = "Source : https://optics.marine.usf.edu"
                bbox_source = draw.textbbox((0, 0), texte_source, font=font_source)
                l_txt = bbox_source[2] - bbox_source[0]
                h_txt = bbox_source[3] - bbox_source[1]
                
                x_source = (img_cropped.width - l_txt) // 2
                y_source = img_cropped.height - h_txt - 20 
                
                draw.rectangle([x_source - 10, y_source - 10, x_source + l_txt + 10, y_source + h_txt + 10], fill=(0, 0, 0))
                draw.text((x_source, y_source), texte_source, font=font_source, fill=(255, 255, 255))

                frames.append(img_cropped)
                texte_statut.text(f"✅ Image du {texte_date} récupérée !")
            else:
                texte_statut.text(f"Image du jour {day_str} non disponible (ignorée)")
        except Exception as e:
            pass 
        
        barre_progression.progress((i + 1) / num_days_history)

    if len(frames) > 0:
        texte_statut.empty()
        output_filename = "animation.gif"
        frames[0].save(output_filename, save_all=True, append_images=frames[1:], duration=1000, loop=0)
        st.success(f"✅ Animation générée avec {len(frames)} images !")
        st.image(output_filename)
    else:
        st.error("❌ Aucune image n'a pu être téléchargée pour le moment. Réessayez demain !")


# --- 3. FONCTION DE LECTURE DES BULLETINS MÉTÉO FRANCE ---
def afficher_bulletin_mf(url_mf, base_url, titre_section):
    st.subheader(titre_section)
    
    try:
        req_mf = requests.get(url_mf, headers=headers, timeout=10)
        
        if req_mf.status_code == 200:
            soup = BeautifulSoup(req_mf.text, 'html.parser')
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='region-content') or soup
            
            # 1. Extraction de la Date
            date_bulletin = None
            for p in main_content.find_all(['p', 'h2', 'div']):
                texte = p.get_text().strip()
                if "202" in texte and len(texte) < 50 and "{" not in texte and "$" not in texte:
                    date_bulletin = texte
                    break
            
            if date_bulletin:
                st.markdown(f"**Mise à jour : {date_bulletin}**")

            # 2. Extraction de la Carte
            url_carte = None
            for el in main_content.find_all(['p', 'h2', 'h3', 'h4', 'div', 'strong', 'figcaption']):
                if "carte de prévision" in el.get_text().lower() or "carte des risques" in el.get_text().lower():
                    img_suivante = el.find_next('img')
                    if img_suivante:
                        url_carte = img_suivante.get('src')
                        break

            if not url_carte:
                for img in main_content.find_all('img'):
                    src = img.get('src', '').lower()
                    alt = img.get('alt', '').lower()
                    mots_interdits = ['logo', 'icon', 'banner', 'bg', 'avatar', 'photo', 'paysage', 'plage', 'baie', 'illustr', 'header', 'default']
                    
                    if not any(mot in src for mot in mots_interdits) and not any(mot in alt for mot in mots_interdits):
                        if 'carte' in src or 'prev' in src or 'risque' in src or 'echouement' in src or 'carte' in alt:
                            url_carte = img.get('src')
                            break

            if url_carte:
                url_carte_complete = urljoin(base_url, url_carte)
                st.image(url_carte_complete, caption="Carte de prévision d'échouement (Météo France)")

            # 3. Récupération et tri des Textes
            titres = main_content.find_all(['h2', 'h3', 'h4', 'strong'])
            
            indice_confiance = None
            previsions_texte = []
            
            for titre in titres:
                texte_titre = titre.get_text().strip()
                
                # Récupération de l'indice
                if "Indice de confiance" in texte_titre:
                    suivant = titre.find_next_sibling()
                    if suivant and "{" not in suivant.get_text():
                        indice_confiance = suivant.get_text().strip()
                
                # Récupération des prévisions
                elif "4 prochains jours" in texte_titre.lower() and not previsions_texte:
                    element_suivant = titre.find_next_sibling()
                    
                    while element_suivant and element_suivant.name in ['p', 'ul', 'div']:
                        texte_para = element_suivant.get_text().strip()
                        if texte_para and "{" not in texte_para and "$" not in texte_para:
                            previsions_texte.append(texte_para)
                        element_suivant = element_suivant.find_next_sibling()

            # 4. Affichage dans l'ordre strict demandé
            if indice_confiance:
                st.
