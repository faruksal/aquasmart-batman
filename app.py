import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="AquaSmart Batman", page_icon="🌱", layout="centered")

st.title("🌱 AquaSmart Batman")
st.subheader("Akıllı Sulama, Bitki Kliniği & Su Tasarrufu Asistanı")
st.caption("Batman Ovası ve Kentsel Yeşil Alanlar İçin Hassas Su Yönetimi")

# 1. API Anahtarı Girişi
api_key = st.sidebar.text_input("Google AI Studio API Key:", type="password")

# 2. Saha Bilgileri
st.write("### 1. Saha Bilgilerini Girin")
col1, col2 = st.columns(2)
with col1:
    alan_tipi = st.selectbox("Alan Türü:", ["Tarla (Mısır, Pamuk, Buğday vb.)", "Belediye Parkı / Çim Alan", "Refüj / Ağaçlandırma"])
    sicaklik = st.number_input("Hava Sıcaklığı (°C):", value=35, min_value=10, max_value=50)
with col2:
    konum = st.text_input("Konum / İlçe:", value="Batman Merkez")
    alan_buyuklugu = st.number_input("Tahmini Alan Büyüklüğü (Dönüm / m²):", value=10, min_value=1)

# 3. Fotoğraf Yükleme
st.write("### 2. Bitki / Toprak Fotoğrafı")
resim_kaynagi = st.radio("Fotoğrafı nasıl yüklemek istersiniz?", ["Kamerayı Aç (Fotoğraf Çek)", "Galeriden Yükle"], horizontal=True)

resim_dosyasi = None
if resim_kaynagi == "Kamerayı Aç (Fotoğraf Çek)":
    resim_dosyasi = st.camera_input("Bitki yaprağını veya kök boğazını çekin")
else:
    resim_dosyasi = st.file_uploader("Fotoğraf seçin...", type=["jpg", "jpeg", "png"])

if resim_dosyasi is not None:
    image = Image.open(resim_dosyasi)
    st.image(image, caption="Analiz Edilecek Görsel", use_container_width=True)

# 4. Teşhis ve Raporlama
api_key = "AIzaSyAiJKfTrkUrG1sE5HN1Ds53WfbKyqqYybE"

if st.button("🔍 Durumu Teşhis Et ve Su Raporunu Çıkar", type="primary"):
    if resim_dosyasi is None:
        st.warning("Lütfen analiz için bir fotoğraf çekin veya yükleyin.")
    else:
        with st.spinner("Yapay zekâ bitki sağlığını, hava koşullarını ve su ihtiyacını analiz ediyor..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-3.8-flash')
                prompt = f"""
                Sen Batman koşullarında uzmanlaşmış bir Ziraat Mühendisi ve Su Muhafızısın.
                SAHA VERİLERİ:
                - Konum: {konum}
                - Alan Tipi: {alan_tipi}
                - Sıcaklık: {sicaklik} °C
                - Alan Büyüklüğü: {alan_buyuklugu}

                GÖRSELDEKİ BELİRTİLERİ İNCELE VE ŞU 3 BAŞLIKTA YANIT VER:
                
                🌱 1. BİTKİ VE TOPRAK TEŞHİSİ:
                (Hastalık, zararlı, kloroz/besin eksikliği, ısı stresi veya aşırı sulama kaynaklı kök çürümesi var mı? Sebebini açıkla.)

                🛑 2. SULAMA REÇETESİ:
                (Şu an sulama yapılmalı mı? Gece 22:00-05:00 arasına mı ertelenmeli? Fıskiye/damlama süresi ne olmalı?)

                💧 3. BEREKET VE GELECEK KARNESİ:
                (Gündüz salma/vahşi sulama yapılmayarak bu alanda kurtarılan tahmini su miktarını ton cinsinden ve kurtarılan elektrik/mazot parasını hesapla. 'Batman Ovası'nın suyunu çocuklarına miras bıraktın' mesajını ver.)
                """

                response = model.generate_content([prompt, image])
                st.success("Analiz Tamamlandı!")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Hata oluştu: {e}")