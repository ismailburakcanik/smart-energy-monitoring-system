from flask import Flask, render_template_string, jsonify
import requests
import pickle
import pandas as pd
import threading
import time
from collections import deque
import numpy as np

app = Flask(__name__)

ESP32_IP = "192.168.0.100"
URL = f"http://{ESP32_IP}/data"
RESET_URL = f"http://{ESP32_IP}/reset"

WINDOW = 10
pencere = deque(maxlen=WINDOW)
onceki_guc = None
tahmin_gecmis = deque(maxlen=3)
camasir_gecmis = deque(maxlen=120)  # Son 120 saniyelik güç geçmişi

etiket_duzenle = {
    "çamaþýr makinesi": "Çamaşır Makinesi",
    "çama??r makinesi": "Çamaşır Makinesi",
    "camasir": "Çamaşır Makinesi",
    "stabil": "Stabil",
    "airfryer": "Airfryer",
    "kettle": "Kettle",
    "fon_1": "Fön Makinesi 1. Devir",
    "fon_2": "Fön Makinesi 2. Devir",
    "fön_1": "Fön Makinesi 1. Devir",
    "fön_2": "Fön Makinesi 2. Devir"
}

etiket_ikon = {
    "Stabil": "🏠",
    "Çamaşır Makinesi": "🫧",
    "Airfryer": "🍳",
    "Kettle": "☕",
    "Fön Makinesi 1. Devir": "💨",
    "Fön Makinesi 2. Devir": "💨"
}

# Her iki modeli yükle
with open("model.pkl", "rb") as f:
    model_anlik = pickle.load(f)

with open("model_window.pkl", "rb") as f:
    model_window = pickle.load(f)

durum = {
    "voltage": "-", "current": "-", "power": "-",
    "energy": "-", "frequency": "-", "pf": "-",
    "cihaz": "Bekleniyor...", "olasilik": 0, "ikon": "⏳",
    "pencere_doluluk": 0
}

