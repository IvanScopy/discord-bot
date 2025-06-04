import discord
from discord.ext import commands

class InviteButton(discord.ui.View):
    def __init__(self, inv: str):
        super().__init__()
        self.inv= inv
        self.add_item(discord.ui.Button(label="Invite link", url=self.inv))

    @discord.ui.button(label="Invite Button", style=discord.ButtonStyle.blurple)
    async def inviteBtn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.inv, ephemeral=True) # NOQA

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            # Chờ người dùng trả lời trong DM
            response = await interaction.client.wait_for("message", check=check, timeout=60)
            user_input = response.content.strip()

            # Lấy user object từ input
            if user_input.startswith("<@") and user_input.endswith(">"):
                user_id = int(user_input[2:-1])
            else:
                user_id = int(user_input)  # Assume input is an ID
            target_user = await interaction.client.fetch_user(user_id)

            # Gửi tin nhắn mời cho người dùng
            await target_user.send(f"Bạn đã được mời vào kênh! Đây là liên kết: {self.inv}")
            await response.channel.send("Liên kết đã được gửi!", ephemeral=True) # NOQA

        except Exception as e:
            print(f"Error: {e}")
            await interaction.followup.send("Không thể gửi lời mời. Hãy thử lại!", ephemeral=True)