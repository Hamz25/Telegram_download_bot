This is a telegram bot used to download media from the internet.

It was created by me using aiogram library with other libraries such as yt_dlp etc..

Note : This bot is still under development it is still in the beta version and there are improvments and other platforms and features i will add.



what platforms it can download media from ?
1- Instagram | Reels , 2- Youtube | Shorts | Videos as mp3 (Audio) or mp4 (video) , 3- Tiktok | Short videos , 4-Spotify | Audio , 5- Snapchat | Short videos.

What will be in the next update of the bot : 

1- Support instagram story download and posts.
2- Convert any video into mp3 audio.
3- Add a new feature : make the bot send a voice message to the user as a third option.
4- Better UI/UX.

How to get the repo :

-simply type this command in your terminal : git clone https://github.com/Hamz25/Telegram_download_bot

!!! TO RUN THE BOT YOU MUST INSTALL FFMPEG AND INSTALL THE REQUIREMENTS.

To install FFMPEG just go to this website https://www.ffmpeg.org

Then install the libraries in requirements || in your command line type : pip install -r requirements.txt,
if it won't work just simplly create a Vertual environment and you should be good to go.



This is where you should add ffmpeg:
Telebot/
├──ffmpeg.exe              #You must download the ffmpeg to make the yt_dlp works
├──ffplay.exe
├──ffprobe.exe

You should make the same code structre especially for ffmpeg to work 