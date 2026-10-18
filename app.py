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
st.subheader("Yapay Zekâ & Canlı Hava Durumu Destekli Tarımsal ve Kentsel Karar Destek Sistemi")
st.markdown("""
Batman ve çevre havzalara özel; anlık hava durumu ve yapay zekâ analizleriyle hastalık ve zararlı tespiti yapar.
Saksıdan refüje, küçük bahçelerden yüzlerce dekarlık tarlalara kadar su israfını, taban suyu kaybını ve gereksiz kimyasal kullanımını önleyecek reçeteler sunar.
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
    
    # Secrets boşsa manuel girme imkanı sunar
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
            st.warning("⚠️ Aşırı buharlaşma riski! Gündüz saatlerinde sulama yapmayınız.")

st.markdown("---")
col1, col2 = st.columns([1, 1])

# --- GİRİŞ PANELİ ---
with col1:
    st.markdown("### 📸 Saha / Bitki Bilgileri")
    uploaded_file = st.file_uploader("Bitki / Yaprak Fotoğrafı Yükleyin:", type=["jpg", "jpeg", "png"])
    
    alan_tipi = st.selectbox(
        "Yetiştirme Alanı / Ölçek:",
        ["Saksı / Balkon / Hobi Bahçesi", "Refüj / Park / Kentsel Yeşil Alan", "Açık Tarla / Dekar Ölçekli Üretim"]
    )
    
    dekar_sayisi = 1
    if alan_tipi == "Açık Tarla / Dekar Ölçekli Üretim":
        dekar_sayisi = st.number_input("Tarla Büyüklüğü (Dekar / Dönüm):", min_value=1, max_value=5000, value=10, step=5)
        
    urun_tipi = st.selectbox(
        "Bitki / Ürün Türü:",
        ["Limon / Narenciye", "Süs Bitkisi / Çalı / Ağaççık", "Dane Mısır (2. Ürün)", "Pamuk", "Buğday / Arpa", "Domates / Biber / Sebze", "Diğer"]
    )
    
    sulama_tipi = st.radio(
        "Uygulanan Sulama Yöntemi:",
        ["Vahşi / Salma / Karık Sulama", "Damlama Sulama", "Yağmurlama Sulama", "Elle / Hortumla Sulama"]
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Görsel", use_container_width=True)

# --- ANALİZ VE RAPOR PANELİ ---
with col2:
    st.markdown("### 🩺 Teşhis & Bilimsel Reçete")
    if uploaded_file is not None:
        if st.button("🔍 Durumu Teşhis Et ve Su Raporunu Çıkar", type="primary"):
            if not api_key:
                st.error("⚠️ Lütfen Streamlit Secrets alanına veya sol menüye API anahtarınızı girin.")
            else:
                with st.spinner("Yapay zekâ ve iklim verileri analiz ediliyor..."):
                    try:
                        # Görseli base64 formatına dönüştür
                        buffered = io.BytesIO()
                        image.save(buffered, format="JPEG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        
                        hava_bilgisi = f"{hava_verisi['sicaklik']}°C, Nem: %{hava_verisi['nem']}, Rüzgar: {hava_verisi['ruzgar']} km/s" if hava_verisi else "Normal Saha Şartları"
                        olcek_bilgisi = f"{alan_tipi} (Büyüklük: {dekar_sayisi} Dekar)" if "Dekar" in alan_tipi else alan_tipi
                        
                        prompt_text = f"""
                        Sen Batman yöresinde ve GAP havzasında uzmanlaşmış kıdemli bir Ziraat Mühendisi ve Bitki Patoloğusun.
                        Aşağıdaki parametreleri ve yüklenen fotoğrafı dikkate alarak detaylı, uygulanabilir ve profesyonel bir rapor hazırla:

                        - Lokasyon: {secilen_ilce} / Batman
                        - Anlık Hava Durumu: {hava_bilgisi}
                        - Yetiştirme Alanı & Ölçek: {olcek_bilgisi}
                        - Bitki / Ürün: {urun_tipi}
                        - Mevcut Sulama: {sulama_tipi}

                        Lütfen raporu tam olarak şu 4 ana başlık altında ver:
                        1. 🔍 GÖRSEL TEŞHİS VE ZARARLI/HASTALIK TANISI:
                           (Görseldeki belirtileri, zararlıyı [unlu bit, akar, mantari leke vb.] ve şiddetini açıkla.)
                        2. ⚠️ KÖK NEDEN VE ÇEVRESEL/SULAMA ETKİSİ:
                           (Uygulanan sulama yönteminin, ortam neminin ve Batman'ın anlık hava şartlarının bu hastalığa/zararlıya etkisi.)
                        3. 🌿 REÇETE & MÜCADELE YÖNTEMLERİ (KİMYASAL VE BİYOLOJİK/KÜLTÜREL):
                           (Seçilen alana [{olcek_bilgisi}] uygun pratik dozlar. Saksı ise ev yapımı arap sabunlu/alkollü karışım veya butik çözüm; Refüj/Park ise kentsel peyzaj çözümü; Dekar/Tarla ise doğru etken maddeli hedefli uygulama ve aşırı pestisit israfını önleme.)
                        4. 💧 AKILLI SU VE SULAMA REÇETESİ:
                           (Batman iklimine ve seçilen ölçeğe göre haftalık sulama periyodu, buharlaşma kayıplarını önleyecek sulama saati ve su tasarrufu tavsiyesi.)
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

                        headers = {"Content-Type": "application/json"}
                        if api_key.startswith("AQ."):
                            headers["Authorization"] = f"Bearer {api_key}"
                            endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
                        else:
                            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

                        res = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=35)
                        result = res.json()

                        if "candidates" in result:
                            rapor = result["candidates"][0]["content"]["parts"][0]["text"]
                            st.success("✅ Teşhis ve Reçete Başarıyla Üretildi!")
                            st.markdown(rapor)
                        else:
                            st.error(f"API Yanıt Hatası: {result}")
                            
                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")
    else:
        st.info("👈 Analiz başlatmak için soldan bir fotoğraf yükleyin.")
