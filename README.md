<div align="center">

# 🎬 LASTIC PRODUCTIONS

### STUDIO CYBER · Multi-Platform Video Downloader

**Download videos & audio from YouTube, Twitter/X, Instagram, TikTok, Facebook and more — in one clean dark-mode app.**

[![Build APK](https://github.com/kinkysweetfeet90-ship-it/lastic-productions-YT/actions/workflows/android-build.yml/badge.svg)](https://github.com/kinkysweetfeet90-ship-it/lastic-productions-YT/actions/workflows/android-build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Windows%20%7C%20Linux-brightgreen)](#-installation)

[🌐 Live Website](https://kinkysweetfeet90-ship-it.github.io/lastic-productions-YT/) · [📥 Download APK](#-get-the-app) · [🚀 Quick Start](#-quick-start) · [❓ FAQ](#-faq--troubleshooting)

</div>

---

## ✨ Features

| | Feature | Details |
|---|---------|---------|
| 🎥 | **Multi-Platform** | YouTube, Twitter/X, Instagram, Facebook, TikTok, Reddit, Vimeo + most direct video links |
| 🎚️ | **Quality Control** | Best available, 1080p, 720p, 480p, 360p |
| 🎵 | **Audio Extraction** | Save any video as MP3 / M4A / WAV |
| 📦 | **Bulk Scraping** | Archive entire profiles / playlists |
| 📊 | **Live Progress** | Real-time progress bar, speed & ETA |
| 🌙 | **Dark Mode UI** | Clean cyber-styled interface, easy on the eyes |
| ⚡ | **Background Threads** | Downloads never freeze the UI |
| 📱 | **Android Native** | Saves straight to your phone's `Download` folder |

---

## 📥 Get the App

### 🖥️ Web Downloader for Windows (Easiest)

**No install wizard, no cloud — runs 100% on YOUR pc:**

1. **[⬇️ Download ZIP](https://github.com/kinkysweetfeet90-ship-it/lastic-productions-YT/archive/refs/heads/main.zip)** *(or green `< > Code` button → Download ZIP)*
2. Extract it anywhere
3. Double-click **`START_WEB_APP.bat`**
4. Your browser opens the full downloader at `http://127.0.0.1:5001` 🎉

> **Requirements:** [Python](https://www.python.org/downloads/) (tick *"Add to PATH"* during install). Optional: [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) for MP3 conversion.
>
> **📱 Bonus:** your phone can use it too — connect to the same Wi-Fi and open `http://<your-pc-ip>:5001` (shown in the launcher window).

### 🤖 Android (APK)
> Every push to `main` automatically builds a fresh APK via GitHub Actions.

1. Open the **[Actions tab](https://github.com/kinkysweetfeet90-ship-it/lastic-productions-YT/actions/workflows/android-build.yml)**
2. Click the latest successful **Build Android APK** run
3. Download the **lasticproductions-debug-apk** artifact
4. Extract → transfer `*.apk` to your phone → install
   *(enable "Install unknown apps" for your browser/file manager when prompted)*

<sub>💡 Stable releases are also attached to GitHub Releases when a `v*` tag is pushed.</sub>

### 🌐 Web Version
No install needed — open the live site and hit **LAUNCH APP**:

**👉 https://kinkysweetfeet90-ship-it.github.io/lastic-productions-YT/**

### 💻 Desktop (Windows / Linux / macOS)
```bash
git clone https://github.com/kinkysweetfeet90-ship-it/lastic-productions-YT.git
cd lastic-productions-YT
pip install -r requirements.txt
python TEST_DESKTOP.py        # runs the desktop test harness
```

---

## 🚀 How to Use

### 1️⃣ Download a Video
```
┌──────────────────────────────────────────────┐
│  1. Copy the video link                      │
│     e.g. https://x.com/user/status/123...    │
│                                              │
│  2. Paste it into the URL field              │
│                                              │
│  3. Pick your quality                        │
│     Best / 1080p / 720p / 480p / MP3         │
│                                              │
│  4. Tap DOWNLOAD ▶                           │
│     → progress bar shows speed + ETA         │
│                                              │
│  5. Find your file:                          │
│     Android → /Download/                     │
│     Desktop → project folder                 │
└──────────────────────────────────────────────┘
```

### 2️⃣ Extract Audio Only
Select **MP3 / M4A / WAV** from the quality picker before downloading — perfect for music & podcasts.

### 3️⃣ Bulk Profile Archive
Paste a profile/playlist URL to queue every video on that page for download.

---

## 🛠️ Build From Source

The APK builds automatically in the cloud (free), or locally on Linux/WSL:

```bash
# 1. Install buildozer + system deps (Linux/WSL)
pip install buildozer cython
sudo apt update && sudo apt install -y git zip unzip openjdk-17-jdk \
  autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
  cmake libffi-dev libssl-dev

# 2. Build debug APK
buildozer android debug          # output lands in bin/

# 3. Or build + deploy straight to a connected device
buildozer android deploy run
```

<details>
<summary><b>⚙️ App configuration</b> (<i>buildozer.spec</i>)</summary>

| Setting | Value |
|---|---|
| App name | Lastic Productions Mobile |
| Package | `com.lasticproductions.lasticproductions` |
| Version | 1.0.0 |
| Min Android | 5.0 (API 21) |
| Target API | 33 |
| Arch | arm64-v8a |
| Permissions | INTERNET, READ/WRITE_EXTERNAL_STORAGE |

</details>

---

## ❓ FAQ & Troubleshooting

<details>
<summary><b>APK won't install?</b></summary>
Enable <b>Settings → Apps → Special access → Install unknown apps</b> for your file manager/browser, then retry.
</details>

<details>
<summary><b>A specific site fails to download?</b></summary>
yt-dlp is updated constantly — sites change their players daily. Rebuild with the latest yt-dlp or wait for the next CI build.
</details>

<details>
<summary><b>Where do downloaded files go?</b></summary>
On Android they're saved to your <code>Download</code> folder. On desktop, into the app's working directory.
</details>

<details>
<summary><b>App crashes on launch?</b></summary>
Run <code>adb logcat | grep python</code> with the phone connected, or check the build logs in Actions.
</details>

---

## 📁 Project Structure

```
lastic-productions-YT/
├── main.py                  # Kivy mobile app entry point
├── main_desktop.py          # Desktop variant
├── buildozer.spec           # Android build configuration
├── requirements.txt         # Python dependencies
├── Flask app/               # Web server version
├── .github/workflows/
│   └── android-build.yml    # Auto-builds the APK on every push
├── docs/                    # Extra documentation
├── FEATURES.md              # Detailed feature breakdown
├── QUICK_START.md           # Fast setup guide
└── INSTALL.sh               # Dependency installer (Linux/macOS)
```

---

## 🧰 Tech Stack

![Kivy](https://img.shields.io/badge/UI-Kivy-7B68EE?logo=kivy&logoColor=white)
![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-red)
![Buildozer](https://img.shields.io/badge/Packaging-Buildozer-orange)
![FFmpeg](https://img.shields.io/badge/Media-FFmpeg-008000?logo=ffmpeg&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)

---

## ⚖️ Legal & License

Released under the **MIT License**.

> ⚠️ **Disclaimer:** This tool downloads publicly available content via yt-dlp. Respect each platform's Terms of Service and copyright law — only download content you own or have permission to save. Not affiliated with YouTube, X, Instagram or TikTok.

---

<div align="center">

**STUDIO CYBER · LASTIC PRODUCTIONS · 2026**

[⬆ Back to top](#-lastic-productions)

</div>
