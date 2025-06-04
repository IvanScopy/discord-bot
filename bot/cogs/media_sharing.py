import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import mimetypes
from typing import Optional, List
from datetime import datetime
import asyncio

from utils.database import db_manager
from utils.logging_config import get_logger, log_command, log_error, log_user_action
from bot.config import Colors, Emojis

class MediaSharing(commands.Cog):
    """Cog for media sharing functionality with Discord SDK integration"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger('media')
        self.max_file_size = 25 * 1024 * 1024  # 25MB Discord limit
        self.allowed_image_types = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        self.allowed_video_types = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv'}
        self.allowed_audio_types = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        self.logger.info("Media Sharing cog loaded successfully")
    
    def get_media_type(self, filename: str) -> str:
        """Determine media type from file extension"""
        ext = os.path.splitext(filename.lower())[1]
        
        if ext in self.allowed_image_types:
            return 'image'
        elif ext in self.allowed_video_types:
            return 'video'
        elif ext in self.allowed_audio_types:
            return 'audio'
        else:
            return 'file'
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed"""
        ext = os.path.splitext(filename.lower())[1]
        all_allowed = (self.allowed_image_types | 
                      self.allowed_video_types | 
                      self.allowed_audio_types)
        return ext in all_allowed
    
    @app_commands.command(name="share_media", description="Chia sẻ media (ảnh, video, audio)")
    async def share_media(self, interaction: discord.Interaction, 
                         file: discord.Attachment, 
                         description: Optional[str] = None):
        """Share media files with the server"""
        try:
            await interaction.response.defer()
            
            # Check file size
            if file.size > self.max_file_size:
                await interaction.followup.send(
                    f"❌ File quá lớn! Kích thước tối đa: {self.max_file_size // (1024*1024)}MB",
                    ephemeral=True
                )
                return
            
            # Check file type
            if not self.is_allowed_file(file.filename):
                await interaction.followup.send(
                    "❌ Loại file không được hỗ trợ! Chỉ chấp nhận: ảnh, video, audio",
                    ephemeral=True
                )
                return
            
            media_type = self.get_media_type(file.filename)
            
            # Create embed for media sharing
            embed = discord.Embed(
                title="📎 Media được chia sẻ",
                description=description or "Không có mô tả",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="📁 Tên file", value=file.filename, inline=True)
            embed.add_field(name="📏 Kích thước", value=f"{file.size // 1024} KB", inline=True)
            embed.add_field(name="🎭 Loại", value=media_type.title(), inline=True)
            embed.set_footer(
                text=f"Chia sẻ bởi {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Set image/video in embed if applicable
            if media_type == 'image':
                embed.set_image(url=file.url)
            elif media_type == 'video':
                embed.add_field(name="🎬 Video", value=f"[Xem video]({file.url})", inline=False)
            
            # Send the media
            await interaction.followup.send(embed=embed, file=await file.to_file())
            
            # Log to database
            await db_manager.log_media_share(
                user_id=interaction.user.id,
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
                media_type=media_type,
                media_url=file.url,
                description=description
            )
            
            log_user_action(
                "media_share", 
                interaction.user.id, 
                interaction.guild.id,
                f"Shared {media_type}: {file.filename}"
            )
            
        except Exception as e:
            log_error(e, "share_media", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi chia sẻ media!",
                ephemeral=True
            )
    
    @app_commands.command(name="share_url", description="Chia sẻ media từ URL")
    async def share_url(self, interaction: discord.Interaction, 
                       url: str, 
                       description: Optional[str] = None):
        """Share media from URL"""
        try:
            await interaction.response.defer()
            
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                await interaction.followup.send(
                    "❌ URL không hợp lệ! Phải bắt đầu bằng http:// hoặc https://",
                    ephemeral=True
                )
                return
            
            # Try to fetch the URL to check if it's valid
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url, timeout=10) as response:
                        if response.status != 200:
                            await interaction.followup.send(
                                f"❌ Không thể truy cập URL! Status: {response.status}",
                                ephemeral=True
                            )
                            return
                        
                        content_type = response.headers.get('content-type', '').lower()
                        content_length = response.headers.get('content-length')
                        
                        # Check file size if available
                        if content_length and int(content_length) > self.max_file_size:
                            await interaction.followup.send(
                                f"❌ File quá lớn! Kích thước tối đa: {self.max_file_size // (1024*1024)}MB",
                                ephemeral=True
                            )
                            return
                        
                except asyncio.TimeoutError:
                    await interaction.followup.send(
                        "❌ Timeout khi kiểm tra URL!",
                        ephemeral=True
                    )
                    return
                except Exception as e:
                    await interaction.followup.send(
                        f"❌ Lỗi khi kiểm tra URL: {str(e)}",
                        ephemeral=True
                    )
                    return
            
            # Determine media type from content type or URL
            media_type = 'file'
            if any(t in content_type for t in ['image/', 'video/', 'audio/']):
                if 'image/' in content_type:
                    media_type = 'image'
                elif 'video/' in content_type:
                    media_type = 'video'
                elif 'audio/' in content_type:
                    media_type = 'audio'
            
            # Create embed
            embed = discord.Embed(
                title="🔗 Media từ URL",
                description=description or "Không có mô tả",
                color=0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="🌐 URL", value=url, inline=False)
            embed.add_field(name="🎭 Loại", value=media_type.title(), inline=True)
            
            if content_length:
                embed.add_field(
                    name="📏 Kích thước", 
                    value=f"{int(content_length) // 1024} KB", 
                    inline=True
                )
            
            embed.set_footer(
                text=f"Chia sẻ bởi {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            # Set image if it's an image URL
            if media_type == 'image':
                embed.set_image(url=url)
            
            await interaction.followup.send(embed=embed)
            
            # Log to database
            await db_manager.log_media_share(
                user_id=interaction.user.id,
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
                media_type=media_type,
                media_url=url,
                description=description
            )
            
            log_user_action(
                "url_share", 
                interaction.user.id, 
                interaction.guild.id,
                f"Shared URL: {url}"
            )
            
        except Exception as e:
            log_error(e, "share_url", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi chia sẻ URL!",
                ephemeral=True
            )
    
    @app_commands.command(name="media_gallery", description="Xem gallery media đã chia sẻ")
    async def media_gallery(self, interaction: discord.Interaction, 
                           media_type: Optional[str] = None):
        """View shared media gallery"""
        try:
            await interaction.response.defer()
            
            # This would require implementing a database query for media shares
            # For now, we'll show a placeholder
            embed = discord.Embed(
                title="🖼️ Media Gallery",
                description="Tính năng đang được phát triển...",
                color=0xffa500,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📝 Ghi chú",
                value="Gallery sẽ hiển thị tất cả media đã được chia sẻ trong server này.",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log_error(e, "media_gallery", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tải gallery!",
                ephemeral=True
            )
    
    @commands.command(name="upload", help="Upload và chia sẻ file")
    async def upload_file(self, ctx: commands.Context, *, description: str = None):
        """Upload file via message attachment"""
        try:
            if not ctx.message.attachments:
                await ctx.send("❌ Vui lòng đính kèm file để upload!")
                return
            
            attachment = ctx.message.attachments[0]
            
            # Check file size
            if attachment.size > self.max_file_size:
                await ctx.send(
                    f"❌ File quá lớn! Kích thước tối đa: {self.max_file_size // (1024*1024)}MB"
                )
                return
            
            media_type = self.get_media_type(attachment.filename)
            
            embed = discord.Embed(
                title="📤 File đã được upload",
                description=description or "Không có mô tả",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="📁 Tên file", value=attachment.filename, inline=True)
            embed.add_field(name="📏 Kích thước", value=f"{attachment.size // 1024} KB", inline=True)
            embed.add_field(name="🎭 Loại", value=media_type.title(), inline=True)
            embed.set_footer(
                text=f"Upload bởi {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            
            if media_type == 'image':
                embed.set_image(url=attachment.url)
            
            await ctx.send(embed=embed)
            
            # Log to database
            await db_manager.log_media_share(
                user_id=ctx.author.id,
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                media_type=media_type,
                media_url=attachment.url,
                description=description
            )
            
            log_command("upload", ctx.author.id, ctx.guild.id, True)
            
        except Exception as e:
            log_error(e, "upload_file", ctx.author.id, ctx.guild.id)
            log_command("upload", ctx.author.id, ctx.guild.id, False, str(e))
            await ctx.send("❌ Có lỗi xảy ra khi upload file!")

async def setup(bot: commands.Bot):
    """Setup function to add the cog"""
    await bot.add_cog(MediaSharing(bot))
