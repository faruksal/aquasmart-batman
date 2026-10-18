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

st.title("🌱 AquaSmart Batman")
st.subheader("Otonom Yapay Zekâ & Canlı Meteoroloji Destekli Tarımsal/Kentsel Karar Destek Sistemi")
st.markdown("""
Batman ve çevre havzalar için akıllı teşhis platformu: Fotoğrafı yükleyin; yapay zekâ **bitkinin türünü**, **yetiştirildiği ortamı (saksı, bahçe, refüj veya açık tarla)** ve **hastalık/zararlı durumunu** otonom olarak belirlesin. Canlı meteoroloji verisiyle harmanlanmış akıllı su tasarrufu ve mücadele reçetesini anında çıkarsın.
""")

# --- API ANAHTARI VE GÜVENLİK YÖNETİMİ ---
api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

# --- YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Sistem ve Saha Ayarları")
    
    user_key = st.text_input("Gemini API Key / Token:", value=api_key, type="password")
    if user_key:
        api_key = user_key
        
    st.markdown("---")
    st.markdown("### 📍 Konum Seçimi")
    ilceler = {
        "Batman Merkez": {"lat": 37.8874, "lon": 41.1322},
        "Kozluk": {"lat": 38.1925, "lon": 41.4875},
        "Beşiri": {"lat": 37.9208, "lon": 41.2858},
        "Hasankeyf": {"lat": 37.7139, "lon": 41.4128},
        "Gercüş": {"lat": 37.5683, "lon": 41.3853},
        "Sason": {"lat": 38.3283, "lon": 41.4158},
        "Bismil Hattı": {"lat": 37.8464, "lon": 40.6653}
    }
    secilen_ilce = st.selectbox("İlçe / Bölge:", list(ilceler.keys()))
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
                "ruzgar": current.get("wind_speed_10m", "N/A")
            }
        except Exception:
            return None

    hava_verisi = hava_durumu_al(lat, lon)
    if hava_verisi and hava_verisi["sicaklik"] != "N/A":
        st.markdown("### 🌤️ Anlık Saha Meteorolojisi")
        c1, c2 = st.columns(2)
        c1.metric("Sıcaklık", f"{hava_verisi['sicaklik']} °C")
        c2.metric("Bağıl Nem", f"%{hava_verisi['nem']}")
        st.caption(f"Rüzgâr: {hava_verisi['ruzgar']} km/s | Hissedilen: {hava_verisi['hissedilen']} °C")
        if float(hava_verisi["sicaklik"]) >= 35:
            st.warning("⚠️ Yüksek sıcaklık ve buharlaşma riski! Gündüz saatlerinde sulama yapmayınız.")

st.markdown("---")
col1, col2 = st.columns([1, 1])

