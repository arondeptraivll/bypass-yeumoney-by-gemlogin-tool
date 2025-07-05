import discord
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv

# --- THAY ĐỔI: Chỉ import KEYWORD_MAP, không import cả module nặng ---
from automation import KEYWORD_MAP

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("⚠️ DISCORD_TOKEN không được tìm thấy trong biến môi trường.")

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f'✅ Bot đã đăng nhập với tên {self.user}.')

client = MyClient()
tree = app_commands.CommandTree(client)

keyword_choices = [
    app_commands.Choice(name=data['name'], value=key)
    for key, data in KEYWORD_MAP.items()
]

@tree.command(name="yeumoney", description="Chạy kịch bản lấy mã từ một website được chọn")
@app_commands.describe(keyword="Chọn website bạn muốn chạy kịch bản")
@app_commands.choices(keyword=keyword_choices)
async def yeumoney_command(interaction: discord.Interaction, keyword: app_commands.Choice[str]):
    # Bước 1: Phản hồi ngay lập tức để không bị timeout. Đây là ưu tiên số 1.
    await interaction.response.defer(ephemeral=False)
    
    user = interaction.user
    chosen_keyword_name = keyword.name
    chosen_keyword_value = keyword.value
    
    await interaction.followup.send(
        f"⏳ {user.mention} đã yêu cầu lấy mã cho **{chosen_keyword_name}**. Quá trình này có thể mất 1-2 phút, vui lòng chờ..."
    )

    try:
        # --- THAY ĐỔI: Import module nặng ở đây, SAU KHI đã defer ---
        from automation import run_automation_task
        
        # Chạy tác vụ blocking (Selenium) trong một luồng khác
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, run_automation_task, chosen_keyword_value
        )
        
        if result['status'] == 'success':
            embed = discord.Embed(
                title=f"✅ Lấy mã thành công cho {chosen_keyword_name}!",
                description=f"Mã của bạn là:",
                color=discord.Color.green()
            )
            embed.add_field(name="🔑 MÃ", value=f"```\n{result['data']}\n```", inline=False)
            embed.set_footer(text=f"Yêu cầu bởi {user.display_name}")
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"❌ Lỗi khi lấy mã cho {chosen_keyword_name}",
                description="Đã có lỗi xảy ra trong quá trình tự động hóa.",
                color=discord.Color.red()
            )
            error_message = result['message'][:1000]
            embed.add_field(name="Chi tiết lỗi", value=f"```{error_message}```", inline=False)
            embed.set_footer(text=f"Yêu cầu bởi {user.display_name}")
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        print(f"Lỗi nghiêm trọng trong lệnh /yeumoney: {e}")
        await interaction.followup.send(
            f" Rất tiếc {user.mention}, đã có lỗi hệ thống không mong muốn xảy ra. Vui lòng thử lại sau."
        )

# Chạy bot
client.run(DISCORD_TOKEN)
