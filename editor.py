#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASS Subtitle Editor with Web UI - GPT Preview Feature
Run: python ass_editor.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import os
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('all_proxy', None)

import re
from io import BytesIO
from openai import OpenAI
import os
from dotenv import load_dotenv

app = Flask(__name__)
# OpenAI API setup
# load .env file
load_dotenv()

# read API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY not found. Please set it in your .env file.")

# initialize client
openai_client = OpenAI(api_key=OPENAI_API_KEY)
CORRECTION_PROMPT = """شما یک دستیار تصحیح زیرنویس فارسی هستید. این متن‌ها زیرنویس‌های تولید شده توسط هوش مصنوعی از طریق تشخیص گفتار (Speech-to-Text) از ویدیوهای آموزشی و سخنرانی‌ها هستند.

ماموریت شما: تصحیح اشتباهات سیستم تشخیص گفتار با استفاده از تحلیل معنایی، زمینه‌ای و آواشناسی.

═══════════════════════════════════════════════════════════════

⚠️ نکته بسیار مهم - انسجام و یکپارچگی زیرنویس‌ها:

🔴 این جملات به ترتیب پشت سر هم هستند و از یک ویدیوی یکپارچه هستند!
🔴 باید با هم انسجام و هماهنگی داشته باشند!
🔴 هیچ تکراری بین خطوط نباید وجود داشته باشد!

مثال از اشتباه رایج TTS:
❌ خط 5: "یک بخش هوش مصنوعی این یکی بخش برنامه‌نویسیه و یکی دیگر بخش رباتیک"
❌ خط 6: "نویسیه و یکی دیگر بخش رباتیک"

این اشتباه است چون:
- خط 6 تکرار قسمتی از خط 5 است
- "نویسیه و یکی دیگر بخش رباتیک" قبلاً در خط 5 آمده
- این باعث عدم انسجام می‌شود

✅ تصحیح درست:
✅ خط 5: "یک بخش هوش مصنوعی، یکی بخش برنامه‌نویسی و یکی دیگر بخش رباتیک"
✅ خط 6: "در این دوره همه این سه بخش را یاد می‌گیرید"

قوانین انسجام:
1. هر خط باید ادامه طبیعی خط قبلی باشد
2. هیچ کلمه یا عبارتی نباید بین دو خط تکرار شود
3. اگر خطی شروعش ناقص است (مثل "نویسیه و یکی دیگر")، حتما قسمت اول آن در خط قبلی تکرار شده
4. به زمینه کلی تمام خطوط توجه کنید نه فقط یک خط
5. اگر یک خط فقط ادامه خط قبلی است و تکراری است، آن را حذف یا ادغام کنید

═══════════════════════════════════════════════════════════════

📋 دستورالعمل‌های اصلی:

1. **تحلیل معنایی و زمینه‌ای (مهم‌ترین قانون)**:
   - موضوع کلی صحبت را شناسایی کنید (فناوری، پزشکی، اقتصاد، ...)
   - معنای هر کلمه را در زمینه جمله بررسی کنید
   - جو و لحن جمله را در نظر بگیرید (رسمی، غیررسمی، علمی، ...)
   - ارتباط منطقی کلمات با یکدیگر را بسنجید
   - **ارتباط هر خط با خطوط قبل و بعدش را بررسی کنید**
   
   مثال‌ها:
   ❌ "این الگوریتم با استفاده از گوش مصنوعی کار می‌کند" 
   ✅ "این الگوریتم با استفاده از هوش مصنوعی کار می‌کند"
   (زمینه: فناوری → باید "هوش مصنوعی" باشد)
   
   ❌ "بیمار از هوش مصنوعی استفاده می‌کند"
   ✅ "بیمار از گوش مصنوعی استفاده می‌کند"
   (زمینه: پزشکی → باید "گوش مصنوعی" باشد)

2. **تحلیل آواشناسی (کلمات هم‌آوا)**:
   سیستم تشخیص گفتار معمولا کلماتی را که تلفظ مشابه دارند اشتباه می‌گیرد:
   
   کلمات هم‌آوای رایج:
   • "رباتیک" ↔ "رواتیک" → در زمینه فناوری حتما "رباتیک"
   • "هوش مصنوعی" ↔ "گوش مصنوعی" → بستگی به زمینه دارد
   • "ذره" ↔ "زره" → در فیزیک "ذره"، در تاریخ "زِره"
   • "صنعت" ↔ "صنت" → معمولا "صنعت"
   • "مصنوعی" ↔ "مسنوعی" → همیشه "مصنوعی"
   • "الگوریتم" ↔ "الگاریتم" → همیشه "الگوریتم"


3.
   و) **تکرار و عدم انسجام (خیلی مهم)**:
      • اگر قسمتی از یک خط در خط بعدی تکرار شده → خط دوم را اصلاح کنید
      • اگر خطی فقط ادامه خط قبلی است → آن را با خط قبل ادغام یا حذف کنید
      • اگر یک کلمه در دو خط متوالی آمده → بررسی کنید که تکراری نباشد

4. **اسم‌های خاص و اصطلاحات تخصصی**:
   - نام افراد را تغییر ندهید مگر املای آن کاملا غلط باشد
   - نام برندها: "گوگل"، "مایکروسافت"، "اپل" (املای فارسی استاندارد)
   - اصطلاحات انگلیسی: API، SDK، GPU → دست نزنید
   - اصطلاحات فارسی شده: "دیتابیس"، "فریمورک"، "بک‌اند"

5. **قوانین ممنوع**:
   ❌ هیچ‌وقت ترتیب کلمات را در یک خط تغییر ندهید
   ❌ کلمات اضافه نکنید (مگر برای رفع تکرار بین خطوط)
   ❌ کلمات را حذف نکنید (مگر برای رفع تکرار بین خطوط)
   ❌ معنی جمله را تغییر ندهید
   ❌ تکرار بین خطوط متوالی نباید باشد
   ✅ فقط املا و انتخاب کلمه درست را اصلاح کنید
   ✅ انسجام بین خطوط را حفظ کنید

6. **فرمت خروجی**:
   - دقیقا به همان فرمت JSON ورودی برگردانید
   - هیچ توضیح، کامنت یا متن اضافی ننویسید
   - فقط JSON خالص

═══════════════════════════════════════════════════════════════

📝 مثال‌های کامل تصحیح:

مثال 1 (زمینه فناوری):
ورودی: "من محمد رضا بحمنی استم مدرس دورهی مقدماتی رواتیک و گوش مصنوعی"
خروجی: "من محمدرضا بهمنی هستم مدرس دوره‌ی مقدماتی رباتیک و هوش مصنوعی"
دلیل: زمینه فناوری → "رواتیک" باید "رباتیک"، "گوش" باید "هوش"


═══════════════════════════════════════════════════════════════

🎯 نکات نهایی:
- همیشه ابتدا زمینه را تشخیص دهید
- به ارتباط خطوط با هم دقت ویژه داشته باشید
- هیچ تکراری بین خطوط متوالی نباید باشد
- سپس کلمات مشکوک را با توجه به آوا و معنی بررسی کنید
- در شک، کلمه‌ای را انتخاب کنید که در زمینه منطقی‌تر است
- نیم‌فاصله‌ها را فراموش نکنید
- فارسی رسمی و استاندارد را رعایت کنید
- تمام خطوط باید با هم انسجام و هماهنگی داشته باشند

🔴 یادت باشه: این خطوط پشت سر هم هستند، نه جداگانه! باید مثل یک متن یکپارچه با هم هماهنگ باشند!

فقط JSON تصحیح شده را برگردان، هیچ توضیح اضافی ننویس."""


