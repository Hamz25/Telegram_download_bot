"""
Language Support Module
Provides multilingual text support for the bot interface.
"""

# Dictionary of language texts
TEXTS = {
    "en": {
        # General
        "welcome": "👋 Welcome to Social Media Downloader Bot!\n\n"
                   "📱 **Supported Platforms:**\n"
                   "• YouTube (Videos, Shorts, Audio)\n"
                   "• TikTok (Videos, Photos, Audio)\n"
                   "• Instagram (Stories, Reels, Posts, Highlights)\n"
                   "• Snapchat\n"
                   "• Spotify (Audio)\n\n"
                   "📝 **How to use:**\n"
                   "Just send me a link from any supported platform!\n\n"
                   "🔧 **Commands:**\n"
                   "/start - start the bot\n"
                   "/report - Report a problem\n",
        
        "uploading": "⏳ Downloading and uploading... Please wait.",
        "fetching": "🔍 Fetching information...",
        "no_media": "❌ No media found or download failed.",
        "upload_failed": "❌ Upload failed. Please try again.",
        "file_too_large": "⚠️ File is too large ({size}MB). Telegram limit is 50MB.",
        "error_general": "❌ Error: {e}",
        "error_file_not_found": "❌ File not found.",
        "error_invalid": "❌ Invalid request.",
        "error_session": "❌ Session expired. Please try again.",
        "error_unsupported_url": "❌ Unsupported URL format.",
        "error_private_profile": "❌ This profile is private.",
        "error_session_expired": "❌ Session expired. Please try again.",
        "error_audio": "❌ Audio extraction failed.",
        
        # Success messages
        "tiktok_success": "✅ TikTok downloaded successfully!",
        "snap_success": "✅ Snapchat downloaded successfully!",
        "insta_reel_success": "✅ Instagram Reel downloaded successfully!",
        "insta_post_success": "✅ Instagram Post downloaded successfully!",
        "highlight_success": "✅ Highlight '{title}' downloaded successfully!",
        "all_highlights_success": "✅ All {count} highlights downloaded successfully!",
        "tiktok_audio": "🎵 TikTok Audio",
        "tiktok_voice": "🎤 TikTok Voice Message",
        
        # Instagram specific
        "insta_stories": "📸 Stories from @{username}",
        "profile_found": "📱 **Instagram Profile Found**\n\n"
                         "👤 **Username:** @{username}\n"
                         "👋 **Name:** {full_name}\n"
                         "👥 **Followers:** {followers}\n"
                         "🤝 **Following:** {following}\n"
                         "📸 **Posts:** {posts}\n"
                         "✅ **Verified:** {verified}\n"
                         "🔐 **Private:** {private}",
        
        "profile_details": "📱 **Profile Details**\n\n"
                           "👤 **Username:** @{username}\n"
                           "👋 **Name:** {full_name}\n"
                           "📝 **Bio:** {bio}\n\n"
                           "📊 **Statistics:**\n"
                           "👥 **Followers:** {followers}\n"
                           "🤝 **Following:** {following}\n"
                           "📸 **Posts:** {posts}\n\n"
                           "⚙️ **Settings:**\n"
                           "✅ **Verified:** {verified}\n"
                           "🔐 **Private:** {private}",
        
        "profile_not_found": "❌ Profile @{username} not found.",
        "no_bio": "No bio available",
        "no_highlights": "ℹ️ No highlights found for @{username}.",
        "no_active_stories": "ℹ️ No active stories found for @{username}.",
        "downloading_stories": "📥 Downloading stories...",
        "downloading_highlight": "📥 Downloading highlight...",
        "select_highlight": "📋 Select a highlight to download ({count} available):",
        
        # YouTube specific
        "shorts_detected": "🎬 YouTube Short detected! Downloading...",
        "video_found": "📺 **Video Found!**\n\nSelect quality:",
        "choose_format": "🎬 **Download Options**\n\nSelect format:",
        
        # Buttons
        "btn_video": "📹 Video",
        "btn_audio": "🎵 Audio",
        "btn_voice": "🎤 Voice",
        "btn_profile_details": "📊 Profile Details",
        "btn_highlights": "📚 Highlights",
        "btn_stories": "📸 Stories",
        "btn_download_all_highlights": "📥 Download All Highlights",
        
        # Yes/No
        "yes": "Yes",
        "no": "No",
        "TestError": "Test",
    },
    
    "ar": {
        # General
        "welcome": "👋 مرحبًا بكم في بوت تحميل منصات التواصل الاجتماعي!\n\n"
                   "📱 **المنصات المدعومة:**\n"
                   "• يوتيوب (فيديوهات، قصير، صوت)\n"
                   "• تيك توك (فيديوهات، صور، صوت)\n"
                   "• إنستجرام (ستوريز، ريلز، منشورات، هايلايتس)\n"
                   "• سناب شات\n"
                   "• سبوتيفاي (صوت)\n\n"
                   "📝 **طريقة الاستخدام:**\n"
                   "فقط أرسل لي رابط من أي منصة مدعومة!\n\n"
                   "🔧 **الأوامر:**\n"
                   "/start - لبدء البوت\n"
                   "/report - الإبلاغ عن مشكلة\n",
        
        "uploading": "⏳ جاري التحميل والرفع... الرجاء الانتظار.",
        "fetching": "🔍 جاري جلب المعلومات...",
        "no_media": "❌ لم يتم العثور على ملفات أو فشل التحميل.",
        "upload_failed": "❌ فشل الرفع. الرجاء المحاولة مرة أخرى.",
        "file_too_large": "⚠️ الملف كبير جدًا ({size} ميجابايت). الحد الأقصى في تليجرام هو 50 ميجابايت.",
        "error_general": "❌ خطأ: {e}",
        "error_file_not_found": "❌ الملف غير موجود.",
        "error_invalid": "❌ طلب غير صالح.",
        "error_session": "❌ انتهت الجلسة. الرجاء المحاولة مرة أخرى.",
        "error_unsupported_url": "❌ تنسيق الرابط غير مدعوم.",
        "error_private_profile": "❌ هذا الحساب خاص.",
        "error_session_expired": "❌ انتهت الجلسة. الرجاء المحاولة مرة أخرى.",
        "error_audio": "❌ فشل استخراج الصوت.",
        
        # Success messages
        "tiktok_success": "✅ تم تحميل التيك توك بنجاح!",
        "snap_success": "✅ تم تحميل السناب شات بنجاح!",
        "insta_reel_success": "✅ تم تحميل ريل الإنستجرام بنجاح!",
        "insta_post_success": "✅ تم تحميل منشور الإنستجرام بنجاح!",
        "highlight_success": "✅ تم تحميل الهايلايت '{title}' بنجاح!",
        "all_highlights_success": "✅ تم تحميل جميع الهايلايتس ({count}) بنجاح!",
        "tiktok_audio": "🎵 صوت تيك توك",
        "tiktok_voice": "🎤 رسالة صوتية من تيك توك",
        
        # Instagram specific
        "insta_stories": "📸 ستوريات @{username}",
        "profile_found": "📱 **تم العثور على حساب إنستجرام**\n\n"
                         "👤 **اسم المستخدم:** @{username}\n"
                         "👋 **الاسم:** {full_name}\n"
                         "👥 **المتابعون:** {followers}\n"
                         "🤝 **يتابع:** {following}\n"
                         "📸 **المنشورات:** {posts}\n"
                         "✅ **موثق:** {verified}\n"
                         "🔐 **خاص:** {private}",
        
        "profile_details": "📱 **تفاصيل الحساب**\n\n"
                           "👤 **اسم المستخدم:** @{username}\n"
                           "👋 **الاسم:** {full_name}\n"
                           "📝 **السيرة:** {bio}\n\n"
                           "📊 **الإحصائيات:**\n"
                           "👥 **المتابعون:** {followers}\n"
                           "🤝 **يتابع:** {following}\n"
                           "📸 **المنشورات:** {posts}\n\n"
                           "⚙️ **الإعدادات:**\n"
                           "✅ **موثق:** {verified}\n"
                           "🔐 **خاص:** {private}",
        
        "profile_not_found": "❌ لم يتم العثور على الحساب @{username}.",
        "no_bio": "لا توجد سيرة ذاتية",
        "no_highlights": "ℹ️ لم يتم العثور على هايلايتس لـ @{username}.",
        "no_active_stories": "ℹ️ لم يتم العثور على ستوريات نشطة لـ @{username}.",
        "downloading_stories": "📥 جاري تحميل الستوريات...",
        "downloading_highlight": "📥 جاري تحميل الهايلايت...",
        "select_highlight": "📋 اختر هايلايت للتحميل ({count} متاح):",
        
        # YouTube specific
        "shorts_detected": "🎬 تم اكتشاف فيديو قصير من يوتيوب! جاري التحميل...",
        "video_found": "📺 **تم العثور على الفيديو!**\n\nاختر الجودة:",
        "choose_format": "🎬 **خيارات التحميل**\n\nاختر التنسيق:",
        
        # Buttons
        "btn_video": "📹 فيديو",
        "btn_audio": "🎵 صوت",
        "btn_voice": "🎤 رسالة صوتية",
        "btn_profile_details": "📊 تفاصيل الحساب",
        "btn_highlights": "📚 الهايلايتس",
        "btn_stories": "📸 الستوريات",
        "btn_download_all_highlights": "📥 تحميل كل الهايلايتس",
        
        # Yes/No
        "yes": "نعم",
        "no": "لا",
    }
}


def get_text(key: str, lang: str = "en") -> str:
    """
    Get translated text for a given key and language.
    
    Args:
        key: Text key to retrieve
        lang: Language code (default: 'en')
        
    Returns:
        str: Translated text or key if not found
    """
    # Default to English if language not supported
    if lang not in TEXTS:
        lang = "en"
    
    # Return the text or the key itself if not found
    return TEXTS.get(lang, {}).get(key, TEXTS["en"].get(key, key))