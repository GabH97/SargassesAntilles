import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import datetime
import os
import urllib.request
from bs4 import BeautifulSoup

st.title("Sargasses - Arc Antillais")
st.write("Suivi satellitaire (USF Marine Optics)")

# --- 1. CONFIGURATION ---
aujourd_hui = datetime.date.today()
year = aujourd_hui.year
end_day = aujourd_hui.timetuple().tm_yday
num_days_history = 25 

crop_box = (1, 520, 710, 1160)
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
                    font_date = ImageFont.truetype(font_filename, 60) 
                    font_source = ImageFont.truetype(font_filename, 42) 
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


# --- 3. BULLETIN MÉTÉO FRANCE (NOUVEAU) ---
st.markdown("---")
st.subheader("Prévisions Météo France")

try:
    url_mf = "https://meteofrance.gp/fr/sargasses"
    req_mf = requests.get(url_mf, headers=headers, timeout=10)
    
    if req_mf.status_code == 200:
        soup = BeautifulSoup(req_mf.text, 'html.parser')
        
        # 1. Recherche de la carte d'échouement (image)
        images = soup.find_all('img')
        url_carte = None
        for img in images:
            src = img.get('src', '')
            # On cherche une image qui ressemble à la carte des sargasses
            if 'sargasse' in src.lower() or 'echouement' in src.lower() or 'carte' in src.lower() or 'prevision' in src.lower():
                url_carte = src
                break
        
        if url_carte:
            # Sécurité si l'URL de l'image est relative (commence par /)
            if url_carte.startswith('/'):
                url_carte = "https://meteofrance.gp" + url_carte
            st.image(url_carte, caption="Carte prévisionnelle (Météo France)")
            
        # 2. Recherche du texte des prévisions
        st.markdown("#### Prévisions pour les 4 prochains jours")
        
        # On cherche tous les titres ou textes en gras
        titres = soup.find_all(['h2', 'h3', 'h4', 'strong', 'div'])
        texte_trouve = False
        
        for titre in titres:
            if "4 prochains jours" in titre.get_text().lower() or "prévisions" in titre.get_text().lower():
                # On parcours les paragraphes qui suivent ce titre
                element_suivant = titre.find_next_sibling()
                
                # Tant qu'on trouve des paragraphes ou des listes, on les affiche
                while element_suivant and element_suivant.name in ['p', 'div', 'ul']:
                    texte = element_suivant.get_text().strip()
                    if texte and len(texte) > 10: # On évite les paragraphes vides
                        st.write(texte)
                        texte_trouve = True
                    element_suivant = element_suivant.find_next_sibling()
                
                if texte_trouve:
                    break # On arrête de chercher si on a trouvé le bon bloc
                    
        if not texte_trouve:
            st.info("Le texte de prévision n'a pas pu être extrait. Consultez le site complet ci-dessous.")
            
        st.markdown("\n\n*Source complète : [meteofrance.gp/fr/sargasses](https://meteofrance.gp/fr/sargasses)*")

    else:
        st.error(f"Impossible de joindre Météo France (Erreur {req_mf.status_code}).")
        
except Exception as e:
    st.warning("Le bulletin Météo France est temporairement indisponible depuis l'application.")
