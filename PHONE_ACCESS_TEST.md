# 📱 How to Access from Your Phone RIGHT NOW

## ✅ Quick Test (2 minutes)

### Step 1: Make sure your computer's server is running
Look at your computer screen - you should see:
```
Server running on http://localhost:5000
Network access: http://192.168.1.11:5000
```
✅ Server is running!

### Step 2: Connect your phone to WiFi
- Open your phone's WiFi settings
- Connect to the **SAME WiFi network** as your computer
- Make sure it's connected (not using mobile data)

### Step 3: Open browser on your phone
- Open **Chrome** (Android) or **Safari** (iPhone)
- In the address bar, type **EXACTLY**:
```
http://192.168.1.11:5000
```
- Press Go/Enter

### Expected Result:
✅ You should see the Wildfire upload page!
✅ You can upload files and use all features!

---

## ❌ If it doesn't work - Fix Firewall

### Option 1: Windows Firewall GUI (Easiest)

1. **Press Windows Key** on your keyboard
2. **Type**: `firewall`
3. **Click**: "Windows Defender Firewall with Advanced Security"
4. **Click**: "Inbound Rules" (left sidebar)
5. **Click**: "New Rule..." (right sidebar)
6. **Select**: "Port" → Click **Next**
7. **Select**: "TCP"
8. **Type**: `5000` in "Specific local ports"
9. **Click**: **Next**
10. **Select**: "Allow the connection"
11. **Click**: **Next**
12. **Check ALL boxes**: Domain, Private, Public
13. **Click**: **Next**
14. **Name**: `Wildfire Server Port 5000`
15. **Click**: **Finish**

✅ Done! Now try accessing from your phone again!

---

### Option 2: PowerShell Command (Faster if you're admin)

**Right-click PowerShell → Run as Administrator**

Then paste this command:
```powershell
netsh advfirewall firewall add rule name="Wildfire Server Port 5000" dir=in action=allow protocol=TCP localport=5000
```

Press Enter. You should see: `Ok.`

✅ Done! Try accessing from your phone again!

---

## 🌐 Access URLs

### From YOUR computer:
```
http://localhost:5000
```

### From OTHER devices on same WiFi:
```
http://192.168.1.11:5000
```

### From ANYWHERE on Internet (using ngrok):
```
See DEPLOYMENT.md for instructions
Quick: Download ngrok → Run: .\ngrok.exe http 5000
```

---

## 🔍 Troubleshooting

### Problem: "This site can't be reached"
**Solutions to try:**
1. ✅ Make sure phone is on SAME WiFi network
2. ✅ Make sure server is running on computer
3. ✅ Check firewall is open (see above)
4. ✅ Try typing the IP slowly and carefully: `192.168.1.11:5000`
5. ✅ Make sure you typed `http://` (not https://)

### Problem: "Connection refused"
**Solution**: Open firewall port 5000 (see instructions above)

### Problem: "Timeout"
**Solutions:**
1. Check if your computer's WiFi is on
2. Check if both devices on same WiFi network
3. Try restarting your computer's WiFi

### Problem: Server shows different IP
**Find your actual IP:**
```powershell
# Run on your computer:
ipconfig | findstr IPv4
```
Look for something like `192.168.X.X` - use that instead!

---

## 📸 What You Should See

### On your phone's browser:
1. Upload page with drag-drop area
2. Can select files
3. Can upload JSON/CSV/ZIP files
4. Can see dashboard with results
5. Can see maps and visualizations
6. Can export data

Everything should work exactly like on your computer!

---

## ✅ Current Status

Your server is **READY** and accessible at:

**Local computer:**
- `http://localhost:5000` ✅

**Same WiFi (after opening firewall):**
- `http://192.168.1.11:5000` ✅

**Internet (needs setup):**
- See `DEPLOYMENT.md` for ngrok/cloud instructions

---

## 🚀 Next Steps

### For immediate phone access:
1. ✅ Open firewall (instructions above)
2. ✅ Connect phone to same WiFi
3. ✅ Open `http://192.168.1.11:5000` on phone

### For internet access:
1. See `DEPLOYMENT.md`
2. Use ngrok for quick public URL
3. Or deploy to cloud for permanent URL

### For production use:
1. Deploy to Render.com or Railway.app
2. Get permanent public URL
3. Share with anyone, anywhere!

---

**Need help? Check:**
- `NETWORK_ACCESS_GUIDE.md` - Detailed networking guide
- `DEPLOYMENT.md` - Cloud deployment guide
- `QUICKSTART.md` - General usage guide
