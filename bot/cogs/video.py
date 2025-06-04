import discord
from discord.ext import commands
import yt_dlp
from datetime import datetime

class Video(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True
        }
        self.current_stream = None

    @commands.command(name="stream", help="Phát nhạc từ video YouTube trong kênh thoại")
    async def stream(self, ctx, url: str):
        try:
            # Kiểm tra xem người dùng có trong kênh voice không
            if not ctx.author.voice:
                await ctx.send("❌ Bạn cần vào kênh thoại để sử dụng lệnh này!")
                return

            # Gửi thông báo đang xử lý
            processing_msg = await ctx.send("🔄 Đang xử lý video...")

            # Kết nối với kênh voice
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                voice_client = await voice_channel.connect()
            else:
                voice_client = ctx.voice_client
                if voice_client.channel != voice_channel:
                    await voice_client.move_to(voice_channel)

            # Lấy thông tin video
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    # Playlist
                    video = info['entries'][0]
                else:
                    # Single video
                    video = info
                
                title = video.get('title', 'Unknown')
                duration = video.get('duration', 0)
                thumbnail = video.get('thumbnail')
                uploader = video.get('uploader', 'Unknown')
                view_count = video.get('view_count', 0)
                stream_url = video.get('url')

            # Tạo embed message
            embed = discord.Embed(
                title="🎵 Đang phát nhạc",
                description=f"**{title}**\n\nĐang phát trong kênh `{voice_channel.name}`",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Kênh", value=uploader, inline=True)
            embed.add_field(name="Thời lượng", value=f"{duration//60}:{duration%60:02d}", inline=True)
            embed.add_field(name="Lượt xem", value=f"{view_count:,}", inline=True)
            
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

            # Phát nhạc
            if voice_client.is_playing():
                voice_client.stop()

            voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(stream_url)))
            self.current_stream = voice_client

            # Gửi embed message
            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Có lỗi xảy ra khi phát nhạc:\n```{str(e)}```",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="vstop", help="Dừng phát nhạc")
    async def vstop(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(
                title="⏹️ Đã dừng phát",
                description="Đã dừng phát nhạc",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Không có nhạc nào đang phát!")

    @commands.command(name="vpause", help="Tạm dừng phát nhạc")
    async def vpause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(
                title="⏸️ Đã tạm dừng",
                description="Đã tạm dừng phát nhạc",
                color=0xffff00,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Không có nhạc nào đang phát!")

    @commands.command(name="vresume", help="Tiếp tục phát nhạc")
    async def vresume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = discord.Embed(
                title="▶️ Tiếp tục phát",
                description="Đã tiếp tục phát nhạc",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Không có nhạc nào đang tạm dừng!")

    @commands.command(name="vleave", help="Bot rời kênh thoại")
    async def vleave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            embed = discord.Embed(
                title="👋 Đã rời kênh",
                description="Bot đã rời kênh thoại",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Bot không ở trong kênh thoại!")

    @commands.command(name="vplay", help="Phát video YouTube")
    async def vplay(self, ctx, url: str):
        try:
            # Gửi thông báo đang xử lý
            processing_msg = await ctx.send("🔄 Đang xử lý video...")

            # Lấy thông tin video
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    # Playlist
                    video = info['entries'][0]
                else:
                    # Single video
                    video = info
                
                title = video.get('title', 'Unknown')
                duration = video.get('duration', 0)
                thumbnail = video.get('thumbnail')
                uploader = video.get('uploader', 'Unknown')
                view_count = video.get('view_count', 0)
                video_url = video.get('webpage_url', url)

            # Tạo embed message
            embed = discord.Embed(
                title="🎥 Video YouTube",
                description=f"**{title}**\n\n[Click vào đây để xem video]({video_url})",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Kênh", value=uploader, inline=True)
            embed.add_field(name="Thời lượng", value=f"{duration//60}:{duration%60:02d}", inline=True)
            embed.add_field(name="Lượt xem", value=f"{view_count:,}", inline=True)
            
            if thumbnail:
                embed.set_image(url=thumbnail)
            
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

            # Gửi embed message
            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Có lỗi xảy ra khi xử lý video:\n```{str(e)}```",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="playlist", help="Hiển thị danh sách phát YouTube")
    async def playlist(self, ctx, url: str):
        try:
            # Gửi thông báo đang xử lý
            processing_msg = await ctx.send("🔄 Đang xử lý playlist...")

            # Lấy thông tin playlist
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' not in info:
                    raise ValueError("URL không phải là playlist")

                playlist_title = info.get('title', 'Unknown Playlist')
                videos = info['entries'][:10]  # Lấy 10 video đầu tiên

            # Tạo embed message
            embed = discord.Embed(
                title="📑 Playlist YouTube",
                description=f"**{playlist_title}**\n\n[Link playlist gốc]({url})",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )

            # Thêm thông tin từng video
            for i, video in enumerate(videos, 1):
                title = video.get('title', 'Unknown')
                duration = video.get('duration', 0)
                video_url = video.get('webpage_url', '')
                embed.add_field(
                    name=f"{i}. {title}",
                    value=f"⏱️ {duration//60}:{duration%60:02d}\n[Link video]({video_url})",
                    inline=False
                )

            if info.get('thumbnail'):
                embed.set_thumbnail(url=info['thumbnail'])
            
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

            # Gửi embed message
            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Có lỗi xảy ra khi xử lý playlist:\n```{str(e)}```",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="search", help="Tìm kiếm video trên YouTube")
    async def search(self, ctx, *, query: str):
        try:
            # Gửi thông báo đang xử lý
            processing_msg = await ctx.send("🔍 Đang tìm kiếm...")

            # Cấu hình tìm kiếm
            search_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': 'ytsearch5'  # Tìm 5 video
            }

            # Thực hiện tìm kiếm
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                videos = info['entries']

            # Tạo embed message
            embed = discord.Embed(
                title="🔍 Kết quả tìm kiếm YouTube",
                description=f"Kết quả cho: **{query}**",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )

            # Thêm thông tin từng video
            for i, video in enumerate(videos, 1):
                title = video.get('title', 'Unknown')
                duration = video.get('duration', 0)
                video_url = video.get('webpage_url', '')
                embed.add_field(
                    name=f"{i}. {title}",
                    value=f"⏱️ {duration//60}:{duration%60:02d}\n[Link video]({video_url})",
                    inline=False
                )

            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

            # Gửi embed message
            await processing_msg.edit(content=None, embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Lỗi",
                description=f"Có lỗi xảy ra khi tìm kiếm:\n```{str(e)}```",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Video(bot)) 