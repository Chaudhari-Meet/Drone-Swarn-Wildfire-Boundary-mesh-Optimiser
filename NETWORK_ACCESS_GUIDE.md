# 🌐 Network Access Guide - Wildfire Drone System

This guide shows how to make your server accessible from other devices (phones, tablets, laptops).

---

## ✅ OPTION 1: Local Network Access (Same WiFi)

**Already Working!** Your server is accessible at:
- **From your computer**: `http://localhost:5000`
- **From other devices on same WiFi**: `http://192.168.1.11:5000`

### Steps to Access from Phone/Tablet:

1. **Connect your phone to the SAME WiFi network** as your computer
2. **Open browser on your phone** (Chrome, Safari, etc.)
3. **Type in the address bar**: `http://192.168.1.11:5000`
4. You should see the upload page!

### If it doesn't work - Fix Windows Firewall:

**Option A - Using Windows Firewall GUI** (Easiest):
1. Press `Windows Key`
2. Type "Windows Defender Firewall"
3. Click "Advanced settings" (left side)
4. Click "Inbound Rules" (left side)
5. Click "New Rule..." (right side)
6. Select "Port" → Click Next
7. Select "TCP" → Type "5000" in Specific local ports → Next
8. Select "Allow the connection" → Next
9. Check all boxes (Domain, Private, Public) → Next
10. Name it "Flask Wildfire Server" → Finish

**Option B - Using PowerShell** (Run as Administrator):
```powershell
# Right-click PowerShell → Run as Administrator, then paste:
netsh advfirewall firewall add rule name="Flask Port 5000" dir=in action=allow protocol=TCP localport=5000
```

### Finding Your Computer's IP (if it changes):
```powershell
# Run this command to see your IP:
ipconfig | findstr IPv4
```

---

## ✅ OPTION 2: Internet Access (Public URL)

Make your server accessible from ANYWHERE over the internet.

### Method 2A: Using ngrok (Recommended - Free & Easy)

**Step 1: Install ngrok**
1. Go to https://ngrok.com/download
2. Download for Windows
3. Extract `ngrok.exe` to your project folder

**Step 2: Get ngrok account** (free)
1. Sign up at https://ngrok.com/
2. Copy your authtoken from dashboard

**Step 3: Setup ngrok**
```powershell
# In your project folder, run:
.\ngrok.exe authtoken YOUR_AUTHTOKEN_HERE
```

**Step 4: Start your Flask server** (keep it running)
```powershell
python app.py
```

**Step 5: In a NEW PowerShell window, run ngrok**
```powershell
.\ngrok.exe http 5000
```

**You'll get a public URL like:**
```
https://abc123.ngrok.io
```

**Share this URL** with anyone! They can access from anywhere in the world.

⚠️ **Ngrok free limitations:**
- URL changes every time you restart ngrok
- Session timeout after 2 hours (need to restart)
- Upgrade to paid plan ($8/month) for permanent URLs

---

### Method 2B: Using localtunnel (Free Alternative)

**Step 1: Install localtunnel**
```powershell
npm install -g localtunnel
```

**Step 2: Start your Flask server** (keep it running)
```powershell
python app.py
```

**Step 3: In a NEW PowerShell window, run localtunnel**
```powershell
lt --port 5000 --subdomain wildfire-drone
```

**You'll get a URL like:**
```
https://wildfire-drone.loca.lt
```

---

### Method 2C: Deploy to Cloud (Professional - Permanent)

For a **permanent, professional deployment**, use one of these platforms:

#### **Render.com** (Easiest - Free tier available)
1. Create account at https://render.com
2. Connect your GitHub repository
3. Create new "Web Service"
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python app.py`
6. Deploy!

You'll get a permanent URL like: `https://wildfire-drone.onrender.com`

#### **Railway.app** (Easy - Free $5 credit)
1. Create account at https://railway.app
2. "New Project" → "Deploy from GitHub"
3. Select your repository
4. Add environment variables if needed
5. Deploy!

#### **PythonAnywhere** (Easy - Free tier)
1. Create account at https://www.pythonanywhere.com
2. Upload your files
3. Configure web app
4. You get: `https://yourusername.pythonanywhere.com`

#### **Heroku** (Popular - Paid after free tier ended)
1. Create account at https://heroku.com
2. Install Heroku CLI
3. Deploy with git

---

## 🔒 Security Considerations

### For Local Network Access:
- ✅ Generally safe - only people on your WiFi can access
- ⚠️ Make sure you trust everyone on your WiFi

### For Internet Access:
- ⚠️ **ADD AUTHENTICATION** before making public!
- ⚠️ Add rate limiting to prevent abuse
- ⚠️ Use HTTPS (handled by ngrok/localtunnel/cloud platforms)
- ⚠️ Consider adding password protection

---

## 📱 Testing from Your Phone

### Test Local Network (192.168.1.11):
1. Connect phone to same WiFi as computer
2. Open browser (Chrome/Safari)
3. Go to: `http://192.168.1.11:5000`
4. Try uploading your Berlin GeoJSON file
5. Test all features

### Test Public URL (ngrok/localtunnel):
1. Can be on any network (4G/5G/Different WiFi)
2. Open browser
3. Go to the ngrok/localtunnel URL
4. Works from anywhere in the world!

---

## 🚀 Quick Start Commands

**Keep server running permanently:**
```powershell
# Method 1: Run in background (Windows)
Start-Process python -ArgumentList "app.py" -WindowStyle Hidden

# Method 2: Run with nohup (if you have Git Bash)
nohup python app.py &

# Method 3: Create Windows Service (advanced)
# Use NSSM (Non-Sucking Service Manager)
```

**Check if server is running:**
```powershell
# Check if port 5000 is listening
netstat -an | findstr :5000
```

**Stop server:**
```powershell
# Find Python process
Get-Process python

# Stop by PID (replace 1234 with actual PID)
Stop-Process -Id 1234
```

---

## 💡 Recommended Setup for You

### For Testing/Development:
1. ✅ Use **Local Network Access** (http://192.168.1.11:5000)
2. Open firewall port 5000
3. Access from phones on same WiFi

### For Demo/Sharing:
1. ✅ Use **ngrok** (easiest, works immediately)
2. Get public URL in 30 seconds
3. Share with anyone

### For Production/Permanent:
1. ✅ Deploy to **Render.com** or **Railway.app**
2. Get permanent URL
3. Professional, always online
4. Free tier available

---

## 📞 Need Help?

**Common Issues:**

**Issue**: Can't access from phone on same WiFi
- **Fix**: Check firewall, make sure phone on SAME WiFi, try IP address not "localhost"

**Issue**: ngrok URL gives error
- **Fix**: Make sure Flask server is running FIRST, then start ngrok

**Issue**: Connection refused
- **Fix**: Check if server is actually running: `netstat -an | findstr :5000`

**Issue**: IP address changed
- **Fix**: Run `ipconfig` to find new IP, update firewall rules if needed

---

## 🎯 Summary

| Method | Access From | Setup Time | Cost | Permanent |
|--------|-------------|------------|------|-----------|
| Local Network | Same WiFi | 2 min | Free | Yes (while PC on) |
| ngrok | Anywhere | 5 min | Free | No (URL changes) |
| localtunnel | Anywhere | 5 min | Free | No (URL changes) |
| Cloud (Render) | Anywhere | 15 min | Free | Yes |
| Cloud (Railway) | Anywhere | 15 min | Free | Yes |

**My Recommendation**: Start with **Local Network** for testing, then use **Render.com** for permanent deployment.
