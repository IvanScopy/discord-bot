import discord
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL
import asyncio
import random
from datetime import datetime
from typing import Optional, List, Dict
from collections import deque

from utils.database import db_manager
from utils.logging_config import get_logger, log_command, log_error, log_user_action
from bot.config import Colors, Emojis

class MusicQueue:
    """Enhanced music queue with additional features"""
    def __init__(self):
        self.queue = deque()  # Sử dụng deque thay vì asyncio.Queue
        self.history = []
        self.current = None
        self.loop = False
        self.shuffle = False
        
    def add(self, item):
        self.queue.append(item)
    
    def get_next(self):
        if self.loop and self.current:
            return self.current
        
        if self.queue:
            item = self.queue.popleft()
            if self.current:
                self.history.append(self.current)
            self.current = item
            return item
        return None
    
    def is_empty(self):
        return len(self.queue) == 0
    
    def get_queue_list(self):
        return list(self.queue)
    
    def clear(self):
        self.queue.clear()
        self.current = None
    
    def size(self):
        return len(self.queue)

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_clients = {}  # Lưu trữ voice clients
        self.queues = {}  # Lưu trữ MusicQueue cho mỗi server (guild)
        self.volumes = {}  # Lưu trữ âm lượng cho mỗi server
        self.current_songs = {}  # Track bài đang phát
        self.logger = get_logger('music')
        
        # YT-DLP options
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

    async def join_voice_channel(self, ctx: commands.Context):
        """Tham gia kênh thoại của người dùng."""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.guild.id not in self.voice_clients:
                self.voice_clients[ctx.guild.id] = await channel.connect()
                self.volumes[ctx.guild.id] = 0.5  # Default volume
                await ctx.send(f"{Emojis.MUSIC} Đã kết nối với kênh thoại: **{channel.name}**")
            else:
                await ctx.send("Bot đã có mặt trong kênh thoại.")
        else:
            await ctx.send("Bạn cần tham gia một kênh thoại trước!")

    async def leave_voice_channel(self, ctx: commands.Context):
        """Rời khỏi kênh thoại."""
        if ctx.guild.id in self.voice_clients:
            await self.voice_clients[ctx.guild.id].disconnect()
            del self.voice_clients[ctx.guild.id]
            
            # Cleanup tất cả data
            if ctx.guild.id in self.queues:
                del self.queues[ctx.guild.id]
            if ctx.guild.id in self.volumes:
                del self.volumes[ctx.guild.id]
            if ctx.guild.id in self.current_songs:
                del self.current_songs[ctx.guild.id]
                
            await ctx.send("👋 Bot đã rời khỏi kênh thoại.")
        else:
            await ctx.send("Bot không có mặt trong kênh thoại.")

    async def cog_load(self):
        """Called when the cog is loaded"""
        self.logger.info("Enhanced Music cog loaded successfully")

    async def search_youtube(self, query: str):
        """Tìm kiếm và lấy thông tin âm thanh từ YouTube."""
        with YoutubeDL(self.ytdl_format_options) as ydl:
            try:
                if query.startswith("http"):
                    # Nếu là link YouTube, xử lý trực tiếp
                    info = ydl.extract_info(query, download=False)
                else:
                    # Nếu là từ khóa, tìm kiếm trên YouTube
                    search_query = f"ytsearch:{query}"
                    info = ydl.extract_info(search_query, download=False)
                    if info['entries']:
                        info = info['entries'][0]
                    else:
                        return None
                
                # Return both URL and metadata
                return {
                    'url': info.get('url'),
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'webpage_url': info.get('webpage_url', ''),
                    'thumbnail': info.get('thumbnail', '')
                }
            except Exception as e:
                self.logger.error(f"Error searching YouTube: {e}")
                return None

    def create_audio_source(self, url: str, volume: float = 0.5):
        """Create audio source with volume control"""
        return discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(url, **self.ffmpeg_options),
            volume=volume
        )

    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to MM:SS or HH:MM:SS"""
        if seconds == 0:
            return "Live"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def play_next_sync(self, guild_id: int):
        """Phát bài tiếp theo (sync function để dùng trong callback)"""
        try:
            if guild_id not in self.queues or self.queues[guild_id].is_empty():
                # Không có bài hát nào trong queue
                asyncio.run_coroutine_threadsafe(
                    self.send_queue_finished_message(guild_id),
                    self.bot.loop
                )
                return

            queue = self.queues[guild_id]
            next_song_info = queue.get_next()
            voice_client = self.voice_clients.get(guild_id)

            if voice_client and voice_client.is_connected() and next_song_info:
                # Xử lý song info
                if isinstance(next_song_info, dict):
                    song_url = next_song_info['url']
                    song_title = next_song_info.get('title', 'Unknown')
                else:
                    song_url = next_song_info
                    song_title = 'Unknown'
                
                # Cập nhật current song
                self.current_songs[guild_id] = next_song_info
                
                # Tạo audio source với volume control
                audio_source = self.create_audio_source(song_url, self.volumes.get(guild_id, 0.5))
                
                voice_client.play(
                    audio_source,
                    after=lambda _: self.play_next_sync(guild_id)
                )
                
                # Gửi thông báo
                asyncio.run_coroutine_threadsafe(
                    self.send_now_playing_message(guild_id, song_title),
                    self.bot.loop
                )
        except Exception as e:
            self.logger.error(f"Error in play_next_sync: {e}")
    
    async def send_queue_finished_message(self, guild_id: int):
        """Gửi thông báo hết queue"""
        guild = self.bot.get_guild(guild_id)
        if guild:
            for channel in guild.text_channels:
                if channel.name in ['general', 'music', 'bot']:
                    try:
                        await channel.send(f"{Emojis.MUSIC} Đã phát hết tất cả bài hát trong hàng đợi.")
                        break
                    except:
                        continue
    
    async def send_now_playing_message(self, guild_id: int, song_title: str):
        """Gửi thông báo đang phát"""
        guild = self.bot.get_guild(guild_id)
        if guild:
            for channel in guild.text_channels:
                if channel.name in ['general', 'music', 'bot']:
                    try:
                        await channel.send(f"{Emojis.MUSIC} Đang phát tiếp: **{song_title}**")
                        break
                    except:
                        continue

    @commands.command(name="play", help="Phát nhạc từ YouTube bằng tên bài hát hoặc link.")
    async def play(self, ctx: commands.Context, *, query: str):
        """Thêm bài hát vào hàng đợi và bắt đầu phát nhạc."""
        await self.join_voice_channel(ctx)

        voice_client = self.voice_clients.get(ctx.guild.id)
        if not voice_client:
            return

        song_info = await self.search_youtube(query)
        if not song_info:
            await ctx.send(f"{Emojis.ERROR} Không thể tìm thấy bài hát hoặc phát bài hát.")
            return

        song_url = song_info['url']
        song_title = song_info['title']

        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = MusicQueue()

        queue = self.queues[ctx.guild.id]

        if not voice_client.is_playing():
            # Phát ngay lập tức
            audio_source = self.create_audio_source(song_url, self.volumes.get(ctx.guild.id, 0.5))
            voice_client.play(
                audio_source,
                after=lambda _: self.play_next_sync(ctx.guild.id)
            )
            # Cập nhật current song
            self.current_songs[ctx.guild.id] = song_info
            queue.current = song_info
            await ctx.send(f"{Emojis.MUSIC} Đang phát: **{song_title}**")
        else:
            # Thêm vào queue
            queue.add(song_info)
            await ctx.send(f"➕ Đã thêm vào hàng đợi: **{song_title}**")

    @commands.command(name="queue", help="Xem hàng đợi nhạc.")
    async def queue(self, ctx: commands.Context):
        """Hiển thị các bài hát trong hàng đợi."""
        if ctx.guild.id in self.queues and not self.queues[ctx.guild.id].is_empty():
            queue = self.queues[ctx.guild.id]
            queue_list = []
            for i, song_info in enumerate(queue.get_queue_list(), 1):
                if isinstance(song_info, dict):
                    title = song_info.get('title', 'Unknown')
                    duration = self.format_duration(song_info.get('duration', 0))
                    queue_list.append(f"{i}. **{title}** `[{duration}]`")
                else:
                    queue_list.append(f"{i}. Unknown Song")

            embed = discord.Embed(
                title=f"{Emojis.QUEUE} Hàng đợi nhạc",
                description="\n".join(queue_list),
                color=Colors.MUSIC
            )

            # Thêm thông tin bài đang phát
            if ctx.guild.id in self.current_songs:
                current = self.current_songs[ctx.guild.id]
                if isinstance(current, dict):
                    current_title = current.get('title', 'Unknown')
                    embed.add_field(
                        name=f"{Emojis.MUSIC} Đang phát",
                        value=f"**{current_title}**",
                        inline=False
                    )

            embed.set_footer(text=f"Tổng cộng {len(queue_list)} bài hát trong hàng đợi")
            await ctx.send(embed=embed)
        else:
            await ctx.send("📭 Hàng đợi đang trống.")

    @commands.command(name="stop", help="Dừng phát nhạc.")
    async def stop(self, ctx: commands.Context):
        """Dừng phát nhạc."""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            # Xóa queue và current song
            if ctx.guild.id in self.queues:
                self.queues[ctx.guild.id].clear()
            if ctx.guild.id in self.current_songs:
                del self.current_songs[ctx.guild.id]
            await ctx.send(f"{Emojis.STOP} Đã dừng phát nhạc và xóa hàng đợi.")
        else:
            await ctx.send(f"{Emojis.ERROR} Hiện tại không có nhạc đang phát.")

    @commands.command(name="skip", help="Bỏ qua bài hát hiện tại.")
    async def skip(self, ctx: commands.Context):
        """Bỏ qua bài hát hiện tại."""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_playing():
            voice_client.stop()  # Sẽ trigger play_next thông qua after callback
            await ctx.send(f"{Emojis.SKIP} Đã bỏ qua bài hát hiện tại.")
        else:
            await ctx.send(f"{Emojis.ERROR} Hiện tại không có nhạc đang phát.")

    @commands.command(name="pause", help="Tạm dừng nhạc.")
    async def pause(self, ctx: commands.Context):
        """Tạm dừng nhạc."""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await ctx.send(f"{Emojis.PAUSE} Đã tạm dừng nhạc.")
        else:
            await ctx.send(f"{Emojis.ERROR} Hiện tại không có nhạc đang phát.")

    @commands.command(name="resume", help="Tiếp tục phát nhạc.")
    async def resume(self, ctx: commands.Context):
        """Tiếp tục phát nhạc."""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await ctx.send(f"{Emojis.PLAY} Đã tiếp tục phát nhạc.")
        else:
            await ctx.send(f"{Emojis.ERROR} Nhạc không bị tạm dừng.")

    @commands.command(name="volume", help="Điều chỉnh âm lượng (0-100).")
    async def volume(self, ctx: commands.Context, volume: int):
        """Điều chỉnh âm lượng."""
        if not 0 <= volume <= 100:
            await ctx.send(f"{Emojis.ERROR} Âm lượng phải từ 0 đến 100.")
            return

        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.source:
            # Lưu volume setting
            self.volumes[ctx.guild.id] = volume / 100.0

            # Điều chỉnh volume hiện tại nếu có
            if hasattr(voice_client.source, 'volume'):
                voice_client.source.volume = volume / 100.0

            await ctx.send(f"{Emojis.VOLUME} Đã đặt âm lượng thành {volume}%.")
        else:
            # Lưu setting cho lần phát tiếp theo
            self.volumes[ctx.guild.id] = volume / 100.0
            await ctx.send(f"{Emojis.VOLUME} Đã đặt âm lượng thành {volume}% cho lần phát tiếp theo.")

    @commands.command(name="nowplaying", help="Xem bài hát đang phát.")
    async def nowplaying(self, ctx: commands.Context):
        """Hiển thị thông tin bài hát đang phát."""
        voice_client = self.voice_clients.get(ctx.guild.id)
        if voice_client and voice_client.is_playing():
            embed = discord.Embed(
                title=f"{Emojis.MUSIC} Đang phát",
                color=Colors.MUSIC
            )

            # Thêm thông tin bài hát hiện tại
            if ctx.guild.id in self.current_songs:
                current = self.current_songs[ctx.guild.id]
                if isinstance(current, dict):
                    title = current.get('title', 'Unknown')
                    duration = self.format_duration(current.get('duration', 0))
                    embed.add_field(
                        name=f"{Emojis.MUSIC} Bài hát",
                        value=f"**{title}** `[{duration}]`",
                        inline=False
                    )

            # Thêm thông tin volume
            current_volume = int(self.volumes.get(ctx.guild.id, 0.5) * 100)
            embed.add_field(name=f"{Emojis.VOLUME} Âm lượng", value=f"{current_volume}%", inline=True)

            # Thêm thông tin queue
            queue_size = 0
            if ctx.guild.id in self.queues:
                queue_size = self.queues[ctx.guild.id].size()
            embed.add_field(name=f"{Emojis.QUEUE} Hàng đợi", value=f"{queue_size} bài", inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{Emojis.ERROR} Hiện tại không có nhạc đang phát.")

    @commands.command(name="leave", help="Bot rời khỏi kênh thoại.")
    async def leave(self, ctx: commands.Context):
        await self.leave_voice_channel(ctx)

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