# Store subtitles in memory
subtitles_data = {
    'header': '',
    'dialogues': [],
    'filename': ''
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ASS Subtitle Editor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #581c87 50%, #1e293b 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 1px solid #475569;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            color: #fff;
        }
        
        .subtitle {
            color: #94a3b8;
            margin-bottom: 30px;
        }
        
        .upload-area {
            border: 2px dashed #475569;
            border-radius: 15px;
            padding: 60px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 30px;
        }
        
        .upload-area:hover {
            border-color: #a855f7;
            background: rgba(168, 85, 247, 0.1);
        }
        
        .upload-area.hidden {
            display: none;
        }
        
        .upload-icon {
            font-size: 4rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .upload-text {
            font-size: 1.2rem;
            color: #cbd5e1;
        }
        
        .file-input {
            display: none;
        }
        
        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(51, 65, 85, 0.5);
            border-radius: 10px;
        }
        
        .file-info {
            font-size: 1.1rem;
        }
        
        .file-name {
            font-weight: bold;
            color: #fff;
        }
        
        .line-count {
            color: #94a3b8;
            font-size: 0.9rem;
        }
        
        .export-btn {
            background: #9333ea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .export-btn:hover {
            background: #7c3aed;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(147, 51, 234, 0.4);
        }
        
        .direction-btn {
            background: #f59e0b;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .direction-btn:hover {
            background: #d97706;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(245, 158, 11, 0.4);
        }
        
        .text-display.rtl {
            direction: rtl;
            text-align: right;
        }
        
        .text-display.ltr {
            direction: ltr;
            text-align: left;
        }
        
        .edit-textarea.rtl {
            direction: rtl;
            text-align: right;
        }
        
        .edit-textarea.ltr {
            direction: ltr;
            text-align: left;
        }
        
        .subtitles-list {
            max-height: 600px;
            overflow-y: auto;
            padding-right: 10px;
        }
        
        .subtitle-item {
            background: rgba(51, 65, 85, 0.5);
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s;
        }
        
        .subtitle-item:hover {
            border-color: #a855f7;
        }
        
        .subtitle-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .timestamp {
            background: #1e293b;
            padding: 5px 12px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            color: #94a3b8;
        }
        
        .line-number {
            color: #64748b;
            font-size: 0.85rem;
        }
        
        .subtitle-content {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 15px;
        }
        
        .text-display {
            flex: 1;
            font-size: 1.2rem;
            color: #fff;
            line-height: 1.6;
            direction: auto;
        }
        
        .edit-area {
            flex: 1;
        }
        
        .edit-textarea {
            width: 100%;
            background: #1e293b;
            color: #fff;
            border: 2px solid #a855f7;
            border-radius: 8px;
            padding: 12px;
            font-size: 1.1rem;
            font-family: inherit;
            resize: vertical;
            min-height: 80px;
            direction: auto;
        }
        
        .edit-textarea:focus {
            outline: none;
            box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.3);
        }
        
        .button-group {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .btn-edit {
            background: #3b82f6;
            color: white;
        }
        
        .btn-edit:hover {
            background: #2563eb;
        }
        
        .btn-delete {
            background: #ef4444;
            color: white;
        }
        
        .btn-delete:hover {
            background: #dc2626;
        }
        
        .btn-save {
            background: #10b981;
            color: white;
        }
        
        .btn-save:hover {
            background: #059669;
        }
        
        .btn-cancel {
            background: #6b7280;
            color: white;
        }
        
        .btn-cancel:hover {
            background: #4b5563;
        }
        
        .edit-buttons {
            margin-top: 10px;
        }
        
        /* Modal Styles */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            backdrop-filter: blur(5px);
        }
        
        .modal-overlay.active {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .modal {
            background: linear-gradient(135deg, #1e293b 0%, #581c87 50%, #1e293b 100%);
            border: 2px solid #a855f7;
            border-radius: 20px;
            padding: 40px;
            max-width: 900px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 25px 80px rgba(168, 85, 247, 0.5);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #475569;
        }
        
        .modal-title {
            font-size: 1.8rem;
            color: #fff;
        }
        
        .modal-close {
            background: #ef4444;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1.2rem;
            transition: all 0.3s;
        }
        
        .modal-close:hover {
            background: #dc2626;
        }
        
        .preview-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(51, 65, 85, 0.5);
            border-radius: 10px;
        }
        
        .preview-info {
            color: #94a3b8;
        }
        
        .reverse-toggle {
            background: #f59e0b;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .reverse-toggle:hover {
            background: #d97706;
        }
        
        .preview-list {
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(30, 41, 59, 0.5);
            border-radius: 10px;
            border: 1px solid #475569;
        }
        
        .preview-item {
            padding: 10px;
            margin-bottom: 10px;
            background: rgba(51, 65, 85, 0.5);
            border-radius: 8px;
            border-left: 3px solid #a855f7;
        }
        
        .preview-number {
            color: #94a3b8;
            font-size: 0.85rem;
            margin-bottom: 5px;
        }
        
        .preview-text {
            color: #fff;
            font-size: 1.1rem;
            direction: rtl;
            text-align: right;
        }
        
        .modal-actions {
            display: flex;
            gap: 15px;
            justify-content: flex-end;
        }
        
        .btn-confirm {
            background: #10b981;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-confirm:hover {
            background: #059669;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(16, 185, 129, 0.4);
        }
        
        .btn-cancel-modal {
            background: #6b7280;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-cancel-modal:hover {
            background: #4b5563;
        }
        
        ::-webkit-scrollbar {
            width: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(30, 41, 59, 0.5);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }
        
        .hidden {
            display: none !important;
        }


        /* Hardsub Modal Styles */
.hardsub-btn {
    background: #ef4444;
    color: white;
    border: none;
    padding: 12px 30px;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    gap: 8px;
}

.hardsub-btn:hover {
    background: #dc2626;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(239, 68, 68, 0.4);
}

.hardsub-modal .modal {
    max-width: 1000px;
}

.video-upload-area {
    border: 2px dashed #475569;
    border-radius: 15px;
    padding: 40px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    margin-bottom: 20px;
    background: rgba(51, 65, 85, 0.3);
}

.video-upload-area:hover {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
}

.video-upload-area.has-file {
    border-color: #10b981;
    background: rgba(16, 185, 129, 0.1);
}

.video-info {
    display: flex;
    align-items: center;
    gap: 15px;
    justify-content: center;
}

.video-filename {
    font-size: 1.1rem;
    color: #fff;
    font-weight: 600;
}

.video-size {
    color: #94a3b8;
    font-size: 0.9rem;
}

.quality-selector {
    margin: 20px 0;
    padding: 20px;
    background: rgba(51, 65, 85, 0.5);
    border-radius: 10px;
}

.quality-selector label {
    display: block;
    color: #cbd5e1;
    font-weight: 600;
    margin-bottom: 10px;
}

.quality-options {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.quality-option {
    background: rgba(30, 41, 59, 0.8);
    border: 2px solid #475569;
    border-radius: 8px;
    padding: 15px;
    cursor: pointer;
    transition: all 0.3s;
    text-align: center;
}

.quality-option:hover {
    border-color: #ef4444;
}

.quality-option.selected {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.2);
}

.quality-option-title {
    font-weight: 600;
    color: #fff;
    margin-bottom: 5px;
}

.quality-option-desc {
    font-size: 0.85rem;
    color: #94a3b8;
}

.hardsub-progress {
    display: none;
    padding: 20px;
    background: rgba(51, 65, 85, 0.5);
    border-radius: 10px;
    margin: 20px 0;
}

.hardsub-progress.active {
    display: block;
}

.progress-bar-container {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 10px;
    height: 30px;
    overflow: hidden;
    margin: 10px 0;
}

.progress-bar {
    background: linear-gradient(90deg, #ef4444, #dc2626);
    height: 100%;
    width: 0%;
    transition: width 0.3s;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.9rem;
}

.progress-status {
    color: #94a3b8;
    text-align: center;
    margin-top: 10px;
}



    </style>
</head>
<body>
    <div class="container">
        <h1>ASS Subtitle Editor</h1>
        <p class="subtitle">Edit subtitle text while preserving timing and styling</p>
        
        <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
            <div class="upload-icon">📤</div>
            <div class="upload-text">Click to upload ASS subtitle file</div>
            <input type="file" id="fileInput" class="file-input" accept=".ass" onchange="uploadFile(this)">
        </div>
        
        <div id="editorSection" class="hidden">
            <div class="header-bar">
                <div class="file-info">
                    <div class="file-name" id="fileName"></div>
                    <div class="line-count" id="lineCount"></div>
                </div>
                <div style="display: flex; gap: 10px;">
                <button class="direction-btn" onclick="toggleDirection()">
                    <span>🔄</span>
                    <span id="directionLabel">Switch to LTR</span>
                </button>
                <button class="direction-btn" style="background: #10b981;" onclick="showGPTPreview()">
                    <span>🤖</span>
                    <span>GPT Correct</span>
                </button>
                <button class="hardsub-btn" onclick="showHardsubModal()">
                    <span>🎬</span>
                    <span>Hardsub Video</span>
                </button>
                <button class="export-btn" onclick="exportFile()">
                    <span>⬇</span>
                    Export ASS
                </button>
            </div>
            </div>
            
            <div class="subtitles-list" id="subtitlesList"></div>
        </div>
    </div>
    
    <!-- GPT Preview Modal -->
    <div class="modal-overlay" id="gptModal">
        <div class="modal">
            <div class="modal-header">
                <h2 class="modal-title">🤖 GPT Correction Preview</h2>
                <button class="modal-close" onclick="closeGPTPreview()">✕</button>
            </div>
            
            <div class="preview-controls">
                <div class="preview-info">
                    <strong id="previewCount">0</strong> lines will be sent to GPT-4
                </div>
                <button class="reverse-toggle" onclick="togglePreviewReverse()">
                    <span>🔄</span>
                    <span id="reverseLabel">Reverse Word Order</span>
                </button>
            </div>
            
            <div class="preview-list" id="previewList"></div>
            
            <div class="modal-actions">
                <button class="btn-cancel-modal" onclick="closeGPTPreview()">Cancel</button>
                <button class="btn-confirm" onclick="confirmGPTCorrection()">
                    <span>✅</span>
                    Send to GPT-4
                </button>
            </div>
        </div>
    </div>
    <!-- Hardsub Modal -->
<div class="modal-overlay hardsub-modal" id="hardsubModal">
    <div class="modal">
        <div class="modal-header">
            <h2 class="modal-title">🎬 Hardsub Video</h2>
            <button class="modal-close" onclick="closeHardsubModal()">✕</button>
        </div>
        
        <div class="video-upload-area" id="videoUploadArea" onclick="document.getElementById('videoInput').click()">
            <div class="upload-icon">🎥</div>
            <div class="upload-text" id="videoUploadText">Click to select video file</div>
            <input type="file" id="videoInput" style="display: none;" accept="video/*" onchange="handleVideoUpload(this)">
        </div>
        
        <div class="quality-selector">
            <label>Select Quality:</label>
            <div class="quality-options">
                <div class="quality-option" onclick="selectQuality('high')">
                    <div class="quality-option-title">High</div>
                    <div class="quality-option-desc">CRF 18 - Best</div>
                </div>
                <div class="quality-option selected" onclick="selectQuality('medium')">
                    <div class="quality-option-title">Medium</div>
                    <div class="quality-option-desc">CRF 23 - Default</div>
                </div>
                <div class="quality-option" onclick="selectQuality('low')">
                    <div class="quality-option-title">Low</div>
                    <div class="quality-option-desc">CRF 28 - Small</div>
                </div>
                <div class="quality-option" onclick="selectQuality('instagram')">
                    <div class="quality-option-title">Instagram</div>
                    <div class="quality-option-desc">5Mbps - Social</div>
                </div>
            </div>
        </div>
        
        <div class="preview-controls">
            <div class="preview-info">
                <strong id="hardsubPreviewCount">0</strong> subtitle lines will be burned
            </div>
            <button class="reverse-toggle" onclick="toggleHardsubReverse()">
                <span>🔄</span>
                <span id="hardsubReverseLabel">Reverse Word Order</span>
            </button>
        </div>
        
        <div class="preview-list" id="hardsubPreviewList"></div>
        
        <div class="hardsub-progress" id="hardsubProgress">
            <div class="progress-bar-container">
                <div class="progress-bar" id="progressBar">0%</div>
            </div>
            <div class="progress-status" id="progressStatus">Preparing...</div>
        </div>
        
        <div class="modal-actions">
            <button class="btn-cancel-modal" onclick="closeHardsubModal()">Cancel</button>
            <button class="btn-confirm" id="hardsubConfirmBtn" onclick="confirmHardsub()">
                <span>🎬</span>
                Start Hardsubbing
            </button>
        </div>
    </div>
</div>
    <script>
        let subtitles = [];
        let isRTL = true; // Default to RTL for Arabic/Persian
        let previewReversed = false;
        let previewTexts = {};
        let hardsubVideoFile = null;
        let hardsubQuality = 'medium';
        let hardsubReversed = false;

        function showHardsubModal() {
            console.log('🎬 Opening hardsub modal...');
            
            // Reset state
            hardsubVideoFile = null;
            hardsubQuality = 'medium';
            hardsubReversed = false;
            
            // Update preview
            document.getElementById('hardsubPreviewCount').textContent = subtitles.length;
            document.getElementById('hardsubReverseLabel').textContent = 'Reverse Word Order';
            
            // Render preview
            renderHardsubPreview();
            
            // Show modal
            document.getElementById('hardsubModal').classList.add('active');
        }

        function closeHardsubModal() {
            document.getElementById('hardsubModal').classList.remove('active');
            hardsubVideoFile = null;
        }

        function handleVideoUpload(input) {
            const file = input.files[0];
            if (!file) return;
            
            hardsubVideoFile = file;
            
            const uploadArea = document.getElementById('videoUploadArea');
            const uploadText = document.getElementById('videoUploadText');
            
            uploadArea.classList.add('has-file');
            
            const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
            uploadText.innerHTML = `
                <div class="video-info">
                    <div class="video-filename">📹 ${file.name}</div>
                    <div class="video-size">${sizeMB} MB</div>
                </div>
            `;
            
            console.log(`✅ Video selected: ${file.name} (${sizeMB} MB)`);
        }

        function selectQuality(quality) {
            hardsubQuality = quality;
            
            // Update UI
            document.querySelectorAll('.quality-option').forEach(el => {
                el.classList.remove('selected');
            });
            event.target.closest('.quality-option').classList.add('selected');
            
            console.log(`✅ Quality selected: ${quality}`);
        }

        function toggleHardsubReverse() {
            hardsubReversed = !hardsubReversed;
            document.getElementById('hardsubReverseLabel').textContent = hardsubReversed ? 'Undo Reverse' : 'Reverse Word Order';
            renderHardsubPreview();
        }

        function renderHardsubPreview() {
            const container = document.getElementById('hardsubPreviewList');
            container.innerHTML = '';
            
            subtitles.forEach((sub, index) => {
                let text = extractVisibleText(sub.text);
                
                // Apply reversal if toggled
                if (hardsubReversed) {
                    text = reverseWords(text);
                }
                
                const div = document.createElement('div');
                div.className = 'preview-item';
                div.innerHTML = `
                    <div class="preview-number">Line ${index + 1} • ${sub.start} → ${sub.end}</div>
                    <div class="preview-text">${text}</div>
                `;
                container.appendChild(div);
            });
        }

        function confirmHardsub() {
            if (!hardsubVideoFile) {
                alert('❌ Please select a video file first!');
                return;
            }
            
            console.log('🎬 Starting hardsub process...');
            
            // Disable button
            const btn = document.getElementById('hardsubConfirmBtn');
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.innerHTML = '<span>⏳</span> Processing...';
            
            // Show progress
            const progress = document.getElementById('hardsubProgress');
            progress.classList.add('active');
            console.log('🔄 hardsubReversed value:', hardsubReversed);
            console.log('🔄 typeof:', typeof hardsubReversed);
            // Prepare FormData
            const formData = new FormData();
            formData.append('video', hardsubVideoFile);
            formData.append('quality', hardsubQuality);
            formData.append('reverse_words', hardsubReversed);
            
            // Upload and process
            fetch('/hardsub', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Hardsub failed');
                }
                return response.blob();
            })
            .then(blob => {
                // Download the result
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = hardsubVideoFile.name.replace(/\.[^/.]+$/, '') + '_subbed.mp4';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                console.log('✅ Hardsub completed!');
                alert('✅ Video with hardcoded subtitles downloaded!');
                
                closeHardsubModal();
            })
            .catch(error => {
                console.error('❌ Hardsub error:', error);
                alert('❌ Error: ' + error.message);
            })
            .finally(() => {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.innerHTML = '<span>🎬</span> Start Hardsubbing';
                progress.classList.remove('active');
            });
        }



        function toggleDirection() {
            isRTL = !isRTL;
            const label = document.getElementById('directionLabel');
            label.textContent = isRTL ? 'Switch to LTR' : 'Switch to RTL';
            
            // Re-render everything with word order change
            renderSubtitles();
        }
        
        function uploadFile(input) {
            const file = input.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    subtitles = data.dialogues;
                    document.getElementById('fileName').textContent = data.filename;
                    document.getElementById('lineCount').textContent = subtitles.length + ' dialogue lines';
                    document.getElementById('uploadArea').classList.add('hidden');
                    document.getElementById('editorSection').classList.remove('hidden');
                    renderSubtitles();
                }
            })
            .catch(error => console.error('Error:', error));
        }
        
        function extractVisibleText(text) {
            // Remove ASS style tags and labels
            let cleaned = text.replace(/\{[^}]*\}/g, '');
            cleaned = cleaned.replace(/\[[A-Z0-9]+\]\s*/g, '');
            return cleaned.trim();
        }
        
        function reverseWords(text) {
            // Reverse the order of words
            return text.split(/\s+/).reverse().join(' ');
        }
        
        function getDisplayText(text) {
            const cleaned = extractVisibleText(text);
            return isRTL ? cleaned : reverseWords(cleaned);
        }
        
        function renderSubtitles() {
            const container = document.getElementById('subtitlesList');
            container.innerHTML = '';
            const dirClass = isRTL ? 'rtl' : 'ltr';
            
            subtitles.forEach((sub, index) => {
                const div = document.createElement('div');
                div.className = 'subtitle-item';
                const displayText = getDisplayText(sub.text);
                
                div.innerHTML = `
                    <div class="subtitle-header">
                        <span class="timestamp">${sub.start} → ${sub.end}</span>
                        <span class="line-number">Line ${index + 1}</span>
                    </div>
                    <div class="subtitle-content" id="content-${index}">
                        <div class="text-display ${dirClass}" id="display-${index}">${displayText}</div>
                        <div class="button-group">
                            <button class="btn btn-edit" onclick="startEdit(${index})">✏️ Edit</button>
                            <button class="btn btn-delete" onclick="deleteSubtitle(${index})">🗑️ Delete</button>
                        </div>
                    </div>
                `;
                container.appendChild(div);
            });
        }
        
        function startEdit(index) {
            const content = document.getElementById(`content-${index}`);
            const currentText = getDisplayText(subtitles[index].text);
            const dirClass = isRTL ? 'rtl' : 'ltr';
            
            content.innerHTML = `
                <div class="edit-area">
                    <textarea class="edit-textarea ${dirClass}" id="edit-${index}">${currentText}</textarea>
                    <div class="edit-buttons">
                        <div class="button-group">
                            <button class="btn btn-save" onclick="saveEdit(${index})">💾 Save</button>
                            <button class="btn btn-cancel" onclick="renderSubtitles()">❌ Cancel</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById(`edit-${index}`).focus();
        }
        
      function saveEdit(index) {
    let newText = document.getElementById(`edit-${index}`).value;
    
    // CRITICAL: When in RTL mode, the user types in RTL order
    // But the ASS file needs words in reversed order for RTL display
    // So we need to reverse the words before sending to backend
    
    if (isRTL) {
        // User typed: "word1 word2 word3" (RTL visual order)
        // ASS file needs: "word3 word2 word1" (reversed for RTL)
        console.log('RTL MODE - Reversing words before save');
        console.log('  User typed:', newText);
        newText = reverseWords(newText);
        console.log('  Sending to backend:', newText);
    } else {
        console.log('LTR MODE - Sending as-is');
        console.log('  Sending to backend:', newText);
    }
    
    fetch('/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            index: index, 
            text: newText,
            reverse_words: false  // Always false, we already reversed above if needed
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            subtitles = data.dialogues;
            renderSubtitles();
        }
    })
    .catch(error => console.error('Error:', error));
}
        
        function deleteSubtitle(index) {
            if (!confirm('Delete this subtitle line?')) return;
            
            fetch('/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: index})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    subtitles = data.dialogues;
                    document.getElementById('lineCount').textContent = subtitles.length + ' dialogue lines';
                    renderSubtitles();
                }
            })
            .catch(error => console.error('Error:', error));
        }
        
        function exportFile() {
            window.location.href = '/export';
        }
        
        function showGPTPreview() {
            console.log('🔍 Preparing GPT preview...');
            
            // Prepare preview data
            previewReversed = false;
            previewTexts = {};
            subtitles.forEach((sub, index) => {
                previewTexts[index + 1] = extractVisibleText(sub.text);
            });
            
            // Update modal
            document.getElementById('previewCount').textContent = Object.keys(previewTexts).length;
            document.getElementById('reverseLabel').textContent = 'Reverse Word Order';
            
            // Render preview
            renderPreview();
            
            // Show modal
            document.getElementById('gptModal').classList.add('active');
        }
        
        function closeGPTPreview() {
            document.getElementById('gptModal').classList.remove('active');
        }
        
        function togglePreviewReverse() {
            previewReversed = !previewReversed;
            document.getElementById('reverseLabel').textContent = previewReversed ? 'Undo Reverse' : 'Reverse Word Order';
            renderPreview();
        }
        
        function renderPreview() {
            const container = document.getElementById('previewList');
            container.innerHTML = '';
            
            Object.keys(previewTexts).forEach(key => {
                let text = previewTexts[key];
                
                // Apply reversal if toggled
                if (previewReversed) {
                    text = reverseWords(text);
                }
                
                const div = document.createElement('div');
                div.className = 'preview-item';
                div.innerHTML = `
                    <div class="preview-number">Line ${key}</div>
                    <div class="preview-text">${text}</div>
                `;
                container.appendChild(div);
            });
        }
        
        function confirmGPTCorrection() {
            console.log('🤖 Starting GPT correction...');
            
            // Prepare final data with reversal applied if needed
            const finalTexts = {};
            Object.keys(previewTexts).forEach(key => {
                let text = previewTexts[key];
                if (previewReversed) {
                    text = reverseWords(text);
                }
                finalTexts[key] = text;
            });
            
            console.log('📤 Sending to GPT:', finalTexts);
            
            // Close modal
            closeGPTPreview();
            
            // Show loading state
            const gptButton = document.querySelector('.direction-btn[style*="10b981"] span:last-child');
            const oldLabel = gptButton.textContent;
            gptButton.textContent = 'Processing...';
            
            fetch('/gpt_correct', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({texts: finalTexts})
            })
            .then(response => response.json())
            .then(data => {
                console.log('✅ GPT response:', data);
                
                if (data.success) {
                    // Apply corrections
                    const corrected = data.corrected_texts;
                    let changeCount = 0;
                    
                    Object.keys(corrected).forEach(key => {
                        const index = parseInt(key) - 1;
                        if (index >= 0 && index < subtitles.length) {
                            const oldText = extractVisibleText(subtitles[index].text);
                            let newText = corrected[key];
                            
                            // If we reversed for GPT, reverse back the result
                            if (previewReversed) {
                                newText = reverseWords(newText);
                            }
                            
                            if (oldText !== newText) {
                                console.log(`📝 Line ${index + 1}: "${oldText}" → "${newText}"`);
                                changeCount++;
                                
                                // Update via backend
                                fetch('/update', {
                                    method: 'POST',
                                    headers: {'Content-Type': 'application/json'},
                                    body: JSON.stringify({
                                        index: index,
                                        text: newText,
                                        reverse_words: false
                                    })
                                })
                                .then(r => r.json())
                                .then(d => {
                                    if (d.success) {
                                        subtitles = d.dialogues;
                                    }
                                });
                            }
                        }
                    });
                    
                    // Reload after all updates
                    setTimeout(() => {
                        renderSubtitles();
                        alert(`✅ GPT corrected ${changeCount} lines!`);
                        console.log(`✅ Total changes: ${changeCount}`);
                    }, 1000);
                } else {
                    alert('❌ GPT correction failed: ' + data.error);
                    console.error('❌ Error:', data.error);
                }
                
                // Restore button
                gptButton.textContent = oldLabel;
            })
            .catch(error => {
                console.error('❌ Error:', error);
                alert('❌ Error: ' + error);
                gptButton.textContent = oldLabel;
            });
        }
    </script>
</body>
</html>
"""

def parse_ass(content):
    """Parse ASS file content"""
    lines = content.split('\n')
    header = []
    dialogues = []
    in_events = False
    
    for line in lines:
        if line.strip().startswith('[Events]'):
            in_events = True
            header.append(line)
            continue
        
        if line.strip().startswith('Format:') and in_events:
            header.append(line)
            continue
        
        if line.strip().startswith('Dialogue:'):
            parts = line.split(',', 9)
            if len(parts) >= 10:
                dialogues.append({
                    'layer': parts[0].replace('Dialogue:', '').strip(),
                    'start': parts[1].strip(),
                    'end': parts[2].strip(),
                    'style': parts[3].strip(),
                    'name': parts[4].strip(),
                    'marginL': parts[5].strip(),
                    'marginR': parts[6].strip(),
                    'marginV': parts[7].strip(),
                    'effect': parts[8].strip(),
                    'text': parts[9].strip()
                })
        elif not in_events:
            header.append(line)
    
    return '\n'.join(header), dialogues

def is_rtl_text(text):
    """Check if text is RTL (Arabic/Persian/Hebrew)"""
    rtl_chars = 0
    total_chars = 0
    
    for char in text:
        if char.isalpha():
            total_chars += 1
            # Check for Arabic, Persian, Hebrew characters
            if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' or '\u0590' <= char <= '\u05FF':
                rtl_chars += 1
    
    if total_chars == 0:
        return False
    
    return rtl_chars / total_chars > 0.5

def extract_visible_text(text):
    """Extract visible text without ASS tags"""
    cleaned = re.sub(r'\{[^}]*\}', '', text)
    cleaned = re.sub(r'\[[A-Z0-9]+\]\s*', '', cleaned)
    cleaned = cleaned.strip()
    
    # If RTL text, add RLE marker to force RTL display
    if cleaned and is_rtl_text(cleaned):
        # Add Right-to-Left Embedding
        cleaned = '\u202B' + cleaned + '\u202C'
    
    return cleaned

def update_dialogue_text(dialogue, new_text, reverse_words=False):
    """Uses exact same styling as original generator"""
    original = dialogue['text']
    
    # Parse new words
    new_words = new_text.strip().split()
    
    if len(new_words) == 0:
        dialogue['text'] = ''
        return dialogue
    
    # Check if original has karaoke timing
    has_karaoke = r'\t(' in original
    
    if has_karaoke:
        # Extract ALL original timings
        timing_pattern = re.findall(r'\{\\t\((\d+),(\d+),[^)]*\)\}', original)
        
        if len(timing_pattern) > 0:
            # Get original word count (each word has 2 timing tags, so divide by 2)
            original_word_count = len(timing_pattern) // 2
            new_word_count = len(new_words)
            
            # Extract all start times to find the true range
            all_start_times = [int(timing_pattern[i][0]) for i in range(0, len(timing_pattern), 2)]
            all_end_times = [int(timing_pattern[i][1]) for i in range(0, len(timing_pattern), 2)]
            
            # True chronological range
            total_start_ms = min(all_start_times)
            total_end_ms = max(all_end_times)
            total_duration_ms = total_end_ms - total_start_ms
            
            print(f"\n=== DEBUG: update_dialogue_text ===")
            print(f"Original word count: {original_word_count}")
            print(f"New word count: {new_word_count}")
            print(f"All start times: {all_start_times}")
            print(f"All end times: {all_end_times}")
            print(f"Total duration: {total_duration_ms}ms ({total_duration_ms/1000:.2f}s)")
            print(f"Total start: {total_start_ms}ms, Total end: {total_end_ms}ms")
            
            # Fix punctuation function
            def fix_punct(s):
                s = s.replace(".", "").replace(",", "").replace("،", "")
                return s.replace("?", "؟").replace(";", "؛")
            
            kao_tokens = []
            
            # CASE 1: Word count MATCHES - use original timings exactly
            if original_word_count == new_word_count:
                print(f"CASE 1: Word count matches, using original timings")
                for i in range(new_word_count-1, -1, -1):  # Reverse for RTL
                    word = fix_punct(new_words[i].strip())
                    if not word:
                        continue
                    
                    # Position in timing order
                    word_index = new_word_count - 1 - i
                    
                    # Get original timing for this word
                    start_ms = int(timing_pattern[word_index * 2][0])
                    end_ms = int(timing_pattern[word_index * 2][1])
                    
                    print(f"  Word '{word}': {start_ms}ms -> {end_ms}ms (duration: {end_ms-start_ms}ms)")
                    
                    # Use EXACT original styling
                    kao_tokens.append(
                        r"{\t(" + str(start_ms) + "," + str(end_ms) + 
                        r",\c&H00FFFF&\3c&H000000&\bord5\b1\fscx125\fscy125)}" + word + 
                        r"{\t(" + str(end_ms) + "," + str(end_ms+1) + 
                        r",\c&HFFFFFF&\3c&H000000&\bord4\b0\fscx100\fscy100)}"
                    )
            
            # CASE 2: Word count DIFFERENT - distribute timing naturally
            else:
                print(f"CASE 2: Word count changed, redistributing timing")
                
                # Calculate total character count for proportional distribution
                char_counts = [len(fix_punct(w.strip())) for w in new_words]
                total_chars = sum(char_counts)
                
                print(f"Character counts: {char_counts}, Total chars: {total_chars}")
                print(f"New words (LTR order): {new_words}")
                
                if total_chars == 0:
                    dialogue['text'] = ''
                    return dialogue
                
                # Special handling for single word - center it in the timeline
                if new_word_count == 1:
                    print(f"SINGLE WORD MODE: Centering highlight in timeline")
                    
                    # Default highlight duration (adjust this to taste)
                    highlight_duration = min(500, total_duration_ms // 2)  # 500ms or half duration
                    
                    # Center the highlight
                    center_point = total_start_ms + (total_duration_ms // 2)
                    start_ms = center_point - (highlight_duration // 2)
                    end_ms = start_ms + highlight_duration
                    
                    print(f"  Center point: {center_point}ms")
                    print(f"  Highlight duration: {highlight_duration}ms")
                    print(f"  Highlight start: {start_ms}ms, end: {end_ms}ms")
                    
                    word = fix_punct(new_words[0].strip())
                    kao_tokens.append(
                        r"{\t(" + str(start_ms) + "," + str(end_ms) + 
                        r",\c&H00FFFF&\3c&H000000&\bord5\b1\fscx125\fscy125)}" + word + 
                        r"{\t(" + str(end_ms) + "," + str(end_ms+1) + 
                        r",\c&HFFFFFF&\3c&H000000&\bord4\b0\fscx100\fscy100)}"
                    )
                else:
                    # Multiple words - distribute proportionally, each word highlights in sequence
                    print(f"MULTIPLE WORDS MODE: Sequential highlighting starting from 0")
                    
                    # Distribute time proportionally based on character count
                    word_durations = []
                    for char_count in char_counts:
                        duration = int((char_count / total_chars) * total_duration_ms)
                        word_durations.append(max(duration, 100))  # Minimum 100ms per word
                    
                    print(f"Initial word durations: {word_durations}")
                    
                    # Adjust to match total duration exactly
                    duration_sum = sum(word_durations)
                    if duration_sum != total_duration_ms:
                        # Add/subtract difference to longest word
                        longest_idx = word_durations.index(max(word_durations))
                        adjustment = total_duration_ms - duration_sum
                        word_durations[longest_idx] += adjustment
                        print(f"Adjusted word {longest_idx} by {adjustment}ms")
                    
                    print(f"Final word durations: {word_durations} (sum: {sum(word_durations)}ms)")
                    
                    # Calculate start/end times for each word - Sequential from 0
                    word_timings = []
                    current_time = 0
                    for idx, duration in enumerate(word_durations):
                        start = current_time
                        end = current_time + duration
                        word_timings.append((start, end))
                        print(f"  Word {idx} LTR ('{new_words[idx]}'): {start}ms -> {end}ms (duration: {duration}ms)")
                        current_time = end
                    
                    # REVERSE word_timings for RTL output!
                    word_timings_rtl = list(reversed(word_timings))
                    print(f"\nRTL timing assignment:")
                    
                    # Build karaoke tokens in REVERSE order (RTL)
                    for i in range(new_word_count-1, -1, -1):
                        word = fix_punct(new_words[i].strip())
                        if not word:
                            continue
                        
                        # For RTL: visual position i gets timing from RTL list
                        visual_position = new_word_count - 1 - i
                        
                        start_ms = word_timings_rtl[visual_position][0]
                        end_ms = word_timings_rtl[visual_position][1]
                        
                        print(f"  Visual pos {visual_position}, Word '{word}' (index {i}): {start_ms}ms -> {end_ms}ms")
                        
                        # Use EXACT same styling as make_ass and Case 1
                        kao_tokens.append(
                            r"{\t(" + str(start_ms) + "," + str(end_ms) + 
                            r",\c&H00FFFF&\3c&H000000&\bord5\b1\fscx125\fscy125)}" + word + 
                            r"{\t(" + str(end_ms) + "," + str(end_ms+1) + 
                            r",\c&HFFFFFF&\3c&H000000&\bord4\b0\fscx100\fscy100)}"
                        )
            
            dialogue['text'] = r"{\an2\q2}" + " ".join(kao_tokens)
            print(f"=== END DEBUG ===\n")
        else:
            dialogue['text'] = ' '.join(new_words)
    else:
        dialogue['text'] = ' '.join(new_words)
    
    return dialogue


def build_dialogue_line(dialogue):
    """Build dialogue line for ASS file"""
    return f"Dialogue: {dialogue['layer']},{dialogue['start']},{dialogue['end']},{dialogue['style']},{dialogue['name']},{dialogue['marginL']},{dialogue['marginR']},{dialogue['marginV']},{dialogue['effect']},{dialogue['text']}"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    content = file.read().decode('utf-8')
    header, dialogues = parse_ass(content)
    
    subtitles_data['header'] = header
    subtitles_data['dialogues'] = dialogues
    subtitles_data['filename'] = file.filename
    
    return jsonify({
        'success': True,
        'filename': file.filename,
        'dialogues': dialogues
    })

@app.route('/update', methods=['POST'])
def update():
    data = request.json
    index = data.get('index')
    new_text = data.get('text')
    reverse_words = data.get('reverse_words', False)
    
    if index is None or index >= len(subtitles_data['dialogues']):
        return jsonify({'success': False, 'error': 'Invalid index'})
    
    dialogue = subtitles_data['dialogues'][index]
    update_dialogue_text(dialogue, new_text, reverse_words=reverse_words)
    
    return jsonify({
        'success': True,
        'dialogues': subtitles_data['dialogues']
    })

@app.route('/delete', methods=['POST'])
def delete():
    data = request.json
    index = data.get('index')
    
    if index is None or index >= len(subtitles_data['dialogues']):
        return jsonify({'success': False, 'error': 'Invalid index'})
    
    subtitles_data['dialogues'].pop(index)
    
    return jsonify({
        'success': True,
        'dialogues': subtitles_data['dialogues']
    })

@app.route('/export')
def export():
    dialogue_lines = [build_dialogue_line(d) for d in subtitles_data['dialogues']]
    full_content = subtitles_data['header'] + '\n' + '\n'.join(dialogue_lines)
    
    buffer = BytesIO()
    buffer.write(full_content.encode('utf-8'))
    buffer.seek(0)
    
    filename = subtitles_data['filename'] or 'edited_subtitles.ass'
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )

@app.route('/gpt_correct', methods=['POST'])
def gpt_correct():
    """Send texts to GPT for grammar/spelling correction"""
    try:
        data = request.json
        texts = data.get('texts', {})
        
        print(f"\n{'='*60}")
        print(f"🤖 GPT CORRECTION REQUEST")
        print(f"{'='*60}")
        print(f"📊 Total lines to correct: {len(texts)}")
        print(f"📝 Input data: {texts}")
        
        # Prepare prompt with JSON data
        user_message = f"Correct the following Persian/Arabic subtitle texts:\n\n{texts}"
        
        print(f"\n📤 Sending to GPT-4...")
        print(f"💬 Prompt length: {len(user_message)} chars")
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": CORRECTION_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        reply = response.choices[0].message.content.strip()
        
        print(f"\n✅ GPT-4 Response received")
        print(f"📊 Tokens used: {response.usage.total_tokens}")
        print(f"💰 Prompt tokens: {response.usage.prompt_tokens}")
        print(f"💰 Completion tokens: {response.usage.completion_tokens}")
        print(f"📝 Response: {reply[:500]}...")
        
        # Parse JSON response
        import json
        try:
            # Try to extract JSON from response (in case GPT adds extra text)
            if '{' in reply and '}' in reply:
                json_start = reply.index('{')
                json_end = reply.rindex('}') + 1
                json_str = reply[json_start:json_end]
                
                # GPT sometimes uses single quotes - fix it
                json_str = json_str.replace("'", '"')
                
                corrected_texts = json.loads(json_str)
            else:
                corrected_texts = json.loads(reply)
            
            print(f"\n✅ Parsed corrected texts: {corrected_texts}")
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': True,
                'corrected_texts': corrected_texts
            })
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parsing error: {e}")
            print(f"📝 Raw response: {reply}")
            print(f"{'='*60}\n")
            return jsonify({
                'success': False,
                'error': f'Failed to parse GPT response: {str(e)}'
            })
            
    except Exception as e:
        print(f"\n❌ ERROR in GPT correction: {str(e)}")
        print(f"{'='*60}\n")
        return jsonify({
            'success': False,
            'error': str(e)
        })
import tempfile
import shutil
import burn_video
@app.route('/hardsub', methods=['POST'])
def hardsub():
    """Apply subtitles to video"""
    try:
        video_file = request.files.get('video')
        quality = request.form.get('quality', 'medium')
        reverse_words_str = request.form.get('reverse_words', 'false')
        reverse_words = reverse_words_str.lower() == 'true'
        
        if not video_file:
            return jsonify({'success': False, 'error': 'No video file'})
        
        print(f"\n{'='*60}")
        print(f"HARDSUB REQUEST")
        print(f"{'='*60}")
        print(f"Video: {video_file.filename}")
        print(f"Quality: {quality}")
        print(f"Reverse parameter received: '{reverse_words_str}'")
        print(f"Reverse boolean: {reverse_words}")
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Save video
            video_path = os.path.join(temp_dir, 'input_video.mp4')
            video_file.save(video_path)
            
            # Save ASS file
            ass_path = os.path.join(temp_dir, 'subtitles.ass')
            
            # Make a deep copy so we don't modify the original
            import copy
            dialogues = copy.deepcopy(subtitles_data['dialogues'])
            
            print(f"\n{'='*60}")
            print(f"PROCESSING DIALOGUES")
            print(f"{'='*60}")
            print(f"Total dialogues: {len(dialogues)}")
            
            if reverse_words:
                # User clicked reverse button - they want LTR
                print(f"\nMODE: REVERSE BUTTON CLICKED (SINGLE REVERSE)")
                for idx, d in enumerate(dialogues):
                    # Extract visible text
                    visible = re.sub(r'\{[^}]*\}', '', d['text'])
                    visible = re.sub(r'\[[A-Z0-9]+\]\s*', '', visible)
                    visible = visible.strip()
                    
                    # Reverse once
                    words = visible.split()
                    reversed_once = list(reversed(words))
                    final_text = ' '.join(reversed_once)
                    
                    print(f"\nLine {idx+1}:")
                    print(f"  Original ASS: {visible}")
                    print(f"  After 1x reverse: {final_text}")
                    
                    update_dialogue_text(d, final_text, reverse_words=False)
            else:
                # User did NOT click reverse - they want RTL (default)
                # DOUBLE REVERSE to fix the bug
                print(f"\nMODE: NO REVERSE BUTTON (DOUBLE REVERSE TO FIX)")
                for idx, d in enumerate(dialogues):
                    # Extract visible text
                    visible = re.sub(r'\{[^}]*\}', '', d['text'])
                    visible = re.sub(r'\[[A-Z0-9]+\]\s*', '', visible)
                    visible = visible.strip()
                    
                    # Reverse twice (to undo whatever fuckery is happening)
                    words = visible.split()
                    
                    reversed_once = list(reversed(words))
                    reversed_twice = list(reversed(reversed_once))
                    final_text = ' '.join(reversed_twice)
                    
                    print(f"\nLine {idx+1}:")
                    print(f"  Original ASS: {visible}")
                    print(f"  After 1x reverse: {' '.join(reversed_once)}")
                    print(f"  After 2x reverse: {final_text}")
                    
                    update_dialogue_text(d, final_text, reverse_words=False)
            
            # Build ASS file
            dialogue_lines = [build_dialogue_line(d) for d in dialogues]
            full_ass = subtitles_data['header'] + '\n' + '\n'.join(dialogue_lines)
            
            with open(ass_path, 'w', encoding='utf-8') as f:
                f.write(full_ass)
            
            print(f"\nASS file saved to: {ass_path}")
            print(f"\n{'='*60}")
            print(f"STARTING FFMPEG")
            print(f"{'='*60}\n")
            
            # Output path
            output_path = os.path.join(temp_dir, 'output_subbed.mp4')
            
            # Run burn_subtitles
            burn_video.burn_subtitles(video_path, ass_path, output_path, quality=quality, verbose=True)
            
            print(f"\nHardsub completed!")
            
            # Send file
            return send_file(
                output_path,
                as_attachment=True,
                download_name=video_file.filename.replace('.', '_subbed.'),
                mimetype='video/mp4'
            )
            
        finally:
            # Cleanup temp files
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        import traceback
        print(f"\nHardsub error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500
if __name__ == '__main__':
    print("=" * 60)
    print("ASS Subtitle Editor - Web UI")
    print("=" * 60)
    print("\n🚀 Server starting...")
    print("📝 Open in browser: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5000)