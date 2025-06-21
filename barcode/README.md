# 📱 Barcode Scanner with HTTPS Support

A Flask-based barcode scanner that works on both web and mobile devices with automatic HTTPS setup for mobile camera access.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install flask cryptography
   ```

2. **Run the Server**
   ```bash
   python barcode_scanner_app.py
   ```

3. **Access the Scanner**
   - **Local:** `https://localhost:5000` or `http://localhost:5000`
   - **Mobile:** Use the network URL shown in the console

## 🔒 HTTPS Features

- **Automatic Certificate Generation:** Creates self-signed certificates for HTTPS
- **Mobile Camera Support:** HTTPS enables camera access on mobile Chrome
- **Dual Protocol:** Supports both HTTP and HTTPS simultaneously
- **Network Access:** Automatically detects your local IP for mobile access

## 📱 Mobile Setup

1. Connect your phone to the **same WiFi network** as your computer
2. Open your browser and go to the **Network Access** URL (shown in console)
3. **Accept the security warning** - click "Advanced" → "Proceed" (Chrome) or "Accept Risk" (Firefox)
4. 🎉 **Camera will work!** The HTTPS connection enables mobile camera access

## 🛠️ Troubleshooting

### Network Access Issues

**Problem:** Mobile devices can't access the scanner

**Solutions:**
1. **Windows Firewall:** Run `fix_firewall.bat` as Administrator
2. **Manual Firewall:** Allow Python through Windows Firewall
3. **Port 5000:** Make sure no other app is using port 5000
4. **WiFi Network:** Ensure both devices are on the same network

### Camera Issues

**Problem:** Camera doesn't work on mobile Chrome

**Solutions:**
1. **HTTPS Required:** Make sure server shows "HTTPS ENABLED" in console
2. **Certificate Warning:** Accept the security certificate warning
3. **Fallback Browser:** Try Firefox or Safari if Chrome doesn't work
4. **Manual Entry:** Always works as a backup option

### Installation Issues

**Problem:** `ModuleNotFoundError` for flask or cryptography

**Solution:**
```bash
pip install flask cryptography
```

## 📋 Console Output Explanation

When you start the server, you'll see:

```
======================================================================
🔗 BARCODE SCANNER ACCESS LINKS
======================================================================
🔒 HTTPS ENABLED - Camera will work on mobile!
📱 Local Access (HTTPS):  https://localhost:5000
🌐 Network Access (HTTPS): https://192.168.0.159:5000
📱 Local Access (HTTP):   http://localhost:5000
🌐 Network Access (HTTP):  http://192.168.0.159:5000
📍 Local IP:         192.168.0.159
======================================================================
```

- **HTTPS URLs:** Enable camera on mobile (use these!)
- **HTTP URLs:** Backup options (camera may not work on mobile)
- **Local IP:** Your computer's network address

## 🔧 Technical Details

### HTTPS Certificate
- **Self-signed certificate** created automatically
- **Valid for 1 year** from creation date
- **Includes your IP address** for network access
- **Files:** `cert.pem` and `key.pem` (auto-generated)

### Network Configuration
- **Binds to 0.0.0.0:5000** for network access
- **Automatic IP detection** for your local network
- **Firewall detection** warns if port might be blocked

### Browser Compatibility
- **Chrome:** Requires HTTPS for camera (✅ Supported)
- **Firefox:** Works with both HTTP and HTTPS (✅ Supported)
- **Safari:** Works with both HTTP and HTTPS (✅ Supported)
- **Mobile browsers:** Require HTTPS for camera (✅ Supported)

## 📄 Files Structure

```
barcode-scanner/
├── barcode_scanner_app.py    # Main Flask application
├── templates/
│   ├── scanner.html          # Scanner interface
│   ├── access_links.html     # Network access page
│   └── product_detail.html   # Product details
├── fix_firewall.bat         # Windows firewall helper
├── cert.pem                 # HTTPS certificate (auto-generated)
├── key.pem                  # HTTPS private key (auto-generated)
└── README.md               # This file
```

## 🆘 Getting Help

1. **Check console output** for detailed status information
2. **Visit `/links`** page for copy-paste URLs and instructions
3. **Run firewall fix** if network access fails
4. **Use manual barcode entry** as a reliable fallback

## 🎯 Why HTTPS?

Modern browsers (especially mobile Chrome) require **secure connections (HTTPS)** to access device cameras for security reasons. This app automatically creates the necessary certificates to enable camera access on all devices.

**Without HTTPS:** Camera works on desktop, fails on mobile  
**With HTTPS:** Camera works everywhere! 🎉 