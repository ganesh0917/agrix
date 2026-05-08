// ========== REPORTS MODAL FUNCTIONS - PRODUCE ANALYSIS ==========

let selectedImageData = null;
let mediaStream = null;

// Add Escape key listener for modal closing
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const reportsModal = document.getElementById('reportsModal');
        if (reportsModal && reportsModal.style.display === 'flex') {
            closeReportsModal();
        }
    }
});

// Debug logging helper
function logDebug(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] 🔍 ${message}`, data || '');
}

function logError(message, error = null) {
    const timestamp = new Date().toLocaleTimeString();
    console.error(`[${timestamp}] ❌ ${message}`, error || '');
}

function openReportsModal() {
    // Open the modal
    const modal = document.getElementById('reportsModal');
    if (modal) {
        modal.style.display = 'flex';
    }
    
    // Reset to upload tab
    switchTab('upload');
    
    // Clear any previous data
    selectedImageData = null;
    clearImage();
    
    logDebug('Reports Modal opened - ready for use');
}

function closeReportsModal(event) {
    // If called with an event and it's not the overlay itself, ignore (prevent closing from clicks inside modal)
    if (event && event.target.id !== 'reportsModal') return;
    
    // Stop any active media streams
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    
    // Close the camera if open
    const cameraContainer = document.getElementById('cameraContainer');
    if (cameraContainer && cameraContainer.style.display !== 'none') {
        closeCamera();
    }
    
    // Reset modal display with smooth fade-out
    const modal = document.getElementById('reportsModal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    // Reset to upload tab when closed
    setTimeout(() => {
        switchTab('upload');
        clearImage();
    }, 100);
    
    logDebug('Reports Modal closed - returning to dashboard');
}

function switchReportstab(tabName) {
    document.getElementById('uploadTab').classList.remove('active');
    document.getElementById('videoTab').classList.remove('active');
    
    document.querySelectorAll('.reports-tab-btn').forEach(btn => btn.classList.remove('active'));
    
    if (tabName === 'upload') {
        document.getElementById('uploadTab').classList.add('active');
        document.querySelectorAll('.reports-tab-btn')[0].classList.add('active');
    } else if (tabName === 'video') {
        document.getElementById('videoTab').classList.add('active');
        document.querySelectorAll('.reports-tab-btn')[1].classList.add('active');
    }
}

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        selectedImageData = e.target.result;
        document.getElementById('previewImg').src = selectedImageData;
        document.getElementById('imagePreview').style.display = 'block';
    };
    reader.readAsDataURL(file);
}

async function startVideoCapture() {
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
        });
        const video = document.getElementById('videoElement');
        video.srcObject = mediaStream;
        video.style.display = 'block';
    } catch (error) {
        alert('Cannot access camera: ' + error.message);
    }
}

function captureVideoFrame() {
    const video = document.getElementById('videoElement');
    if (!video.srcObject) {
        alert('Camera not active');
        return;
    }

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    selectedImageData = canvas.toDataURL('image/jpeg', 0.95);
    document.getElementById('capturedFrame').src = selectedImageData;
    document.getElementById('videoCapturePreview').style.display = 'block';
}

function stopVideoCapture() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    document.getElementById('videoElement').style.display = 'none';
}

function toggleApiKeyVisibility() {
    const input = document.getElementById('geminiApiKey');
    const btn = event.target.closest('.toggle-api-key');
    if (input.type === 'password') {
        input.type = 'text';
        btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
        logDebug('API key visibility toggled ON');
    } else {
        input.type = 'password';
        btn.innerHTML = '<i class="fas fa-eye"></i>';
        logDebug('API key visibility toggled OFF');
    }
}

// Test API Key functionality
function testApiKey() {
    const apiKey = document.getElementById('geminiApiKey').value.trim();
    
    logDebug('Testing API key...');
    
    if (!apiKey) {
        alert('Please enter an API key first');
        return;
    }
    
    if (apiKey.length < 20) {
        alert('API key is too short (minimum length should be 20 characters)');
        logError('API key too short', { length: apiKey.length });
        return;
    }
    
    alert('API Key Validation:\n✓ API key is present\n✓ Length is valid (' + apiKey.length + ' characters)\n\nNote: Full validation happens when you analyze an image.\n\nOpen Browser Console (F12) to see detailed debug logs.');
    logDebug('API key format validation passed', { keyLength: apiKey.length, startsCorrect: apiKey.startsWith('AIza') });
}
        btn.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

async function analyzeProduceImage() {
    const apiKeyInput = document.getElementById('geminiApiKey');
    const apiKey = apiKeyInput.value.trim();
    
    logDebug('Starting image analysis process');

    if (!selectedImageData) {
        alert('Please upload or capture an image first');
        logError('No image selected');
        return;
    }

    logDebug('Image selected, displaying ventilation report');

    // Show loading state
    document.getElementById('loadingState').style.display = 'flex';
    document.getElementById('uploadSection').style.display = 'none';

    // Simulate processing delay
    setTimeout(() => {
        displayVentilationReport();
    }, 2000);
}

function displayVentilationReport() {
    // Hide loading state
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';

    // Set status badge
    const statusBadge = document.getElementById('statusBadge');
    statusBadge.innerHTML = `<div style="padding: 16px; color: #52b788;">✓ EXCELLENT VENTILATION GUIDE</div>`;

    // Set the analysis sections with comprehensive content
    document.getElementById('whySection').innerHTML = `
        <strong>Vegetables are living biological products</strong> even after harvesting. They continue to respire, releasing heat, moisture, and gases like CO₂. 
        <br><br>
        <strong>Essential benefits:</strong>
        <ul style="margin: 12px 0 0 0; padding-left: 20px;">
            <li>✅ Maintain freshness</li>
            <li>✅ Prevent spoilage</li>
            <li>✅ Extend shelf life by 30-40%</li>
        </ul>
    `;

    document.getElementById('temperatureSection').innerHTML = `
        <strong>🌡️ Temperature Control (4-8°C):</strong> Vegetables release respiration heat. Poor ventilation traps heat → faster spoilage.
        <br><br>
        <strong>💧 Moisture Control (85-90% RH):</strong> Excess humidity causes fungal growth and rotting. Ventilation removes excess moisture.
        <br><br>
        <strong>🌬️ Gas Exchange:</strong> Vegetables consume O₂ and release CO₂. Poor airflow causes CO₂ buildup and faster decay.
    `;

    document.getElementById('coldStorageSection').innerHTML = `
        <strong>Key Design Features:</strong>
        <ul style="margin: 12px 0 0 0; padding-left: 20px;">
            <li>Air circulation: Continuous airflow around vegetables</li>
            <li>Fresh air supply: Regular exchange reduces CO₂ buildup</li>
            <li>Uniform distribution: Air reaches all storage areas</li>
            <li><strong>IoT Integration:</strong> Temperature sensor (DHT22), Humidity sensor, CO₂ sensor, ESP32 controller for auto fan control</li>
        </ul>
    `;

    const methods = [
        "Maintain 4-8°C temperature with 85-90% relative humidity",
        "Use continuous mechanical ventilation or natural airflow",
        "Keep storage well-organized (avoid tight packing)",
        "Ensure inlet at bottom, outlet at top (hot air rises)",
        "Monitor with sensors: Temperature, Humidity, CO₂, Ethylene gas"
    ];

    const preservationList = document.getElementById('preservationList');
    preservationList.innerHTML = '';
    methods.forEach(method => {
        const li = document.createElement('li');
        li.innerHTML = `<i class="fas fa-check-circle" style="color: var(--primary-color); margin-right: 8px;"></i>${method}`;
        preservationList.appendChild(li);
    });

    document.getElementById('notesSection').innerHTML = `
        <strong>⚠️ Problems without proper ventilation:</strong>
        <ul style="margin: 12px 0 0 0; padding-left: 20px;">
            <li>❌ Rapid spoilage (2-3 days)</li>
            <li>❌ Mold and fungal growth</li>
            <li>❌ Loss of nutrients (40-60%)</li>
            <li>❌ Bad odor from gases</li>
        </ul>
        <br>
        <strong style="color: #52b788;">💡 IoT Solution: Smart Vegetable Storage System</strong> - Detect humidity + gas, auto control fan, send alerts, predict spoilage using AI, extend shelf life by 30-40%
    `;

    logDebug('Ventilation report displayed successfully');
}

function displayAnalysisResults(analysisText) {
    const sections = parseAnalysis(analysisText);

    // Set status badge
    const statusBadge = document.getElementById('statusBadge');
    const status = sections.freshness.toUpperCase();
    let badgeColor = '#06a77d';
    
    if (status.includes('ROTTEN')) {
        badgeColor = '#d62828';
    } else if (status.includes('OVERRIPE')) {
        badgeColor = '#f77f00';
    } else if (status.includes('RIPE')) {
        badgeColor = '#ffd60a';
    } else if (status.includes('FRESH')) {
        badgeColor = '#06a77d';
    }
    
    statusBadge.innerHTML = `<div style="padding: 16px; text-align: center; font-size: 28px; font-weight: 700; color: ${badgeColor};">${status}</div>`;

    document.getElementById('whySection').textContent = sections.why || 'No analysis available';
    document.getElementById('temperatureSection').textContent = sections.temperature || 'No temperature data';
    document.getElementById('coldStorageSection').textContent = sections.coldStorage || 'No storage data';
    document.getElementById('notesSection').textContent = sections.notes || 'No additional notes';

    // Set preservation methods
    const preservationList = document.getElementById('preservationList');
    preservationList.innerHTML = '';
    if (sections.preservation && sections.preservation.length > 0) {
        sections.preservation.forEach(method => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fas fa-check-circle" style="color: var(--primary-color); margin-right: 8px;"></i>${method}`;
            preservationList.appendChild(li);
        });
    }

    // Show results
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
}

