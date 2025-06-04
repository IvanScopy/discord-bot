import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from typing import Optional, List
import asyncio

from utils.database import db_manager
from utils.logging_config import get_logger, log_command, log_error, log_user_action
from bot.config import Colors, Emojis

class UserInfo(commands.Cog):
    """Cog for user information and profile management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger('userinfo')
    
    async def cog_load(self):
        """Called when the cog is loaded"""
        self.logger.info("User Info cog loaded successfully")
    
    def get_user_status_emoji(self, status: discord.Status) -> str:
        """Get emoji for user status"""
        status_emojis = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        return status_emojis.get(status, "❓")
    
    def get_activity_info(self, member: discord.Member) -> str:
        """Get formatted activity information"""
        if not member.activities:
            return "Không có hoạt động"
        
        activities = []
        for activity in member.activities:
            if isinstance(activity, discord.Game):
                activities.append(f"🎮 Đang chơi: {activity.name}")
            elif isinstance(activity, discord.Streaming):
                activities.append(f"📺 Đang stream: {activity.name}")
            elif isinstance(activity, discord.Listening):
                if isinstance(activity, discord.Spotify):
                    activities.append(f"🎵 Spotify: {activity.title} - {activity.artist}")
                else:
                    activities.append(f"🎧 Đang nghe: {activity.name}")
            elif isinstance(activity, discord.Watching):
                activities.append(f"👀 Đang xem: {activity.name}")
            elif isinstance(activity, discord.CustomActivity):
                if activity.name:
                    activities.append(f"💭 {activity.name}")
        
        return "\n".join(activities) if activities else "Không có hoạt động"
    
    def format_permissions(self, permissions: discord.Permissions) -> str:
        """Format permissions into a readable string"""
        important_perms = [
            ('administrator', 'Quản trị viên'),
            ('manage_guild', 'Quản lý server'),
            ('manage_channels', 'Quản lý kênh'),
            ('manage_roles', 'Quản lý vai trò'),
            ('manage_messages', 'Quản lý tin nhắn'),
            ('kick_members', 'Kick thành viên'),
            ('ban_members', 'Ban thành viên'),
            ('moderate_members', 'Điều hành thành viên'),
            ('manage_nicknames', 'Quản lý nickname'),
            ('manage_webhooks', 'Quản lý webhook'),
            ('view_audit_log', 'Xem audit log')
        ]
        
        user_perms = []
        for perm, name in important_perms:
            if getattr(permissions, perm, False):
                user_perms.append(name)
        
        return ", ".join(user_perms) if user_perms else "Không có quyền đặc biệt"
    
    @app_commands.command(name="userinfo", description="Hiển thị thông tin chi tiết về người dùng")
    async def userinfo(self, interaction: discord.Interaction, 
                      user: Optional[discord.Member] = None):
        """Display detailed user information"""
        try:
            await interaction.response.defer()
            
            target_user = user or interaction.user
            
            # Update user in database
            await db_manager.add_or_update_user(
                target_user.id, 
                target_user.name, 
                target_user.display_name
            )
            
            # Get user data from database
            user_data = await db_manager.get_user(target_user.id)
            
            # Create main embed
            embed = discord.Embed(
                title=f"👤 Thông tin người dùng: {target_user.display_name}",
                color=target_user.color if target_user.color != discord.Color.default() else 0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            # Set user avatar
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Basic information
            embed.add_field(
                name="🏷️ Tên người dùng",
                value=f"{target_user.name}#{target_user.discriminator}",
                inline=True
            )
            
            embed.add_field(
                name="🎭 Tên hiển thị",
                value=target_user.display_name,
                inline=True
            )
            
            embed.add_field(
                name="🆔 User ID",
                value=str(target_user.id),
                inline=True
            )
            
            # Status and activity
            if isinstance(target_user, discord.Member):
                status_emoji = self.get_user_status_emoji(target_user.status)
                embed.add_field(
                    name="📊 Trạng thái",
                    value=f"{status_emoji} {target_user.status.name.title()}",
                    inline=True
                )
                
                # Activity information
                activity_info = self.get_activity_info(target_user)
                embed.add_field(
                    name="🎯 Hoạt động",
                    value=activity_info,
                    inline=False
                )
            
            # Account creation date
            created_at = target_user.created_at
            embed.add_field(
                name="📅 Ngày tạo tài khoản",
                value=f"{created_at.strftime('%d/%m/%Y %H:%M')}\n({(datetime.now(timezone.utc) - created_at).days} ngày trước)",
                inline=True
            )
            
            # Server join date (if member)
            if isinstance(target_user, discord.Member) and target_user.joined_at:
                joined_at = target_user.joined_at
                embed.add_field(
                    name="📥 Ngày tham gia server",
                    value=f"{joined_at.strftime('%d/%m/%Y %H:%M')}\n({(datetime.now(timezone.utc) - joined_at).days} ngày trước)",
                    inline=True
                )
            
            # Database information
            if user_data:
                embed.add_field(
                    name="💬 Số tin nhắn",
                    value=str(user_data.get('message_count', 0)),
                    inline=True
                )
                
                if user_data.get('last_seen'):
                    last_seen = datetime.fromisoformat(user_data['last_seen'])
                    embed.add_field(
                        name="👁️ Lần cuối hoạt động",
                        value=last_seen.strftime('%d/%m/%Y %H:%M'),
                        inline=True
                    )
            
            # Roles (if member)
            if isinstance(target_user, discord.Member):
                roles = [role.mention for role in target_user.roles[1:]]  # Exclude @everyone
                if roles:
                    # Limit roles display to avoid embed limits
                    if len(roles) > 10:
                        role_text = ", ".join(roles[:10]) + f" và {len(roles) - 10} vai trò khác"
                    else:
                        role_text = ", ".join(roles)
                    
                    embed.add_field(
                        name=f"🎭 Vai trò ({len(roles)})",
                        value=role_text,
                        inline=False
                    )
                
                # Permissions
                permissions = self.format_permissions(target_user.guild_permissions)
                embed.add_field(
                    name="🔐 Quyền hạn",
                    value=permissions,
                    inline=False
                )
                
                # Boost information
                if target_user.premium_since:
                    boost_since = target_user.premium_since
                    embed.add_field(
                        name="💎 Nitro Boost",
                        value=f"Từ {boost_since.strftime('%d/%m/%Y')}\n({(datetime.now(timezone.utc) - boost_since).days} ngày)",
                        inline=True
                    )
            
            # Bot information
            if target_user.bot:
                embed.add_field(
                    name="🤖 Bot",
                    value="Đây là một bot",
                    inline=True
                )
                
                if target_user.public_flags:
                    flags = []
                    if target_user.public_flags.verified_bot:
                        flags.append("✅ Bot được xác minh")
                    if target_user.public_flags.verified_bot_developer:
                        flags.append("👨‍💻 Nhà phát triển bot được xác minh")
                    
                    if flags:
                        embed.add_field(
                            name="🏆 Huy hiệu",
                            value="\n".join(flags),
                            inline=True
                        )
            
            # User flags/badges
            if hasattr(target_user, 'public_flags') and target_user.public_flags:
                badges = []
                flags = target_user.public_flags
                
                if flags.staff:
                    badges.append("👨‍💼 Discord Staff")
                if flags.partner:
                    badges.append("🤝 Discord Partner")
                if flags.hypesquad:
                    badges.append("🎉 HypeSquad Events")
                if flags.bug_hunter:
                    badges.append("🐛 Bug Hunter")
                if flags.hypesquad_bravery:
                    badges.append("💪 HypeSquad Bravery")
                if flags.hypesquad_brilliance:
                    badges.append("💡 HypeSquad Brilliance")
                if flags.hypesquad_balance:
                    badges.append("⚖️ HypeSquad Balance")
                if flags.early_supporter:
                    badges.append("⭐ Early Supporter")
                if flags.verified_bot_developer:
                    badges.append("👨‍💻 Verified Bot Developer")
                if flags.discord_certified_moderator:
                    badges.append("🛡️ Discord Certified Moderator")
                
                if badges:
                    embed.add_field(
                        name="🏆 Huy hiệu",
                        value="\n".join(badges),
                        inline=False
                    )
            
            embed.set_footer(
                text=f"Yêu cầu bởi {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
            
            log_user_action(
                "userinfo_view",
                interaction.user.id,
                interaction.guild.id,
                f"Viewed info for {target_user.name}"
            )
            
        except Exception as e:
            log_error(e, "userinfo", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tải thông tin người dùng!",
                ephemeral=True
            )
    
    @app_commands.command(name="avatar", description="Hiển thị avatar của người dùng")
    async def avatar(self, interaction: discord.Interaction, 
                    user: Optional[discord.Member] = None):
        """Display user's avatar"""
        try:
            await interaction.response.defer()
            
            target_user = user or interaction.user
            
            embed = discord.Embed(
                title=f"🖼️ Avatar của {target_user.display_name}",
                color=target_user.color if target_user.color != discord.Color.default() else 0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            # Set the avatar as the main image
            embed.set_image(url=target_user.display_avatar.url)
            
            # Add download links
            avatar_formats = []
            for fmt in ['png', 'jpg', 'webp']:
                avatar_formats.append(f"[{fmt.upper()}]({target_user.display_avatar.with_format(fmt).url})")
            
            if target_user.display_avatar.is_animated():
                avatar_formats.append(f"[GIF]({target_user.display_avatar.with_format('gif').url})")
            
            embed.add_field(
                name="📥 Tải xuống",
                value=" | ".join(avatar_formats),
                inline=False
            )
            
            embed.set_footer(
                text=f"Yêu cầu bởi {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log_error(e, "avatar", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tải avatar!",
                ephemeral=True
            )
    
    @app_commands.command(name="serverinfo", description="Hiển thị thông tin về server")
    async def serverinfo(self, interaction: discord.Interaction):
        """Display server information"""
        try:
            await interaction.response.defer()
            
            guild = interaction.guild
            
            embed = discord.Embed(
                title=f"🏰 Thông tin Server: {guild.name}",
                color=0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            # Basic server info
            embed.add_field(
                name="🆔 Server ID",
                value=str(guild.id),
                inline=True
            )
            
            embed.add_field(
                name="👑 Chủ sở hữu",
                value=guild.owner.mention if guild.owner else "Không xác định",
                inline=True
            )
            
            embed.add_field(
                name="📅 Ngày tạo",
                value=guild.created_at.strftime('%d/%m/%Y'),
                inline=True
            )
            
            # Member statistics
            total_members = guild.member_count
            online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
            bots = sum(1 for member in guild.members if member.bot)
            humans = total_members - bots
            
            embed.add_field(
                name="👥 Thành viên",
                value=f"Tổng: {total_members}\nOnline: {online_members}\nCon người: {humans}\nBot: {bots}",
                inline=True
            )
            
            # Channel statistics
            text_channels = len(guild.text_channels)
            voice_channels = len(guild.voice_channels)
            categories = len(guild.categories)
            
            embed.add_field(
                name="📺 Kênh",
                value=f"Text: {text_channels}\nVoice: {voice_channels}\nDanh mục: {categories}",
                inline=True
            )
            
            # Role count
            embed.add_field(
                name="🎭 Vai trò",
                value=str(len(guild.roles)),
                inline=True
            )
            
            # Boost information
            if guild.premium_tier > 0:
                embed.add_field(
                    name="💎 Boost Level",
                    value=f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts",
                    inline=True
                )
            
            # Features
            if guild.features:
                features = []
                feature_names = {
                    'COMMUNITY': 'Cộng đồng',
                    'VERIFIED': 'Đã xác minh',
                    'PARTNERED': 'Đối tác',
                    'VANITY_URL': 'URL tùy chỉnh',
                    'ANIMATED_ICON': 'Icon động',
                    'BANNER': 'Banner',
                    'WELCOME_SCREEN_ENABLED': 'Màn hình chào mừng'
                }
                
                for feature in guild.features:
                    features.append(feature_names.get(feature, feature.replace('_', ' ').title()))
                
                if features:
                    embed.add_field(
                        name="✨ Tính năng",
                        value=", ".join(features[:5]),  # Limit to 5 features
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log_error(e, "serverinfo", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tải thông tin server!",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    """Setup function to add the cog"""
    await bot.add_cog(UserInfo(bot))
