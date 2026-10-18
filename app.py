import os
from google import genai
from google.genai import types
from PIL import Image
import requests
import streamlit as st

st.set_page_config(
    page_title="AquaSmart Batman",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌱 AquaSmart Batman")
st.subheader(
    "Yapay Zekâ & Canlı Hava Durumu Destekli Tarımsal Karar Destek Sistemi"
)
st.markdown("""
Batman ve çevre havzalara özel; anlık hava durumu ve yapay zekâ analizleriyle 
hastalık tespiti yapar, vahşi sulama kayıplarını ve kimyasal israfını önleyecek reçeteler sunar.
""")

# API Anahtarı Yönetimi
api_key = None
if "GEMINI_API_KEY" in st.secrets:
  api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
  api_key = os.environ["GEMINI_API_KEY"]

with st.sidebar:
  st.header("⚙️ Sistem Ayarları")
  if not api_key:
    user_key = st.text_input("Gemini API Anahtarı:", type="password")
    if user_key:
      api_key = user_key

  st.markdown("---")
  st.markdown("### 📍 Konum ve Bölge")
  ilceler = {
      "Batman Merkez": {"lat": 37.8874, "lon": 41.1322},
      "Kozluk": {"lat": 38.1925, "lon": 41.4875},
      "Beşiri": {"lat": 37.9208, "lon": 41.2858},
      "Hasankeyf": {"lat": 37.7139, "lon": 41.4128},
      "Gercüş": {"lat": 37.5683, "lon": 41.3853},
      "Sason": {"lat": 38.3283, "lon": 41.4158},
      "Bismil Hattı": {"lat": 37.8464, "lon": 40.6653},
  }
  secilen_ilce = st.selectbox("İlçe / Tarla Konumu:", list(ilceler.keys()))
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
          "sicaklik": current.get("temperature_2m", "N/A"),
          "hissedilen": current.get("apparent_temperature", "N/A"),
          "nem": current.get("relative_humidity_2m", "N/A"),
          "ruzgar": current.get("wind_speed_10m", "N/A"),
      }
    except Exception:
      return None


  hava_verisi = hava_durumu_al(lat, lon)
  if hava_verisi and hava_verisi["sicaklik"] != "N/A":
    st.markdown("### 🌤️ Anlık Saha Meteorolojisi")
    c1, c2 = st.columns(2)
    c1.metric("Sıcaklık", f"{hava_verisi['sicaklik']} °C")
    c2.metric("Bağıl Nem", f"%{hava_verisi['nem']}")
    st.caption(
        f"Rüzgâr: {hava_verisi['ruzgar']} km/s | Hissedilen:"
        f" {hava_verisi['hissedilen']} °C"
    )
    if float(hava_verisi["sicaklik"]) >= 35:
      st.warning("⚠️ Yüksek buharlaşma riski! Gündüz vahşi sulama yapmayınız.")

if not api_key:
  st.warning(
      "⚠️ Devam etmek için Secrets alanına veya sol menüye API anahtarını girin."
  )
  st.stop()

# İstemciyi başlat
try:
  client = genai.Client(api_key=api_key)
except Exception as e:
  st.error(f"İstemci başlatılamadı: {e}")
  st.stop()

st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
  st.markdown("### 📸 Saha / Bitki Fotoğrafı")
  uploaded_file = st.file_uploader(
      "Fotoğraf yükleyin:", type=["jpg", "jpeg", "png"]
  )
  urun_tipi = st.selectbox(
      "Ürün Türü:",
      ["Dane Mısır", "Pamuk", "Buğday", "Sebze / Saksı Bitkisi", "Diğer"],
  )
  sulama_tipi = st.radio(
      "Sulama Yöntemi:", ["Vahşi / Salma Sulama", "Damlama Sulama"]
  )

  if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Yüklenen Görsel", use_column_width=True)

with col2:
  st.markdown("### 🩺 Teşhis & Rapor")
  if uploaded_file is not None:
    if st.button("🔍 Durumu Teşhis Et ve Su Raporunu Çıkar", type="primary"):
      with st.spinner("Analiz ediliyor..."):
        try:
          hava_bilgisi = (
              f"{hava_verisi['sicaklik']}°C, Nem: %{hava_verisi['nem']}"
              if hava_verisi
              else "Normal"
          )
          prompt = f"""
                    Sen Batman yöresinde uzmanlaşmış kıdemli bir Ziraat Mühendisi ve Bitki Patoloğusun.
                    Görseldeki bitkiyi incele:
                    - Konum: {secilen_ilce} / Batman
                    - Anlık Hava Durumu: {hava_bilgisi}
                    - Ürün: {urun_tipi}
                    - Mevcut Sulama: {sulama_tipi}
                    
                    Lütfen şu başlıklarda pratik ve net bilgi ver:
                    1. GÖRSEL TEŞHİS: Belirtiler ve tespit edilen zararlı/hastalık (Örn: Unlu bit, kloroz, yanıklık).
                    2. KÖK NEDEN VE ÇEVRESEL ETKİ: Vahşi sulama, aşırı nem veya kuraklık etkisi var mı?
                    3. KÜLTÜREL VE KİMYASAL MÜCADELE: Aşırı ilaç ve hormon israfını önleyecek hedefli çözümler.
                    4. AKILLI SULAMA REÇETESİ: Batman iklimine uygun su tasarrufu önerisi.
                    """
          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=[prompt, image]
          )
          st.success("✅ Teşhis Tamamlandı!")
          st.markdown(response.text)
        except Exception as e:
          st.error(f"Hata oluştu: {e}")
  else:
    st.info("👈 Analiz için soldan bir fotoğraf yükleyin.")
