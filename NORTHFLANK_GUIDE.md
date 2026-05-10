# 🚀 Northflank Deployment Guide

## Deploy Telegram Bot on Northflank

Northflank is a powerful containerized deployment platform with excellent free tier options.

## Prerequisites

- GitHub account with your bot repository
- Northflank account: https://app.northflank.com/
- Bot token from @BotFather

## Step 1: Prepare Repository

Push your code to GitHub:

```bash
git add .
git commit -m "Add bot with Northflank Dockerfile"
git push origin main
```

Make sure these files exist:
- ✅ `bot_new.py` - Main bot
- ✅ `requirements.txt` - Dependencies
- ✅ `Dockerfile` - Container configuration
- ✅ `.env` - Environment variables (local only)
- ✅ `.gitignore` - Git ignore rules

## Step 2: Create Northflank Account

1. Go to https://app.northflank.com/
2. Sign up with GitHub or email
3. Authorize Northflank to access GitHub repositories

## Step 3: Deploy on Northflank

### 3.1 Create New Service

1. Log in to Northflank Dashboard
2. Click "Create" button
3. Select "Service from GitHub"
4. Choose your repository

### 3.2 Configure Service

1. **Service Settings**:
   - Name: `telegram-bot`
   - Dockerfile Path: `/Dockerfile`
   - Docker Build Context: `/`

2. **Environment Variables**:
   - Click "Add Variables"
   - Add these environment variables:

   ```
   BOT_TOKEN = your_bot_token_here
   CHANNEL_ID = -1002693989550
   CHANNEL_USERNAME = cyberkid25
   ADMIN_ID = 1530069749
   ```

3. **Resources** (Free Tier):
   - CPU: 0.1 - 0.5
   - Memory: 128 - 512 MB
   - Disk: Optional

### 3.3 Advanced Settings (Optional)

- **Restart Policy**: Always
- **Port**: Not needed (polling bot doesn't need HTTP port)

## Step 4: Deploy

1. Click "Deploy" button
2. Wait for build and deployment (2-5 minutes)
3. Check logs to verify bot is running

## Step 5: Verify Deployment

1. Open Telegram
2. Search for your bot
3. Send `/start` command
4. Verify you get welcome message

Test admin features:
```
/dashboard
```

## Monitoring

### View Logs

1. Go to Service Details
2. Click "Logs" tab
3. Check for any errors

### Common Issues

**Bot not responding?**
- Check if service is running
- Verify all environment variables are set
- Check bot token is valid

**Build failed?**
- Ensure Dockerfile is correct
- Check Python version compatibility
- Verify requirements.txt syntax

## Troubleshooting

### Deploy fails with error

1. Check Northflank build logs
2. Verify Dockerfile syntax:
   ```bash
   docker build -t telegram-bot .
   docker run telegram-bot
   ```
3. Test locally first

### Bot not starting

Check environment variables:
- `BOT_TOKEN` must be valid
- `ADMIN_ID` must be numeric
- `CHANNEL_ID` must be negative number

### Database files not persisting

Northflank containers are ephemeral. For persistent storage:

**Option 1: Use Northflank Volumes**
1. Go to Service Settings
2. Add Volume at `/app/data`
3. Mount point: `/app/data`

**Option 2: Use External Database**
- MongoDB Atlas (free tier)
- Firebase Firestore
- Supabase PostgreSQL

## Auto-Deploy on Push

Northflank automatically redeploys when you push to GitHub:

```bash
git push origin main  # Automatic redeploy triggered
```

## Scaling

Upgrade your deployment:

1. Free Tier → Starter
2. Increase CPU/Memory resources
3. Enable auto-scaling (paid plans)

## Costs

| Tier | Cost | Features |
|------|------|----------|
| Free | $0 | Basic resources, good for testing |
| Starter | $5-20 | Better resources, more reliability |
| Production | $20+ | Auto-scaling, advanced features |

## Quick Links

- 🌐 Northflank Dashboard: https://app.northflank.com/
- 📚 Northflank Docs: https://northflank.com/docs
- 🐳 Docker Docs: https://docs.docker.com/
- 🤖 BotFather: https://t.me/botfather

## Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] Dockerfile created and tested locally
- [ ] requirements.txt updated
- [ ] Bot token obtained from @BotFather
- [ ] Northflank account created
- [ ] Service created on Northflank
- [ ] Environment variables added
- [ ] Deployment successful
- [ ] Bot responds to /start
- [ ] Admin /dashboard working

---

**Status**: ✅ Ready for Northflank Deployment
**Last Updated**: May 1, 2026

For more information, visit https://northflank.com/
