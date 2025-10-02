#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# python burn_video.py --video /Users/yaldahaghighi/NokhbehShoVideos/promoteVideo.mov  --ass promoteVideo.ass  --quality instagram

import argparse, os, subprocess, sys

def run(cmd, verbose=False):
    """اجرای دستور و بررسی خروجی"""
    if verbose:
        print(f"[CMD] {' '.join(cmd)}")
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        print(p.stdout)
        raise SystemExit(f"Command failed: {' '.join(cmd)}")
    return p.stdout

def check_files(video_path, ass_path):
    """بررسی وجود فایل‌های ورودی"""
    if not os.path.exists(video_path):
        raise SystemExit(f"[خطا] فایل ویدیو پیدا نشد: {video_path}")
    if not os.path.exists(ass_path):
        raise SystemExit(f"[خطا] فایل زیرنویس پیدا نشد: {ass_path}")
    return True

def get_video_info(video_path):
    """دریافت اطلاعات ویدیو با ffprobe"""
    try:
        cmd = [
            "ffprobe", "-v", "error", 
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name,duration",
            "-of", "json", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            if info.get("streams"):
                stream = info["streams"][0]
                return {
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                    "codec": stream.get("codec_name"),
                    "duration": stream.get("duration")
                }
    except:
        pass
    return None



def burn_subtitles(video_path, ass_path, output_path, quality="high", verbose=False):
    """اعمال زیرنویس روی ویدیو"""
    
    # تنظیمات کیفیت
    quality_presets = {
        "high": {
            "crf": "18",
            "preset": "slow",
            "bitrate": None
        },
        "medium": {
            "crf": "23",
            "preset": "medium",
            "bitrate": None
        },
        "low": {
            "crf": "28",
            "preset": "fast",
            "bitrate": None
        },
        "instagram": {
            "crf": "23",
            "preset": "medium",
            "bitrate": "5M"
        }
    }
    
    preset = quality_presets.get(quality, quality_presets["medium"])
     #Use the working static FFmpeg build
    ffmpeg_bin = '/home/imanbahmani/ffmpeg-7.0.2-amd64-static/ffmpeg'
    # ساخت دستور ffmpeg
    cmd = [
        ffmpeg_bin, "-y",
        "-i", video_path,
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264",
        "-crf", preset["crf"],
        "-preset", preset["preset"],
        "-c:a", "copy"  # کپی صدا بدون تغییر
    ]
    
    # اضافه کردن bitrate اگر تنظیم شده
    if preset["bitrate"]:
        cmd.extend(["-b:v", preset["bitrate"]])
    
    # اضافه کردن خروجی
    cmd.append(output_path)
    
    print(f"[i] اعمال زیرنویس با کیفیت {quality}...")
    run(cmd, verbose=verbose)




def main():
    ap = argparse.ArgumentParser(
        description="اعمال فایل زیرنویس ASS روی ویدیو",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
مثال‌های استفاده:
  %(prog)s --video input.mp4 --ass subtitles.ass
  %(prog)s --video input.mp4 --ass subtitles.ass --out output_with_subs.mp4
  %(prog)s --video input.mp4 --ass subtitles.ass --quality instagram
  
کیفیت‌های موجود:
  high      - بالاترین کیفیت (CRF 18)
  medium    - کیفیت متوسط (CRF 23) - پیش‌فرض
  low       - کیفیت پایین برای حجم کم (CRF 28)
  instagram - بهینه برای اینستاگرام (CRF 23 + 5Mbps)
        """
    )
    
    ap.add_argument("--video", dest="video", required=True, 
                   help="فایل ویدیو ورودی")
    ap.add_argument("--ass", dest="ass", required=True,
                   help="فایل زیرنویس ASS")
    ap.add_argument("--out", dest="out",
                   help="فایل ویدیو خروجی (پیش‌فرض: نام_ویدیو_subbed.mp4)")
    ap.add_argument("--quality", dest="quality", default="medium",
                   choices=["high", "medium", "low", "instagram"],
                   help="کیفیت خروجی (پیش‌فرض: medium)")
    ap.add_argument("--verbose", dest="verbose", action="store_true",
                   help="نمایش دستورات ffmpeg")
    ap.add_argument("--info", dest="info", action="store_true",
                   help="نمایش اطلاعات ویدیو ورودی")
    
    args = ap.parse_args()
    
    # بررسی وجود فایل‌ها
    check_files(args.video, args.ass)
    
    # نمایش اطلاعات ویدیو
    if args.info:
        print("\n[i] اطلاعات ویدیو ورودی:")
        info = get_video_info(args.video)
        if info:
            print(f"  - رزولوشن: {info['width']}x{info['height']}")
            print(f"  - کدک: {info['codec']}")
            if info['duration']:
                duration = float(info['duration'])
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                print(f"  - مدت زمان: {minutes}:{seconds:02d}")
        print()
    
    # تعیین نام خروجی
    if not args.out:
        base_name = os.path.splitext(os.path.basename(args.video))[0]
        ext = os.path.splitext(args.video)[1]
        args.out = f"{base_name}_subbed{ext}"
    
    # نمایش اطلاعات پردازش
    print(f"[i] فایل ویدیو: {args.video}")
    print(f"[i] فایل زیرنویس: {args.ass}")
    print(f"[i] فایل خروجی: {args.out}")
    print(f"[i] کیفیت: {args.quality}")
    print()
    
    # اعمال زیرنویس
    try:
        burn_subtitles(args.video, args.ass, args.out, 
                      quality=args.quality, verbose=args.verbose)
        print(f"\n[✓] ویدیو با موفقیت ذخیره شد: {args.out}")
        
        # نمایش حجم فایل‌ها
        video_size = os.path.getsize(args.video) / (1024 * 1024)
        output_size = os.path.getsize(args.out) / (1024 * 1024)
        print(f"[i] حجم ویدیو اصلی: {video_size:.1f} MB")
        print(f"[i] حجم ویدیو خروجی: {output_size:.1f} MB")
        
    except KeyboardInterrupt:
        print("\n[!] عملیات توسط کاربر لغو شد.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[خطا] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()