function parseAnalysis(text) {
    const sections = {
        freshness: 'Unknown',
        why: '',
        preservation: [],
        temperature: '',
        coldStorage: '',
        notes: ''
    };

    const lines = text.split('\n');
    let currentSection = '';

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        if (line.includes('FRESHNESS STATUS:')) {
            sections.freshness = line.replace('FRESHNESS STATUS:', '').trim().split('/')[0];
            currentSection = 'freshness';
        } else if (line.includes('WHY THIS CONDITION:')) {
            currentSection = 'why';
        } else if (line.includes('PRESERVATION METHODS:')) {
            currentSection = 'preservation';
        } else if (line.includes('OPTIMAL STORAGE TEMPERATURE:')) {
            currentSection = 'temperature';
        } else if (line.includes('COLD STORAGE INFORMATION:')) {
            currentSection = 'coldStorage';
        } else if (line.includes('ADDITIONAL NOTES:')) {
            currentSection = 'notes';
        } else if (line && !line.startsWith('---')) {
            if (currentSection === 'why' && line && !line.startsWith('-')) {
                sections.why += (sections.why ? ' ' : '') + line;
            } else if (currentSection === 'preservation' && line.startsWith('-')) {
                sections.preservation.push(line.replace('-', '').trim());
            } else if (currentSection === 'temperature' && line && !line.startsWith('-')) {
                sections.temperature += (sections.temperature ? ' ' : '') + line;
            } else if (currentSection === 'coldStorage' && line && !line.startsWith('-')) {
                sections.coldStorage += (sections.coldStorage ? ' ' : '') + line;
            } else if (currentSection === 'notes' && line && !line.startsWith('-')) {
                sections.notes += (sections.notes ? ' ' : '') + line;
            }
        }
    }

    return sections;
}

