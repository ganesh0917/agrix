const functions = require('firebase-functions');
const admin = require('firebase-admin');
const twilio = require('twilio');

// Initialize Firebase Admin SDK
admin.initializeApp();
const db = admin.firestore();
const database = admin.database();  // Realtime Database reference

// Twilio credentials - Use Firebase environment variables for production
// Set these in Firebase Console: Functions > Runtime environment variables
const TWILIO_ACCOUNT_SID = process.env.TWILIO_ACCOUNT_SID || 'YOUR_ACCOUNT_SID';
const TWILIO_AUTH_TOKEN = process.env.TWILIO_AUTH_TOKEN || 'YOUR_AUTH_TOKEN';
const MESSAGING_SERVICE_SID = process.env.TWILIO_MESSAGING_SID || 'YOUR_MESSAGING_SERVICE_SID';

// Initialize Twilio client
const twilioClient = twilio(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN);

/**
 * Cloud Function to send SMS alerts
 * Triggered from frontend after crop analysis
 */
exports.sendSMS = functions.https.onCall(async (data, context) => {
    try {
        // Verify user is authenticated
        if (!context.auth) {
            throw new functions.https.HttpsError(
                'unauthenticated',
                'User must be logged in to send SMS'
            );
        }

        // Extract phone and message from request
        const { phoneNumber, message } = data;

        // Validate inputs
        if (!phoneNumber) {
            throw new functions.https.HttpsError(
                'invalid-argument',
                'Phone number is required'
            );
        }

        if (!message) {
            throw new functions.https.HttpsError(
                'invalid-argument',
                'Message is required'
            );
        }

        console.log(`Sending SMS to ${phoneNumber}`);

        // Send SMS through Twilio
        const smsResult = await twilioClient.messages.create({
            messagingServiceSid: MESSAGING_SERVICE_SID,
            body: message,
            to: phoneNumber
        });

        console.log(`SMS sent successfully. Message SID: ${smsResult.sid}`);

        // Return success response
        return {
            success: true,
            messageId: smsResult.sid,
            status: 'SMS sent successfully',
            timestamp: new Date().toISOString()
        };

    } catch (error) {
        console.error('Error sending SMS:', error.message);
        
        // Handle specific Twilio errors
        if (error.code === 21211) {
            throw new functions.https.HttpsError(
                'invalid-argument',
                'Invalid phone number format'
            );
        }

        throw new functions.https.HttpsError(
            'internal',
            `Failed to send SMS: ${error.message}`
        );
    }
});

/**
 * Optional: Trigger SMS on complex analysis conditions
 * This can be extended for more sophisticated automation
 */
exports.sendVentilationAlert = functions.https.onCall(async (data, context) => {
    try {
        if (!context.auth) {
            throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
        }

        const { phoneNumber, ventilationStatus } = data;

        if (!phoneNumber) {
            throw new functions.https.HttpsError('invalid-argument', 'Phone number required');
        }

        let message = '';
        
        if (ventilationStatus === 'good') {
            message = '✅ Ventilation process is good and running successfully';
        } else if (ventilationStatus === 'warning') {
            message = '⚠️ Ventilation process needs attention - check your system';
        } else if (ventilationStatus === 'critical') {
            message = '🔴 Critical: Ventilation system failure detected - immediate action needed';
        } else {
            message = 'Ventilation status update available - check your AGRIX dashboard';
        }

        const result = await twilioClient.messages.create({
            messagingServiceSid: MESSAGING_SERVICE_SID,
            body: message,
            to: phoneNumber
        });

        return {
            success: true,
            messageId: result.sid,
            message: message
        };

    } catch (error) {
        console.error('Ventilation alert error:', error);
        throw new functions.https.HttpsError('internal', error.message);
    }
});

/**
 * Cloud Function to send preservation warning SMS
 * Sends alert about stored food getting rotten
 */
