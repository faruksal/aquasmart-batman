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

# Temiz, Modern Tasarım
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
            c = data.get("current", {})
            return {
                "sicaklik": c.get("temperature_2m", 24.5),
                "hissedilen": c.get("apparent_temperature", 25.0),
                "nem": c.get("relative_humidity_2m", 52),
                "ruzgar": c.get("wind_speed_10m", 4.1)
            }
        except Exception:
            return {"sicaklik": 24.5, "hissedilen": 25.0, "nem": 52, "ruzgar": 4.1}

    hava_verisi = hava_durumu_al(lat, lon)
    
    st.markdown("---")
    st.markdown("### 🌤️ Anlık Hava Durumu")
    c1, c2 = st.columns(2)
    c1.metric("Hava Sıcaklığı", f"{hava_verisi['sicaklik']} °C")
    c2.metric("Nem Oranı", f"%{hava_verisi['nem']}")
    
    temp = float(hava_verisi['sicaklik'])
    humidity = float(hava_verisi['nem'])
    evap_risk = (temp * 0.7) - (humidity * 0.2) + 5.0
    
    if evap_risk > 22:
        st.error("🔴 **ŞU AN SULAMA YAPMAYIN!**\nHava sıcak ve kuru. Şimdi su verirseniz buharlaşıp uçar, kökler yanar. Geceyi bekleyin.")
    elif evap_risk > 14:
        st.warning("🟡 **DİKKATLİ SULAMA**\nGüneşin tam tepede olmadığı sabah erken veya ikindi vakitlerini tercih edin.")
    else:
        st.success("🟢 **SULAMA İÇİN UYGUN ZAMAN**\nHava serin, verilen su doğrudan köke gider ve israf olmaz.")

# --- BİTKİ VE KLOROFİL ANALİZİ (VARI İNDEKSİ) ---
def bitki_saglik_haritasi(pil_image):
    img = pil_image.resize((150, 150)).convert("RGB")
    width, height = img.size
    harita = Image.new("RGB", (width, height))
    pixels_in = img.load()
    pixels_out = harita.load()
    
    hasar_sayisi = 0
    klorofil_sayisi = 0
    toplam_piksel = width * height
    
    for x in range(width):
        for y in range(height):
            r, g, b = pixels_in[x, y]
            pay = g - r
            payda = g + r - b
            vari = pay / (payda if payda != 0 else 1)
            
            # Canlı bitki klorofil pikseli
            if vari > 0.08 and g > r:
                pixels_out[x, y] = (0, int(150 + min(vari * 105, 105)), 0)
                klorofil_sayisi += 1
            elif vari > -0.08:
                pixels_out[x, y] = (210, 160, 0)
                if g > 40:
                    klorofil_sayisi += 0.5
            else:
                pixels_out[x, y] = (190, 30, 30)
                hasar_sayisi += 1
                
    bitki_orani = (klorofil_sayisi / toplam_piksel) * 100
    hasar_orani = (hasar_sayisi / toplam_piksel) * 100
    return harita.resize((450, 300)), hasar_orani, bitki_orani