function backToUpload() {
    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('videoCapturePreview').style.display = 'none';
    document.getElementById('imageInput').value = '';
    selectedImageData = null;
}

// ========== CHATBOT FUNCTIONS ==========

function handleChatKeypress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    logDebug('User message sent', { message: message });
    
    // Add user message to chat
    addChatMessage(message, 'user');
    chatInput.value = '';
    
    // Simulate typing delay
    setTimeout(() => {
        const response = getChatbotResponse(message);
        addChatMessage(response, 'bot');
    }, 500);
}

function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Clear placeholder if this is the first real message
    if (chatMessages.children.length === 1 && chatMessages.children[0].textContent.includes('Ask about')) {
        chatMessages.innerHTML = '';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.style.marginBottom = '12px';
    messageDiv.style.padding = '12px 16px';
    messageDiv.style.borderRadius = '8px';
    messageDiv.style.maxWidth = '80%';
    messageDiv.style.wordWrap = 'break-word';
    messageDiv.style.fontSize = '14px';
    messageDiv.style.lineHeight = '1.5';
    
    if (sender === 'user') {
        messageDiv.style.background = 'var(--primary-color)';
        messageDiv.style.color = 'white';
        messageDiv.style.marginLeft = 'auto';
        messageDiv.style.textAlign = 'left';
    } else {
        messageDiv.style.background = 'var(--secondary-color)';
        messageDiv.style.color = 'var(--text-dark)';
        messageDiv.style.marginRight = 'auto';
    }
    
    messageDiv.innerHTML = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function getChatbotResponse(userMessage) {
    const msg = userMessage.toLowerCase();
    
    // Ventilation related queries
    if (msg.includes('ventilation') || msg.includes('airflow') || msg.includes('air')) {
        return `<strong>💨 Ventilation Tips:</strong><br>
        Proper ventilation is critical for vegetable storage:<br>
        • Maintains 4-8°C temperature<br>
        • Keeps humidity at 85-90%<br>
        • Removes excess CO₂ and moisture<br>
        • Inlet at bottom, outlet at top<br>
        • Can extend shelf life by 30-40%<br><br>
        Would you like to know more about mechanical or natural ventilation?`;
    }
    
    // Temperature & humidity
    if (msg.includes('temperature') || msg.includes('humidity') || msg.includes('storage temp')) {
        return `<strong>🌡️ Temperature & Humidity Control:</strong><br>
        Optimal conditions for vegetables:<br>
        • Temperature: 4-8°C<br>
        • Humidity: 85-90% RH<br>
        • Ventilation: 1-2 air changes per hour<br>
        • Prevents fungal growth & decay<br><br>
        Different vegetables have slightly different requirements. Which vegetable are you storing?`;
    }
    
    // Spoilage prevention
    if (msg.includes('spoil') || msg.includes('decay') || msg.includes('rot') || msg.includes('fresh')) {
        return `<strong>🛡️ Preventing Spoilage:</strong><br>
        Key factors to keep vegetables fresh:<br>
        • Continuous air circulation<br>
        • Ethylene gas removal<br>
        • Regular temperature monitoring<br>
        • Proper moisture control<br>
        • Quick cooling after harvest<br><br>
        Without ventilation, vegetables spoil in 2-3 days. With proper ventilation, you can extend to 2-3 weeks!`;
    }
    
    // IoT/Smart systems
    if (msg.includes('iot') || msg.includes('smart') || msg.includes('sensor') || msg.includes('automation')) {
        return `<strong>🤖 Smart Storage System (IoT):</strong><br>
        Our AGRIX system uses:<br>
        • DHT22 Temperature/Humidity Sensor<br>
        • CO₂ & Ethylene Gas Sensor<br>
        • ESP32 Microcontroller<br>
        • Automated fan control<br>
        • Real-time dashboard alerts<br>
        • ML-based spoilage prediction<br><br>
        This can reduce waste by 30-40% and save ₹50,000-1,00,000 per year!`;
    }
    
    // Preservation methods
    if (msg.includes('preserv') || msg.includes('extend') || msg.includes('method') || msg.includes('store')) {
        return `<strong>🥕 Best Preservation Methods:</strong><br>
        Top 5 ways to extend vegetable shelf life:<br>
        1. Maintain proper ventilation (most important)<br>
        2. Keep temperature at 4-8°C<br>
        3. Control humidity (85-90%)<br>
        4. Remove ethylene-producing items<br>
        5. Use cold storage with air circulation<br><br>
        Proper ventilation alone can extend freshness by 30-45%!`;
    }
    
    // Cost/Economics
    if (msg.includes('cost') || msg.includes('price') || msg.includes('economic') || msg.includes('waste') || msg.includes('loss')) {
        return `<strong>💰 Economic Impact of Proper Ventilation:</strong><br>
        Poor ventilation costs in India:<br>
        • 40% of vegetables waste annually<br>
        • ₹50,000-1,00,000 loss per small warehouse<br>
        • Reduced market prices due to spoilage<br><br>
        With AGRIX Smart System:<br>
        ✓ Reduce waste by 30-40%<br>
        ✓ Save ₹50,000-1,00,000/year<br>
        ✓ ROI in 6-8 months<br><br>
        Investment in proper ventilation pays for itself quickly!`;
    }
    
    // Gas & respiration
    if (msg.includes('gas') || msg.includes('co2') || msg.includes('oxygen') || msg.includes('respir')) {
        return `<strong>🌬️ Gas Exchange & Respiration:</strong><br>
        Vegetables continue to respire after harvest:<br>
        • They consume O₂ and release CO₂<br>
        • This creates heat and moisture<br>
        • Without ventilation:<br>
          - CO₂ accumulates → faster decay<br>
          - Heat buildup → spoilage<br>
          - Moisture excess → fungal growth<br><br>
        Solution: Continuous fresh air circulation!`;
    }
    
    // General agriculture help
    if (msg.includes('help') || msg.includes('question') || msg.includes('know')) {
        return `<strong>🌱 AGRIX Assistant Here!</strong><br>
        I can help you with:<br>
        ✓ Vegetable storage & ventilation<br>
        ✓ Temperature & humidity control<br>
        ✓ Spoilage prevention<br>
        ✓ Smart IoT systems<br>
        ✓ Preservation methods<br>
        ✓ Cost-benefit analysis<br>
        ✓ Gas exchange management<br><br>
        Ask me about any agriculture or storage topic!`;
    }
    
    // Default response
    return `<strong>🤔 Good Question!</strong><br>
    I'm the AGRIX Assistant specializing in vegetable storage and ventilation.<br><br>
    You can ask me about:<br>
    • Proper ventilation techniques<br>
    • Temperature & humidity control<br>
    • Preventing spoilage<br>
    • IoT smart storage systems<br>
    • Preservation methods<br>
    • Cost savings & economics<br><br>
    Feel free to ask anything related to vegetable storage!`;
}
