import requests
import pickle
import pandas as pd
import time

ESP32_IP = "192.168.0.100"
URL = f"http://{ESP32_IP}/data"

# Etiket düzeltme
etiket_duzenle = {
    "çamaþýr makinesi": "Çamaşır Makinesi",
    "stabil": "Stabil (Ampul+Buzdolabı)",
    "airfryer": "Airfryer",
    "kettle": "Kettle",
    "fön_1": "Fön Makinesi 1. Devir",
    "fön_2": "Fön Makinesi 2. Devir"
}

# Modeli yükle
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

print("Model yüklendi! Tahmin başlıyor...\n")

while True:
    try:
        r = requests.get(URL, timeout=5)
        d = r.json()

        if "Error" in d.values():
            print("Okuma hatası, atlanıyor...")
            time.sleep(5)
            continue

        # Veriyi hazırla
        veri = pd.DataFrame([[
            float(d["voltage"]),
            float(d["current"]),
            float(d["power"]),
            float(d["pf"])
        ]], columns=["voltaj", "akim", "guc", "pf"])

        # Tahmin yap
        tahmin = model.predict(veri)[0]
        olasilik = model.predict_proba(veri).max() * 100

        # Etiketi düzelt
        cihaz = etiket_duzenle.get(tahmin, tahmin)

        print(f"Güç: {d['power']}W | Akım: {d['current']}A | PF: {d['pf']} → {cihaz} (%{olasilik:.1f})")
        time.sleep(5)

    except KeyboardInterrupt:
        print("\nDurduruldu.")
        break
    except Exception as e:
        print(f"Hata: {e}")
        time.sleep(5)