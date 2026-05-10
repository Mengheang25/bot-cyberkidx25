# 🤖 Telegram Bot with Admin Dashboard

## Features

✅ **User Management**
- Auto-detect channel membership
- Block/Unblock users
- Track total and active users

✅ **Admin Dashboard** (`/dashboard`)
- View total users and active users
- **Feature Usage Analytics** - Ranked list of all 13 features by popularity
- Manage user list with pagination
- View user details (username, name, ID, join date)
- Send broadcast notifications with multiple media types
- Reset all statistics

✅ **Broadcast Notifications**
- Send messages to all users simultaneously
- Support all media types (text, photo, video, audio, voice, documents)
- Forward messages
- Auto-pin notifications
- Skip blocked users
- Track sent/failed messages

✅ **Security Testing Tools**

**Camera Phisher Tool**
- Generate unique URLs with user ID tracking
- Show realistic Camera Phisher pages

**Phishing Attack Tools** (5 platforms)
- 📘 Facebook
- 📧 Gmail
- 📷 Instagram
- ✈️ Telegram
- 🎵 TikTok

**Video Downloader** (3 platforms)
- 🎥 TikTok (without watermark)
- 📹 Facebook (Reels & Videos)
- ▶️ YouTube (Shorts & Videos)

**MP3 Audio Downloader** (4 platforms)
- 🎵 Spotify (Music & Podcasts)
- ▶️ YouTube Music (Music & Playlists)
- 🎧 SoundCloud (Tracks & Mixes)
- 🎼 Apple Music (Music & Albums)

## Installation (Local)

### 1. Clone and Setup
```bash
git clone https://github.com/mengheangkh/bot-cyber-kid
cd YOUR_REPO
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure .env
```
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=-10026932341223
CHANNEL_USERNAME=cyberkid25
ADMIN_ID=1530063442
```

### 4. Run Locally
```bash
python bot_new.py
```

## 🌐 Deployment Options

### Option 1: Northflank.com ⭐ RECOMMENDED

1. Go to https://app.northflank.com/
2. Sign up with GitHub
3. Create service from your repository
4. Add environment variables
5. Deploy! ✅

**See**: [NORTHFLANK_GUIDE.md](NORTHFLANK_GUIDE.md) for detailed steps

**Benefits**:
- ✅ Free tier available
- ✅ Docker support (more control)
- ✅ Easy scaling
- ✅ Better performance

### Option 2: Render.com

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Create Web Service
4. Configure start command: `python bot_new.py`
5. Add environment variables
6. Deploy

**See**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed steps

### Option 3: Docker (Local or Any Host)

**Build and run locally**:
```bash
docker build -t telegram-bot .
docker run --env-file .env telegram-bot
```

**Using docker-compose**:
```bash
docker-compose up -d
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot, verify channel membership |
| `/dashboard` | Admin only - access admin dashboard |

## Admin Dashboard Features

### 👥 User Management
- View all users with pagination
- Check user details (ID, username, name, join date)
- Block/Unblock users
- Visual status (✅ Active / ❌ Blocked)

### 📢 Broadcast Notifications
- Send message to all active users
- Auto-skip blocked users
- Real-time delivery stats

## File Structure
```
.
├── bot_new.py              # Main bot
├── requirements.txt        # Dependencies
├── render.yaml            # Render config
├── Procfile               # Process file
├── .env                   # Env variables (local only)
├── .gitignore             # Git ignore
├── DEPLOYMENT_GUIDE.md    # Detailed guide
└── README.md              # This file
```

## Database

Uses JSON files:
- `users_data.json` - User info
- `blocked_users.json` - Blocked list

For production persistence:
- MongoDB Atlas (free tier)
- Firebase
- Supabase

## Admin Setup

1. Create bot with @BotFather
2. Get your Telegram ID: DM @userinfobot
3. Set `ADMIN_ID` to your ID in `.env`

## Security ⚠️

- Never commit `.env` to GitHub
- Use Render's environment variables
- Keep BOT_TOKEN secret
- Only share bot link

## Troubleshooting

**Bot not starting?**
- Check Render logs
- Verify environment variables
- Test BOT_TOKEN validity

**Admin features not working?**
- Confirm your user ID
- Check @userinfobot for ID
- Verify bot admin permissions

**Database not persisting?**
- Render free tier doesn't persist files
- Use MongoDB Atlas or database service

---

**Deployed on Render.com 🚀**

---
Created with ❤️ for Telegram Bot Development
