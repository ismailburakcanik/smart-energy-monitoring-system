import requests
import csv
import time
from datetime import datetime

ESP32_IP = "192.168.0.100"  # senin IP'n
URL = f"http://{ESP32_IP}/data"
CSV_FILE = "veri2.csv"

cihaz = input("Hangi cihaz açık? (örn: stabil, kettle, camasir): ")

print(f"'{cihaz}' için veri toplanıyor... Durdurmak için CTRL+C")

with open(CSV_FILE, "a", newline="") as f:
    writer = csv.writer(f)
    
    # İlk çalıştırmada başlık yaz
    if f.tell() == 0:
        writer.writerow(["zaman", "cihaz", "voltaj", "akim", "guc", "pf"])
    
    while True:
        try:
            r = requests.get(URL, timeout=5)
            d = r.json()
            
            # Error gelen değerleri atla
            if "Error" in d.values():
                print("Okuma hatası, atlanıyor...")
                time.sleep(1)
                continue
            
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                cihaz,
                d["voltage"],
                d["current"],
                d["power"],
                d["pf"]
            ]
            writer.writerow(row)
            f.flush()  # Anında diske yaz
            
            print(f"{row[0]} | {cihaz} | {d['power']}W | {d['current']}A | PF:{d['pf']}")
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nVeri toplama durduruldu.")
            break
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(1)