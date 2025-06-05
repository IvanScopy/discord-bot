import discord
from discord.ext import commands
from discord import app_commands
import requests
import datetime
from typing import Optional

from utils.logging_config import get_logger, log_command, log_error, log_user_action
from bot.config import Colors, Emojis, Config

class Weather(commands.Cog):
    """Weather system with current, forecast, and hourly weather"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = get_logger('weather')
        self.weather_api_key = Config.WEATHER_API_KEY
        
    async def cog_load(self):
        """Called when the cog is loaded"""
        self.logger.info("Weather cog loaded successfully")
        if not self.weather_api_key:
            self.logger.warning("Weather API key not found - weather commands will not work")

    def get_weather_data(self, city: str):
        """Get current weather data"""
        if not self.weather_api_key:
            return None
            
        url = f"http://api.weatherapi.com/v1/current.json?key={self.weather_api_key}&q={city}&aqi=no"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching weather data: {e}")
        return None

    def get_forecast_data(self, city: str, days: int = 3):
        """Get forecast weather data"""
        if not self.weather_api_key:
            return None
            
        url = f"http://api.weatherapi.com/v1/forecast.json?key={self.weather_api_key}&q={city}&days={days}&aqi=no&alerts=no"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching forecast data: {e}")
        return None

    @app_commands.command(name="weather", description="Lấy thông tin thời tiết hiện tại của một thành phố")
    async def weather_command(self, interaction: discord.Interaction, city: str):
        """Get current weather for a city"""
        await interaction.response.defer()
        
        if not self.weather_api_key:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Tính năng không khả dụng",
                description="Weather API key chưa được cấu hình.",
                color=Colors.ERROR
            )
            await interaction.followup.send(embed=embed)
            return

        weather_data = self.get_weather_data(city)

        if weather_data:
            current = weather_data["current"]
            location = weather_data["location"]
            condition = current["condition"]
            
            embed = discord.Embed(
                title=f"🌤️ Thời tiết hiện tại tại {location['name']}, {location['country']}",
                description=f"{condition['text']}",
                color=Colors.INFO,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )

            # Add weather fields
            embed.add_field(name="🌡️ Nhiệt độ", value=f"{current['temp_c']}°C / {current['temp_f']}°F", inline=True)
            embed.add_field(name="🤒 Cảm giác như", value=f"{current['feelslike_c']}°C / {current['feelslike_f']}°F", inline=True)
            embed.add_field(name="💧 Độ ẩm", value=f"{current['humidity']}%", inline=True)
            embed.add_field(name="💨 Tốc độ gió", value=f"{current['wind_kph']} km/h", inline=True)
            embed.add_field(name="📊 Áp suất", value=f"{current['pressure_mb']} hPa", inline=True)
            embed.add_field(name="🌧️ Lượng mưa", value=f"{current['precip_mm']} mm", inline=True)
            embed.add_field(name="☀️ Chỉ số UV", value=f"{current['uv']}", inline=True)
            embed.add_field(name="💎 Điểm sương", value=f"{current['dewpoint_c']}°C", inline=True)
            embed.add_field(name="👁️ Tầm nhìn", value=f"{current['vis_km']} km", inline=True)

            # Add weather icon
            icon_url = f"http:{condition['icon']}"
            embed.set_thumbnail(url=icon_url)

            embed.set_footer(text="Dữ liệu từ WeatherAPI • Sử dụng /forecast để xem dự báo")

            await interaction.followup.send(embed=embed)
            log_command("weather", interaction.user.id, interaction.guild.id if interaction.guild else None, f"Weather for {city}")
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Không thể lấy dữ liệu thời tiết",
                description="Vui lòng kiểm tra tên thành phố và thử lại sau!",
                color=Colors.ERROR
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="forecast", description="Dự báo thời tiết 3 ngày tới")
    async def forecast_command(self, interaction: discord.Interaction, city: str):
        """Get 3-day weather forecast"""
        await interaction.response.defer()

        if not self.weather_api_key:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Tính năng không khả dụng",
                description="Weather API key chưa được cấu hình.",
                color=Colors.ERROR
            )
            await interaction.followup.send(embed=embed)
            return

        forecast_data = self.get_forecast_data(city, 3)

        if forecast_data:
            location = forecast_data["location"]
            forecast_days = forecast_data["forecast"]["forecastday"]

            embed = discord.Embed(
                title=f"📅 Dự báo thời tiết 3 ngày - {location['name']}, {location['country']}",
                color=Colors.INFO,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )

            for day in forecast_days:
                date = day["date"]
                day_data = day["day"]
                condition = day_data["condition"]

                # Format date
                date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m (%A)")

                field_value = f"🌡️ **{day_data['mintemp_c']}°C - {day_data['maxtemp_c']}°C**\n"
                field_value += f"🌤️ {condition['text']}\n"
                field_value += f"🌧️ Khả năng mưa: {day_data['daily_chance_of_rain']}%\n"
                field_value += f"💨 Gió: {day_data['maxwind_kph']} km/h\n"
                field_value += f"💧 Độ ẩm: {day_data['avghumidity']}%"

                embed.add_field(
                    name=f"📆 {formatted_date}",
                    value=field_value,
                    inline=False
                )

            embed.set_footer(text="Dữ liệu từ WeatherAPI • Sử dụng /hourly để xem dự báo theo giờ")
            await interaction.followup.send(embed=embed)
            log_command("forecast", interaction.user.id, interaction.guild.id if interaction.guild else None, f"Forecast for {city}")
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Không thể lấy dữ liệu dự báo",
                description="Vui lòng kiểm tra tên thành phố và thử lại sau!",
                color=Colors.ERROR
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="hourly", description="Dự báo thời tiết theo giờ trong ngày")
    async def hourly_command(self, interaction: discord.Interaction, city: str):
        """Get hourly weather forecast for today"""
        await interaction.response.defer()

        if not self.weather_api_key:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Tính năng không khả dụng",
                description="Weather API key chưa được cấu hình.",
                color=Colors.ERROR
            )
            await interaction.followup.send(embed=embed)
            return

        forecast_data = self.get_forecast_data(city, 1)

        if forecast_data:
            location = forecast_data["location"]
            today = forecast_data["forecast"]["forecastday"][0]
            hourly_data = today["hour"]

            embed = discord.Embed(
                title=f"⏰ Dự báo theo giờ hôm nay - {location['name']}",
                color=Colors.WARNING,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )

            # Lấy giờ hiện tại
            current_hour = datetime.datetime.now().hour

            # Hiển thị 8 giờ tiếp theo
            hours_to_show = []
            for i in range(8):
                hour_index = (current_hour + i) % 24
                hours_to_show.append(hourly_data[hour_index])

            field_value = ""
            for hour in hours_to_show:
                time = hour["time"].split(" ")[1]  # Lấy phần giờ
                temp = hour["temp_c"]
                condition = hour["condition"]["text"]
                rain_chance = hour["chance_of_rain"]

                field_value += f"🕐 **{time}** - {temp}°C - {condition}\n"
                field_value += f"   🌧️ Mưa: {rain_chance}% | 💨 Gió: {hour['wind_kph']} km/h\n\n"

            embed.add_field(
                name="📊 Dự báo 8 giờ tiếp theo",
                value=field_value,
                inline=False
            )

            embed.set_footer(text="Dữ liệu từ WeatherAPI")
            await interaction.followup.send(embed=embed)
            log_command("hourly", interaction.user.id, interaction.guild.id if interaction.guild else None, f"Hourly for {city}")
        else:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Không thể lấy dữ liệu dự báo theo giờ",
                description="Vui lòng kiểm tra tên thành phố và thử lại sau!",
                color=Colors.ERROR
            )
            await interaction.followup.send(embed=embed)

    # Prefix commands for compatibility
    @commands.command(name="weather", help="Xem thời tiết hiện tại")
    async def weather_prefix(self, ctx: commands.Context, *, city: str):
        """Prefix version of weather command"""
        if not self.weather_api_key:
            await ctx.send(f"{Emojis.ERROR} Weather API key chưa được cấu hình.")
            return

        weather_data = self.get_weather_data(city)
        if weather_data:
            current = weather_data["current"]
            location = weather_data["location"]
            condition = current["condition"]
            
            embed = discord.Embed(
                title=f"🌤️ Thời tiết tại {location['name']}",
                description=f"{condition['text']} - {current['temp_c']}°C",
                color=Colors.INFO
            )
            embed.add_field(name="💧 Độ ẩm", value=f"{current['humidity']}%", inline=True)
            embed.add_field(name="💨 Gió", value=f"{current['wind_kph']} km/h", inline=True)
            
            icon_url = f"http:{condition['icon']}"
            embed.set_thumbnail(url=icon_url)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{Emojis.ERROR} Không thể lấy dữ liệu thời tiết cho {city}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))