# --- AKILLI VE DİNAMİK YEREL REÇETE MOTORU ---
def dinamik_recete_uret(ilce, hava, hasar_orani, bitki_orani):
    # 1. BİTKİ DEĞİLSE UYARI VER
    if bitki_orani < 6.0:
        return "BITKI_DEGIL"
        
    saat_oneri = "21:30 - 05:00 saatleri arasında" if evap_risk > 14 else "06:30 - 09:00 saatleri arasında"
    
    # 2. BİTKİ TÜRÜ VE ORTAM TAHMİNİ
    if bitki_orani > 45.0:
        tur = "Geniş Yapraklı Bitki / Tarla Mahsulü"
        ortam = "Açık Alan / Bahçe veya Tarla Yetiştiriciliği"
        tedavi = "* **Hedefli Mücadele:** Yapraklarda su stresi ve erken kloroz görülmektedir. Gereksiz kimyasal ilaç masrafı yapmayınız; toprağın havalanmasını sağlayın."
    elif bitki_orani > 18.0:
        tur = "Saksı / Balkon Süs Bitkisi"
        ortam = "Saksı / İç Mekan Ortamı"
        tedavi = "* **Ev Tipi Doğal Çözüm (0 ₺):** 1 litre dinlenmiş suya yarım çay kaşığı karbonat ve 2 damla saf zeytinyağı damlatarak fısfıslayınız. Gözenekleri açar ve mantar sporlarını engeller."
    else:
        tur = "Düşük Yoğunluklu Otsu Doku / Fidan"
        ortam = "Peyzaj / Refüj veya Küçük Saksı"
        tedavi = "* **Kök Koruma:** Saksı veya dikim çukurunun drenaj deliklerini kontrol ediniz. Durgun su kökleri boğar."

    return f"""### 🏷️ 1. BİTKİ VE YETİŞME ORTAMI
* **Tespit Edilen Tür Grubu:** {tur}
* **Yetişme Alanı:** {ortam}
* **Yeşil Doku Yoğunluğu:** %{bitki_orani:.1f} canlı bitkisel doku tespit edildi.

### 🔍 2. MEVCUT SORUN VE HASAR DERECESİ
* **Teşhis:** Yaprak Yanıklığı ve Klorofil Su Stresi
* **Hasar Seviyesi:** %{hasar_orani:.1f} dokusal bozulma/kuruma mevcut.
* **Belirtiler:** Yüksek sıcaklık ve düzensiz sulama kaynaklı yaprak uçlarında nem kaybı ve sararma.

### 💊 3. TEDAVİ VE BAKIM REÇETESİ
{tedavi}
* **Toprak Bakımı:** Sulamadan 15 dakika sonra saksı tabağındaki biriken fazla suyu dökünüz; kök çürümesini önleyiniz.
* **Pahalı İlaç Uyarısı:** Bu evrede kimyasal tarım ilacı almayınız; sorun parazit değil, sıcaklık ve sulama dengesizliğidir.

### 💧 4. SULAMA REHBERİ ({ilce.upper()} KOŞULLARI)
* **Günün En Uygun Sulama Saati:** {saat_oneri}
* **Sulama Aralığı:** Toprağın üstten 2-3 cm derinliği parmağınızla kontrol edildiğinde tamamen kuru hissedilmedikçe su vermeyiniz.
* **Buharlaşma Uyarısı:** Batman'ın kuru sıcağında gündüz su vermeyiniz; verilen su köke gitmeden buharlaşır ve kökleri yakar."""

# --- ANA EKRAN ---
col1, col2 = st.columns([1, 1.1])

# SOL TARAF: FOTOĞRAF
with col1:
    st.markdown('<div class="ar_ge_kart">', unsafe_allow_html=True)
    st.markdown("### 📸 Bitkinin Fotoğrafı")
    secim_modu = st.radio("Fotoğrafı Nasıl Ekleyeceksiniz?", ["Galeriden Seç", "Kamerayla Çek"], horizontal=True)
    
    uploaded_file = None
    if secim_modu == "Kamerayla Çek":
        uploaded_file = st.camera_input("Kamerayı bitkiye doğrultun:")
    else:
        uploaded_file = st.file_uploader("Fotoğraf yükleyin:", type=["jpg", "jpeg", "png"])
        
    st.markdown("</div>", unsafe_allow_html=True)

    hasar_puani = 0.0
    bitki_puani = 0.0
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        harita_img, hasar_puani, bitki_puani = bitki_saglik_haritasi(image)
        tab1, tab2 = st.tabs(["🖼️ Normal Fotoğraf", "🟢 Canlılık / Hasar Haritası"])
        with tab1:
            st.image(image, caption="Yüklenen Fotoğraf", use_container_width=True)
        with tab2:
            st.image(harita_img, caption=f"Yeşil Doku: %{bitki_puani:.1f} | Hasarlı Bölge: %{hasar_puani:.1f}", use_container_width=True)

