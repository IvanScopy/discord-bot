# 🤖 Discord Bot - Comprehensive Music & Utility Bot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

Một Discord bot đa chức năng được viết bằng Python với đầy đủ tính năng nghe nhạc, quản lý sự kiện, nhắc nhở và nhiều tiện ích khác.

## ✨ Tính Năng Chính

### 🎵 **Hệ Thống Nghe Nhạc**
- Phát nhạc từ YouTube với chất lượng cao
- Hàng đợi nhạc thông minh với auto-next
- Điều khiển đầy đủ: play, pause, skip, stop, volume
- Hiển thị thông tin bài hát và thời lượng
- Không bị dừng giữa chừng

### 🎉 **Quản Lý Sự Kiện**
- Tạo và quản lý sự kiện server
- Hệ thống đăng ký tham gia
- Thông báo tự động
- Giới hạn số lượng tham gia

### ⏰ **Hệ Thống Nhắc Nhở**
- Đặt nhắc nhở cá nhân
- Hỗ trợ nhắc nhở định kỳ
- Quản lý nhiều nhắc nhở
- Thông báo chính xác

### 📎 **Chia Sẻ Media**
- Upload và chia sẻ file
- Hỗ trợ nhiều định dạng
- Quản lý kích thước file
- Lưu trữ lịch sử

### 👤 **Thông Tin Người Dùng**
- Xem thông tin profile
- Thống kê hoạt động
- Lịch sử tham gia
- Cài đặt cá nhân

### 🔍 **Tìm Kiếm Hình Ảnh**
- Tìm kiếm từ Pinterest
- Tìm kiếm từ Unsplash/Pexels
- Kết quả chất lượng cao
- Bộ lọc thông minh

## 🚀 Cài Đặt Nhanh

### **Yêu Cầu Hệ Thống**
- Python 3.11+
- FFmpeg
- Git
- 512MB RAM (tối thiểu)

### **1. Clone Repository**
```bash
git clone https://github.com/yourusername/discord-bot.git
cd discord-bot
```

### **2. Cài Đặt Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Cấu Hình Environment**
```bash
cp .env.example .env
# Chỉnh sửa .env với thông tin bot của bạn
```

### **4. Chạy Bot**
```bash
python bot/main.py
```

## 🐳 Docker Deployment

### **Sử dụng Docker Compose (Khuyến nghị)**
```bash
# Clone và cấu hình
git clone https://github.com/yourusername/discord-bot.git
cd discord-bot
cp .env.example .env
# Chỉnh sửa .env

# Chạy với Docker Compose
docker-compose up -d
```

### **Sử dụng Docker thông thường**
```bash
# Build image
docker build -t discord-bot .

# Chạy container
docker run -d --name discord-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  discord-bot
```

## ☁️ Hosting Miễn Phí

### **1. Heroku (Khuyến nghị)**
```bash
# Cài đặt Heroku CLI
# Tạo app
heroku create your-bot-name

# Set environment variables
heroku config:set DISCORD_TOKEN=your_token
heroku config:set DISCORD_APPLICATION_ID=your_app_id

# Deploy
git push heroku main
```

### **2. Railway**
1. Kết nối GitHub repository
2. Set environment variables
3. Deploy tự động

### **3. Render**
1. Connect GitHub
2. Choose "Web Service"
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python bot/main.py`

### **4. Fly.io**
```bash
# Cài đặt flyctl
# Tạo app
fly launch

# Set secrets
fly secrets set DISCORD_TOKEN=your_token

# Deploy
fly deploy
```

## 📋 Lệnh Bot

### **🎵 Nhạc**
```
!play <bài hát>     - Phát nhạc từ YouTube
!queue              - Xem hàng đợi
!skip               - Bỏ qua bài hiện tại
!pause              - Tạm dừng
!resume             - Tiếp tục
!volume <0-100>     - Điều chỉnh âm lượng
!nowplaying         - Xem bài đang phát
!stop               - Dừng và xóa queue
!leave              - Bot rời kênh thoại
```

### **🎉 Sự Kiện**
```
!event create       - Tạo sự kiện mới
!event list         - Xem danh sách sự kiện
!event join <id>    - Tham gia sự kiện
!event leave <id>   - Rời sự kiện
!event info <id>    - Thông tin sự kiện
```

### **⏰ Nhắc Nhở**
```
!remind <time> <message>  - Đặt nhắc nhở
!reminders                - Xem nhắc nhở của bạn
!remind delete <id>       - Xóa nhắc nhở
```

### **👤 Người Dùng**
```
!userinfo [@user]   - Thông tin người dùng
!avatar [@user]     - Avatar người dùng
!serverinfo         - Thông tin server
```

### **🔍 Tìm Kiếm**
```
!search <từ khóa>   - Tìm kiếm hình ảnh
!pinterest <từ khóa> - Tìm từ Pinterest
```

## ⚙️ Cấu Hình

### **Environment Variables**
```env
# Required
DISCORD_TOKEN=your_bot_token
DISCORD_APPLICATION_ID=your_app_id

# Optional
WEATHER_API_KEY=your_weather_key
OPENAI_APIKEY=your_openai_key
P_APIKEY=your_pexels_key
UnS_APIKEY=your_unsplash_key
```

### **Bot Permissions**
Bot cần các quyền sau:
- Send Messages
- Embed Links
- Attach Files
- Connect (Voice)
- Speak (Voice)
- Use Voice Activity
- Manage Messages (optional)

## 🔧 Development

### **Cấu Trúc Dự Án**
```
discord-bot/
├── bot/                 # Core bot files
│   ├── main.py         # Entry point
│   ├── config.py       # Configuration
│   └── cogs/           # Bot features
├── utils/              # Utilities
├── data/               # Database & data
├── logs/               # Log files
├── docs/               # Documentation
└── scripts/            # Utility scripts
```

### **Thêm Tính Năng Mới**
1. Tạo file cog mới trong `bot/cogs/`
2. Thêm vào `COGS` list trong `config.py`
3. Implement commands và events
4. Test và deploy

### **Database Schema**
Bot sử dụng SQLite với các bảng:
- `users` - Thông tin người dùng
- `events` - Sự kiện server
- `reminders` - Nhắc nhở
- `media_shares` - Chia sẻ media
- `bot_logs` - Logs hệ thống

## 🐛 Troubleshooting

### **Lỗi Thường Gặp**

**Bot không phát nhạc:**
```bash
# Kiểm tra FFmpeg
ffmpeg -version

# Kiểm tra permissions
# Bot cần quyền Connect và Speak
```

**Database errors:**
```bash
# Xóa database cũ
rm data/bot_database.db

# Restart bot để tạo lại
```

**Import errors:**
```bash
# Cài đặt lại dependencies
pip install -r requirements.txt --force-reinstall
```

## 📊 Monitoring

### **Logs**
```bash
# Xem logs real-time
tail -f logs/bot.log

# Xem error logs
tail -f logs/errors.log
```

### **Health Check**
```bash
# Docker health check
docker ps

# Manual check
curl http://localhost:8080/health
```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License

MIT License - xem [LICENSE](LICENSE) để biết thêm chi tiết.

## 🆘 Support

- 📧 Email: your-email@example.com
- 💬 Discord: Your Discord Server
- 🐛 Issues: GitHub Issues
- 📖 Wiki: GitHub Wiki

## 🙏 Credits

- [discord.py](https://discordpy.readthedocs.io/) - Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [FFmpeg](https://ffmpeg.org/) - Audio processing

---

⭐ **Nếu project này hữu ích, hãy cho một star!** ⭐
