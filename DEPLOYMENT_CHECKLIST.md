# 📋 Render.com Deployment Checklist

## Pre-Deployment Checklist ✅

### Local Setup
- [ ] Install Python 3.8+
- [ ] Clone/create repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with credentials
- [ ] Test bot locally: `python bot_new.py`

### Files Created
- [x] `bot_new.py` - Main bot with admin features
- [x] `requirements.txt` - Python dependencies
- [x] `render.yaml` - Render configuration
- [x] `Procfile` - Process file for Render
- [x] `.env` - Environment variables (local)
- [x] `.gitignore` - Git ignore rules
- [x] `README.md` - Documentation
- [x] `DEPLOYMENT_GUIDE.md` - Detailed guide

### GitHub Setup
- [ ] Create GitHub repository
- [ ] Add files to git:
  ```bash
  git add .
  git commit -m "Initial commit - Telegram bot with admin dashboard"
  git push origin main
  ```
- [ ] Verify files on GitHub (except .env)

## Render.com Deployment

### Step 1: Create Account
- [ ] Go to [render.com](https://render.com)
- [ ] Sign up with GitHub
- [ ] Authorize Render.com access to your repositories

### Step 2: Create Web Service
1. Click "New +" button
2. Select "Web Service"
3. Connect your GitHub repository
4. Fill in configuration:
   - **Name**: `telegram-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot_new.py`
   - **Plan**: Choose Free or Paid

### Step 3: Environment Variables
In Render Dashboard:
1. Go to Service → Settings → Environment
2. Add these variables:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Your bot token from @BotFather |
| `CHANNEL_ID` | -1002693989550 |
| `CHANNEL_USERNAME` | cyberkid25 |
| `ADMIN_ID` | 1530069749 |

### Step 4: Deploy
- [ ] Click "Create Web Service"
- [ ] Wait for deployment (2-5 minutes)
- [ ] Check logs for any errors
- [ ] Test bot with `/start` command

## Post-Deployment

### Verify Bot is Running
1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Verify you get the welcome message

### Test Admin Features
1. DM `/dashboard` from your ADMIN_ID
2. Verify you see admin dashboard
3. Test user management
4. Test broadcast notification

### Monitor
- Check Render logs regularly
- Monitor bot health in Render dashboard
- Test features periodically

## Important Notes

⚠️ **Security**
- Never share BOT_TOKEN
- Don't commit `.env` to GitHub
- Use Render's secure environment variables
- Regenerate token if accidentally exposed

📌 **Render Free Tier**
- Service spins down after 15 minutes of inactivity
- For production use, upgrade to paid plan
- No persistent storage (use database service)

🔄 **Auto-Redeploy**
- Any push to `main` branch triggers auto-redeploy
- Useful for quick updates

## Database Persistence

Current setup uses JSON files (not persistent on free Render).

For production, consider:

### Option 1: MongoDB Atlas
1. Go to [mongodb.com/cloud](https://www.mongodb.com/cloud)
2. Create free cluster
3. Update bot to use MongoDB

### Option 2: Firebase
1. Go to [firebase.google.com](https://firebase.google.com)
2. Create project
3. Use Firestore database

### Option 3: Supabase PostgreSQL
1. Go to [supabase.com](https://supabase.com)
2. Create free PostgreSQL project
3. Connect bot to database

## Troubleshooting

### Bot not responding?
```
1. Check Render logs
2. Verify BOT_TOKEN is correct
3. Test local version first
4. Check internet connection
```

### Admin dashboard not working?
```
1. Verify ADMIN_ID is correct
2. Get ID from @userinfobot
3. Restart service in Render
4. Check error logs
```

### Files not saving?
```
1. Use database service for persistence
2. Free Render tier doesn't save files
3. Consider paid Render plan
```

## Quick Links

- 🤖 [BotFather](https://t.me/botfather) - Create/manage bots
- 🆔 [@userinfobot](https://t.me/userinfobot) - Get your user ID
- 🌐 [Render.com](https://render.com) - Hosting
- 📚 [python-telegram-bot docs](https://python-telegram-bot.readthedocs.io/)

## Support Resources

1. **Bot Issues**: Check Render logs
2. **Telegram API**: See telegram-bot-api docs
3. **Python Help**: See python-telegram-bot docs
4. **Render Help**: Check Render documentation

---

**Status**: ✅ Ready for Deployment
**Last Updated**: May 1, 2026
