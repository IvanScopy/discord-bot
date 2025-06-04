import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio

from utils.database import db_manager
from utils.logging_config import get_logger, log_command, log_error, log_user_action
from bot.config import Colors, Emojis

class EventView(discord.ui.View):
    """View for event interaction buttons"""
    
    def __init__(self, event_id: int):
        super().__init__(timeout=None)
        self.event_id = event_id
    
    @discord.ui.button(label="Tham gia", style=discord.ButtonStyle.green, emoji="✅")
    async def join_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Join an event"""
        try:
            success = await db_manager.join_event(self.event_id, interaction.user.id)
            
            if success:
                await interaction.response.send_message(
                    "✅ Bạn đã tham gia sự kiện thành công!",
                    ephemeral=True
                )
                log_user_action(
                    "event_join",
                    interaction.user.id,
                    interaction.guild.id,
                    f"Joined event {self.event_id}"
                )
            else:
                await interaction.response.send_message(
                    "❌ Bạn đã tham gia sự kiện này rồi!",
                    ephemeral=True
                )
        except Exception as e:
            log_error(e, "join_event", interaction.user.id, interaction.guild.id)
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi tham gia sự kiện!",
                ephemeral=True
            )
    
    @discord.ui.button(label="Rời khỏi", style=discord.ButtonStyle.red, emoji="❌")
    async def leave_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Leave an event"""
        try:
            success = await db_manager.leave_event(self.event_id, interaction.user.id)
            
            if success:
                await interaction.response.send_message(
                    "✅ Bạn đã rời khỏi sự kiện!",
                    ephemeral=True
                )
                log_user_action(
                    "event_leave",
                    interaction.user.id,
                    interaction.guild.id,
                    f"Left event {self.event_id}"
                )
            else:
                await interaction.response.send_message(
                    "❌ Bạn chưa tham gia sự kiện này!",
                    ephemeral=True
                )
        except Exception as e:
            log_error(e, "leave_event", interaction.user.id, interaction.guild.id)
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi rời khỏi sự kiện!",
                ephemeral=True
            )
    
    @discord.ui.button(label="Xem thành viên", style=discord.ButtonStyle.blurple, emoji="👥")
    async def view_participants(self, interaction: discord.Interaction, button: discord.ui.Button):
        """View event participants"""
        try:
            participants = await db_manager.get_event_participants(self.event_id)
            event = await db_manager.get_event(self.event_id)
            
            if not event:
                await interaction.response.send_message(
                    "❌ Không tìm thấy sự kiện!",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"👥 Thành viên tham gia: {event['title']}",
                color=0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            if participants:
                participant_list = []
                for user_id in participants:
                    try:
                        user = await interaction.client.fetch_user(user_id)
                        participant_list.append(f"• {user.display_name} ({user.mention})")
                    except:
                        participant_list.append(f"• User ID: {user_id}")
                
                embed.description = "\n".join(participant_list)
                embed.add_field(
                    name="📊 Thống kê",
                    value=f"Tổng số người tham gia: **{len(participants)}**",
                    inline=False
                )
            else:
                embed.description = "Chưa có ai tham gia sự kiện này."
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            log_error(e, "view_participants", interaction.user.id, interaction.guild.id)
            await interaction.response.send_message(
                "❌ Có lỗi xảy ra khi xem danh sách thành viên!",
                ephemeral=True
            )

class EventManagement(commands.Cog):
    """Cog for event creation and management"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger('events')
    
    async def cog_load(self):
        """Called when the cog is loaded"""
        self.logger.info("Event Management cog loaded successfully")
    
    def parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string in various formats"""
        formats = [
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    
    @app_commands.command(name="create_event", description="Tạo sự kiện mới")
    async def create_event(self, interaction: discord.Interaction,
                          title: str,
                          date: str,
                          description: Optional[str] = None,
                          max_participants: Optional[int] = None):
        """Create a new event"""
        try:
            await interaction.response.defer()
            
            # Parse the date
            event_date = self.parse_datetime(date)
            if not event_date:
                await interaction.followup.send(
                    "❌ Định dạng ngày không hợp lệ! Sử dụng: YYYY-MM-DD HH:MM hoặc DD/MM/YYYY HH:MM",
                    ephemeral=True
                )
                return
            
            # Check if date is in the future
            if event_date <= datetime.now():
                await interaction.followup.send(
                    "❌ Ngày sự kiện phải là thời gian trong tương lai!",
                    ephemeral=True
                )
                return
            
            # Create event in database
            event_id = await db_manager.create_event(
                title=title,
                description=description or "Không có mô tả",
                creator_id=interaction.user.id,
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
                event_date=event_date.isoformat(),
                max_participants=max_participants or -1
            )
            
            # Create embed for the event
            embed = discord.Embed(
                title=f"🎉 Sự kiện mới: {title}",
                description=description or "Không có mô tả",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📅 Thời gian",
                value=event_date.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
            
            embed.add_field(
                name="👤 Người tạo",
                value=interaction.user.mention,
                inline=True
            )
            
            if max_participants and max_participants > 0:
                embed.add_field(
                    name="👥 Số người tối đa",
                    value=str(max_participants),
                    inline=True
                )
            
            embed.add_field(
                name="🆔 Event ID",
                value=str(event_id),
                inline=True
            )
            
            embed.set_footer(
                text="Sử dụng các nút bên dưới để tham gia hoặc rời khỏi sự kiện"
            )
            
            # Create view with buttons
            view = EventView(event_id)
            
            await interaction.followup.send(embed=embed, view=view)
            
            log_user_action(
                "event_create",
                interaction.user.id,
                interaction.guild.id,
                f"Created event: {title} (ID: {event_id})"
            )
            
        except Exception as e:
            log_error(e, "create_event", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tạo sự kiện!",
                ephemeral=True
            )
    
    @app_commands.command(name="list_events", description="Xem danh sách sự kiện")
    async def list_events(self, interaction: discord.Interaction):
        """List all active events in the guild"""
        try:
            await interaction.response.defer()
            
            events = await db_manager.get_guild_events(interaction.guild.id)
            
            if not events:
                embed = discord.Embed(
                    title="📅 Danh sách sự kiện",
                    description="Hiện tại không có sự kiện nào.",
                    color=0xffa500
                )
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="📅 Danh sách sự kiện",
                color=0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            for event in events[:10]:  # Limit to 10 events
                event_date = datetime.fromisoformat(event['event_date'])
                participants = await db_manager.get_event_participants(event['id'])
                
                field_value = f"📝 {event['description']}\n"
                field_value += f"📅 {event_date.strftime('%d/%m/%Y %H:%M')}\n"
                field_value += f"👥 {len(participants)} người tham gia"
                
                if event['max_participants'] > 0:
                    field_value += f"/{event['max_participants']}"
                
                embed.add_field(
                    name=f"🎉 {event['title']} (ID: {event['id']})",
                    value=field_value,
                    inline=False
                )
            
            if len(events) > 10:
                embed.set_footer(text=f"Hiển thị 10/{len(events)} sự kiện")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            log_error(e, "list_events", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tải danh sách sự kiện!",
                ephemeral=True
            )
    
    @app_commands.command(name="event_info", description="Xem thông tin chi tiết sự kiện")
    async def event_info(self, interaction: discord.Interaction, event_id: int):
        """Get detailed information about an event"""
        try:
            await interaction.response.defer()
            
            event = await db_manager.get_event(event_id)
            if not event:
                await interaction.followup.send(
                    "❌ Không tìm thấy sự kiện với ID này!",
                    ephemeral=True
                )
                return
            
            participants = await db_manager.get_event_participants(event_id)
            event_date = datetime.fromisoformat(event['event_date'])
            created_date = datetime.fromisoformat(event['created_at'])
            
            embed = discord.Embed(
                title=f"🎉 {event['title']}",
                description=event['description'],
                color=0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📅 Thời gian sự kiện",
                value=event_date.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
            
            embed.add_field(
                name="📝 Ngày tạo",
                value=created_date.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
            
            embed.add_field(
                name="🆔 Event ID",
                value=str(event['id']),
                inline=True
            )
            
            embed.add_field(
                name="👥 Số người tham gia",
                value=f"{len(participants)}" + (f"/{event['max_participants']}" if event['max_participants'] > 0 else ""),
                inline=True
            )
            
            embed.add_field(
                name="📊 Trạng thái",
                value=event['status'].title(),
                inline=True
            )
            
            # Add creator info
            try:
                creator = await self.bot.fetch_user(event['creator_id'])
                embed.add_field(
                    name="👤 Người tạo",
                    value=creator.mention,
                    inline=True
                )
            except:
                embed.add_field(
                    name="👤 Người tạo",
                    value=f"User ID: {event['creator_id']}",
                    inline=True
                )
            
            # Create view with buttons
            view = EventView(event_id)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            log_error(e, "event_info", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tải thông tin sự kiện!",
                ephemeral=True
            )
    
    @commands.command(name="event", help="Tạo sự kiện nhanh")
    async def quick_event(self, ctx: commands.Context, title: str, date: str, *, description: str = None):
        """Quick event creation via prefix command"""
        try:
            # Parse the date
            event_date = self.parse_datetime(date)
            if not event_date:
                await ctx.send(
                    "❌ Định dạng ngày không hợp lệ! Sử dụng: YYYY-MM-DD HH:MM hoặc DD/MM/YYYY HH:MM"
                )
                return
            
            # Check if date is in the future
            if event_date <= datetime.now():
                await ctx.send("❌ Ngày sự kiện phải là thời gian trong tương lai!")
                return
            
            # Create event in database
            event_id = await db_manager.create_event(
                title=title,
                description=description or "Không có mô tả",
                creator_id=ctx.author.id,
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                event_date=event_date.isoformat()
            )
            
            embed = discord.Embed(
                title=f"🎉 Sự kiện: {title}",
                description=description or "Không có mô tả",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📅 Thời gian",
                value=event_date.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
            
            embed.add_field(
                name="🆔 Event ID",
                value=str(event_id),
                inline=True
            )
            
            embed.set_footer(text=f"Tạo bởi {ctx.author.display_name}")
            
            view = EventView(event_id)
            await ctx.send(embed=embed, view=view)
            
            log_command("event", ctx.author.id, ctx.guild.id, True)
            
        except Exception as e:
            log_error(e, "quick_event", ctx.author.id, ctx.guild.id)
            log_command("event", ctx.author.id, ctx.guild.id, False, str(e))
            await ctx.send("❌ Có lỗi xảy ra khi tạo sự kiện!")

async def setup(bot: commands.Bot):
    """Setup function to add the cog"""
    await bot.add_cog(EventManagement(bot))
