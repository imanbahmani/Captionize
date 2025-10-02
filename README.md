# Captionize

**Captionize – Smart Subtitle Generator, Sync & Embed Tool**  
زیرنویس‌ساز هوشمند برای ویدیوها، مخصوصاً به زبان فارسی 

---

## 📌 توضیحات (فارسی)

**Captionize** یک ابزار متن‌باز مبتنی بر پایتون است که برای ساخت و ویرایش زیرنویس ویدیو طراحی شده است.  

ویژگی‌های اصلی آن:
- 🎙️ **تبدیل گفتار به متن (Speech-to-Text)** با دقت بالا  
- ⏱️ **هماهنگ‌سازی خودکار زیرنویس** با زمان ویدیو  
- 📝 **اتصال به هوش مصنوعی GPT** برای اصلاح و بازنویسی حرفه‌ای زیرنویس‌ها (مثلاً تصحیح غلط‌های املایی یا بهبود نگارش)  
- 🎥 **قراردادن (Burn-in) زیرنویس روی ویدیو** به‌صورت مستقیم  
- 🌐 پشتیبانی ویژه از **زبان فارسی** به همراه سایر زبان‌ها  

---

## 📌 Description (English)

**Captionize** is an open-source Python-based tool designed to **generate, sync, and embed subtitles** into videos.  

### Key Features:
- 🎙️ **Speech-to-Text** transcription with high accuracy  
- ⏱️ **Automatic subtitle synchronization** with video timeline  
- 📝 **GPT-powered subtitle editing** for grammar correction, phrasing improvements, and localization  
- 🎥 **Burn-in subtitles** directly onto video files  
- 🌐 Special support for the **Persian language (Farsi)** along with other languages  

---

## 🚀 Installation

### Clone Project
```bash
git clone https://github.com/imanbahmani/Captionize.git
cd Captionize
pip install -r requirements.txt
```

### Dependencies
```bash
# Core libraries
pip install flask openai faster-whisper torch

# For WhisperX (better accuracy, optional)
pip install whisperx

# Persian font (Ubuntu/Debian)
sudo apt-get install fonts-vazirmatn

# FFmpeg (required)
sudo apt-get install ffmpeg
```

---

## ⚙️ Components

### 1. `bahmanPi.py` – Subtitle Generator
Generates karaoke-style ASS subtitles from video/audio with word-level timestamps.

**Usage:**
```bash
python bahmanPi.py --in video.mp4 --ass output.ass
```

---

### 2. `editor.py` – Web Editor
Flask-based web app for editing ASS subtitles with GPT correction and hardsub features.  

**Run:**
```bash
python editor.py
```
Open in browser: [http://localhost:5000](http://localhost:5000)

**GPT Setup:**  
API key is read from `.env` file. Example:
```env
OPENAI_API_KEY=your-key-here
```

---

### 3. `burn_video.py` – Video Hardsubber
Standalone script to burn ASS subtitles into video.

**Usage:**
```bash
python burn_video.py --video input.mp4 --ass subs.ass --quality medium
```

**Quality presets:**
- `high` – CRF 18 (best quality, large file)  
- `medium` – CRF 23 (balanced, default)  
- `low` – CRF 28 (small file)  
- `instagram` – 5Mbps bitrate (social media)  

---

## 🔄 Workflow Example

```bash
# 1. Generate subtitles
python bahmanPi.py --in video.mp4 --ass subs.ass

# 2. Edit in browser with GPT correction
python editor.py
# Upload subs.ass, edit, apply GPT fixes, export

# 3. Burn subtitles into video
python burn_video.py --video video.mp4 --ass edited_subs.ass --quality instagram
```

Or just use the editor to burn the subtitle to video directly.  

---

## 🛠️ Troubleshooting

- **Hardsub not working:**  
  Check the FFmpeg path in `burn_video.py` (line ~81).  

---

## 📂 Project Structure

```
Captionize/
│── bahmanPi.py       # Subtitle Generator
│── burn_video.py     # Video Hardsubber
│── editor.py         # Subtitle Editor (Flask + GPT)
│── docs.txt          # Documentation notes
│── README.md
│── .env.example      # Example environment variables
```

---

## 🧠 Powered by
- [Whisper / Faster-Whisper] for Speech-to-Text  
- [OpenAI GPT] for subtitle refinement  
- [FFmpeg] for video processing  

---

## 📜 License
MIT License © 2025 [Iman Bahmani](https://github.com/imanbahmani)
