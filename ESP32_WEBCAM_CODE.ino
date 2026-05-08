/*
 * ============================================
 * AGRIX ESP32-CAM VIDEO STREAMING
 * Real-time Crop/Soil Monitoring Camera Feed
 * ============================================
 * 
 * This Arduino sketch configures ESP32-CAM to:
 * - Stream live video feed via HTTP
 * - Capture still images for analysis
 * - Integrate with Firebase Realtime Database
 * - Compatible with AGRIX Dashboard
 * 
 * Required Hardware: ESP32-CAM with OV2640 camera
 */

#include <WiFi.h>
#include <WebServer.h>
#include <esp_camera.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ============================================
// CAMERA PIN CONFIGURATION (ESP32-CAM)
// ============================================

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ============================================
// WiFi & SERVER CONFIGURATION
// ============================================

const char* ssid = "YOUR_SSID";                    // Replace with your WiFi SSID
const char* password = "YOUR_PASSWORD";            // Replace with your WiFi password

// Firebase Configuration
const char* firebaseHost = "agrix-3703d-default-rtdb.firebaseio.com";
const char* databaseSecret = "YOUR_DATABASE_SECRET"; // Optional
const char* deviceID = "esp32-cam-agrix-001";

// Web Server Port
WebServer server(80);

// ============================================
// GLOBAL VARIABLES
// ============================================

unsigned long lastFrameTime = 0;
unsigned long frameCount = 0;
float fps = 0;
bool cameraInitialized = false;

// ============================================
// CAMERA INITIALIZATION
// ============================================

bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d7 = Y7_GPIO_NUM;
  config.pin_d6 = Y6_GPIO_NUM;
  config.pin_d5 = Y5_GPIO_NUM;
  config.pin_d4 = Y4_GPIO_NUM;
  config.pin_d3 = Y3_GPIO_NUM;
  config.pin_d2 = Y2_GPIO_NUM;
  config.pin_d1 = Y9_GPIO_NUM;
  config.pin_d0 = Y8_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Resolution options:
  // FRAMESIZE_QQVGA (160x120), FRAMESIZE_QVGA (320x240)
  // FRAMESIZE_VGA (640x480), FRAMESIZE_SVGA (800x600)
  // FRAMESIZE_XGA (1024x768), FRAMESIZE_SXGA (1280x1024)
  
  config.frame_size = FRAMESIZE_VGA;  // 640x480
  config.jpeg_quality = 10;            // 0-63 (lower = higher quality)
  config.fb_count = 1;                 // 1 or 2

  // Power on camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("✗ Camera init failed with error 0x%x\n", err);
    return false;
  }

  // Adjust camera settings for better quality
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_gains(s, 0, 0, 0);         // Turn off AGC (Auto Gain Control)
    s->set_brightness(s, 0);           // Brightness (-2 to 2)
    s->set_contrast(s, 1);             // Contrast (-2 to 2)
    s->set_saturation(s, 0);           // Saturation (-2 to 2)
    s->set_sharpness(s, 1);            // Sharpness (0-2)
    s->set_exposure_ctrl(s, 1);        // Enable exposure control
    s->set_aec_value(s, 300);          // Auto exposure control
    s->set_white_balance(s, 1);        // White balance
    s->set_awb_gain(s, 1);             // Auto white balance gain
  }

  Serial.println("✓ Camera initialized successfully!");
  return true;
}

// ============================================
// WiFi CONNECTION
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
    Serial.println("\n✓ WiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    return;
  }
  
  Serial.println("\n✗ WiFi connection failed!");
}

// ============================================
// WEB SERVER ROUTES
// ============================================

// Route: Root page with stream info
void handleRoot() {
  String response = "<!DOCTYPE html>";
  response += "<html><head><title>AGRIX ESP32-CAM Feed</title></head>";
  response += "<body style='font-family: Arial; text-align: center; background: #1a1a1a; color: white; padding: 20px;'>";
  response += "<h1>🌾 AGRIX ESP32-CAM Video Stream</h1>";
  response += "<p>Device ID: " + String(deviceID) + "</p>";
  response += "<p>IP: " + WiFi.localIP().toString() + "</p>";
  response += "<p>Uptime: " + String(millis() / 1000) + " seconds</p>";
  response += "<p>FPS: " + String(fps, 2) + "</p>";
  response += "<h2>Video Stream URLs:</h2>";
  response += "<p><strong>MJPEG Stream:</strong> http://" + WiFi.localIP().toString() + ":80/stream</p>";
  response += "<p><strong>Single JPEG:</strong> http://" + WiFi.localIP().toString() + ":80/capture</p>";
  response += "<p><strong>Camera Status:</strong> http://" + WiFi.localIP().toString() + ":80/status</p>";
  response += "</body></html>";
  
  server.send(200, "text/html", response);
}