exports.sendWarningsSMS = functions.https.onCall(async (data, context) => {
    try {
        // Verify user is authenticated
        if (!context.auth) {
            throw new functions.https.HttpsError(
                'unauthenticated',
                'User must be logged in to send warnings'
            );
        }

        const { phoneNumber, message } = data;

        // Validate phone number
        if (!phoneNumber) {
            throw new functions.https.HttpsError(
                'invalid-argument',
                'Phone number is required'
            );
        }

        // Validate message
        if (!message) {
            throw new functions.https.HttpsError(
                'invalid-argument',
                'Message is required'
            );
        }

        console.log(`📱 Sending warning SMS to ${phoneNumber}`);

        // Send SMS through Twilio
        const smsResult = await twilioClient.messages.create({
            messagingServiceSid: MESSAGING_SERVICE_SID,
            body: message,
            to: phoneNumber
        });

        console.log(`✅ Warning SMS sent successfully. Message SID: ${smsResult.sid}`);

        // Store warning log in Firestore for record-keeping
        await db.collection('warning_logs').add({
            phoneNumber: phoneNumber,
            message: message,
            messageSid: smsResult.sid,
            timestamp: admin.firestore.FieldValue.serverTimestamp(),
            userId: context.auth.uid,
            status: 'sent'
        });

        return {
            success: true,
            messageId: smsResult.sid,
            status: 'SMS warning sent successfully',
            recipientNumber: phoneNumber,
            timestamp: new Date().toISOString()
        };

    } catch (error) {
        console.error('Error sending warning SMS:', error.message);
        
        // Handle specific Twilio errors
        if (error.code === 21211) {
            throw new functions.https.HttpsError(
                'invalid-argument',
                'Invalid phone number format. Please use format: +91XXXXXXXXXX'
            );
        }

        // Handle messaging service errors
        if (error.code === 21606) {
            throw new functions.https.HttpsError(
                'failed-precondition',
                'SMS service not available. Please contact support.'
            );
        }

        throw new functions.https.HttpsError(
            'internal',
            `Failed to send warning SMS: ${error.message}`
        );
    }
});

/**
 * ============================================
 * ESP32 SENSOR DATA INTEGRATION
 * ============================================
 */

/**
 * HTTP Function to receive sensor data from ESP32
 * POST /receiveSensorData
 * Body: { temperature, humidity, gas, deviceId, timestamp }
 */
exports.receiveSensorData = functions.https.onRequest(async (req, res) => {
    try {
        // Enable CORS
        res.set('Access-Control-Allow-Origin', '*');
        res.set('Access-Control-Allow-Methods', 'GET, POST');
        res.set('Access-Control-Allow-Headers', 'Content-Type');

        if (req.method === 'OPTIONS') {
            res.status(204).send('');
            return;
        }

        if (req.method !== 'POST') {
            return res.status(405).json({ error: 'Method not allowed' });
        }

        const { temperature, humidity, gas, deviceId } = req.body;

        // Validate required fields
        if (temperature === undefined || humidity === undefined || gas === undefined) {
            return res.status(400).json({ 
                error: 'Missing required fields: temperature, humidity, gas' 
            });
        }

        const timestamp = new Date();
        const sensorData = {
            temperature: parseFloat(temperature),
            humidity: parseFloat(humidity),
            gas: parseFloat(gas),
            deviceId: deviceId || 'esp32-001',
            timestamp: admin.firestore.Timestamp.fromDate(timestamp),
            receivedAt: timestamp.toISOString()
        };

        // Save to Firestore
        const docRef = await db.collection('sensor_data').add(sensorData);

        // Update latest sensor data document in Firestore
        await db.collection('sensor_data').doc('latest').set(sensorData);

        // Store in time-series collection for analytics
        const dateStr = timestamp.toISOString().split('T')[0];
        await db.collection(`sensor_data_${dateStr}`).add(sensorData);

        // IMPORTANT: Update Realtime Database for real-time dashboard updates
        const realtimeData = {
            temperature: parseFloat(temperature),
            humidity: parseFloat(humidity),
            gas: parseFloat(gas),
            deviceId: deviceId || 'esp32-001',
            timestamp: timestamp.toISOString()
        };

        // Write to Realtime Database at 'sensor' path
        await database.ref('sensor').set(realtimeData);
        
        // Also maintain a history of sensor readings
        await database.ref(`sensor_history/${timestamp.getTime()}`).set(realtimeData);

        console.log(`✅ Sensor data received and stored: Temp=${temperature}°C, Humidity=${humidity}%, Gas=${gas}ppm`);

        return res.status(200).json({
            success: true,
            message: 'Sensor data received successfully',
            docId: docRef.id,
            data: sensorData
        });

    } catch (error) {
        console.error('❌ Error receiving sensor data:', error);
        return res.status(500).json({ 
            error: 'Failed to process sensor data',
            details: error.message 
        });
    }
});