def veri_guncelle():
    global onceki_guc

    while True:
        try:
            r = requests.get(URL, timeout=5)
            d = r.json()
            if "Error" not in d.values():
                yeni_guc = float(d["power"])

                durum.update({
                    "voltage": d["voltage"], "current": d["current"],
                    "power": d["power"], "energy": d["energy"],
                    "frequency": d["frequency"], "pf": d["pf"]
                })

                # Debounce: airfryer için 40, çamaşır için 25, diğerleri için 5 ölçüm
                pencere.append([yeni_guc, float(d["current"]), float(d["pf"])])
                if durum["cihaz"] == "Airfryer":
                    if len(pencere) >= 60:
                        son_ort = sum([p[0] for p in list(pencere)[-60:]]) / 60
                        if onceki_guc is not None and abs(son_ort - onceki_guc) > 150:
                            pencere.clear()
                            durum.update({"cihaz": "Bekleniyor...", "ikon": "⏳"})
                elif durum["cihaz"] == "Çamaşır Makinesi":
                    if len(pencere) >= 25:
                        son_ort = sum([p[0] for p in list(pencere)[-25:]]) / 25
                        if onceki_guc is not None and abs(son_ort - onceki_guc) > 150:
                            pencere.clear()
                            durum.update({"cihaz": "Bekleniyor...", "ikon": "⏳"})
                else:
                    if len(pencere) >= 5:
                        son_5_ort = sum([p[0] for p in list(pencere)[-5:]]) / 5
                        if onceki_guc is not None and abs(son_5_ort - onceki_guc) > 150:
                            pencere.clear()
                            durum.update({"cihaz": "Bekleniyor...", "ikon": "⏳"})

                onceki_guc = yeni_guc
                camasir_gecmis.append(yeni_guc)

                # Çamaşır makinesi için son 60 saniyede 350W+ gelmemişse temizle
                if durum["cihaz"] == "Çamaşır Makinesi":
                    if len(camasir_gecmis) >= 60 and max(list(camasir_gecmis)[-60:]) < 350:
                        pencere.clear()
                        tahmin_gecmis.clear()
                        camasir_gecmis.clear()
                        durum.update({"cihaz": "Bekleniyor...", "ikon": "⏳"})

                # Airfryer için son 90 saniyede 500W+ gelmemişse temizle
                if durum["cihaz"] == "Airfryer":
                    if len(camasir_gecmis) >= 90 and max(list(camasir_gecmis)[-90:]) < 500:
                        pencere.clear()
                        tahmin_gecmis.clear()
                        camasir_gecmis.clear()
                        durum.update({"cihaz": "Bekleniyor...", "ikon": "⏳"})
                
                # Pencere doluluk oranını güncelle
                doluluk = int((len(pencere) / WINDOW) * 100)
                durum.update({"pencere_doluluk": doluluk})

                if len(pencere) == WINDOW:
                    # Window model kullan
                    p = pd.DataFrame(list(pencere), columns=["guc", "akim", "pf"])
                    ozellikler = []
                    for col in ["guc", "akim", "pf"]:
                        ozellikler.append(p[col].mean())
                        ozellikler.append(p[col].std())
                        ozellikler.append(p[col].max())
                        ozellikler.append(p[col].min())
                        ozellikler.append(p[col].iloc[-1] - p[col].iloc[0])
                    veri = pd.DataFrame([ozellikler])
                    tahmin = model_window.predict(veri)[0]
                    olasilik = model_window.predict_proba(veri).max() * 100
                    cihaz = etiket_duzenle.get(tahmin, tahmin)

                    # Tahmin değiştiyse bekleniyor yaz, pencereyi temizle
                    # Airfryer ve çamaşır makinesi için bu kontrolü atla
                    if cihaz != durum["cihaz"] and durum["cihaz"] not in ["Bekleniyor...", "Airfryer", "Çamaşır Makinesi"]:
                        pencere.clear()
                        tahmin_gecmis.clear()
                        durum.update({"cihaz": "Bekleniyor...", "ikon": "⏳"})
                    elif durum["cihaz"] in ["Airfryer", "Çamaşır Makinesi"]:
                        # Airfryer ve çamaşır için tahmin geçmişini güncelleme, debounce halleder
                        pass
                    else:
                        tahmin_gecmis.append(cihaz)
                        # Sadece art arda 3 kez aynı tahmin gelirse göster
                        if len(tahmin_gecmis) == 3 and len(set(tahmin_gecmis)) == 1:
                            durum.update({
                                "cihaz": cihaz,
                                "olasilik": round(olasilik, 1),
                                "ikon": etiket_ikon.get(cihaz, "🔌")
                            })

        except Exception as e:
            pass
        time.sleep(1)

threading.Thread(target=veri_guncelle, daemon=True).start()

