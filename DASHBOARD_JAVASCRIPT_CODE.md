# Dashboard JavaScript Code - Realtime Database Integration

## Copy this code and paste into dashboard.html

### Find and Replace the `fetchLatestSensorData()` function:

```javascript
// Real-time Sensor Data Listener
function fetchLatestSensorData() {
    try {
        console.log('🔴 Setting up real-time listener...');
        
        // Get Firebase Realtime Database reference
        const dbRef = firebase.database().ref('sensor');
        
        // Listen for changes in real-time
        dbRef.on('value', (snapshot) => {
            if (snapshot.exists()) {
                const data = snapshot.val();
                
                console.log('✅ Real-time Data Received:', {
                    temperature: data.temperature,
                    humidity: data.humidity,
                    gas: data.gas,
                    timestamp: new Date().toLocaleTimeString()
                });
                
                // Update dashboard display
                updateSensorDisplay({
                    temperature: data.temperature || 0,
                    humidity: data.humidity || 0,
                    gas: data.gas || 0
                });
            } else {
                console.warn('⚠️ No data in Firebase yet...');
            }
        }, (error) => {
            console.error('❌ Database read error:', error);
            // Show error state on dashboard
            updateSensorDisplayError();
        });
        
    } catch (error) {
        console.error('❌ Error setting up real-time listener:', error);
    }
}

// Stop real-time listener
function stopRealTimeListener() {
    try {
        const dbRef = firebase.database().ref('sensor');
        dbRef.off(); // Remove all listeners
        console.log('⏹️ Real-time listener stopped');
    } catch (error) {
        console.error('Error stopping listener:', error);
    }
}

// Update sensor display with data
function updateSensorDisplay(data) {
    const { temperature, humidity, gas } = data;

    // Update Temperature
    const tempElement = document.getElementById('tempValue');
    if (tempElement) {
        tempElement.textContent = temperature.toFixed(1) + '°C';
        
        // Update bar width (range 10-35°C)
        const tempPercent = Math.min(100, Math.max(0, ((temperature - 10) / (35 - 10)) * 100));
        const tempBar = document.getElementById('tempBar');
        if (tempBar) tempBar.style.width = tempPercent + '%';

        // Update status
        const tempStatus = document.getElementById('tempStatus');
        if (tempStatus) {
            if (temperature >= 20 && temperature <= 28) {
                tempStatus.textContent = 'Optimal';
                tempStatus.style.color = '#52b788';
            } else if (temperature >= 15 && temperature <= 32) {
                tempStatus.textContent = 'Normal';
                tempStatus.style.color = '#ffd60a';
            } else {
                tempStatus.textContent = 'Out of Range';
                tempStatus.style.color = '#ff6b6b';
            }
        }
    }

    // Update Humidity
    const humidityElement = document.getElementById('humidityValue');
    if (humidityElement) {
        humidityElement.textContent = humidity.toFixed(1) + '%';

        // Update bar width (range 20-90%)
        const humidityPercent = Math.min(100, Math.max(0, ((humidity - 20) / (90 - 20)) * 100));
        const humidityBar = document.getElementById('humidityBar');
        if (humidityBar) humidityBar.style.width = humidityPercent + '%';

        // Update status
        const humidityStatus = document.getElementById('humidityStatus');
        if (humidityStatus) {
            if (humidity >= 40 && humidity <= 70) {
                humidityStatus.textContent = 'Optimal';
                humidityStatus.style.color = '#52b788';
            } else if (humidity >= 30 && humidity <= 80) {
                humidityStatus.textContent = 'Normal';
                humidityStatus.style.color = '#ffd60a';
            } else {
                humidityStatus.textContent = 'Out of Range';
                humidityStatus.style.color = '#ff6b6b';
            }
        }
    }

    // Update Gas
    const gasElement = document.getElementById('gasValue');
    if (gasElement) {
        gasElement.textContent = gas.toFixed(1) + ' ppm';

        // Update bar width (range 0-500 ppm)
        const gasPercent = Math.min(100, (gas / 500) * 100);
        const gasBar = document.getElementById('gasBar');
        if (gasBar) gasBar.style.width = gasPercent + '%';

        // Update status
        const gasStatus = document.getElementById('gasStatus');
        if (gasStatus) {
            if (gas <= 100) {
                gasStatus.textContent = 'Safe';
                gasStatus.style.color = '#06a77d';
            } else if (gas <= 200) {
                gasStatus.textContent = 'Normal';
                gasStatus.style.color = '#52b788';
            } else if (gas <= 350) {
                gasStatus.textContent = 'Warning';
                gasStatus.style.color = '#ffd60a';
            } else {
                gasStatus.textContent = 'Critical';
                gasStatus.style.color = '#ff6b6b';
            }
        }
    }

    // Update system status
    updateSystemStatus(temperature, humidity, gas);
}

// Error state display
function updateSensorDisplayError() {
    const tempElement = document.getElementById('tempValue');
    const humidityElement = document.getElementById('humidityValue');
    const gasElement = document.getElementById('gasValue');
    
    if (tempElement) tempElement.textContent = '--°C';
    if (humidityElement) humidityElement.textContent = '--%';
    if (gasElement) gasElement.textContent = '-- ppm';
    
    console.log('Waiting for ESP32 data...');
}

// Update system status indicator
function updateSystemStatus(temp, humidity, gas) {
    const statusDiv = document.querySelector('[style*="background: linear-gradient(135deg, #52b788"]');
    if (!statusDiv) return;

    let isOptimal = 
        (temp >= 20 && temp <= 28) &&
        (humidity >= 40 && humidity <= 70) &&
        (gas <= 200);

    let statusText = '';
    let statusColor = '';

    if (isOptimal) {
        statusText = 'All Parameters Optimal ✓';
        statusColor = '#52b788';
    } else {
        statusText = 'Some Parameters in Warning Zone ⚠️';
        statusColor = '#ffd60a';
    }

    const content = statusDiv.innerHTML;
    if (content.includes('System Status:')) {
        statusDiv.style.background = `linear-gradient(135deg, ${statusColor} 0%, ${statusColor} 100%)`;
    }
}
```

