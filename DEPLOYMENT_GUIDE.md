# 🤖 Telegram Bot - Render.com Deployment Guide

## Step 1: Prepare Your Repository

1. Clone or create a new repository on GitHub
2. Push all files to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub account
3. Authorize Render to access your GitHub repositories

## Step 3: Deploy on Render

1. Click "New +" button
2. Select "Web Service"
3. Connect your GitHub repository
4. Fill in the configuration:
   - **Name**: `telegram-bot` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot_new.py`
   - **Plan**: Free tier (optional, choose paid for better stability)

## Step 4: Add Environment Variables

In Render Dashboard:
1. Go to your service settings
2. Click "Environment"
3. Add these variables:

```
BOT_TOKEN = 8690323383:AAE0SWM9UcA8NtHH11fg_MuDX1zMHNlzy18
CHANNEL_ID = -1002693989550
CHANNEL_USERNAME = cyberkid25
ADMIN_ID = 1530069749
```

## Step 5: Deploy

1. Click "Create Web Service"
2. Render will automatically deploy your bot
3. Check the logs to see if it's running properly

## File Structure

```
.
├── bot_new.py           # Main bot file
├── requirements.txt     # Python dependencies
├── render.yaml         # Render configuration
├── Procfile           # Process file for Render
├── .env               # Local environment variables (not pushed to GitHub)
├── .gitignore         # Git ignore file
└── README.md          # Deployment guide
```

## Important Notes

⚠️ **Security:**
- Never commit `.env` file to GitHub
- Use Render's environment variable system instead
- Keep your BOT_TOKEN secret

📌 **Free Tier Limitations:**
- Render's free tier spins down after 15 minutes of inactivity
- For production, consider upgrading to a paid plan

🔄 **Auto-Redeploy:**
- Any push to `main` branch will automatically redeploy your bot

## Troubleshooting

### Bot not starting?
- Check the logs in Render dashboard
- Ensure all environment variables are set correctly
- Verify BOT_TOKEN is valid

### Database files missing?
- Render doesn't persist files between restarts
- Consider using a database service instead of JSON files

## Upgrading Database

For persistent storage, consider:
- MongoDB Atlas (free tier available)
- Supabase PostgreSQL
- Firebase Realtime Database

---

**Created for Telegram Bot Deployment on Render.com** 🚀
