# ESP32-CAM AGRIX Video Stream Setup Guide

## Overview
This guide explains how to set up ESP32-CAM for real-time video streaming with the AGRIX dashboard. The system supports two streaming modes:
- **MJPEG Stream**: Continuous video feed
- **JPEG Snapshot**: Single frame with customizable refresh rate

---

## Hardware Requirements

### ESP32-CAM Module
- ESP32-CAM with OV2640 camera
- USB-to-UART adapter (for programming)
- MicroSD card (optional, for local storage)
- 5V power supply (recommended)
- USB cable

### Network
- WiFi network (2.4GHz recommended)
- Computer on same network as ESP32-CAM

---

## Step 1: Arduino IDE Setup

### 1.1 Install Arduino IDE
Download from: https://www.arduino.cc/en/software

### 1.2 Add ESP32 Board Support
1. Open Arduino IDE
2. Go to `File` → `Preferences`
3. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click `OK`
5. Go to `Tools` → `Board Manager`
6. Search for "ESP32"
7. Click "Install" on "ESP32 by Espressif Systems"

### 1.3 Install Required Libraries
1. Go to `Sketch` → `Include Library` → `Manage Libraries`
2. Search and install:
   - **ArduinoJson** (by Benoit Blanchon)
   - **esp32-camera** (built-in with board support)

---

## Step 2: Upload Firmware

### 2.1 Connect ESP32-CAM
1. Connect USB-to-UART adapter to ESP32-CAM:
   - GND → GND
   - TX → U0RX
   - RX → U0TX
   - 5V → 5V (if your adapter has 5V output)
2. Connect USB adapter to computer

### 2.2 Configure Arduino IDE
1. Go to `Tools` → `Board` → Select "AI Thinker ESP32-CAM"
2. Select `Tools` → `Port` → Choose your COM port
3. Set `Tools` → `Upload Speed` → 921600
4. Set `Tools` → `Partition Scheme` → "Huge APP (3MB No OTA)"

### 2.3 Load and Configure Code
1. Open `ESP32_WEBCAM_CODE.ino` in Arduino IDE
2. Find these lines at the top:
   ```cpp
   const char* ssid = "YOUR_SSID";
   const char* password = "YOUR_PASSWORD";
   ```
3. Replace with your WiFi credentials:
   ```cpp
   const char* ssid = "YourNetworkName";
   const char* password = "YourNetworkPassword";
   ```
4. (Optional) Update Firebase settings if using Firebase integration

### 2.4 Upload Sketch
1. Click `Sketch` → `Upload`
2. When you see "Uploading...", do NOT disconnect the board
3. Wait for "Upload complete" message

### 2.5 Check Serial Monitor
1. Click `Tools` → `Serial Monitor`
2. Set baud rate to **115200**
3. You should see:
   ```
   =============================================
   AGRIX ESP32-CAM Initialization
   =============================================
   ✓ Camera initialized successfully!
   ✓ WiFi connected!
   IP Address: 192.168.1.XXX
   ✓ Web server started
   
   Camera Ready!
   Stream URL: http://192.168.1.XXX/stream
   ```

**Important**: Write down the IP address displayed (e.g., 192.168.1.100)

---

## Step 3: Connect to AGRIX Dashboard

### 3.1 Open Dashboard
1. Open AGRIX dashboard in your web browser
2. Click on the Reports modal button
3. Navigate to "ESP32 Video Feed" tab

### 3.2 Enter ESP32 Details
1. In **ESP32 IP Address** field, enter:
   - The IP address from Serial Monitor (e.g., 192.168.1.100)
   - Or use `esp32.local` if your network supports mDNS
2. **Port**: Leave as 80 (unless you changed it in code)
3. **Select Stream Type**:
   - **MJPEG Stream**: For continuous live video
   - **JPEG Snapshot**: For periodic frame updates

### 3.3 Connect
1. Click **Connect** button
2. If successful, you'll see:
   - Green "Connected" status
   - Live video feed displayed
   - Frame rate and timestamp

---

## Troubleshooting

### ❌ "Failed to connect to ESP32"

**Problem 1: ESP32 not powered on**
- Check power supply
- LED on ESP32-CAM should be lit
- Check Serial Monitor for startup messages

**Problem 2: Wrong IP address**
- Check Serial Monitor for correct IP
- If IP not showing, check WiFi credentials in code
- Try uploading again

**Problem 3: Firewall blocking**
- Disable firewall temporarily for testing
- Or add HTTP exception for port 80
- Check if computer and ESP32 are on same WiFi network

**Problem 4: Board not uploading**
- Hold GPIO0 to GND while uploading
- Try lower upload speed (115200 instead of 921600)
- Check USB cable is working
- Try different USB port

### 🔧 Can't see IP address in Serial Monitor