# --- GİRİŞ PANELİ ---
with col1:
    st.markdown("### 📸 Bitki / Saha Fotoğrafı")
    uploaded_file = st.file_uploader("Analiz Edilecek Fotoğrafı Yükleyin:", type=["jpg", "jpeg", "png"])
    
    st.caption("ℹ️ *Bitki türünü, yetiştirme alanını (saksı, bahçe, refüj veya tarla) yapay zekâ görselden kendisi tespit edecektir.*")
    
    sulama_tipi = st.selectbox(
        "Mevcut Sulama / Su Verme Şekli:",
        ["Bilinmiyor / Belirtilmedi", "Vahşi / Salma / Karık Sulama", "Damlama Sulama", "Yağmurlama Sulama", "Manuel (Hortum / Saksı Kabı)"]
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Görsel", use_container_width=True)

# --- ANALİZ VE RAPOR PANELİ ---
with col2:
    st.markdown("### 🩺 Otonom Teşhis & Bilimsel Reçete")
    if uploaded_file is not None:
        if st.button("🔍 Fotoğrafı Analiz Et ve Raporu Çıkar", type="primary"):
            if not api_key:
                st.error("⚠️ Devam etmek için Secrets alanına veya sol menüye geçerli anahtarınızı ekleyin.")
            else:
                with st.spinner("Görsel taranıyor, bitki türü, ortamı ve hastalık durumu belirleniyor..."):
                    try:
                        buffered = io.BytesIO()
                        image.save(buffered, format="JPEG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        
                        hava_bilgisi = f"{hava_verisi['sicaklik']}°C, Nem: %{hava_verisi['nem']}, Rüzgar: {hava_verisi['ruzgar']} km/s" if hava_verisi else "Normal Saha Şartları"
                        
                        prompt_text = f"""
                        Sen GAP havzası ve Batman ikliminde uzmanlaşmış kıdemli bir Ziraat Mühendisi, Bitki Patoloğu ve Peyzaj Uzmanısın.
                        Kullanıcı sana bir fotoğraf yükledi. Bitkiyi ve ortamı sen teşhis edeceksin.

                        Saha Parametreleri:
                        - Lokasyon: {secilen_ilce} / Batman
                        - Canlı Meteoroloji: {hava_bilgisi}
                        - Bildirilen Sulama Yöntemi: {sulama_tipi}

                        Görseli detaylı inceleyerek şu 4 bölümü eksiksiz doldur:

                        1. 🏷️ OTONOM BİTKİ VE YETİŞME ALANI TEŞHİSİ:
                           - Bitkinin Türü / Cinsi (Örn: Limon/Narenciye, Dane Mısır, Pamuk, Sukulent, Gül vb.)
                           - Yetiştirildiği Alan / Ölçek (Fotoğraftaki arka plana ve saksı/toprak durumuna göre: Saksı/Balkon mu, Park/Refüj/Peyzaj mı, yoksa Açık Tarla/Dekar ölçeği mi olduğunu belirt.)

                        2. 🔍 GÖRSEL TEŞHİS VE ZARARLI/HASTALIK TANISI:
                           - Tespit edilen patojen, mantar veya zararlı (Örn: Unlu bit / Pseudococcidae, kloroz vb.)
                           - Zararlının/hasarın yoğunluk derecesi.

                        3. 🌿 HEDEFLİ MÜCADELE REÇETESİ (ALANA ÖZEL DOZ VE ÇÖZÜM):
                           - Eğer saksı/balkon bitkisi ise: Ev tipi pratik formül (Arap sabunu solüsyonu, alkollü pamukla temizlik vb.).
                           - Eğer refüj/peyzaj alanı ise: Kentsel çevreye uygun peyzaj ilaçlama tavsiyesi.
                           - Eğer açık tarla ise: Dekar başına uygun ruhsatlı etken madde ve aşırı kimyasal israfını önleme uyarısı.

                        4. 💧 AKILLI SU VE SULAMA TAKVİMİ (BATMAN İKLİMİNE UYGUN):
                           - Batman'ın anlık hava şartları ({hava_bilgisi}) göz önüne alındığında bu bitki için optimum sulama saati ve periyodu.
                           - Vahşi sulama / aşırı su kaynaklı riskler (kök boğulması, tuzlanma) ve su tasarrufu tavsiyesi.
                        """

                        payload = {
                            "contents": [{
                                "parts": [
                                    {"text": prompt_text},
                                    {
                                        "inline_data": {
                                            "mime_type": "image/jpeg",
                                            "data": img_b64
                                        }
                                    }
                                ]
                            }]
                        }

                        # Anahtar üzerindeki olası tırnak ve gizli boşlukları temizleyelim
                        clean_key = str(api_key).strip().replace('"', '').replace("'", '').replace('\n', '').replace('\r', '')
                        
                        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={clean_key}"
                        headers = {"Content-Type": "application/json"}

                        res = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=35)
                        result = res.json()

                        if "candidates" in result:
                            rapor = result["candidates"][0]["content"]["parts"][0]["text"]
                            st.success("✅ Teşhis ve Alana Özel Reçete Üretildi!")
                            st.markdown(rapor)
                        else:
                            st.error(f"API Yanıt Hatası: {result}")
                            
                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")
    else:
        st.info("👈 Analiz başlatmak için soldan bir fotoğraf yükleyin.")
