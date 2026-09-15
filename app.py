import streamlit as st
import yfinance as yf
import pandas as pd
import psycopg2
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="BIST Sınırsız Yatırım Terminali", page_icon="📈", layout="wide")

st.title("🚀 BIST Sınırsız Karar Destek ve Portföy Terminali")
st.markdown("Canlı veri akışı, portföy yönetimi, akıllı alarmlar ve bulut veritabanı entegrasyonu.")

# Veritabanı Bağlantı Fonksiyonu (Supabase Bulut Uyumlu)
def baglanti_kur():
    try:
        db_url = st.secrets.get("DATABASE_URL")
        if not db_url:
            st.error("⚠️ Streamlit Cloud Secrets içinde 'DATABASE_URL' bulunamadı!")
            return None
        return psycopg2.connect(db_url)
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")
        return None
# Popüler Hisseler
POPULER_HISSELER = [
    "THYAO.IS", "GARAN.IS", "EREGL.IS", "ASELS.IS", "KCHOL.IS", 
    "AKBNK.IS", "BIMAS.IS", "TUPRS.IS", "SASA.IS", "FROTO.IS", 
    "PGSUS.IS", "MGROS.IS", "KRDMD.IS", "SAHOL.IS", "SISE.IS",
    "ISCTR.IS", "YKBNK.IS", "PETKM.IS", "TOASO.IS", "TAVHL.IS"
]

