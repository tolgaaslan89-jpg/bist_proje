import yfinance as yf
import pandas as pd

hisse_kodu = "THYAO.IS"
print(f"{hisse_kodu} için analiz motoru çalıştırılıyor...")

# Verileri çekelim
df = yf.download(hisse_kodu, period="6mo", interval="1d")
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# 1. 20 Günlük Basit Hareketli Ortalama (SMA)
df['SMA_20'] = df['Close'].rolling(window=20).mean()

# 2. RSI (Göreceli Güç Endeksi - 14) Hesaplama
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# 3. MACD Hesaplama (12, 26, 9)
exp1 = df['Close'].ewm(span=12, adjust=False).mean()
exp2 = df['Close'].ewm(span=26, adjust=False).mean()
df['MACD'] = exp1 - exp2
df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

# Son değerleri alalım
son_rsi = df['RSI'].iloc[-1]
son_fiyat = df['Close'].iloc[-1]

print(f"\nGüncel Fiyat: {son_fiyat:.2f} TL")
print(f"Güncel RSI Değeri: {son_rsi:.2f}")

if son_rsi < 30:
    print("SİNYAL: 🟢 AL (Hisse aşırı satım bölgesinde!)")
elif son_rsi > 70:
    print("SİNYAL: 🔴 SAT (Hisse aşırı alım bölgesinde!)")
else:
    print("SİNYAL: ⚪ NÖTR (Bekle / Yatay seyir)")