
import discord
from discord.ext import commands
from discord import app_commands
from playwright.async_api import async_playwright

class PinterestSearch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def scrape_pinterest(self, query: str):
        # Sử dụng Playwright Async API
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Chạy trình duyệt ở chế độ không hiển thị
            page = await browser.new_page()
            search_url = f"https://www.pinterest.com/search/pins/?q={query.replace(' ', '+')}"
            await page.goto(search_url)

            # Chờ nội dung tải xong
            await page.wait_for_timeout(5000)  # 5 giây

            # Tìm URL ảnh đầu tiên
            images = await page.query_selector_all("img")
            image_urls = [
                await img.get_attribute("src")
                for img in images
                if await img.get_attribute("src") and "pinimg" in (await img.get_attribute("src"))
            ]
            await browser.close()
            return image_urls[0] if image_urls else None

    @app_commands.command(name="pinterest", description="Tìm kiếm nội dung trên Pinterest và hiển thị ảnh")
    async def pinterest(self, interaction: discord.Interaction, query: str):
        # Scrape ảnh từ Pinterest bằng Playwright Async API
        image_url = await self.scrape_pinterest(query)
        if image_url:
            embed = discord.Embed(
                title=f"Kết quả tìm kiếm Pinterest cho: {query}",
                description="Đây là kết quả tìm kiếm:",
                color=discord.Color.green(),
            )
            embed.set_image(url=image_url)
            embed.set_footer(text="Powered by Playwright Async API")

            await interaction.response.send_message(embed=embed) # NOQA
        else:
            await interaction.response.send_message("Không tìm thấy kết quả nào trên Pinterest.", ephemeral=True ) # NOQA