HTML = """
<!DOCTYPE HTML>
<html>
<head>
  <title>ESP32 Power Monitor</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f0f0f0; }
    h1 { text-align: center; margin: 30px 0; color: #2c3e50; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
    .card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: flex; align-items: center; }
    .icon { font-size: 40px; margin-right: 25px; min-width: 50px; text-align: center; }
    .content { display: flex; flex-direction: column; }
    .label { font-size: 16px; color: #7f8c8d; margin-bottom: 5px; font-weight: bold; }
    .value { font-size: 24px; color: #2c3e50; }
    .unit { font-size: 16px; color: #95a5a6; margin-left: 5px; }
    .tahmin-card { background: linear-gradient(135deg, #2c3e50, #3498db); color: white; border-radius: 15px; padding: 30px; max-width: 1200px; margin: 0 auto 20px auto; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .tahmin-ikon { font-size: 60px; margin-bottom: 10px; }
    .tahmin-cihaz { font-size: 32px; font-weight: bold; margin-bottom: 5px; }
    .progress-container { width: 80%; margin: 10px auto 0 auto; background: rgba(255,255,255,0.2); border-radius: 10px; height: 8px; }
    .progress-bar { height: 8px; border-radius: 10px; background: #2ecc71; transition: width 0.5s; }
    .reset-container { text-align: center; margin-bottom: 25px; }
    .reset-btn { background: #e74c3c; color: white; border: none; padding: 12px 30px; border-radius: 10px; font-size: 16px; cursor: pointer; }
    .reset-btn:hover { background: #c0392b; }
    .fa-bolt { color: #f1c40f; }
    .fa-exchange-alt { color: #3498db; }
    .fa-plug { color: #e74c3c; }
    .fa-chart-line { color: #2ecc71; }
    .fa-wave-square { color: #9b59b6; }
    .fa-percent { color: #e67e22; }
  </style>
  <script>
    function updateData() {
      fetch('/data')
        .then(r => r.json())
        .then(d => {
          document.getElementById('voltage').innerHTML = d.voltage + '<span class="unit">V</span>';
          document.getElementById('current').innerHTML = d.current + '<span class="unit">A</span>';
          document.getElementById('power').innerHTML = d.power + '<span class="unit">W</span>';
          document.getElementById('energy').innerHTML = d.energy + '<span class="unit">kWh</span>';
          document.getElementById('frequency').innerHTML = d.frequency + '<span class="unit">Hz</span>';
          document.getElementById('pf').innerHTML = d.pf;
          document.getElementById('tahmin-ikon').innerHTML = d.ikon;
          document.getElementById('tahmin-cihaz').innerHTML = d.cihaz;
          document.getElementById('progress-bar').style.width = d.pencere_doluluk + '%';
        });
    }
    function resetEnergy() {
      if (confirm("Enerji sayacı sıfırlansın mı?")) {
        fetch('/reset');
        setTimeout(() => { updateData(); }, 3000);
      }
    }
    setInterval(updateData, 1000);
    window.onload = updateData;
  </script>
</head>
<body>
  <h1><i class="fas fa-plug"></i> ESP32 Power Monitor</h1>
  <div class="tahmin-card">
    <div class="tahmin-ikon" id="tahmin-ikon">⏳</div>
    <div class="tahmin-cihaz" id="tahmin-cihaz">Bekleniyor...</div>
    <div class="progress-container">
      <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
    </div>
  </div>
  <div class="reset-container">
    <button class="reset-btn" onclick="resetEnergy()">&#128260; Enerjiyi Sıfırla</button>
  </div>
  <div class="grid">
    <div class="card"><i class="fas fa-bolt icon"></i><div class="content"><div class="label">VOLTAJ</div><div class="value" id="voltage">-<span class="unit">V</span></div></div></div>
    <div class="card"><i class="fas fa-exchange-alt icon"></i><div class="content"><div class="label">AKIM</div><div class="value" id="current">-<span class="unit">A</span></div></div></div>
    <div class="card"><i class="fas fa-plug icon"></i><div class="content"><div class="label">GÜÇ</div><div class="value" id="power">-<span class="unit">W</span></div></div></div>
    <div class="card"><i class="fas fa-chart-line icon"></i><div class="content"><div class="label">ENERJİ</div><div class="value" id="energy">-<span class="unit">kWh</span></div></div></div>
    <div class="card"><i class="fas fa-wave-square icon"></i><div class="content"><div class="label">FREKANS</div><div class="value" id="frequency">-<span class="unit">Hz</span></div></div></div>
    <div class="card"><i class="fas fa-percent icon"></i><div class="content"><div class="label">GÜÇ FAKTÖRÜ</div><div class="value" id="pf">-</div></div></div>
  </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/data")
def data():
    return jsonify(durum)

@app.route("/reset")
def reset():
    try:
        requests.get(RESET_URL, timeout=2)
    except:
        pass
    return "Enerji sayaci sifirlanadi!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
