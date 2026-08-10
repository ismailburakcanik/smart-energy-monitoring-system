#include <PZEM004Tv30.h>
#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <AsyncTCP.h>
 
// WiFi credentials
const char* ssid = "TURKSAT-KABLONET-2.4G-wsL3";
const char* password = "SkpxMoMt7a8r";
 
#define PZEM_RX_PIN 16
#define PZEM_TX_PIN 17
 
volatile bool resetFlag = false;

AsyncWebServer server(80);
 
PZEM004Tv30 pzem(Serial2, PZEM_RX_PIN, PZEM_TX_PIN);

 
float voltage = 0.0;
float current = 0.0;
float power = 0.0;
float energy = 0.0;
float frequency = 0.0;
float pf = 0.0;
 
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML>
<html>
<head>
  <title>ESP32 Power Monitor</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  <style>
    body { 
      font-family: Arial, sans-serif; 
      margin: 0;
      padding: 20px;
      background-color: #f0f0f0;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }
    .card {
      background: white;
      border-radius: 15px;
      padding: 25px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
      display: flex;
      align-items: center;
      text-align: left;
    }
    .icon {
      font-size: 40px;
      margin-right: 25px;
      min-width: 50px;
      text-align: center;
    }
    .content {
      display: flex;
      flex-direction: column;
    }
    .label {
      font-size: 16px;
      color: #7f8c8d;
      margin-bottom: 5px;
      font-weight: bold;
    }
    .value {
      font-size: 24px;
      color: #2c3e50;
      display: flex;
      align-items: baseline;
    }
    .unit {
      font-size: 16px;
      color: #95a5a6;
      margin-left: 5px;
    }
    .fa-bolt { color: #f1c40f; }
    .fa-exchange-alt { color: #3498db; }
    .fa-plug { color: #e74c3c; }
    .fa-chart-line { color: #2ecc71; }
    .fa-wave-square { color: #9b59b6; }
    .fa-percent { color: #e67e22; }
    h1 {
      text-align: center;
      margin: 30px 0;
      color: #2c3e50;
    }
    .reset-container {
      text-align: center;
      margin-bottom: 25px;
    }
    .reset-btn {
      background: #e74c3c;
      color: white;
      border: none;
      padding: 12px 30px;
      border-radius: 10px;
      font-size: 16px;
      cursor: pointer;
      box-shadow: 0 4px 8px rgba(0,0,0,0.15);
      transition: background 0.2s;
    }
    .reset-btn:hover {
      background: #c0392b;
    }
  </style>
  <script>
    function updateData() {
      var xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
          var data = JSON.parse(this.responseText);
          document.getElementById('voltage').innerHTML = data.voltage + '<span class="unit">V</span>';
          document.getElementById('current').innerHTML = data.current + '<span class="unit">A</span>';
          document.getElementById('power').innerHTML = data.power + '<span class="unit">W</span>';
          document.getElementById('energy').innerHTML = data.energy + '<span class="unit">kWh</span>';
          document.getElementById('frequency').innerHTML = data.frequency + '<span class="unit">Hz</span>';
          document.getElementById('pf').innerHTML = data.pf;
        }
      };
      xhttp.open("GET", "/data", true);
      xhttp.send();
    }

    function resetEnergy() {
      if (confirm("Enerji sayaci sifirlansin mi?")) {
        fetch('/reset')
          .then(response => response.text())
          .then(msg => {
            alert(msg);
            updateData();
          });
      }
    }

    setInterval(updateData, 5000);
    window.onload = updateData;
  </script>
</head>
<body>
  <h1><i class="fas fa-plug"></i> ESP32 Power Monitor</h1>

  <div class="reset-container">
    <button class="reset-btn" onclick="resetEnergy()">
      &#128260; Enerjiyi Sifirla
    </button>
  </div>

  <div class="grid">
    <div class="card">
      <i class="fas fa-bolt icon"></i>
      <div class="content">
        <div class="label">VOLTAJ</div>
        <div class="value" id="voltage">%VOLTAGE%<span class="unit">V</span></div>
      </div>
    </div>
    <div class="card">
      <i class="fas fa-exchange-alt icon"></i>
      <div class="content">
        <div class="label">AKIM</div>
        <div class="value" id="current">%CURRENT%<span class="unit">A</span></div>
      </div>
    </div>
    <div class="card">
      <i class="fas fa-plug icon"></i>
      <div class="content">
        <div class="label">GUC</div>
        <div class="value" id="power">%POWER%<span class="unit">W</span></div>
      </div>
    </div>
    <div class="card">
      <i class="fas fa-chart-line icon"></i>
      <div class="content">
        <div class="label">ENERJI</div>
        <div class="value" id="energy">%ENERGY%<span class="unit">kWh</span></div>
      </div>
    </div>
    <div class="card">
      <i class="fas fa-wave-square icon"></i>
      <div class="content">
        <div class="label">FREKANS</div>
        <div class="value" id="frequency">%FREQUENCY%<span class="unit">Hz</span></div>
      </div>
    </div>
    <div class="card">
      <i class="fas fa-percent icon"></i>
      <div class="content">
        <div class="label">GUC FAKTORU</div>
        <div class="value" id="pf">%PF%</div>
      </div>
    </div>
  </div>
</body>
</html>
)rawliteral";
 
String processor(const String& var) {
  if(var == "VOLTAGE") return isnan(voltage) ? "Error" : String(voltage, 1);
  else if(var == "CURRENT") return isnan(current) ? "Error" : String(current, 2);
  else if(var == "POWER") return isnan(power) ? "Error" : String(power, 1);
  else if(var == "ENERGY") return isnan(energy) ? "Error" : String(energy, 3);
  else if(var == "FREQUENCY") return isnan(frequency) ? "Error" : String(frequency, 1);
  else if(var == "PF") return isnan(pf) ? "Error" : String(pf, 2);
  return String();
}
 
void setup() {
  Serial.begin(115200);

  IPAddress local_IP(192, 168, 0, 100);
  IPAddress gateway(192, 168, 0, 1);
  IPAddress subnet(255, 255, 255, 0);
  IPAddress dns(8, 8, 8, 8);
  WiFi.config(local_IP, gateway, subnet, dns);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
 
  // Route for root / web page
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    request->send_P(200, "text/html", index_html, processor);
  });
 
  // Route for JSON data
  server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request){
    String json = "{";
    json += "\"voltage\":\"" + String(isnan(voltage) ? "Error" : String(voltage, 1)) + "\",";
    json += "\"current\":\"" + String(isnan(current) ? "Error" : String(current, 2)) + "\",";
    json += "\"power\":\"" + String(isnan(power) ? "Error" : String(power, 1)) + "\",";
    json += "\"energy\":\"" + String(isnan(energy) ? "Error" : String(energy, 3)) + "\",";
    json += "\"frequency\":\"" + String(isnan(frequency) ? "Error" : String(frequency, 1)) + "\",";
    json += "\"pf\":\"" + String(isnan(pf) ? "Error" : String(pf, 2)) + "\"";
    json += "}";
    request->send(200, "application/json", json);
  });

  // Route for energy reset
  server.on("/reset", HTTP_GET, [](AsyncWebServerRequest *request){
    resetFlag = true;
    request->send(200, "text/plain", "Enerji sayaci sifirlanadi!");

  });
 
  server.begin();
}
 
void loop() {

  if (resetFlag) {
    resetFlag = false;
    pzem.resetEnergy();
    delay(3000);
    return;
}
  
  // Read all values first
  float v = pzem.voltage();
  float c = pzem.current();
  float p = pzem.power();
  float e = pzem.energy();
  float f = pzem.frequency();
  float pf_val = pzem.pf();
 
  // Update global variables atomically
  if (!isnan(v)) voltage = v;
  if (!isnan(c)) current = c;
  if (!isnan(p)) power = p;
  if (!isnan(e)) energy = e;
  if (!isnan(f)) frequency = f;
  if (!isnan(pf_val)) pf = pf_val;
 
  // Serial output
  Serial.print("Voltage: "); Serial.print(voltage); Serial.println("V");
  Serial.print("Current: "); Serial.print(current); Serial.println("A");
  Serial.print("Power: "); Serial.print(power); Serial.println("W");
  Serial.print("Energy: "); Serial.print(energy,3); Serial.println("kWh");
  Serial.print("Frequency: "); Serial.print(frequency); Serial.println("Hz");
  Serial.print("PF: "); Serial.println(pf);
  Serial.println("-------------------");
 
  delay(1000);
}