# Veritabanı Tablolarını Oluşturma
def veritabani_tablolari_kur():
    conn = baglanti_kur()
    if conn:
        try:
            cursor = conn.cursor()
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
                CREATE TABLE IF NOT EXISTS portfoy_islemleri (
                    id SERIAL PRIMARY KEY,
                    hisse VARCHAR(20),
                    adet FLOAT,
                    maliyet FLOAT
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("Tablo kurulum hatası:", e)

veritabani_tablolari_kur()

# Sekmeler Oluşturma
sekme1, sekme2, sekme3 = st.tabs(["📈 Detaylı Analiz & Alarm", "💼 Portföy Takibi", "🔍 Hızlı Piyasa Tarama"])

@st.cache_data(ttl=300)
def veri_getir(hisse, per):
    df = yf.download(hisse, period=per, interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def teknik_hesapla(df):
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# ================= SEKME 1: DETAYLI ANALİZ & ALARM =================
with sekme1:
    st.subheader("🎯 Hisse Teknik Analiz ve Alarm Merkezi")
    
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        secim_turu = st.radio("Hisse Seçim Yöntemi", ["Popüler Listeden Seç", "Özel / Manuel Kod Yaz"])
        
        if secim_turu == "Popüler Listeden Seç":
            secilen_hisse = st.selectbox("Hisse Senedi", POPULER_HISSELER)
        else:
            secilen_hisse = st.text_input("Hisse Kodunu Yazın (Örn: THYAO.IS, FROTO.IS)", value="THYAO.IS").upper().strip()

        periyot = st.selectbox("Periyot", ["3mo", "6mo", "1y"], index=1)
        hedef_fiyat = st.number_input("Alarm Hedef Fiyatı (TL)", value=0.0)

    with st.spinner(f"{secilen_hisse} yükleniyor..."):
        df_secilen = veri_getir(secilen_hisse, periyot)
        
    if not df_secilen.empty and len(df_secilen) > 14:
        df_secilen = teknik_hesapla(df_secilen)
        son_fiyat = float(df_secilen['Close'].iloc[-1])
        onceki_fiyat = float(df_secilen['Close'].iloc[-2])
        fark_yuzde = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
        son_rsi = float(df_secilen['RSI'].iloc[-1])

        if son_rsi < 30:
            sinyal = "GÜÇLÜ AL (Aşırı Satım)"
        elif son_rsi > 70:
            sinyal = "GÜÇLÜ SAT (Aşırı Alım)"
        else:
            sinyal = "NÖTR (Bekle)"

        if hedef_fiyat > 0 and son_fiyat <= hedef_fiyat:
            st.warning(f"🚨 ALARM: {secilen_hisse} fiyatı ({son_fiyat:.2f} TL) hedef fiyatınızın altında/üzerinde!")

        m1, m2, m3 = st.columns(3)
        m1.metric("Güncel Fiyat", f"{son_fiyat:.2f} TL", f"{fark_yuzde:.2f}%")
        m2.metric("14 Günlük RSI", f"{son_rsi:.2f}")
        
        if "AL" in sinyal:
            m3.error(f"SİNYAL: 🟢 {sinyal}")
        elif "SAT" in sinyal:
            m3.success(f"SİNYAL: 🔴 {sinyal}")
        else:
            m3.info(f"SİNYAL: ⚪ {sinyal}")

        st.line_chart(df_secilen[['Close', 'SMA_20']])
    else:
        st.error("Girilen hisse kodu bulunamadı veya veri çekilemedi. Kodun sonuna '.IS' eklediğinizden emin olun.")

# ================= SEKME 2: PORTFÖY TAKİBİ =================
with sekme2:
    st.subheader("💼 Portföy ve Varlık Yönetimi")
    
   with st.form("portfoy_form"):
            col_p1, col_p2, col_p3 = st.columns(3)
            p_hisse_ham = col_p1.text_input("Hisse Kodunu Yazın (Örn: EREGL veya EREGL.IS)", value="EREGL.IS").upper().strip()
            
            if p_hisse_ham and "." not in p_hisse_ham:
                p_hisse = p_hisse_ham + ".IS"
            else:
                p_hisse = p_hisse_ham

            p_adet = col_p2.number_input("Adet / Lot Miktarı", min_value=1.0, value=100.0)
            p_maliyet = col_p3.number_input("Alış Maliyeti (TL)", min_value=0.0, value=10.0)
            
            kayit_buton = st.form_submit_button("Portföye Ekle / Kaydet")
            
            if kayit_buton and p_hisse:
                conn = baglanti_kur()
                if conn:
                    try:
                        cur = conn.cursor()
                        # Önce tablonun garanti olması için tablo oluşturma komutu
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS portfoy_islemleri (
                                id SERIAL PRIMARY KEY,
                                hisse VARCHAR(20),
                                adet FLOAT,
                                maliyet FLOAT
                            )
                        """)
                        cur.execute("INSERT INTO portfoy_islemleri (hisse, adet, maliyet) VALUES (%s, %s, %s)", (p_hisse, p_adet, p_maliyet))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"✅ {p_hisse} portföye başarıyla eklendi!")
                    except Exception as ex:
                        st.error(f"❌ Veritabanına kayıt yazılırken hata oluştu: {ex}")
                else:
                    st.error("❌ Veritabanı bağlantısı kurulamadığı için kayıt yapılamadı.")

    st.markdown("---")
    st.markdown("### 📊 Mevcut Portföy Durumunuz")
    conn = baglanti_kur()
    if conn:
        try:
            df_portfoy = pd.read_sql("SELECT id, hisse, adet, maliyet FROM portfoy_islemleri", conn)
            conn.close()

            if not df_portfoy.empty:
                toplam_deger = 0
                toplam_maliyet = 0
                portfoy_ozet = []

                for index, row in df_portfoy.iterrows():
                    h = row['hisse']
                    adet = row['adet']
                    maliyet = row['maliyet']
                    
                    df_h = veri_getir(h, "1mo")
                    guncel_fiyat = float(df_h['Close'].iloc[-1]) if not df_h.empty else maliyet

                    toplam_tutar = adet * guncel_fiyat
                    maliyet_tutar = adet * maliyet
                    kar_zarar = toplam_tutar - maliyet_tutar
                    kar_zarar_yuzde = ((guncel_fiyat - maliyet) / maliyet) * 100 if maliyet > 0 else 0

                    toplam_deger += toplam_tutar
                    toplam_maliyet += maliyet_tutar

                    portfoy_ozet.append({
                        "ID": row['id'],
                        "Hisse": h,
                        "Adet": adet,
                        "Maliyet (TL)": maliyet,
                        "Güncel Fiyat (TL)": round(guncel_fiyat, 2),
                        "Toplam Değer (TL)": round(toplam_tutar, 2),
                        "Kâr/Zarar (TL)": round(kar_zarar, 2),
                        "Kâr/Zarar (%)": round(kar_zarar_yuzde, 2)
                    })

                df_ozet_tablo = pd.DataFrame(portfoy_ozet)
                st.dataframe(df_ozet_tablo, use_container_width=True)

                genel_kar = toplam_deger - toplam_maliyet
                col_d1, col_d2 = st.columns(2)
                col_d1.metric("Toplam Portföy Değeri", f"{toplam_deger:,.2f} TL")
                col_d2.metric("Toplam Kâr / Zarar", f"{genel_kar:,.2f} TL", delta_color="normal" if genel_kar >=0 else "inverse")
            else:
                st.info("Portföyünüzde henüz kayıtlı hisse bulunmuyor.")
        except Exception as e:
            st.info("Portföy verileri yükleniyor...")

# ================= SEKME 3: HIZLI PİYASA TARAMA =================
with sekme3:
    st.subheader("🔍 Özel Hisse Tarama ve Kontrol Paneli")
    toplu_liste_input = st.text_area("Hisse Kodlarını Girin (Virgülle Ayırın)", value="THYAO.IS, GARAN.IS, EREGL.IS, ASELS.IS, KCHOL.IS")

    if st.button("🚀 Listelenen Hisseleri Analiz Et"):
        hisseler = [h.strip().upper() for h in toplu_liste_input.split(",") if h.strip()]
        tarama_sonuclari = []
        
        with st.spinner("Hisseler analiz ediliyor..."):
            for h in hisseler:
                df_t = veri_getir(h, "3mo")
                if not df_t.empty and len(df_t) > 14:
                    df_t = teknik_hesapla(df_t)
                    fiyat = float(df_t['Close'].iloc[-1])
                    rsi = float(df_t['RSI'].iloc[-1])
                    
                    s = "🟢 GÜÇLÜ AL" if rsi < 30 else ("🔴 GÜÇLÜ SAT" if rsi > 70 else "⚪ NÖTR")

                    tarama_sonuclari.append({
                        "Hisse": h,
                        "Fiyat (TL)": round(fiyat, 2),
                        "RSI (14)": round(rsi, 2),
                        "Sinyal": s
                    })

        if tarama_sonuclari:
            st.dataframe(pd.DataFrame(tarama_sonuclari), use_container_width=True)
        else:
            st.warning("Geçerli bir hisse verisi bulunamadı.")