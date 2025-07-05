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
    from automation import run_automation_task
    print("✅ Worker tự động hóa đã sẵn sàng.")

    while True:
        try:
            interaction, keyword_value, keyword_name = await queue.get()
            print(f"Worker đã nhận công việc cho: {keyword_name}")

            # Sửa tin nhắn gốc để thông báo cho người dùng
            await interaction.edit_original_response(
                content=f"⏳ Đang chạy kịch bản cho **{keyword_name}**... Vui lòng chờ."
            )

            # Chạy tác vụ blocking (Selenium)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, run_automation_task, keyword_value
            )
            
            # Gửi kết quả bằng một tin nhắn followup mới
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

            # Xóa tin nhắn "Đang chạy..." ban đầu để đỡ rối chat
            await interaction.edit_original_response(content="Hoàn thành!", view=None)

            queue.task_done()
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong worker: {e}")
            try:
                # Cố gắng thông báo lỗi cho người dùng
                await interaction.followup.send(f"Rất tiếc {interaction.user.mention}, đã có lỗi hệ thống không mong muốn.")
            except:
                pass # Bỏ qua nếu không gửi được tin nhắn

# --- CẤU HÌNH BOT CHÍNH ---
class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False
        self.task_queue = asyncio.Queue()

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        
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
    # Bước 1: Xác nhận tương tác. Bot sẽ hiển thị "Bot is thinking..."
    await interaction.response.defer(ephemeral=False)
    
    # Bước 2: Đưa công việc vào hàng đợi.
    job = (interaction, keyword.value, keyword.name)
    await client.task_queue.put(job)
    
    # Hàm kết thúc ở đây. Worker sẽ xử lý phần còn lại.

client.run(DISCORD_TOKEN)
