# 🚀 Northflank Quick Start

Deploy your Telegram bot in minutes on Northflank!

## 30-Second Setup

### 1. Go to Northflank
https://app.northflank.com/

### 2. Sign Up
- Click "Sign up"
- Choose "GitHub" option
- Authorize Northflank

### 3. Create Service
1. Click "Create"
2. Select "Service from GitHub"
3. Choose your telegram-bot repository
4. Click "Create"

### 4. Configure

**Dockerfile Path**: `/Dockerfile`

**Environment Variables** (click "Add Variables"):
```
BOT_TOKEN = your_bot_token_from_botfather
CHANNEL_ID = -1002693989550
CHANNEL_USERNAME = cyberkid25
ADMIN_ID = 1530069749
```

### 5. Deploy
Click "Deploy" button

✅ Done! Bot is now running!

## Verify Bot is Working

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Verify you get welcome message

## Test Admin Dashboard

Send `/dashboard` (if you're the admin)

Should see:
```
📊 ADMIN DASHBOARD
📈 Statistics
```

## Useful Links

- 🌐 Northflank Dashboard: https://app.northflank.com/
- 🤖 Your Bot: @YourBotUsername
- 📋 Logs: Service → Logs tab
- ⚙️ Settings: Service → Settings

## Troubleshooting

**Bot not responding?**
- Check Logs tab for errors
- Verify BOT_TOKEN is correct
- Make sure service is "Running"

**Logs show error?**
- Check environment variables
- Verify Python syntax in bot_new.py
- Check .gitignore doesn't exclude needed files

## Scale Up (Optional)

Upgrade when you need more resources:
1. Service Settings
2. Increase CPU/Memory
3. Enable auto-scaling

## Questions?

See full guide: [NORTHFLANK_GUIDE.md](NORTHFLANK_GUIDE.md)
