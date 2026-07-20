"""
Language Support Module
Provides multilingual text support for the bot interface.
"""

# Dictionary of language texts
TEXTS = {
    "en": {
        # General
        "welcome": "👋 Welcome to <b>Spoon Download bot</b>\n\n"
                   "  **Supported Platforms:**\n"
                    "• YouTube (Videos, Shorts, Audio)\n"
                    "• TikTok (Videos, Photos, Audio)\n"
                    "• Instagram (Reels, Posts)\n"
                    "• Pinterest (Pins, Boards)\n"
                    "• Snapchat\n"
                    "• Spotify (Audio)\n\n"
                    "  **How to use:**\n"
                    "Just send me a <b>link</b> from any supported platform\n\n"
                    "  **Commands:**\n"
                    "/start - start the bot\n"
                    "/report - Report a problem\n"
                    "This bot was developed by @dillR_2",

        "update": "<b>This feature is currently unavailable and will be available in the next update. Thank you for your understanding.</b>",
        "uploading": "<b>Downloading and uploading... Please wait.</b>",
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
        "tiktok_success": "@SpoonDbot",
        "snap_success": "@SpoonDbot",
        "insta_reel_success": "@SpoonDbot",
        "insta_post_success": "@SpoonDbot",
        "pinterest_pin_success": "@SpoonDbot",
        "pinterest_board_success": "@SpoonDbot",
        "highlight_success": "@SpoonDbot",
        "all_highlights_success": "@SpoonDbot",
        "tiktok_audio": "@SpoonDbot",
        "tiktok_voice": "@SpoonDbot",
        "x_success": "@SpoonDbot",
        "threads_sucess": "@SpoonDbot",
        "facebook_success": "@SpoonDbot",
        
        # Instagram specific
        "insta_stories": " Stories from @{username}",
        "profile_found": " **Instagram Profile Found**\n\n"
                         " **Username:** @{username}\n"
                         " **Name:** {full_name}\n"
                         " **Followers:** {followers}\n"
                         " **Following:** {following}\n"
                         " **Posts:** {posts}\n"
                         " **Verified:** {verified}\n"
                         " **Private:** {private}",
        
        "profile_details": " **Profile Details**\n\n"
                           " **Username:** @{username}\n"
                           " **Name:** {full_name}\n"
                           " **Bio:** {bio}\n\n"
                           " **Statistics:**\n"
                           " **Followers:** {followers}\n"
                           " **Following:** {following}\n"
                           " **Posts:** {posts}\n\n"
                           " **Settings:**\n"
                           " **Verified:** {verified}\n"
                           " **Private:** {private}",
        
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
        "spoon": "@spoonDbot",



        # Testing
        "test_mode_activated": "✅ Test mode activated! You can now use test commands.",
    },
    
    "ar": {
        # General
        "welcome": "<b>اهلا بكم ببوت سبون</b>\n\n"
                    " <b>المنصات المدعومة:</b>\n"
                    "• يوتيوب (فيديوهات، يوتيوب شورت， صوت)\n"
                    "• تيك توك (فيديوهات， صور， صوت)\n"
                    "• إنستجرام (ريلز， منشورات)\n"
                    "• بينترست (صور، مجموعات)\n"
                    "• سناب شات\n"
                    "• سبوتيفاي (صوت)\n\n"
                    " <b>طريقة الاستخدام:</b>\n"
                    "فقط أرسل لي رابط من أي منصة مدعومة!\n\n"
                    " <b>الأوامر:</b>\n"
                    "/start - لبدء البوت\n"
                    "/report - الإبلاغ عن مشكلة\n",
        "update":"<b> حاليا هذه الخاصية غير متوفرة ستتوفر في اقرب تحديث شكرا لتفهمكم</b>",
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
        "tiktok_success": "@SpoonDbot",
        "snap_success": "@SpoonDbot",
        "insta_reel_success": "@SpoonDbot",
        "insta_post_success": "@SpoonDbot",
        "pinterest_pin_success": "@SpoonDbot",
        "pinterest_board_success": "@SpoonDbot",
        "highlight_success": "@SpoonDbot",
        "all_highlights_success": "@SpoonDbot",
        "tiktok_audio": "@SpoonDbot",
        "tiktok_voice": "@SpoonDbot",
        "x_success": "@SpoonDbot",
        "threads_sucess": "@SpoonDbot",
        "facebook_success": "@SpoonDbot",
        
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
        "no_bio": "لا يوجد بايو",
        "no_highlights": " لم يتم العثور على هايلايتس لـ @{username}.",
        "no_active_stories": "لم يتم العثور على ستوريات نشطة لـ @{username}.",
        "downloading_stories": "جار تحميل الستوريات...",
        "downloading_highlight": "جار تحميل الهايلايت...",
        "select_highlight": "اختر هايلايت للتحميل ({count} متاح):",
        
        # YouTube specific
        "shorts_detected": "🎬 تم اكتشاف فيديو قصير من يوتيوب! جاري التحميل...",
        "video_found": "📺 **تم العثور على الفيديو!**\n\nاختر الجودة:",
        "choose_format": "🎬 **خيارات التحميل**\n\nاختر التنسيق:",
        
        # Buttons
        "btn_video": "فيديو",
        "btn_audio": " صوت",
        "btn_voice": "رسالة صوتية",
        "btn_profile_details": "تفاصيل الحساب",
        "btn_highlights": "الهايلايت",
        "btn_stories": " الستوريات",
        "btn_download_all_highlights": " تحميل كل الهايلايت",
        
        # Yes/No
        "yes": "نعم",
        "no": "لا",
        "spoon": "@spoonDbot",


        # Testing
        "test_mode_activated": "✅ انت هسه بمود التست تكدر تجرب كل شي جديد وتحت التطوير",
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