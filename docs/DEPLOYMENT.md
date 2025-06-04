# 🚀 Hướng Dẫn Deployment Discord Bot

## 📋 Tổng Quan

Tài liệu này hướng dẫn deploy Discord bot lên các platform hosting miễn phí và trả phí.

## ☁️ Hosting Miễn Phí (Khuyến Nghị)

### 1. 🟣 **Heroku** (Tốt nhất cho beginners)

#### **Ưu điểm:**
- ✅ Miễn phí 550-1000 giờ/tháng
- ✅ Dễ setup và deploy
- ✅ Auto-scaling
- ✅ Add-ons phong phú

#### **Nhược điểm:**
- ❌ Sleep sau 30 phút không hoạt động
- ❌ Giới hạn RAM (512MB)

#### **Cách Deploy:**

```bash
# 1. Cài đặt Heroku CLI
# Download từ: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login
heroku login

# 3. Tạo app
heroku create your-bot-name

# 4. Set environment variables
heroku config:set DISCORD_TOKEN=your_discord_token
heroku config:set DISCORD_APPLICATION_ID=your_app_id

# 5. Add buildpack cho FFmpeg
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git

# 6. Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# 7. Scale worker
heroku ps:scale worker=1
```

#### **Giữ Bot Luôn Online:**
```bash
# Sử dụng Heroku Scheduler (miễn phí)
heroku addons:create scheduler:standard

# Hoặc sử dụng UptimeRobot để ping
# Tạo HTTP endpoint trong bot và ping mỗi 25 phút
```

---

### 2. 🚂 **Railway** (Dễ sử dụng nhất)

#### **Ưu điểm:**
- ✅ $5 credit miễn phí/tháng
- ✅ Không sleep
- ✅ Deploy từ GitHub tự động
- ✅ Database miễn phí

#### **Cách Deploy:**