// Route: MJPEG stream (continuous video feed)
void handleStream() {
  WiFiClient client = server.client();
  
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n";
  response += "Access-Control-Allow-Origin: *\r\n";
  response += "\r\n";
  client.write((uint8_t *)response.c_str(), response.length());

  while (client.connected()) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("✗ Camera capture failed");
      break;
    }

    // Update FPS calculation
    unsigned long currentTime = millis();
    if (lastFrameTime > 0) {
      fps = 1000.0 / (currentTime - lastFrameTime);
    }
    lastFrameTime = currentTime;
    frameCount++;

    // Send MJPEG frame
    String part = "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ";
    part += fb->len;
    part += "\r\nX-Timestamp: " + String(millis());
    part += "\r\n\r\n";
    
    client.write((uint8_t *)part.c_str(), part.length());
    client.write(fb->buf, fb->len);
    client.write((uint8_t *)"\r\n", 2);
    
    esp_camera_fb_return(fb);

    // Timeout check
    if (!client.connected()) {
      break;
    }
  }

  Serial.println("✓ Stream client disconnected");
}

// Route: Single JPEG capture
void handleCapture() {
  camera_fb_t * fb = esp_camera_fb_get();
  
  if (!fb) {
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  server.sendHeader("Content-Type", "image/jpeg");
  server.sendHeader("Content-Length", String(fb->len));
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send_P(200, "image/jpeg", (const char *)fb->buf, fb->len);
  
  esp_camera_fb_return(fb);
}

// Route: Camera status
void handleStatus() {
  DynamicJsonDocument doc(1024);
  
  doc["status"] = "ok";
  doc["device_id"] = deviceID;
  doc["ip_address"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["uptime_ms"] = millis();
  doc["frame_count"] = frameCount;
  doc["fps"] = fps;
  doc["camera_initialized"] = cameraInitialized;
  
  String response;
  serializeJson(doc, response);
  
  server.send(200, "application/json", response);
}

// Route: 404 Not Found
void handleNotFound() {
  server.send(404, "text/plain", "Not Found");
}

// ============================================
// FIREBASE INTEGRATION (Optional)
// ============================================

void updateFirebaseStatus() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;
  String url = "https://" + String(firebaseHost) + "/devices/" + String(deviceID) + "/camera.json";
  
  DynamicJsonDocument doc(256);
  doc["status"] = "online";
  doc["ip"] = WiFi.localIP().toString();
  doc["fps"] = fps;
  doc["frame_count"] = frameCount;
  doc["timestamp"] = millis();
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.PATCH(jsonPayload);
  
  if (httpResponseCode > 0) {
    Serial.print("✓ Firebase update: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("✗ Firebase error: ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  
  http.end();
}

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n");
  Serial.println("=============================================");
  Serial.println("AGRIX ESP32-CAM Initialization");
  Serial.println("=============================================");
  
  // Initialize camera
  if (!initCamera()) {
    Serial.println("✗ Camera initialization failed!");
    while (true) {
      delay(1000);
    }
  }
  cameraInitialized = true;
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup web server routes
  server.on("/", handleRoot);
  server.on("/stream", handleStream);
  server.on("/capture", handleCapture);
  server.on("/status", handleStatus);
  server.onNotFound(handleNotFound);
  
  // Start server
  server.begin();
  Serial.println("✓ Web server started");
  
  Serial.println("\n=============================================");
  Serial.println("Camera Ready!");
  Serial.println("Stream URL: http://" + WiFi.localIP().toString() + "/stream");
  Serial.println("Capture URL: http://" + WiFi.localIP().toString() + "/capture");
  Serial.println("Status URL: http://" + WiFi.localIP().toString() + "/status");
  Serial.println("=============================================\n");
}

// ============================================
// MAIN LOOP
// ============================================

void loop() {
  server.handleClient();
  
  // Update Firebase status every 30 seconds
  static unsigned long lastFirebaseUpdate = 0;
  if (millis() - lastFirebaseUpdate > 30000) {
    updateFirebaseStatus();
    lastFirebaseUpdate = millis();
  }
}
