import streamlit as st
from PIL import Image
import requests
import json
import base64
import io
import os

st.set_page_config(
    page_title="AquaSmart Batman",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Temiz, Modern ve Ferah Tasarım
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top right, #0d3b1e 0%, #061f10 50%, #020e07 100%);
        color: #f0fdf4 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(6, 31, 16, 0.85) !important;
        border-right: 1.5px solid #10b981;
    }
    .ar_ge_kart {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
    }
    .kar_kutusu {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid #10b981;
        border-radius: 12px;
        padding: 16px;
        margin-top: 15px;
    }
    h1, h2, h3 {
        color: #6ee7b7 !important;
        font-family: 'Inter', sans-serif;
    }
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #047857 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌱 AquaSmart Batman")
st.subheader("Akıllı Bitki Sağlığı ve Doğru Sulama Rehberi")

# --- API ANAHTARI ---
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

# --- YAN MENÜ: KONUM VE CANLI HAVA DURUMU ---
with st.sidebar:
    st.header("📍 Konum Seçimi")
    ilceler = {
        "Batman Merkez": {"lat": 37.8874, "lon": 41.1322},
        "Kozluk": {"lat": 38.1925, "lon": 41.4875},
        "Beşiri": {"lat": 37.9208, "lon": 41.2858},
        "Hasankeyf": {"lat": 37.7139, "lon": 41.4128},
        "Gercüş": {"lat": 37.5683, "lon": 41.3853},
        "Sason": {"lat": 38.3283, "lon": 41.4158},
        "Bismil Hattı": {"lat": 37.8464, "lon": 40.6653}
    }
    secilen_ilce = st.selectbox("Bölgenizi Seçin:", list(ilceler.keys()))
    lat = ilceler[secilen_ilce]["lat"]
    lon = ilceler[secilen_ilce]["lon"]
    
    @st.cache_data(ttl=600)
    def hava_durumu_al(enlem, boylam):
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={enlem}&longitude={boylam}&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m&timezone=auto"
            res = requests.get(url, timeout=5)
            data = res.json()
            current = data.get("current", {})
            return {
                "sicaklik": current.get("temperature_2m", 24.5),
                "hissedilen": current.get("apparent_temperature", 25.0),
