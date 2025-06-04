import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import schedule
import threading
import time

from utils.database import db_manager
from utils.logging_config import get_logger, log_command, log_error, log_user_action
from bot.config import Colors, Emojis

class ReminderSystem(commands.Cog):
    """Advanced reminder system with scheduling capabilities"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger('reminders')
        self.reminder_check_task.start()
        self.schedule_thread = None
        self.start_schedule_thread()
    
    def start_schedule_thread(self):
        """Start the schedule thread for recurring reminders"""
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.schedule_thread = threading.Thread(target=run_schedule, daemon=True)
        self.schedule_thread.start()
        self.logger.info("Schedule thread started for recurring reminders")
    
    async def cog_load(self):
        """Called when the cog is loaded"""
        self.logger.info("Reminder System cog loaded successfully")
    
    def cog_unload(self):
        """Called when the cog is unloaded"""
        self.reminder_check_task.cancel()
        self.logger.info("Reminder System cog unloaded")
    
    @tasks.loop(minutes=1)
    async def reminder_check_task(self):
        """Check for due reminders every minute"""
        try:
            reminders = await db_manager.get_active_reminders()
            current_time = datetime.now()
            
            for reminder in reminders:
                remind_time = datetime.fromisoformat(reminder['remind_time'])
                
                if remind_time <= current_time:
                    await self.send_reminder(reminder)
                    
                    if reminder['is_recurring'] and reminder['recurring_pattern']:
                        await self.schedule_next_occurrence(reminder)
                    else:
                        await db_manager.complete_reminder(reminder['id'])
                        
        except Exception as e:
            self.logger.error(f"Error in reminder check task: {e}")
    
    @reminder_check_task.before_loop
    async def before_reminder_check(self):
        """Wait until the bot is ready before starting the task"""
        await self.bot.wait_until_ready()
    
    async def send_reminder(self, reminder: dict):
        """Send a reminder to the user"""
        try:
            channel = self.bot.get_channel(reminder['channel_id'])
            if not channel:
                self.logger.warning(f"Channel {reminder['channel_id']} not found for reminder {reminder['id']}")
                return
            
            user = self.bot.get_user(reminder['user_id'])
            if not user:
                try:
                    user = await self.bot.fetch_user(reminder['user_id'])
                except:
                    self.logger.warning(f"User {reminder['user_id']} not found for reminder {reminder['id']}")
                    return
            
            embed = discord.Embed(
                title="🔔 Nhắc nhở!",
                description=reminder['message'],
                color=0xff6b6b,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="👤 Người nhận",
                value=user.mention,
                inline=True
            )
            
            if reminder['is_recurring']:
                embed.add_field(
                    name="🔄 Loại",
                    value="Nhắc nhở định kỳ",
                    inline=True
                )
            
            embed.set_footer(text=f"Reminder ID: {reminder['id']}")
            
            await channel.send(content=user.mention, embed=embed)
            
            log_user_action(
                "reminder_sent",
                reminder['user_id'],
                reminder['guild_id'],
                f"Reminder sent: {reminder['message'][:50]}..."
            )
            
        except Exception as e:
            log_error(e, "send_reminder", reminder['user_id'], reminder['guild_id'])
    
    async def schedule_next_occurrence(self, reminder: dict):
        """Schedule the next occurrence of a recurring reminder"""
        try:
            current_time = datetime.fromisoformat(reminder['remind_time'])
            pattern = reminder['recurring_pattern']
            
            # Calculate next occurrence based on pattern
            if pattern == 'daily':
                next_time = current_time + timedelta(days=1)
            elif pattern == 'weekly':
                next_time = current_time + timedelta(weeks=1)
            elif pattern == 'monthly':
                next_time = current_time + timedelta(days=30)  # Approximate
            elif pattern == 'hourly':
                next_time = current_time + timedelta(hours=1)
            else:
                # Invalid pattern, mark as completed
                await db_manager.complete_reminder(reminder['id'])
                return
            
            # Update the reminder time in database
            await db_manager.create_reminder(
                user_id=reminder['user_id'],
                guild_id=reminder['guild_id'],
                channel_id=reminder['channel_id'],
                message=reminder['message'],
                remind_time=next_time.isoformat(),
                is_recurring=True,
                recurring_pattern=pattern
            )
            
            # Mark current reminder as completed
            await db_manager.complete_reminder(reminder['id'])
            
        except Exception as e:
            log_error(e, "schedule_next_occurrence")
    
    def parse_time_input(self, time_str: str) -> Optional[datetime]:
        """Parse various time input formats"""
        now = datetime.now()
        
        # Handle relative time (e.g., "5m", "2h", "1d")
        if time_str.endswith('m'):
            try:
                minutes = int(time_str[:-1])
                return now + timedelta(minutes=minutes)
            except ValueError:
                pass
        elif time_str.endswith('h'):
            try:
                hours = int(time_str[:-1])
                return now + timedelta(hours=hours)
            except ValueError:
                pass
        elif time_str.endswith('d'):
            try:
                days = int(time_str[:-1])
                return now + timedelta(days=days)
            except ValueError:
                pass
        
        # Handle absolute time formats
        formats = [
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M",
            "%H:%M",  # Today at specific time
        ]
        
        for fmt in formats:
            try:
                if fmt == "%H:%M":
                    # For time only, assume today
                    time_obj = datetime.strptime(time_str, fmt).time()
                    result = datetime.combine(now.date(), time_obj)
                    # If the time has already passed today, schedule for tomorrow
                    if result <= now:
                        result += timedelta(days=1)
                    return result
                else:
                    return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @app_commands.command(name="remind", description="Tạo nhắc nhở")
    async def create_reminder(self, interaction: discord.Interaction,
                            time: str,
                            message: str,
                            recurring: Optional[str] = None):
        """Create a new reminder"""
        try:
            await interaction.response.defer()
            
            # Parse the time
            remind_time = self.parse_time_input(time)
            if not remind_time:
                await interaction.followup.send(
                    "❌ Định dạng thời gian không hợp lệ!\n"
                    "Sử dụng: `5m`, `2h`, `1d`, `HH:MM`, hoặc `YYYY-MM-DD HH:MM`",
                    ephemeral=True
                )
                return
            
            # Check if time is in the future
            if remind_time <= datetime.now():
                await interaction.followup.send(
                    "❌ Thời gian nhắc nhở phải là thời gian trong tương lai!",
                    ephemeral=True
                )
                return
            
            # Validate recurring pattern
            is_recurring = False
            if recurring:
                valid_patterns = ['hourly', 'daily', 'weekly', 'monthly']
                if recurring.lower() not in valid_patterns:
                    await interaction.followup.send(
                        f"❌ Mẫu lặp lại không hợp lệ! Sử dụng: {', '.join(valid_patterns)}",
                        ephemeral=True
                    )
                    return
                is_recurring = True
                recurring = recurring.lower()
            
            # Create reminder in database
            reminder_id = await db_manager.create_reminder(
                user_id=interaction.user.id,
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
                message=message,
                remind_time=remind_time.isoformat(),
                is_recurring=is_recurring,
                recurring_pattern=recurring
            )
            
            # Create confirmation embed
            embed = discord.Embed(
                title="⏰ Nhắc nhở đã được tạo",
                description=f"**Nội dung:** {message}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📅 Thời gian",
                value=remind_time.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
            
            if is_recurring:
                embed.add_field(
                    name="🔄 Lặp lại",
                    value=recurring.title(),
                    inline=True
                )
            
            embed.add_field(
                name="🆔 Reminder ID",
                value=str(reminder_id),
                inline=True
            )
            
            embed.set_footer(
                text=f"Tạo bởi {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.followup.send(embed=embed)
            
            log_user_action(
                "reminder_create",
                interaction.user.id,
                interaction.guild.id,
                f"Created reminder: {message[:50]}... at {remind_time}"
            )
            
        except Exception as e:
            log_error(e, "create_reminder", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tạo nhắc nhở!",
                ephemeral=True
            )
    
    @app_commands.command(name="my_reminders", description="Xem danh sách nhắc nhở của bạn")
    async def list_user_reminders(self, interaction: discord.Interaction):
        """List user's active reminders"""
        try:
            await interaction.response.defer()
            
            reminders = await db_manager.get_user_reminders(interaction.user.id)
            
            if not reminders:
                embed = discord.Embed(
                    title="⏰ Nhắc nhở của bạn",
                    description="Bạn không có nhắc nhở nào.",
                    color=0xffa500
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="⏰ Nhắc nhở của bạn",
                color=0x0099ff,
                timestamp=datetime.utcnow()
            )
            
            for reminder in reminders[:10]:  # Limit to 10 reminders
                remind_time = datetime.fromisoformat(reminder['remind_time'])
                
                field_value = f"📝 {reminder['message']}\n"
                field_value += f"📅 {remind_time.strftime('%d/%m/%Y %H:%M')}"
                
                if reminder['is_recurring']:
                    field_value += f"\n🔄 Lặp lại: {reminder['recurring_pattern']}"
                
                embed.add_field(
                    name=f"🔔 Reminder #{reminder['id']}",
                    value=field_value,
                    inline=False
                )
            
            if len(reminders) > 10:
                embed.set_footer(text=f"Hiển thị 10/{len(reminders)} nhắc nhở")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            log_error(e, "list_user_reminders", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi tải danh sách nhắc nhở!",
                ephemeral=True
            )
    
    @app_commands.command(name="cancel_reminder", description="Hủy nhắc nhở")
    async def cancel_reminder(self, interaction: discord.Interaction, reminder_id: int):
        """Cancel a reminder"""
        try:
            await interaction.response.defer()
            
            success = await db_manager.delete_reminder(reminder_id, interaction.user.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Nhắc nhở đã được hủy",
                    description=f"Nhắc nhở #{reminder_id} đã được xóa thành công.",
                    color=0x00ff00
                )
                
                log_user_action(
                    "reminder_cancel",
                    interaction.user.id,
                    interaction.guild.id,
                    f"Cancelled reminder {reminder_id}"
                )
            else:
                embed = discord.Embed(
                    title="❌ Không thể hủy nhắc nhở",
                    description="Không tìm thấy nhắc nhở hoặc bạn không có quyền xóa nhắc nhở này.",
                    color=0xff0000
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            log_error(e, "cancel_reminder", interaction.user.id, interaction.guild.id)
            await interaction.followup.send(
                "❌ Có lỗi xảy ra khi hủy nhắc nhở!",
                ephemeral=True
            )
    
    @commands.command(name="remind_me", help="Tạo nhắc nhở nhanh")
    async def quick_reminder(self, ctx: commands.Context, time: str, *, message: str):
        """Quick reminder creation via prefix command"""
        try:
            # Parse the time
            remind_time = self.parse_time_input(time)
            if not remind_time:
                await ctx.send(
                    "❌ Định dạng thời gian không hợp lệ!\n"
                    "Sử dụng: `5m`, `2h`, `1d`, `HH:MM`, hoặc `YYYY-MM-DD HH:MM`"
                )
                return
            
            # Check if time is in the future
            if remind_time <= datetime.now():
                await ctx.send("❌ Thời gian nhắc nhở phải là thời gian trong tương lai!")
                return
            
            # Create reminder in database
            reminder_id = await db_manager.create_reminder(
                user_id=ctx.author.id,
                guild_id=ctx.guild.id,
                channel_id=ctx.channel.id,
                message=message,
                remind_time=remind_time.isoformat()
            )
            
            embed = discord.Embed(
                title="⏰ Nhắc nhở đã được tạo",
                description=f"**Nội dung:** {message}",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="📅 Thời gian",
                value=remind_time.strftime("%d/%m/%Y %H:%M"),
                inline=True
            )
            
            embed.add_field(
                name="🆔 Reminder ID",
                value=str(reminder_id),
                inline=True
            )
            
            await ctx.send(embed=embed)
            
            log_command("remind_me", ctx.author.id, ctx.guild.id, True)
            
        except Exception as e:
            log_error(e, "quick_reminder", ctx.author.id, ctx.guild.id)
            log_command("remind_me", ctx.author.id, ctx.guild.id, False, str(e))
            await ctx.send("❌ Có lỗi xảy ra khi tạo nhắc nhở!")

async def setup(bot: commands.Bot):
    """Setup function to add the cog"""
    await bot.add_cog(ReminderSystem(bot))
