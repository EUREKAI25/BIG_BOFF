import os
import streamlit as st
from backend.fbadvertising import collect_ads

def show_ad_visual(ad):
    """Affiche une miniature sans jamais faire planter Streamlit."""
    tp = ad.get("thumb_path")
    iu = ad.get("image_url")

    # 1) fichier local existant (Playwright)
    if isinstance(tp, str) and tp:
        fp = Path(tp)
        if fp.exists() and fp.is_file() and fp.stat().st_size > 0:
            st.image(str(fp), width="stretch")
            return

    # 2) URL directe
    if isinstance(iu, str) and iu.startswith(("http://", "https://")):
        st.image(iu, width="stretch")
        return

    st.warning("Aucun visuel (miniature indisponible)")
st.set_page_config(layout="wide")
st.title("Ad Library Watch")

token = os.getenv("META_ACCESS_TOKEN")
if not token:
    st.error("META_ACCESS_TOKEN manquant")
    st.stop()

keyword = st.text_input("Mot-clé", "coach")
countries = [c.strip().upper() for c in countries_text.split(',') if c.strip()]
active_only = st.checkbox("Actives seulement", True)
limit = st.slider("Nombre max", 10, 200, 50)
use_pw = st.checkbox("Miniatures via Playwright (lent, mais fiable)", False)
thumb_max = st.slider("Miniatures max (Playwright)", 0, 80, 30)
st.caption("Astuce: active Playwright seulement quand tu veux vraiment les visuels. Sinon, c’est beaucoup plus rapide.")

if st.button("Lancer"):
    ads = collect_ads(
        token,
        keyword,
        countries.split(","),
        limit=limit,
        active_only=active_only,
        use_playwright_thumbs=use_pw,
        thumb_max=thumb_max,
    )

    for ad in ads:
        col1, col2 = st.columns([1, 2])
        with col1:
            show_ad_visual(ad)
        with col2:
            st.markdown(f"**{ad['page_name']}**")
            st.write(f"Début : {ad['start_mm_yy']}")
            st.write(f"Longévité : {ad['longevity_human']} — {ad['longevity_days']} jours")
            st.write(f"Statut : {ad['status']}")
            st.markdown(f"[Ouvrir l’annonce]({ad['ad_snapshot_url']})")
        st.divider()