1. **Truy cập [Railway.app](https://railway.app)**
2. **Connect GitHub account**
3. **New Project → Deploy from GitHub repo**
4. **Chọn repository của bot**
5. **Add Environment Variables:**
   ```
   DISCORD_TOKEN=your_token
   DISCORD_APPLICATION_ID=your_app_id
   ```
6. **Deploy tự động!**

---

### 3. 🎨 **Render** (Tốt cho production)

#### **Ưu điểm:**
- ✅ 750 giờ miễn phí/tháng
- ✅ Không sleep với paid plan
- ✅ SSL miễn phí
- ✅ Auto-deploy từ Git

#### **Cách Deploy:**

1. **Truy cập [Render.com](https://render.com)**
2. **New → Web Service**
3. **Connect GitHub repository**
4. **Cấu hình:**
   ```
   Name: discord-bot
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python bot/main.py
   ```
5. **Add Environment Variables**
6. **Deploy**

---

### 4. ✈️ **Fly.io** (Tốt cho advanced users)

#### **Ưu điểm:**
- ✅ $5 credit miễn phí/tháng
- ✅ Global deployment
- ✅ Docker native
- ✅ Scaling tốt

#### **Cách Deploy:**

```bash
# 1. Cài đặt flyctl
# macOS: brew install flyctl
# Windows: iwr https://fly.io/install.ps1 -useb | iex

# 2. Login
fly auth login

# 3. Launch app
fly launch

# 4. Set secrets
fly secrets set DISCORD_TOKEN=your_token
fly secrets set DISCORD_APPLICATION_ID=your_app_id

# 5. Deploy
fly deploy
```

---

### 5. 🔷 **Replit** (Tốt cho testing)

#### **Ưu điểm:**
- ✅ Hoàn toàn miễn phí
- ✅ IDE online
- ✅ Dễ share và collaborate

#### **Nhược điểm:**
- ❌ Sleep khi không hoạt động
- ❌ Performance hạn chế

#### **Cách Deploy:**

1. **Tạo Repl mới với Python**
2. **Upload code hoặc import từ GitHub**
3. **Tạo file `.env`:**
   ```env
   DISCORD_TOKEN=your_token
   DISCORD_APPLICATION_ID=your_app_id
   ```
4. **Chạy `python bot/main.py`**
5. **Sử dụng UptimeRobot để keep alive**

---

## 💰 Hosting Trả Phí (Production)

### 1. **DigitalOcean Droplet**
- $5/tháng cho 1GB RAM
- Full control
- Tốt cho multiple bots

### 2. **AWS EC2**
- Free tier 12 tháng đầu
- Scalable
- Professional grade

### 3. **Google Cloud Platform**
- $300 credit miễn phí
- Always Free tier
- Enterprise features

### 4. **Linode**
- $5/tháng
- SSD storage
- Excellent performance

---

## 🐳 Docker Deployment

### **Sử dụng Docker Compose:**

```bash
# 1. Clone repository
git clone your-repo-url
cd discord-bot

# 2. Cấu hình environment
cp .env.example .env
# Chỉnh sửa .env

# 3. Build và run
docker-compose up -d

# 4. Xem logs
docker-compose logs -f

# 5. Stop
docker-compose down
```

### **Deploy lên Docker Hub:**

```bash
# 1. Build image
docker build -t yourusername/discord-bot .

# 2. Push to Docker Hub
docker push yourusername/discord-bot

# 3. Deploy anywhere
docker run -d --env-file .env yourusername/discord-bot
```

---

## 🔧 Cấu Hình Production

### **Environment Variables Cần Thiết:**

```env
# Required
DISCORD_TOKEN=your_bot_token
DISCORD_APPLICATION_ID=your_application_id

# Optional but recommended
LOG_LEVEL=INFO
DATABASE_PATH=data/bot_database.db
MAX_QUEUE_SIZE=100
DEFAULT_VOLUME=0.5

# API Keys (optional)
WEATHER_API_KEY=your_weather_key
OPENAI_APIKEY=your_openai_key
P_APIKEY=your_pexels_key
UnS_APIKEY=your_unsplash_key
```

### **Resource Requirements:**

| Platform | RAM | CPU | Storage | Bandwidth |
|----------|-----|-----|---------|-----------|
| Minimum  | 256MB | 0.1 vCPU | 1GB | 1GB/month |
| Recommended | 512MB | 0.5 vCPU | 5GB | 10GB/month |
| Optimal | 1GB | 1 vCPU | 10GB | Unlimited |

---

## 📊 Monitoring & Maintenance

### **Health Checks:**

```python
# Thêm vào bot/main.py
@bot.event
async def on_ready():
    # Health check endpoint
    from aiohttp import web
    
    async def health(request):
        return web.Response(text="Bot is healthy")
    
    app = web.Application()
    app.router.add_get('/health', health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
```

### **Logging:**

```bash
# Xem logs real-time
tail -f logs/bot.log

# Rotate logs để tránh đầy disk
logrotate /etc/logrotate.d/discord-bot
```

### **Backup Database:**

```bash
# Backup SQLite database
cp data/bot_database.db backups/bot_database_$(date +%Y%m%d).db

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp data/bot_database.db backups/bot_database_$DATE.db
find backups/ -name "*.db" -mtime +7 -delete
```

---

## 🚨 Troubleshooting

### **Common Issues:**

#### **Bot không start:**
```bash
# Check logs
docker logs container_name

# Check environment variables
env | grep DISCORD

# Verify token
curl -H "Authorization: Bot YOUR_TOKEN" \
  https://discord.com/api/v10/users/@me
```

#### **Memory issues:**
```bash
# Check memory usage
free -h

# Optimize Python memory
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

#### **FFmpeg not found:**
```bash
# Install FFmpeg
apt-get update && apt-get install -y ffmpeg

# Verify installation
ffmpeg -version
```

### **Performance Optimization:**

```python
# bot/config.py
import gc

# Enable garbage collection optimization
gc.set_threshold(700, 10, 10)

# Use uvloop for better performance (Linux/macOS)
try:
    import uvloop
    uvloop.install()
except ImportError:
    pass
```

---

## 📈 Scaling

### **Horizontal Scaling:**
- Sử dụng Discord sharding
- Load balancer cho multiple instances
- Database clustering

### **Vertical Scaling:**
- Tăng RAM và CPU
- SSD storage
- CDN cho media files

---

## 🔐 Security Best Practices

1. **Never commit .env files**
2. **Use environment variables for secrets**
3. **Regular security updates**
4. **Monitor for suspicious activity**
5. **Backup regularly**
6. **Use HTTPS for webhooks**

---

## 📞 Support

Nếu gặp vấn đề khi deploy:

1. **Check logs** đầu tiên
2. **Verify environment variables**
3. **Test locally** trước khi deploy
4. **Create GitHub issue** với logs đầy đủ

---

**🎉 Chúc bạn deploy thành công!** 🎉
