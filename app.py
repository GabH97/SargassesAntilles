import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import datetime
import os

st.title("Sargasses - Arc Antillais")
st.write("Suivi satellitaire (USF Marine Optics)")

# Configuration dynamique : Calcule automatiquement les 20 derniers jours
aujourd_hui = datetime.date.today()
year = aujourd_hui.year
# On recule de 2 jours car les images satellites mettent un peu de temps à être publiées
end_day = aujourd_hui.timetuple().tm_yday - 2 
num_days = 20

crop_box = (1, 520, 710, 1160)
mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

if st.button("Générer la mise à jour (Patientez ~15 sec)"):
    barre_progression = st.progress(0)
    texte_statut = st.empty()
    
    legende_img = None
    if os.path.exists("legende.png"):
        legende_img = Image.open("legende.png").convert("RGBA")

    frames = []
    
    for i in range(num_days):
        day = end_day - num_days + 1 + i
        day_str = f"{day:03d}"
        start_day = day - 6
        
        # Gestion du changement d'année pour le start_day
        if start_day < 1:
            start_day = 365 + start_day
            start_year = year - 1
        else:
            start_year = year
            
        start_day_str = f"{start_day:03d}"
        
        url = f"https://optics.marine.usf.edu/subscription/multi_sensor_fusion/C_ATLANTIC/{year}/comp/{day_str}/c{year}{start_day_str}{year}{day_str}.1KM.C_ATLANTIC.7DAY.L3D.FAD.png"
        
        try:
            response = requests.get(url)
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

                date_obj = datetime.datetime.strptime(f"{year}-{day_str}", "%Y-%j")
                texte_date = f"{date_obj.day} {mois_fr[date_obj.month - 1]} {date_obj.year}"

                bbox_jour = draw.textbbox((10, 10), texte_date, font=font_date)
                draw.rectangle([bbox_jour[0]-5, bbox_jour[1]-5, bbox_jour[2]+5, bbox_jour[3]+5], fill=(0, 0, 0))
                draw.text((10, 10), texte_date, font_date, fill=(255, 255, 255))

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
        except Exception as e:
            pass
        
        # Mise à jour de la barre de progression
        barre_progression.progress((i + 1) / num_days)

    if len(frames) > 0:
        texte_statut.empty() # On efface le texte de chargement
        output_filename = "animation.gif"
        frames[0].save(output_filename, save_all=True, append_images=frames[1:], duration=1000, loop=0)
        st.success("✅ Voici la dernière animation :")
        st.image(output_filename) # Affiche le GIF sur la page
    else:
        st.error("❌ Aucune image récente trouvée.")
