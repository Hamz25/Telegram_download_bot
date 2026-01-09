TEXTS = {
    "en": {
        "welcome": "Welcome! Send a link to begin.",
        "shorts_detected": "⚡ <b>Shorts detected!</b> Downloading...",
        "video_found": "📺 <b>Video Found!</b> Select quality:",
        "uploading": "⏳ <b>Uploading to Telegram...</b>",
        "duration": "Duration",
        "title": "Title",
        "quality": "Quality",
        "error_general": "❌ <b>Error:</b> {e}",
        "tiktok_success": "✅ <b>TikTok Downloaded</b>",
        "snap_success": "✅ <b>Snap Downloaded</b>",
        "insta_stories": "📱 <b>Stories from @{username}</b>",
        "file_too_large": "❌ <b>File too large ({size}MB)</b>",
        "no_media": "❌ No media found.",
        "fetching": "⏳ Fetching content...",
    },
    "ar": {
        "welcome": "أهلاً بك! أرسل رابطاً للبدء.",
        "shorts_detected": "⚡ <b>تم اكتشاف فيديو قصير!</b> جاري التحميل...",
        "video_found": "📺 <b>تم العثور على الفيديو!</b> اختر الجودة:",
        "uploading": "⏳ <b>جاري الرفع إلى تليجرام...</b>",
        "duration": "المدة",
        "title": "عنوان الفيديو",
        "quality": "الجودة",
        "error_general": "❌ <b>خطأ:</b> {e}",
        "tiktok_success": "✅ <b>تم تحميل تيك توك</b>",
        "snap_success": "✅ <b>تم تحميل سناب شات</b>",
        "insta_stories": "📱 <b>ستوري من @{username}</b>",
        "file_too_large": "❌ <b>الملف كبير جداً ({size} ميجابايت)</b>",
        "no_media": "❌ لم يتم العثور على وسائط.",
        "fetching": "⏳ جاري جلب البيانات...",
    }
}

def get_text(key, lang_code):
    lang = lang_code if lang_code in TEXTS else "en"
    return TEXTS[lang].get(key, TEXTS["en"][key])