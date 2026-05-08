# AGRIX Produce Analysis Feature

## Overview
The **Produce Analysis Report** feature enables users to upload images or capture video frames of agricultural produce and receive AI-powered analysis using Google's Gemini API.

## Features

### 1. **Image Upload**
- Click on the upload area or drag-and-drop an image
- Supported formats: PNG, JPG, GIF
- Maximum file size: 10MB
- Image preview shown before analysis

### 2. **Video Capture**
- Access device camera to capture real-time video
- Capture frames directly from the video feed
- Controls:
  - **Start Camera**: Activate your device's camera
  - **Capture**: Extract a single frame from the video
  - **Stop**: Deactivate the camera

### 3. **Gemini API Integration**
- Paste your Gemini API key (obtained from https://makersuite.google.com/app/apikey)
- API key is **never stored** - only used for the current analysis session
- Limited scope: API is restricted to produce analysis only

### 4. **AI-Powered Analysis**
The system analyzes produce images and provides:

- **Freshness Status**: Fresh / Ripe / Overripe / Rotten / Mixed
- **Why This Condition**: Detailed explanation of visible signs:
  - Color changes
  - Texture assessment
  - Decay indicators
  - Ripeness level
  
- **Best Preservation Methods** (up to 5 methods):
  - Specific storage techniques
  - Environmental controls
  - Handling recommendations
  - Best practices
  
- **Optimal Storage Temperature**:
  - Temperature range in Celsius
  - Humidity percentage
  - Environmental conditions
  
- **Cold Storage Information**:
  - Recommended storage duration
  - Humidity level maintenance
  - Ventilation requirements
  - Ethylene gas sensitivity
  - Shelf life expectations
  
- **Additional Notes**:
  - Handling tips
  - Spoilage warning signs
  - Maturity indicators
  - Special considerations

## How to Use

### Step 1: Open Reports Modal
1. Go to Dashboard
2. Click "View Reports" button in the Reports card
3. The "Produce Analysis Report" modal will appear

### Step 2: Provide Your Image
Choose one of two methods:

**Method A - Upload Image:**
- Click the upload area or drag-and-drop an image
- Preview will appear after selection
- Click "Analyze Produce with Gemini AI" to proceed

**Method B - Capture Video:**
- Switch to "Capture Video" tab
- Click "Start Camera" to activate your device camera
- Click "Capture" to extract a frame
- Click "Stop" to deactivate the camera
- Click "Analyze Produce with Gemini AI" to proceed

### Step 3: Enter API Key
1. Scroll to the "Gemini API Key" section
2. Get your free API key from: https://makersuite.google.com/app/apikey
3. Paste your API key in the input field
4. Click the eye icon to toggle visibility (optional)
5. **Important**: Your key is never saved - enter it each time

### Step 4: Analyze
1. Click "Analyze Produce with Gemini AI" button
2. Wait for the AI to process (takes a few seconds)
3. View the detailed analysis results
4. Click "Analyze Another Image" to perform another analysis

## Security & Privacy

✅ **Your API Key is Safe:**
- API keys are **NOT stored** on the server
- API keys are **NOT stored** in browser storage
- API keys are **NOT logged** anywhere
- Each analysis session requires manual key entry
- API scope is **limited to produce analysis only**

## Getting Your Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Paste it in the Produce Analysis modal
6. Ready to analyze!

## Supported Produce

The AI can analyze any agricultural produce including:
- Vegetables (tomatoes, peppers, lettuce, etc.)
- Fruits (apples, oranges, bananas, etc.)
- Leafy greens (spinach, kale, etc.)
- Root vegetables (potatoes, carrots, etc.)
- Melons and gourds
- Berries
- And many more!

## Analysis Quality

The accuracy of analysis depends on:
- Image clarity and lighting
- Angle of the produce
- Completeness of the view
- Resolution of the image
- Color representation
- Context (multiple angles better)

**Tip**: For best results:
- Use good natural lighting
- Capture multiple angles
- Ensure the produce is visible and clear
- Take close-up shots when possible

## Troubleshooting

### "Cannot access camera"
- Check browser camera permissions
- Grant camera permission when prompted
- Try a different browser if issue persists
- Ensure your device has a camera

### "Failed to analyze image"
- Verify your Gemini API key is correct
- Check internet connection
- Try with a smaller image file
- Generate a new API key and try again

### "API key error"
- Double-check the key spelling
- Copy directly from Google's maker suite
- Ensure there are no extra spaces
- Some browsers may have issues - try a different browser

### Image not uploading
- Check file format (PNG, JPG, GIF)
- Verify file size is under 10MB
- Try refreshing the page
- Clear browser cache and retry

## Features in This Version

✨ **Version 1.0 Features:**
- ✅ Image upload with preview
- ✅ Video capture from device camera
- ✅ Gemini API integration
- ✅ Real-time AI analysis
- ✅ Detailed produce assessment
- ✅ Temperature & storage recommendations
- ✅ Preservation method suggestions
- ✅ Cold storage guidelines
- ✅ Mobile-responsive design
- ✅ Secure API key handling
- ✅ Beautiful results display
- ✅ Multiple analyze capability

## Future Enhancements

Planned features for upcoming versions:
- Batch image analysis
- History of previous analyses
- Export results as PDF
- Multi-language support
- Comparison mode (before/after)
- Advanced filtering options
- Integration with inventory system
- Cost-benefit analysis for preservation methods

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review your API key configuration
3. Ensure browser permissions are granted
4. Contact support through the Help & Support section

---

**Last Updated**: March 27, 2026  
**Version**: 1.0  
**Status**: ✅ Active
