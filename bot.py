import discord
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv

# Chỉ import biến cấu hình nhẹ
from automation import KEYWORD_MAP

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("⚠️ DISCORD_TOKEN không được tìm thấy trong biến môi trường.")

# --- TÁC VỤ NỀN ĐỂ XỬ LÝ HÀNG ĐỢI ---
async def automation_worker(queue: asyncio.Queue):
    """
    "Người làm việc" chạy nền vĩnh viễn.
    Nó chờ đợi công việc trong hàng đợi và xử lý chúng.
    """
    # Import module nặng một lần duy nhất khi worker bắt đầu
    from automation import run_automation_task
    print("✅ Worker tự động hóa đã sẵn sàng.")

    while True:
        try:
            # Chờ đợi để lấy một công việc từ hàng đợi
            interaction, keyword_value, keyword_name = await queue.get()
            print(f"Worker đã nhận công việc cho: {keyword_name}")

            # Chạy tác vụ blocking (Selenium) trong một luồng khác
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, run_automation_task, keyword_value
            )
            
            # Gửi kết quả bằng interaction.followup
            if result['status'] == 'success':
                embed = discord.Embed(
                    title=f"✅ Lấy mã thành công cho {keyword_name}!",
                    description=f"Mã của bạn là:",
                    color=discord.Color.green()
                )
                embed.add_field(name="🔑 MÃ", value=f"```\n{result['data']}\n```", inline=False)
                embed.set_footer(text=f"Yêu cầu bởi {interaction.user.display_name}")
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"❌ Lỗi khi lấy mã cho {keyword_name}",
                    description="Đã có lỗi xảy ra trong quá trình tự động hóa.",
                    color=discord.Color.red()
                )
                error_message = result['message'][:1000]
                embed.add_field(name="Chi tiết lỗi", value=f"```{error_message}```", inline=False)
                embed.set_footer(text=f"Yêu cầu bởi {interaction.user.display_name}")
                await interaction.followup.send(embed=embed)

            # Đánh dấu công việc đã hoàn thành
            queue.task_done()
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong worker: {e}")


# --- CẤU HÌNH BOT CHÍNH ---
class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False
        self.task_queue = asyncio.Queue() # Tạo hàng đợi

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        
        # Khởi động worker chạy nền khi bot sẵn sàng
        asyncio.create_task(automation_worker(self.task_queue))
        
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
    # Bước 1: Phản hồi ngay lập tức (luôn thành công)
    await interaction.response.defer(ephemeral=False, thinking=True)
    
    # Bước 2: Thêm công việc vào hàng đợi
    job = (interaction, keyword.value, keyword.name)
    await client.task_queue.put(job)
    
    # Bước 3: Gửi tin nhắn xác nhận ban đầu
    await interaction.followup.send(
        f"⏳ Đã nhận yêu cầu cho **{keyword.name}**! "
        f"Bot đang xử lý trong nền, vui lòng chờ kết quả..."
    )

# Chạy bot
client.run(DISCORD_TOKEN)
