# AGRIX Twilio SMS Integration Guide

## ✅ Setup Complete!

Your AGRIX agricultural dashboard now includes SMS alert functionality to send analysis notifications via Twilio.

---

## 📋 What Was Configured

### **Frontend Updates** (`dashboard.html`)
1. **Phone Number Management**
   - Input field in Settings modal to save phone number
   - Phone stored in localStorage for persistence
   - Saves as `agrix_phone` key

2. **SMS Toggle**
   - Checkbox to enable/disable SMS notifications
   - Auto-loads saved phone number on page load

3. **Auto SMS Alerts**
   - Automatically sends SMS when crop analysis completes
   - Message: *"Ventilation process is good and running successfully"*
   - Can customize message in code if needed

4. **Visual Notifications**
   - Shows toast notification when SMS is sent
   - Graceful error handling if SMS feature not configured

### **Backend Setup** (`functions/`)
- Firebase Cloud Function: `sendSMS`
- Callable from frontend with phone number and message
- Secure credential handling
- Error management and logging

---

## 🚀 Deploy to Firebase

### **Step 1: Install Dependencies**
```bash
cd c:\Users\GANESHRAM\Desktop\agrix\functions
npm install
```

### **Step 2: Configure Firebase Project**
If you haven't already, set up Firebase CLI:
```bash
npm install -g firebase-tools
firebase login
firebase init
```

### **Step 3: Deploy Cloud Functions**
```bash
cd c:\Users\GANESHRAM\Desktop\agrix
firebase deploy --only functions
```

After deployment, you'll see the function URL:
```
✓  deployed to Cloud Functions
Function URL (sendSMS): https://us-central1-your-project.cloudfunctions.net/sendSMS
```

---

## 💬 How It Works

### **User Flow:**
1. User logs into AGRIX dashboard
2. Opens **Settings** → **Notification Settings**
3. Enters phone number (e.g., `+8072766784`)
4. Checks ✓ "SMS Alerts" to enable
5. Clicks **Save Phone**
6. Uploads crop image in **Reports & Analysis**
7. Clicks **Generate Analysis Report**
8. Analysis completes → **SMS sent automatically!**

### **SMS Message Example:**
```
✅ Ventilation process is good and running successfully

Timestamp: [Date and Time]
AGRIX Crop Analysis
```

---

## ⚙️ Configuration

### **Twilio Credentials** (Set in Firebase Functions)
```javascript
Note: Credentials are stored as Firebase Cloud Function environment variables
for security. Never commit credentials to version control.

To set up:
1. Go to Firebase Console > Functions
2. Set environment variables in .env.local
3. Deploy with: firebase deploy --only functions
```

### **Default Phone Number**
```
8072766784
```

### **Customize SMS Message**
Edit `dashboard.html`, line ~1920:
```javascript
// Change this message to customize
await sendAnalysisAlertSMS(null, 'Your custom message here');
```

---

## 🔐 Security Best Practices

✅ **What We Did Right:**
- Credentials stored in Cloud Function (NOT exposed in frontend code)
- Firebase authentication required for SMS sending
- Phone number stored in user's browser (localStorage)
- Error messages don't expose sensitive info

✅ **Additional Recommendations:**
- Store Twilio credentials in Firebase Environment Variables:
  ```bash
  firebase functions:config:set twilio.account_sid="YOUR_SID" twilio.auth_token="YOUR_TOKEN"
  ```
- Use Twilio API Keys instead of Auth Token in production
- Implement rate limiting if SMS usage increases
- Log all SMS activity for audit trail

---

## 📞 Available Functions

### **1. sendSMS** (Main Function)
Sends SMS to any phone number
```javascript
const functions = firebase.functions();
const sendSMS = functions.httpsCallable('sendSMS');

await sendSMS({
    phoneNumber: '+1234567890',
    message: 'Your custom message'
});
```

### **2. sendVentilationAlert** (Extended)
Sends status-specific ventilation alerts
```javascript
await sendVentilationAlert({
    phoneNumber: '+1234567890',
    ventilationStatus: 'good' | 'warning' | 'critical'
});
```

Responses:
- ✅ good: "Ventilation process is good and running successfully"
- ⚠️ warning: "Ventilation process needs attention"
- 🔴 critical: "Critical: Ventilation system failure detected"

---

## 🧪 Testing

### **Local Testing:**
```bash
firebase emulators:start --only functions
# Use emulator in dashboard.html for testing
```

### **Manual Test**
1. Click **Settings** → Enter phone → Save
2. Go to **Reports & Analysis**
3. Upload any crop image
4. Click **Generate Analysis Report**
5. Check your phone for SMS! 📱

---

## ❌ Troubleshooting

| Problem | Solution |
|---------|----------|
| SMS not sending | Check if "SMS Alerts" checkbox is enabled in Settings |
| Phone number not saved | Enter valid format (digits, +, or -) with 10+ digits |
| Firebase error | Run `firebase deploy --only functions` |
| Twilio error | Check phone number is valid (include country code) |
| No notification shown | Check browser console for errors (F12 > Console) |

---

## 📊 Integration Points

| Component | Location | Purpose |
|-----------|----------|---------|
| Phone Input | dashboard.html Settings | Store user phone |
| SMS Checkbox | dashboard.html Settings | Enable/disable alerts |
| Send Trigger | generateReport() function | Auto-sends after analysis |
| Functions | functions/index.js | Cloud backend |
| Config | functions/package.json | Dependencies |

---

## 📌 Important Notes

- SMS costs ~$0.0075 per message (on Twilio free tier)
- Phone number is stored locally (not sent to servers unless SMS enabled)
- Firebase authentication is required to deploy functions
- Twilio service must be active and funded

---

## 🎯 Next Steps

1. ✅ Deploy Cloud Functions: `firebase deploy --only functions`
2. ✅ Test SMS by generating a report
3. ✅ Customize message in `generateReport()` if needed
4. ✅ Save phone number in Settings modal

---

## 📞 Support

For Twilio issues: https://www.twilio.com/console
For Firebase issues: https://console.firebase.google.com

Enjoy your SMS-enabled AGRIX dashboard! 🚀