1. Reset ESP32 by pressing EN button
2. Watch Serial Monitor startup messages
3. If WiFi fails, check:
   - SSID and password in code (no extra spaces)
   - WiFi network is 2.4GHz (not 5GHz)
   - Network doesn't have special characters in password

### 📹 Video feed is choppy

- Try JPEG Snapshot instead of MJPEG
- Reduce refresh rate in JPEG mode (try 1000ms)
- Place ESP32-CAM closer to WiFi router
- Check for interference from other devices

### 🔌 USB device not recognized

- Update CH340 drivers from: https://sparks.gogo.co.nz/ch340.html
- Try different USB cable
- Try different USB port
- Restart computer

---

## Camera Settings

You can customize camera behavior by editing `ESP32_WEBCAM_CODE.ino`:

### Resolution Options
```cpp
config.frame_size = FRAMESIZE_VGA;  // Current: 640x480
```

Available options:
- `FRAMESIZE_QQVGA` → 160x120
- `FRAMESIZE_QVGA` → 320x240
- `FRAMESIZE_VGA` → 640x480 (Default)
- `FRAMESIZE_SVGA` → 800x600
- `FRAMESIZE_XGA` → 1024x768

### JPEG Quality
```cpp
config.jpeg_quality = 10;  // 0-63 (lower = higher quality)
```

### Brightness/Contrast
```cpp
s->set_brightness(s, 0);      // -2 to 2
s->set_contrast(s, 1);        // -2 to 2
s->set_saturation(s, 0);      // -2 to 2
```

---

## API Endpoints

### Stream Endpoints

**MJPEG Continuous Stream**
```
http://192.168.1.100:80/stream
```
- Returns continuous MJPEG video
- Best for real-time viewing

**JPEG Single Capture**
```
http://192.168.1.100:80/capture
```
- Returns single JPEG frame
- Good for snapshots or low-bandwidth

**Camera Status**
```
http://192.168.1.100:80/status
```
- Returns JSON with camera stats
- Example response:
  ```json
  {
    "status": "ok",
    "device_id": "esp32-cam-agrix-001",
    "ip_address": "192.168.1.100",
    "rssi": -45,
    "fps": 30,
    "frame_count": 1523
  }
  ```

---

## Integration with AGRIX

### Dashboard Features
- ✅ Automatic status detection
- ✅ Real-time FPS display
- ✅ Video snapshot capture
- ✅ Recording capability
- ✅ Resolution display
- ✅ Timestamp sync

### Firebase Integration (Optional)
The code automatically sends status updates to Firebase every 30 seconds:
- Online/offline status
- FPS and frame count
- Current timestamp
- Device IP address

To enable, set your Firebase credentials in the code.

---

## Safety & Best Practices

### Network Security
- Use unique passwords for WiFi
- Keep WiFi password protected
- Consider using static IP for reliability
- Test on isolated network first

### Hardware Care
- Don't touch camera lens
- Avoid direct sunlight on lens for extended periods
- Use proper power supply (avoid USB port as sole power)
- Keep ESP32-CAM in well-ventilated area

### Performance
- Don't use MJPEG at max resolution on slow WiFi
- Use JPEG snapshot for battery-powered applications
- Monitor temperature if running 24/7
- Consider adding heatsink for continuous operation

---

## Next Steps

1. **Integrate with Sensors** (Optional)
   - Use same WiFi network as sensor ESP32
   - Send crop analysis data alongside video

2. **Remote Access** (Advanced)
   - Use ngrok or similar service for remote access
   - Set up VPN for secure connection

3. **Cloud Integration** (Advanced)
   - Send video snapshots to Firebase Storage
   - Archive frames periodically

4. **AI Integration** (Advanced)
   - Send frames to cloud AI for analysis
   - Real-time crop health monitoring

---

## Support Resources

- **ESP32-CAM Documentation**: https://github.com/espressif/esp32-camera
- **Arduino IDE Help**: https://support.arduino.cc/
- **AGRIX Dashboard**: See dashboard documentation
- **Firebase Setup**: https://firebase.google.com/docs/realtime-database

---

## FAQ

**Q: Can I use this with other ESP32 boards?**
A: Yes, but you need to adjust pin configurations. See ESP32_WEBCAM_CODE.ino for pin definitions.

**Q: What if I don't have an OV2640 camera?**
A: This code is specifically for OV2640. Other camera modules need different libraries.

**Q: Can I access the video feed from outside my home network?**
A: Yes, but requires port forwarding or VPN setup (advanced).

**Q: Is the video stream encrypted?**
A: By default, no. For security, place behind authentication proxy.

**Q: How much bandwidth does MJPEG use?**
A: Approximately 1-2 Mbps at 30 FPS and 640x480 resolution.

**Q: Can I record video permanently?**
A: Yes, if ESP32-CAM has microSD card, code can be modified to save frames.

---

Last Updated: May 2026
AGRIX System v1.0