/**
 * Callable function to get latest sensor data
 * Called from frontend
 */
exports.getLatestSensorData = functions.https.onCall(async (data, context) => {
    try {
        const doc = await db.collection('sensor_data').doc('latest').get();

        if (!doc.exists) {
            return {
                success: true,
                data: null,
                message: 'No sensor data available yet'
            };
        }

        const sensorData = doc.data();
        return {
            success: true,
            data: {
                temperature: sensorData.temperature,
                humidity: sensorData.humidity,
                gas: sensorData.gas,
                deviceId: sensorData.deviceId,
                timestamp: sensorData.timestamp.toDate().toISOString()
            }
        };

    } catch (error) {
        console.error('Error fetching sensor data:', error);
        throw new functions.https.HttpsError('internal', error.message);
    }
});

/**
 * Callable function to get historical sensor data
 * Called from frontend for graphs
 */
exports.getSensorDataHistory = functions.https.onCall(async (data, context) => {
    try {
        const { limit = 50, hoursBack = 24 } = data;

        const cutoffTime = new Date(Date.now() - hoursBack * 60 * 60 * 1000);

        const snapshot = await db.collection('sensor_data')
            .where('timestamp', '>=', admin.firestore.Timestamp.fromDate(cutoffTime))
            .orderBy('timestamp', 'desc')
            .limit(limit)
            .get();

        const history = [];
        snapshot.forEach(doc => {
            const data = doc.data();
            history.push({
                id: doc.id,
                temperature: data.temperature,
                humidity: data.humidity,
                gas: data.gas,
                timestamp: data.timestamp.toDate().toISOString()
            });
        });

        return {
            success: true,
            data: history.reverse()
        };

    } catch (error) {
        console.error('Error fetching sensor history:', error);
        throw new functions.https.HttpsError('internal', error.message);
    }
});

/**
 * Scheduled function to check sensor anomalies every 5 minutes
 */
exports.checkSensorAnomalies = functions.pubsub
    .schedule('every 5 minutes')
    .onRun(async (context) => {
        try {
            const doc = await db.collection('sensor_data').doc('latest').get();

            if (!doc.exists) {
                console.log('No sensor data available for anomaly check');
                return;
            }

            const data = doc.data();
            const { temperature, humidity, gas } = data;

            // Define acceptable ranges
            const ranges = {
                temperature: { min: 10, max: 35 },
                humidity: { min: 20, max: 90 },
                gas: { min: 0, max: 500 }
            };

            const anomalies = [];

            if (temperature < ranges.temperature.min || temperature > ranges.temperature.max) {
                anomalies.push(`Temperature out of range: ${temperature}°C`);
            }

            if (humidity < ranges.humidity.min || humidity > ranges.humidity.max) {
                anomalies.push(`Humidity out of range: ${humidity}%`);
            }

            if (gas < ranges.gas.min || gas > ranges.gas.max) {
                anomalies.push(`Gas level out of range: ${gas}ppm`);
            }

            if (anomalies.length > 0) {
                console.warn('Sensor anomalies detected:', anomalies);
                
                // Store anomaly alert
                await db.collection('anomaly_alerts').add({
                    anomalies: anomalies,
                    sensorData: {
                        temperature,
                        humidity,
                        gas
                    },
                    timestamp: admin.firestore.Timestamp.now(),
                    status: 'unread'
                });
            }

            return null;

        } catch (error) {
            console.error('Error in anomaly check:', error);
        }
    });