---

## Update `startSensorDataRefresh()` function:

Replace this function:
```javascript
function startSensorDataRefresh() {
    if (sensorRefreshInterval) clearInterval(sensorRefreshInterval);
    sensorRefreshInterval = setInterval(fetchLatestSensorData, 5000);
}
```

With this:
```javascript
function startSensorDataRefresh() {
    // For Realtime Database, listener is set up in fetchLatestSensorData
    // Data updates automatically when ESP32 sends it
    console.log('📡 Real-time listener activated');
    fetchLatestSensorData();
}
```

---

## Update `stopSensorDataRefresh()` function:

Replace:
```javascript
function stopSensorDataRefresh() {
    if (sensorRefreshInterval) {
        clearInterval(sensorRefreshInterval);
        sensorRefreshInterval = null;
    }
}
```

With:
```javascript
function stopSensorDataRefresh() {
    // Stop real-time listener
    stopRealTimeListener();
}
```

---

## How to Add to dashboard.html:

1. **Open dashboard.html** in code editor
2. **Find** these functions (use Ctrl+F to search):
   - `fetchLatestSensorData`
   - `startSensorDataRefresh`
   - `stopSensorDataRefresh`
   - `updateSensorDisplay`
3. **Replace** each function with the code above
4. **Save** the file
5. **Refresh** browser to load updated code

---

## Firebase Configuration Required:

Make sure dashboard.html has Firebase Realtime Database config:

```javascript
// Firebase Configuration - Load from environment variables
const firebaseConfig = {
    apiKey: process.env.FIREBASE_API_KEY,
    authDomain: "agrix-3703d.firebaseapp.com",
    projectId: "agrix-3703d",
    storageBucket: "agrix-3703d.firebasestorage.app",
    messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.FIREBASE_APP_ID,
    measurementId: process.env.FIREBASE_MEASUREMENT_ID
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Add this line for Realtime Database
const database = firebase.database();
```

---

## Test the Integration:

1. **Upload ESP32 code** (follow ESP32_REALTIME_DB_COMPLETE_GUIDE.md)
2. **Update dashboard.html** with code above
3. **Open dashboard.html** in browser
4. **Click "View Vitals"** button
5. **Watch for real-time updates** (should update every 10 seconds)
6. **Check browser console** (F12) for debug messages

---

## What You Should See:

### In Browser Console:
```
📡 Setting up real-time listener...
✅ Real-time Data Received: {
    temperature: 24.5,
    humidity: 55.2,
    gas: 150.3,
    timestamp: "10:30:45 AM"
}
```

### On Dashboard:
- 🌡️ Temp: 24.5°C (Green - Optimal)
- 💧 Humidity: 55.2% (Green - Optimal)
- 💨 Gas: 150.3 ppm (Green - Normal)

Values update automatically without page refresh! 🎉

---

Ready to integrate? Let me know if you need help finding these functions in dashboard.html!
