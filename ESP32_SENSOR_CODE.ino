/*
 * ============================================
 * AGRIX ESP32 SENSOR INTEGRATION
 * Temperature, Humidity & Gas Sensor Data Logger
 * ============================================
 * 
 * This Arduino sketch reads sensor data from:
 * - DHT22 (Temperature & Humidity)
 * - MQ-135 (Gas Sensor)
 * 
 * And sends the data to Firebase Cloud Functions
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ============================================
// CONFIGURATION
// ============================================

// WiFi Credentials
const char* ssid = "YOUR_SSID";                    // Replace with your WiFi SSID
const char* password = "YOUR_PASSWORD";            // Replace with your WiFi password

// Firebase Cloud Function URL
const char* serverUrl = "https://us-central1-agrix-3703d.cloudfunctions.net/receiveSensorData";

// DHT Sensor Configuration
#define DHTPIN 4                                   // GPIO4 (D4) for DHT22
#define DHTTYPE DHT22                              // DHT 22 sensor type
DHT dht(DHTPIN, DHTTYPE);

// Gas Sensor Configuration (MQ-135)
#define GAS_SENSOR_PIN 34                          // GPIO34 (ADC pin) for MQ-135
#define CALIBRATION_SAMPLE_TIMES 50
#define CALIBRATION_SAMPLE_INTERVAL 50             // ms

// Sensor calibration values (adjust based on your sensor)
#define RO_CLEAN_AIR_FACTOR 9.83                  // RO of sensor at 100ppm in clean air
#define MQ135_CALIBRATION_VOLTAGE 4.0             // Voltage to use for calibration
#define ADC_RESOLUTION 4095                        // ESP32 ADC is 12-bit (4095)
#define REFERENCE_VOLTAGE 5.0

// Update interval
#define SEND_INTERVAL 10000                        // Send data every 10 seconds

// Device ID
#define DEVICE_ID "esp32-agrix-001"

// ============================================
// GLOBAL VARIABLES
// ============================================

unsigned long lastSendTime = 0;
float RO = RO_CLEAN_AIR_FACTOR;

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n");
  Serial.println("=============================================");
  Serial.println("AGRIX ESP32 Sensor Module Initializing...");
  Serial.println("=============================================");
  
  // Initialize DHT sensor
  pinMode(DHTPIN, INPUT);
  dht.begin();
  Serial.println("✓ DHT22 sensor initialized");
  
  // Initialize Gas sensor
  pinMode(GAS_SENSOR_PIN, INPUT);
  Serial.println("✓ Gas sensor pin configured");
  
  // Connect to WiFi
  connectToWiFi();
  
  // Calibrate gas sensor
  Serial.println("\nCalibrating MQ-135 Gas Sensor...");
  Serial.println("Keep sensor in clean air for accurate reading...");
  calibrateGasSensor();
  
  Serial.println("\n✓ System Ready!");
  Serial.println("=============================================\n");
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Attempting to reconnect...");
    connectToWiFi();
  }
  
  // Send sensor data at specified interval
  if (millis() - lastSendTime >= SEND_INTERVAL) {
    readAndSendSensorData();
    lastSendTime = millis();
  }
  
  delay(100);
}

// ============================================
// WIFI CONNECTION
// ============================================

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi Connection Failed!");
  }
}

// ============================================
// DHT SENSOR READING
// ============================================

bool readDHTSensor(float &temperature, float &humidity) {
  // DHT readings can take up to 250ms
  // Sensor readings may also be up to 2 seconds 'old'
  
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();  // Read as Celsius
  
  // Check if any reads failed
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("✗ Failed to read from DHT sensor!");
    return false;
  }
  
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print("°C | Humidity: ");
  Serial.print(humidity);
  Serial.println("%");
  
  return true;
}

// ============================================
// GAS SENSOR CALIBRATION
// ============================================

void calibrateGasSensor() {
  float RS = 0;
  
  for (int i = 0; i < CALIBRATION_SAMPLE_TIMES; i++) {
    RS += getMQ135Resistance();
    delay(CALIBRATION_SAMPLE_INTERVAL);
  }
  
  RS = RS / CALIBRATION_SAMPLE_TIMES;
  RO = RS / RO_CLEAN_AIR_FACTOR;
  
  Serial.print("✓ Calibration Complete. RO = ");
  Serial.println(RO);
}

// ============================================
// GAS SENSOR READING
// ============================================

float getMQ135Resistance() {
  int adc = analogRead(GAS_SENSOR_PIN);
  float voltage = adc * (REFERENCE_VOLTAGE / ADC_RESOLUTION);
  float RS = (REFERENCE_VOLTAGE - voltage) / voltage * 10.0;  // RL = 10k
  return RS;
}

float readGasSensor() {
  float RS = getMQ135Resistance();
  float ratio = RS / RO;
  
  // MQ-135 PPM calculation for various gases
  // Using CO2 approximation: PPM = a * X^b
  float ppm = 116.6020682 * pow(ratio, -2.769034857);
  
  // Constrain to reasonable values
  if (ppm < 0) ppm = 0;
  if (ppm > 1000) ppm = 1000;
  
  Serial.print("Gas Level: ");
  Serial.print(ppm);
  Serial.println(" ppm");
  
  return ppm;
}

// ============================================
// READ & SEND SENSOR DATA
// ============================================

void readAndSendSensorData() {
  Serial.println("\n--- Reading Sensors ---");
  
  float temperature, humidity, gas;
  
  // Read DHT sensor
  if (!readDHTSensor(temperature, humidity)) {
    Serial.println("Skipping this reading due to DHT error");
    return;
  }
  
  // Read Gas sensor
  gas = readGasSensor();
  
  // Send to Firebase
  sendToFirebase(temperature, humidity, gas);
}

// ============================================
// SEND DATA TO FIREBASE
// ============================================

void sendToFirebase(float temperature, float humidity, float gas) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("✗ WiFi not connected, cannot send data");
    return;
  }
  
  HTTPClient http;
  
  // Create JSON payload
  StaticJsonDocument<200> jsonDoc;
  jsonDoc["temperature"] = round(temperature * 10) / 10.0;  // 1 decimal place
  jsonDoc["humidity"] = round(humidity * 10) / 10.0;        // 1 decimal place
  jsonDoc["gas"] = round(gas * 10) / 10.0;                  // 1 decimal place
  jsonDoc["deviceId"] = DEVICE_ID;
  jsonDoc["timestamp"] = millis();
  
  String jsonString;
  serializeJson(jsonDoc, jsonString);
  
  Serial.println("\nSending data to Firebase...");
  Serial.print("Payload: ");
  Serial.println(jsonString);
  
  // Send POST request
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  int httpCode = http.POST(jsonString);
  
  if (httpCode > 0) {
    String response = http.getString();
    
    if (httpCode == 200) {
      Serial.println("✓ Data sent successfully!");
      Serial.print("Response: ");
      Serial.println(response);
    } else {
      Serial.print("✗ HTTP Error Code: ");
      Serial.println(httpCode);
      Serial.print("Response: ");
      Serial.println(response);
    }
  } else {
    Serial.print("✗ Connection failed: ");
    Serial.println(http.errorToString(httpCode));
  }
  
  http.end();
}

/*
 * ============================================
 * WIRING DIAGRAM
 * ============================================
 * 
 * DHT22 Sensor:
 *   - VCC (1) → 3.3V
 *   - Data (2) → GPIO4 (D4)
 *   - GND (4) → GND
 *   - Add 10kΩ resistor between VCC and Data
 * 
 * MQ-135 Gas Sensor:
 *   - VCC → 5V (or 3.3V with adjusted calibration)
 *   - GND → GND
 *   - A0 → GPIO34 (ADC)
 *   - (If module has D0, connect to another GPIO for threshold detection)
 * 
 * ============================================
 * INSTALLATION STEPS
 * ============================================
 * 
 * 1. Install Required Libraries:
 *    - Sketch → Include Library → Manage Libraries
 *    - Search and install:
 *      * DHT sensor library by Adafruit
 *      * ArduinoJson by Benoit Blanchon
 * 
 * 2. Configure Your WiFi:
 *    - Replace "YOUR_SSID" with your WiFi network name
 *    - Replace "YOUR_PASSWORD" with your WiFi password
 * 
 * 3. Update Firebase URL:
 *    - Find your Firebase project URL
 *    - Update "serverUrl" with your project's cloud function URL
 *    - Format: https://region-projectid.cloudfunctions.net/receiveSensorData
 * 
 * 4. Pin Configuration (if different):
 *    - DHTPIN: GPIO pin connected to DHT22 data pin
 *    - GAS_SENSOR_PIN: Analog pin connected to MQ-135 A0
 *    - Adjust based on your wiring
 * 
 * 5. Upload to ESP32:
 *    - Select Tools → Board → ESP32 Dev Module
 *    - Select correct COM port
 *    - Click Upload
 *    - Open Serial Monitor (115200 baud) to view data
 * 
 * ============================================
 * TROUBLESHOOTING
 * ============================================
 * 
 * WiFi Connection Issues:
 *   - Check SSID and password are correct
 *   - Ensure WiFi is on 2.4GHz (not 5GHz)
 *   - Check signal strength
 * 
 * DHT Sensor Not Working:
 *   - Check wiring, especially the pull-up resistor
 *   - Ensure sensor is DHT22, not DHT11
 *   - Temperature/humidity readings seem wrong?
 *     Try moving sensor away from ESP32 (heat source)
 * 
 * Gas Sensor Not Working:
 *   - Ensure MQ-135 has warmed up for 20+ seconds
 *   - Check ADC reference voltage matches your setup
 *   - Calibration values might need adjustment
 * 
 * Firebase Not Receiving Data:
 *   - Verify Firebase URL is correct
 *   - Check Firebase Security Rules allow public writes
 *   - Check network/firewall isn't blocking HTTPS
 *   - Review Firebase Cloud Functions logs
 * 
 * ============================================
 */
