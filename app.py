import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import datetime
import os

st.title("Sargasses - Arc Antillais")
st.write("Suivi satellitaire (USF Marine Optics)")

# Ajout d'un réglage au cas où l'université a du retard dans ses publications
decalage = st.number_input("Décalage des données (jours de retard)", min_value=1, max_value=15, value=2)

aujourd_hui = datetime.date.today()
year = aujourd_hui.year
end_day = aujourd_hui.timetuple().tm_yday - decalage
num_days = 20

crop_box = (1, 520, 710, 1160)
mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

# Fausse identité pour éviter d'être bloqué par le serveur de l'université
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
}

if st.button("Générer la mise à jour"):
    barre_progression = st.progress(0)
    texte_statut = st.empty()
    
    legende_img = None
    if os.path.exists("legende.png"):
        legende_img = Image.open("legende.png").convert("RGBA")

    frames = []
    derniere_erreur = "Raison inconnue"
    
    for i in range(num_days):
        day = end_day - num_days + 1 + i
        
        # Gestion des années (si on chevauche entre décembre et janvier)
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
            # On envoie la requête avec le faux navigateur (headers)
            response = requests.get(url, headers=headers, timeout=10)
            
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
                    font_date = ImageFont.truetype("LiberationSans-Bold.ttf", 20)
                    font_source = ImageFont.truetype("LiberationSans-Regular.ttf", 14)
                except:
                    font_date = ImageFont.load_default()
                    font_source = ImageFont.load_default()

                date_obj = datetime.datetime.strptime(f"{year_corrige}-{day_str}", "%Y-%j")
                texte_date = f"{date_obj.day} {mois_fr[date_obj.month - 1]} {date_obj.year}"

                bbox_jour = draw.textbbox((10, 10), texte_date, font=font_date)
                draw.rectangle([bbox_jour[0]-5, bbox_jour[1]-5, bbox_jour[2]+5, bbox_jour[3]+5], fill=(0, 0, 0))
                draw.text((10, 10), texte_date, font=font_date, fill=(255, 255, 255))

                texte_source = "Source : https://optics.marine.usf.edu"
                bbox_source = draw.textbbox((0, 0), texte_source, font=font_source)
                l_txt = bbox_source[2] - bbox_source[0]
                h_txt = bbox_source[3] - bbox_source[1]
                
                x_source = (img_cropped.width - l_txt) // 2
                y_source = img_cropped.height - h_txt - 15
                
                draw.rectangle([x_source - 5, y_source - 5, x_source + l_txt + 5, y_source + h_txt + 5], fill=(0, 0, 0))
                draw.text((x_source, y_source), texte_source, font=font_source, fill=(255, 255, 255))

                frames.append(img_cropped)
                texte_statut.text(f"Téléchargement du {texte_date}...")
            else:
                derniere_erreur = f"Erreur {response.status_code} (Le fichier du jour {day_str} n'existe pas encore sur le serveur)"
        except Exception as e:
            derniere_erreur = f"Erreur technique : {str(e)}"
        
        # Mise à jour de la barre de progression
        barre_progression.progress((i + 1) / num_days)

    if len(frames) > 0:
        texte_statut.empty()
        output_filename = "animation.gif"
        frames[0].save(output_filename, save_all=True, append_images=frames[1:], duration=1000, loop=0)
        st.success("✅ Voici la dernière animation :")
        st.image(output_filename)
    else:
        # Affichage précis du problème si ça échoue encore
        st.error(f"❌ Aucune image récente trouvée.\n\n**Détail du problème :** {derniere_erreur}")
