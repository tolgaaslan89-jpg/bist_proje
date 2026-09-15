import yfinance as yf
import pandas as pd

# BIST hisse kodu (Yahoo Finance formatında sonuna .IS eklenir)
hisse_kodu = "THYAO.IS"
print(f"{hisse_kodu} için veriler indiriliyor...")

# Son 3 aylık günlük verileri çekelim
df = yf.download(hisse_kodu, period="3mo", interval="1d")

# Sütun isimlerini düzenleyelim
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

print("\nVeri başarıyla indirildi. Son 5 günün kapanış fiyatları:")
print(df['Close'].tail())

# Basit İndikatör Hesaplama: 20 günlük Hareketli Ortalama (SMA)
df['SMA_20'] = df['Close'].rolling(window=20).mean()
print("\n20 Günlük Hareketli Ortalama (SMA) başarıyla hesaplandı.")