import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle

WINDOW = 10  # Son 10 ölçüm = 10 saniye

df = pd.read_csv("veri2.csv", encoding="latin-1")
df["guc"] = pd.to_numeric(df["guc"], errors="coerce")
df["akim"] = pd.to_numeric(df["akim"], errors="coerce")
df["voltaj"] = pd.to_numeric(df["voltaj"], errors="coerce")
df["pf"] = pd.to_numeric(df["pf"], errors="coerce")
df = df.dropna()

print(f"Toplam veri: {len(df)} satır")

# Her cihaz için ayrı ayrı sliding window uygula
X_list = []
y_list = []

for cihaz in df["cihaz"].unique():
    alt = df[df["cihaz"] == cihaz].reset_index(drop=True)
    for i in range(WINDOW, len(alt)):
        pencere = alt.iloc[i-WINDOW:i]
        ozellikler = []
        for col in ["guc", "akim", "pf"]:
            ozellikler.append(pencere[col].mean())   # ortalama
            ozellikler.append(pencere[col].std())    # standart sapma
            ozellikler.append(pencere[col].max())    # max
            ozellikler.append(pencere[col].min())    # min
            ozellikler.append(pencere[col].iloc[-1] - pencere[col].iloc[0])  # değişim
        X_list.append(ozellikler)
        y_list.append(cihaz)

X = np.array(X_list)
y = np.array(y_list)

print(f"Window sonrası veri: {len(X)} satır")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("\n--- MODEL SONUÇLARI ---")
print(classification_report(y_test, y_pred))

with open("model_window.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model 'model_window.pkl' olarak kaydedildi!")
