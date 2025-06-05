import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import requests
from typing import Optional

from utils.logging_config import get_logger, log_command, log_error, log_user_action
from utils.btn import InviteButton
from bot.config import Colors, Emojis, Config

# Try to import openai, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class Utilities(commands.Cog):
    """Utility commands: ChatGPT, images, polls, dice, etc."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger('utilities')
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE and Config.OPENAI_API_KEY:
            try:
                self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            except Exception as e:
                self.logger.error(f"OpenAI initialization failed: {e}")
                OPENAI_AVAILABLE = False
                self.openai_client = None
        else:
            self.openai_client = None
            
        self.pexels_api_key = Config.PEXELS_API_KEY
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        self.logger.info("Utilities cog loaded successfully")
        if not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI not available - ChatGPT features disabled")
        if not self.pexels_api_key:
            self.logger.warning("Pexels API key not found - image features limited")

    def get_chatgpt_response(self, prompt: str) -> str:
        """Get response from ChatGPT"""
        if not OPENAI_AVAILABLE or not self.openai_client:
            return "❌ Tính năng ChatGPT không khả dụng. Vui lòng cài đặt thư viện OpenAI và cấu hình API key."

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            if "insufficient_quota" in str(e):
                return "Bạn đã vượt quá giới hạn sử dụng API. Vui lòng kiểm tra gói dịch vụ và thông tin thanh toán của bạn."
            return f"Lỗi API: {e}"

    def get_random_image(self):
        """Get random image from Pexels"""
        if not self.pexels_api_key:
            return None
            
        url = "https://api.pexels.com/v1/curated?per_page=1"
        headers = {"Authorization": self.pexels_api_key}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "photos" in data and len(data["photos"]) > 0:
                    return data["photos"][0]["src"]["medium"]
        except Exception as e:
            self.logger.error(f"Error fetching random image: {e}")
        return None

    def get_images_by_topic(self, query: str):
        """Get images by topic from Pexels"""
        if not self.pexels_api_key:
            return None
            
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=4"
        headers = {"Authorization": self.pexels_api_key}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "photos" in data and len(data["photos"]) > 0:
                    return [photo["src"]["original"] for photo in data["photos"]]
        except Exception as e:
            self.logger.error(f"Error fetching images by topic: {e}")
        return None

    def get_birthday_image(self):
        """Get birthday image from Pexels"""
        if not self.pexels_api_key:
            return None
            
        url = f"https://api.pexels.com/v1/search?query=birthday&per_page=1"
        headers = {"Authorization": self.pexels_api_key}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "photos" in data and len(data["photos"]) > 0:
                    return data["photos"][0]["src"]["original"]
        except Exception as e:
            self.logger.error(f"Error fetching birthday image: {e}")
        return None

    # ChatGPT Commands
    @app_commands.command(name="chatgpt", description="Gửi prompt đến ChatGPT và nhận phản hồi")
    async def chatgpt_command(self, interaction: discord.Interaction, prompt: str):
        """ChatGPT slash command"""
        await interaction.response.defer()
        response = self.get_chatgpt_response(prompt)
        await interaction.followup.send(f"**ChatGPT trả lời:**\n{response}")
        log_command("chatgpt", interaction.user.id, interaction.guild.id if interaction.guild else None, f"Prompt: {prompt[:50]}...")

    @app_commands.command(name="ask", description="Hỏi ChatGPT một câu hỏi")
    async def ask_command(self, interaction: discord.Interaction, question: str):
        """Ask ChatGPT a question"""
        await interaction.response.defer()
        response = self.get_chatgpt_response(question)
        await interaction.followup.send(f"**ChatGPT trả lời:**\n{response}")
        log_command("ask", interaction.user.id, interaction.guild.id if interaction.guild else None, f"Question: {question[:50]}...")

    # Utility Commands
    @commands.command(name="roll", help="Lăn xúc xắc")
    async def roll_dice_command(self, ctx: commands.Context):
        """Roll a dice"""
        result = random.randint(1, 6)
        embed = discord.Embed(
            title="🎲 Kết quả xúc xắc",
            description=f"Bạn đã lăn được số: **{result}**",
            color=Colors.SUCCESS
        )
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
        log_command("roll", ctx.author.id, ctx.guild.id if ctx.guild else None, f"Rolled: {result}")

    @commands.command(name="invite", help="Tạo link mời server")
    async def invite_command(self, ctx: commands.Context):
        """Create server invite"""
        try:
            inv = await ctx.channel.create_invite()
            embed = discord.Embed(
                title="🔗 Link mời",
                description="Click nút bên dưới để mời người khác vào server!",
                color=Colors.SUCCESS
            )
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed, view=InviteButton(str(inv)))
            log_command("invite", ctx.author.id, ctx.guild.id if ctx.guild else None, "Created invite")
        except Exception as e:
            await ctx.send(f"{Emojis.ERROR} Không thể tạo link mời: {str(e)}")

    @commands.command(name="poll", help="Tạo cuộc khảo sát")
    async def poll_command(self, ctx: commands.Context, question: str, *options):
        """Create a poll"""
        if len(options) < 2:
            await ctx.send(f"{Emojis.ERROR} Cần ít nhất 2 lựa chọn cho cuộc khảo sát!")
            return
        
        if len(options) > 10:
            await ctx.send(f"{Emojis.ERROR} Tối đa 10 lựa chọn cho cuộc khảo sát!")
            return

        poll_embed = discord.Embed(
            title="📊 Cuộc khảo sát",
            description=question,
            color=Colors.INFO
        )
        
        for i, option in enumerate(options):
            poll_embed.add_field(name=f"{chr(127462 + i)} {option}", value="\u200b", inline=False)
        
        poll_embed.set_footer(text=f"Tạo bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        message = await ctx.send(embed=poll_embed)
        
        for i in range(len(options)):
            await message.add_reaction(f"{chr(127462 + i)}")
        
        log_command("poll", ctx.author.id, ctx.guild.id if ctx.guild else None, f"Poll: {question}")

    @commands.command(name="random_image", help="Gửi ảnh ngẫu nhiên từ Pexels")
    async def random_image_command(self, ctx: commands.Context):
        """Get random image"""
        image_url = self.get_random_image()
        if image_url:
            embed = discord.Embed(
                title="📷 Ảnh ngẫu nhiên từ Pexels",
                description="Một bức ảnh đẹp cho bạn!",
                color=Colors.SUCCESS
            )
            embed.set_image(url=image_url)
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Lỗi",
                description="Không thể lấy ảnh, vui lòng thử lại sau!",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed)

    @commands.command(name="search_image", help="Tìm kiếm ảnh trên Pexels theo chủ đề")
    async def search_image_command(self, ctx: commands.Context, *, topic: str):
        """Search images by topic"""
        images = self.get_images_by_topic(topic)
        if images:
            for i, image_url in enumerate(images, 1):
                embed = discord.Embed(
                    title=f"🔍 Kết quả {i}/4 cho '{topic}'",
                    color=Colors.SUCCESS
                )
                embed.set_image(url=image_url)
                embed.set_footer(
                    text=f"Ảnh {i}/4 - Yêu cầu bởi {ctx.author.name}",
                    icon_url=ctx.author.avatar.url if ctx.author.avatar else None
                )
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Không tìm thấy ảnh",
                description=f"Không tìm thấy ảnh nào cho chủ đề '{topic}', vui lòng thử chủ đề khác.",
                color=Colors.ERROR
            )
            await ctx.send(embed=embed)

    @commands.command(name="birthday", help="Chúc mừng sinh nhật với ảnh chủ đề birthday 🎂")
    async def birthday_command(self, ctx: commands.Context, *, name: str):
        """Birthday wishes with image"""
        image_url = self.get_birthday_image()
        embed = discord.Embed(
            title="🎉 Chúc mừng sinh nhật!",
            description=f"Chúc mừng sinh nhật {name}! Chúc cậu một ngày tốt lành! 🥳",
            color=0xff69b4
        )
        if image_url:
            embed.set_image(url=image_url)
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
        log_command("birthday", ctx.author.id, ctx.guild.id if ctx.guild else None, f"Birthday for {name}")

    @commands.command(name="create_channel", help="Tạo kênh mới")
    @commands.has_permissions(administrator=True)
    async def create_channel_command(self, ctx: commands.Context, channel_name: str):
        """Create a new channel"""
        try:
            guild = ctx.guild
            await guild.create_text_channel(channel_name)
            embed = discord.Embed(
                title=f"{Emojis.SUCCESS} Kênh mới đã được tạo",
                description=f"Kênh {channel_name} đã được tạo thành công!",
                color=Colors.SUCCESS
            )
            embed.set_footer(text=f"Tạo bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
            log_command("create_channel", ctx.author.id, ctx.guild.id if ctx.guild else None, f"Created channel: {channel_name}")
        except Exception as e:
            await ctx.send(f"{Emojis.ERROR} Không thể tạo kênh: {str(e)}")

    # Simple reminder (basic version)
    @commands.command(name="remind_simple", help="Nhắc nhở đơn giản (phút)")
    async def remind_simple_command(self, ctx: commands.Context, time: int, *, task: str):
        """Simple reminder command"""
        if time > 1440:  # Max 24 hours
            await ctx.send(f"{Emojis.ERROR} Thời gian tối đa là 1440 phút (24 giờ)!")
            return
            
        embed = discord.Embed(
            title="⏰ Đã đặt nhắc nhở",
            description=f"Tôi sẽ nhắc nhở bạn về '{task}' sau {time} phút.",
            color=Colors.SUCCESS
        )
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
        
        await asyncio.sleep(time * 60)
        
        reminder_embed = discord.Embed(
            title="🔔 Nhắc nhở!",
            description=f"Đây là nhắc nhở của bạn: **{task}**",
            color=Colors.WARNING
        )
        await ctx.send(f"{ctx.author.mention}", embed=reminder_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utilities(bot))
