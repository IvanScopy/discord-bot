"""
Discord Bot Main Entry Point
Enhanced Discord Bot với đầy đủ tính năng
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import discord
from discord.ext import commands

from bot.config import Config, get_bot_intents, COGS, Colors, Emojis
from utils.database import db_manager
from utils.logging_config import setup_logging, get_logger

class DiscordBot(commands.Bot):
    """Enhanced Discord Bot class"""
    
    def __init__(self):
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=get_bot_intents(),
            application_id=Config.DISCORD_APPLICATION_ID,
            help_command=None  # We'll create custom help
        )
        
        self.logger = get_logger('main')
        self.config = Config
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        self.logger.info("Setting up bot...")
        
        # Initialize database
        await db_manager.init_database()
        self.logger.info("Database initialized")
        
        # Load all cogs
        for cog in COGS:
            try:
                await self.load_extension(cog)
                self.logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                self.logger.error(f"Failed to load cog {cog}: {e}")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        self.logger.info(f"{self.user} đã sẵn sàng hoạt động!")
        self.logger.info(f"Bot ID: {self.user.id}")
        self.logger.info(f"Servers: {len(self.guilds)}")
        self.logger.info(f"Users: {len(set(self.get_all_members()))}")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{Config.COMMAND_PREFIX}help | {Config.BOT_VERSION}"
        )
        await self.change_presence(activity=activity)
        
        # Print optional features status
        features = Config.get_optional_features()
        self.logger.info("Optional features:")
        for feature, enabled in features.items():
            status = "✅" if enabled else "❌"
            self.logger.info(f"  {feature}: {status}")
    
    async def on_guild_join(self, guild):
        """Called when bot joins a guild"""
        self.logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Send welcome message to general channel
        for channel in guild.text_channels:
            if channel.name.lower() in ['general', 'welcome', 'bot']:
                try:
                    embed = discord.Embed(
                        title=f"{Emojis.SUCCESS} Cảm ơn bạn đã thêm {Config.BOT_NAME}!",
                        description=f"Sử dụng `{Config.COMMAND_PREFIX}help` để xem danh sách lệnh.",
                        color=Colors.SUCCESS
                    )
                    embed.add_field(
                        name="🚀 Tính năng chính",
                        value="• Nghe nhạc từ YouTube\n• Quản lý sự kiện\n• Hệ thống nhắc nhở\n• Chia sẻ media\n• Thông tin người dùng",
                        inline=False
                    )
                    await channel.send(embed=embed)
                    break
                except:
                    continue
    
    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors

        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Thiếu tham số",
                description=f"Sử dụng: `{Config.COMMAND_PREFIX}help {ctx.command.name}` để xem hướng dẫn.",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Không đủ quyền",
                description="Bạn không có quyền sử dụng lệnh này.",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed)
            return

        # Log unexpected errors
        self.logger.error(f"Unexpected error in {ctx.command}: {error}", exc_info=True)

        embed = discord.Embed(
            title=f"{Emojis.ERROR} Có lỗi xảy ra",
            description="Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.",
            color=Colors.ERROR
        )
        await ctx.send(embed=embed)

    # Basic Commands
    @commands.command(name="hello", help="Trả lời câu chào")
    async def hello_command(self, ctx: commands.Context):
        embed = discord.Embed(
            title="👋 Xin chào!",
            description=f"Chào {ctx.author.mention}!",
            color=Colors.SUCCESS
        )
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name="ping", help="Kiểm tra độ trễ bot")
    async def ping_command(self, ctx: commands.Context):
        latency = round(self.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Độ trễ: {latency}ms",
            color=Colors.SUCCESS
        )
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name="help", help="Hiển thị danh sách lệnh")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="📚 Danh sách lệnh",
            description="Dưới đây là danh sách các lệnh có sẵn:",
            color=Colors.INFO
        )

        # Thêm các lệnh prefix
        prefix_commands = "**Các lệnh prefix:**\n"
        for command in self.commands:
            prefix_commands += f"`{Config.COMMAND_PREFIX}{command.name}` - {command.help}\n"
        embed.add_field(name="Prefix Commands", value=prefix_commands[:1024], inline=False)

        # Thêm các lệnh slash
        slash_commands = "**Các lệnh Slash:**\n"
        for command in self.tree.get_commands():
            slash_commands += f"`/{command.name}` - {command.description}\n"
        if slash_commands != "**Các lệnh Slash:**\n":
            embed.add_field(name="Slash Commands", value=slash_commands[:1024], inline=False)

        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

async def main():
    """Main function"""
    # Setup logging
    setup_logging()
    logger = get_logger('main')
    
    logger.info(f"Starting {Config.BOT_NAME} v{Config.BOT_VERSION}")
    
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed")
        return
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("Bot shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Failed to start bot: {e}")
        sys.exit(1)
