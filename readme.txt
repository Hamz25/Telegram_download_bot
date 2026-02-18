# Social Media Downloader Bot - Enhanced Version 🚀

A powerful Telegram bot for downloading media from YouTube, Instagram, TikTok, Snapchat, and Spotify.

## 🎉 New Features & Improvements

### 1. Instagram Profile Search & Management
- **Send Instagram username** (e.g., `@username`) to access interactive profile options
- **Three-button menu** for each profile:
  - 👤 **Profile Details**: View full profile information with profile picture
  - 📦 **Highlights**: Select and download specific highlights or all at once
  - 📱 **Stories**: Download all active stories

### 2. Smart Highlight Download
- **Multiple highlights detection**: If a profile has multiple highlights, bot shows selection menu
- **Individual selection**: Choose specific highlight to download
- **Batch download**: Option to download all highlights at once
- **Preview info**: Shows highlight title and item count before download

### 3. Enhanced Story Downloads
- **Mixed media support**: Handles both photos and videos in stories
- **Dual method approach**: Tries yt-dlp with cookies first, falls back to Instaloader
- **Better reliability**: More robust error handling and retry logic

### 4. Video Thumbnails
- **Automatic thumbnail detection**: Finds and attaches .jpg thumbnails to videos
- **Smart pairing**: Matches thumbnails with videos by filename
- **Upload optimization**: Sends thumbnails with videos in media groups

### 5. Improved Error Handling
- **Specific error messages**: Clear feedback for each error type:
  - Profile not found
  - Private profile
  - Rate limiting
  - No active content
  - Session expired
- **Graceful degradation**: Falls back to alternative methods when primary fails
- **User-friendly messages**: Available in English and Arabic

### 6. Better Code Structure

#### Enhanced Instagram Module (`insta.py`)
```python
# New functions:
- search_instagram_profile()    # Search and retrieve profile info
- get_profile_highlights()      # List all highlights with metadata
- Enhanced error handling in all functions
- Better session management
- Comprehensive logging
```

#### Enhanced Handler (`socialHandle.py`)
```python
# New handlers:
- handle_instagram_username()     # Process username input
- handle_profile_details()        # Show profile information
- handle_highlights_request()     # Manage highlight selection
- handle_highlight_download()     # Download selected highlights
- handle_stories_download()       # Download stories

# FSM States for Instagram:
- waiting_for_action
- waiting_for_highlight_choice
```

#### Enhanced Uploader (`Uploader.py`)
```python
# Improvements:
- Automatic thumbnail detection and attachment
- Better media group handling
- Smart file filtering (skip thumbnails when paired)
- Fallback upload for failed groups
- Comprehensive error recovery
```

### 7. Language Support
- **Expanded translations**: All new features have English and Arabic translations
- **Consistent messaging**: Professional, clear messages throughout
- **Error context**: Detailed error messages with helpful suggestions

### 8. Security & Stability

#### Session Management
- **Persistent sessions**: Saves Instagram session to avoid repeated logins
- **Session validation**: Checks session health before use
- **Automatic re-authentication**: Seamlessly re-logs when session expires

#### Rate Limiting
- **Anti-flood delays**: Built-in delays between uploads
- **Rate limit detection**: Catches and reports Instagram rate limits
- **Graceful handling**: Informs users to wait before retrying

#### File Management
- **Automatic cleanup**: Removes temporary files after 40 seconds
- **Periodic cleanup**: Background task removes old files every 6 hours
- **Disk space monitoring**: Warns when disk space is low
- **Safe deletion**: Uses `ignore_errors` to prevent crashes

### 9. Performance Optimizations

#### Download Strategy
```python
# Priority order for Instagram stories:
1. yt-dlp with cookies (fast, reliable)
2. Instaloader with session (fallback)
3. Clear error message if both fail
```

#### Upload Strategy
```python
# Smart grouping:
- Groups photos/videos up to 45MB
- Maximum 10 items per group
- Sends audio files individually
- Attaches thumbnails to videos
```

### 10. Developer Experience

#### Comprehensive Logging
```python
logger.info(f"✅ Downloaded {count} stories from @{username}")
logger.error(f"❌ Profile @{username} does not exist")
logger.warning(f"⚠️ Low disk space detected!")
```

#### Clear Code Documentation
- **Docstrings**: Every function has detailed documentation
- **Type hints**: Clear parameter and return types
- **Inline comments**: Explains complex logic
- **Example usage**: Commented examples where helpful

## 📋 Usage Examples

### Instagram Profile Search
```
User sends: @cristiano
Bot responds: 
- Profile details with photo
- Three-button menu:
  [👤 Profile Details] [📦 Highlights] [📱 Stories]
```

### Highlight Selection
```
User clicks: "Highlights"
Bot shows: List of all highlights with item counts
User selects: "Euro 2024 (15 items)"
Bot downloads: All 15 items from that highlight
```

### Story Download
```
User clicks: "Stories"
Bot downloads: All active stories (photos + videos)
Bot uploads: Mixed media group to Telegram
```

## 🔧 Configuration

### Instagram Authentication
Update `Token.py`:
```python
Insta_username = 'your_instagram_username'
Insta_password = 'your_instagram_password'
Insta_cookies = 'cookies/instagram_cookies.txt'  # Optional
```

### Bot Token
```python
TToken = "your_telegram_bot_token"
```

### Customization
```python
# Adjust cleanup delay (seconds)
await cleanup(folder_to_clean, delay=40)

# Adjust periodic cleanup interval (hours)
await asyncio.sleep(6 * 3600)

# Adjust max file age for cleanup (hours)
cleaned_count = await cleanup_old_downloads(max_age_hours=24)
```

## 🐛 Error Handling

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Profile not found" | Username doesn't exist | Verify username spelling |
| "This profile is private" | Account is private | Follow the account first |
| "Rate limit hit" | Too many requests | Wait 10-15 minutes |
| "No active stories" | No stories posted | User has no current stories |
| "Session expired" | Instagram session invalid | Bot will re-authenticate |

## 📊 Code Quality Improvements

### Before vs After

#### Before:
```python
# Hard to understand logic
if "/stories/" in url or (not url.startswith("http") and not "/highlights/" in url):
    # Download stories
```

#### After:
```python
# Clear, documented logic with proper routing
@router.message(F.text.contains("instagram.com"))
async def handle_instagram_url(message: types.Message):
    """Handle Instagram URLs (posts, reels, stories, highlights)."""
    if "/stories/" in url:
        # Download stories with detailed logging
        logger.info(f"[Instagram] Downloading stories for @{username}")
```

## 🎯 Future Enhancements

Potential additions:
- ⭐ Instagram post likes/comments scraping
- 📊 Analytics dashboard
- 🔔 Story notifications
- 💾 Download history
- 🎨 Custom caption templates
- 📥 Batch URL processing

## 🤝 Contributing

When contributing, please:
1. Follow existing code style
2. Add docstrings to new functions
3. Update language files for new features
4. Test with both public and private accounts
5. Handle errors gracefully

## 📝 License

This enhanced version maintains compatibility with the original codebase while adding significant improvements to functionality, reliability, and user experience.

---

**Note**: This bot requires proper Instagram authentication. Never share your credentials. Consider using Instagram's official API for production use.