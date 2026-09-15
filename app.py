import streamlit as st
import yfinance as yf
import pandas as pd
import psycopg2
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="BIST Akıllı Analiz Paneli", page_icon="📈", layout="wide")

st.title("🚀 BIST Akıllı Karar Destek ve Alarm Sistemi")
st.markdown("Anlık takip, teknik indikatörler, akıllı uyarılar ve PostgreSQL veritabanı entegrasyonu.")

# PostgreSQL Bağlantı Bilgileri
DB_CONFIG = {
    "dbname": "bist_db",
    "user": "postgres",
    "password": "esma3762",  # Şifreni buraya yazmayı unutma
    "host": "localhost",
    "port": "5432"
}

def veritabani_kaydet(hisse, fiyat, rsi, sinyal):
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analiz_gecmisi (
                id SERIAL PRIMARY KEY,
                hisse VARCHAR(20),
                tarih TIMESTAMP,
                fiyat FLOAT,
                rsi FLOAT,
                sinyal VARCHAR(50)
            )
        """)
        cursor.execute("""
            INSERT INTO analiz_gecmisi (hisse, tarih, fiyat, rsi, sinyal)
            VALUES (%s, %s, %s, %s, %s)
        """, (hisse, datetime.now(), fiyat, rsi, sinyal))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print("Veritabanı kayıt hatası:", e)
        return False

def gecmis_verileri_getir():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        df_gecmis = pd.read_sql("SELECT hisse, tarih, fiyat, rsi, sinyal FROM analiz_gecmisi ORDER BY tarih DESC LIMIT 10", connection)
        connection.close()
        return df_gecmis
    except:
        return pd.DataFrame()

# Yan Menü (Kontrol Paneli ve Alarmlar)
st.sidebar.header("⚙️ Kontrol Paneli")
hisse_secimi = st.sidebar.selectbox(
    "Hisse Senedi Seçin", 
    ["THYAO.IS", "GARAN.IS", "EREGL.IS", "ASELS.IS", "KCHOL.IS", "AKBNK.IS"]
)
periyot = st.sidebar.selectbox("Veri Periyodu", ["3mo", "6mo", "1y"], index=1)

st.sidebar.markdown("---")
st.sidebar.header("🔔 Fiyat Alarm Kriterleri")
hedef_fiyat = st.sidebar.number_input("Uyarı Verilecek Hedef Fiyat (TL)", value=0.0)

@st.cache_data
def veri_getir(hisse, per):
    df = yf.download(hisse, period=per, interval="1d")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# Verileri Yükle
with st.spinner(f"{hisse_secimi} verileri yükleniyor..."):
    df = veri_getir(hisse_secimi, periyot)

# İndikatör Hesaplamaları
df['SMA_20'] = df['Close'].rolling(window=20).mean()
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# Son Değerler
son_fiyat = float(df['Close'].iloc[-1])
onceki_fiyat = float(df['Close'].iloc[-2])
fark = son_fiyat - onceki_fiyat
fark_yuzde = (fark / onceki_fiyat) * 100
son_rsi = float(df['RSI'].iloc[-1])

# Sinyal Belirleme
if son_rsi < 30:
    sinyal_metni = "GÜÇLÜ AL (Aşırı Satım)"
elif son_rsi > 70:
    sinyal_metni = "GÜÇLÜ SAT (Aşırı Alım)"
else:
    sinyal_metni = "NÖTR (Bekle)"

# Alarm Kontrolü
if hedef_fiyat > 0:
    if son_fiyat <= hedef_fiyat:
        st.warning(f"🚨 ALARM: {hisse_secimi} fiyatı ({son_fiyat:.2f} TL), belirlediğin {hedef_fiyat} TL hedef fiyatın altına düştü veya ulaştı!")

# Üst Özet Kartları
col1, col2, col3 = st.columns(3)
col1.metric("Güncel Fiyat", f"{son_fiyat:.2f} TL", f"{fark_yuzde:.2f}%")
col2.metric("14 Günlük RSI", f"{son_rsi:.2f}")

if "AL" in sinyal_metni:
    col3.error(f"SİNYAL: 🟢 {sinyal_metni}")
elif "SAT" in sinyal_metni:
    col3.success(f"SİNYAL: 🔴 {sinyal_metni}")
else:
    col3.info(f"SİNYAL: ⚪ {sinyal_metni}")

# Kayıt Butonu
if st.button("💾 Bu Analizi Veritabanına Kaydet"):
    if veritabani_kaydet(hisse_secimi, son_fiyat, son_rsi, sinyal_metni):
        st.success("Analiz başarıyla PostgreSQL veritabanına kaydedildi!")
    else:
        st.error("Kayıt sırasında hata oluştu. Şifrenizi kontrol edin.")

# Grafik ve Tablolar
st.subheader(f"📊 {hisse_secimi} Fiyat ve Hareketli Ortalama Grafiği")
st.line_chart(df[['Close', 'SMA_20']])

st.subheader("🗄️ Veritabanındaki Kayıtlı Geçmiş Analizlerin")
df_gecmis = gecmis_verileri_getir()
if not df_gecmis.empty:
    st.dataframe(df_gecmis, use_container_width=True)
else:
    st.info("Henüz veritabanına kaydedilmiş bir analiz bulunmuyor. Yukarıdaki butona basarak ilk kaydı oluşturabilirsin.")