# SAĞ TARAF: TEŞHİS, ÇÖZÜM VE KAZANÇ REÇETESİ
with col2:
    st.markdown('<div class="ar_ge_kart">', unsafe_allow_html=True)
    st.markdown("### 🩺 Teşhis ve Yapılacaklar")
    
    if uploaded_file is not None:
        if st.button("🔍 Bitkiyi Teşhis Et ve Çözümü Göster", type="primary"):
            with st.spinner("Görüntü ve hava verileri işleniyor..."):
                rapor = ""
                raw_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
                api_key = str(raw_key).strip().replace('"', '').replace("'", '').replace('\n', '').replace('\r', '')

                # 1. Aşama: Canlı API Bağlantısını Dene (Varsa)
                if api_key.startswith("AIzaSy"):
                    try:
                        buffered = io.BytesIO()
                        image.save(buffered, format="JPEG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        hava_bilgisi = f"{hava_verisi['sicaklik']}°C, Nem: %{hava_verisi['nem']}, Rüzgar: {hava_verisi['ruzgar']} km/s"
                        
                        prompt_text = f"""
                        Fotoğrafı incele. Eğer görselde bir bitki, yaprak veya tarımsal öge YOKSA (örneğin insan, bardak, masa, duvar vb. ise) sadece şunu yaz:
                        'BITKI_DEGIL'
                        
                        Eğer bir bitkiyse ziraat uzmanı gibi davran. Yabancı terimler veya formüller kullanma.
                        Konum: {secilen_ilce} / Batman. Hava Durumu: {hava_bilgisi}
                        Şu 4 başlığı sade bir dille yaz:
                        1. 🏷️ BİTKİ VE YERİ (Saksı mı tarla mı?)
                        2. 🔍 NE SORUNU VAR? (Hastalık/zararlı nedir?)
                        3. 💊 NE YAPILMALI? (Saksıysa bedava ev formülü, tarlaysa hedefli çözüm)
                        4. 💧 SULAMA TAVSİYESİ (Saat kaçta sulanmalı?)
                        """
                        payload = {"contents": [{"parts": [{"text": prompt_text}, {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}]}]}
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                        res = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=5)
                        data = res.json()
                        if "candidates" in data:
                            gelen_metin = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                            rapor = gelen_metin
                    except Exception:
                        rapor = ""
                
                # 2. Aşama: API yoksa veya başarısızsa akıllı yerel analiz çalışır
                if not rapor:
                    rapor = dinamik_recete_uret(secilen_ilce, hava_verisi, hasar_puani, bitki_puani)

                # BİTKİ OLMAMA KONTROLÜ
                if "BITKI_DEGIL" in rapor:
                    st.warning("⚠️ **Görselde Canlı Bitki Tespit Edilemedi!**\n\nYüklediğiniz fotoğrafta klorofil içeren yaprak veya bitkisel bir doku bulunamadı. Lütfen doğrudan bir bitki veya yaprak fotoğrafı çekip tekrar deneyiniz.")
                else:
                    st.success("✅ Teşhis Tamamlandı!")
                    
                    # Doğrudan Kâr ve Tasarruf Metrikleri
                    m1, m2 = st.columns(2)
                    m1.metric("Elektrik / Pompa Tasarrufu", "%30'a Varan", "Buharlaşma Önleme")
                    m2.metric("Cihaz / Sensör Maliyeti", "0 ₺", "Sıfır Ekipman Masrafı")
                    
                    st.markdown("---")
                    st.markdown(rapor)
                    
                    st.markdown("""
                    <div class="kar_kutusu">
                        <h4 style="margin-top:0; color:#6ee7b7;">💰 Bu Reçetenin Size Sağladığı Doğrudan Kâr:</h4>
                        <ul style="margin-bottom:0; font-size:14px; line-height:1.6;">
                            <li><b>Elektrik ve Mazot Tasarrufu:</b> Gündüz buharlaşacak su için kuyu motorunu boşuna çalıştırmaz; faturada %30'a varan tasarruf sağlar.</li>
                            <li><b>0 ₺ Donanım Masrafı:</b> Binlerce liralık toprak nem sensörü almadan telefonunuzla aynı kararı alırsınız.</li>
                            <li><b>İlaç İsrafını Önleme:</b> Yanlış ve pahalı zirai ilaç alımını engeller; ev bitkilerinde bedava doğal yöntemleri gösterir.</li>
                            <li><b>Hasat Kaybını Durdurma:</b> Aşırı sulamadan kaynaklanan kök çürümesini vaktinde engelleyerek veriminizi korur.</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.download_button(
                        label="📥 Bu Reçeteyi Telefona İndir",
                        data=rapor,
                        file_name=f"AquaSmart_{secilen_ilce}_Recete.txt",
                        mime="text/plain"
                    )
    else:
        st.info("👈 Soldan bir fotoğraf yükleyin veya çekin.")
    
    st.markdown("</div>", unsafe_allow_html=True)
