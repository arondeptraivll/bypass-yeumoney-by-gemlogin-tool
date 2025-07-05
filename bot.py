import discord
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv
from aiohttp import web
from automation import KEYWORD_MAP, run_automation_task

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("⚠️ DISCORD_TOKEN không được tìm thấy trong biến môi trường.")

# --- TÁC VỤ NỀN ĐỂ XỬ LÝ HÀNG ĐỢI ---
async def automation_worker(queue: asyncio.Queue):
    print("✅ Worker tự động hóa đã sẵn sàng.")
    while True:
        try:
            interaction, keyword_value, keyword_name = await queue.get()
            print(f"Worker đã nhận công việc cho: {keyword_name}")
            await interaction.edit_original_response(
                content=f"⏳ Đang chạy kịch bản cho **{keyword_name}**... Vui lòng chờ."
            )
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, run_automation_task, keyword_value)
            if result['status'] == 'success':
                embed = discord.Embed(title=f"✅ Lấy mã thành công cho {keyword_name}!", description="Mã của bạn là:", color=discord.Color.green())
                embed.add_field(name="🔑 MÃ", value=f"```\n{result['data']}\n```", inline=False)
                embed.set_footer(text=f"Yêu cầu bởi {interaction.user.display_name}")
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(title=f"❌ Lỗi khi lấy mã cho {keyword_name}", description="Đã có lỗi xảy ra trong quá trình tự động hóa.", color=discord.Color.red())
                error_message = result['message'][:1000]
                embed.add_field(name="Chi tiết lỗi", value=f"```{error_message}```", inline=False)
                embed.set_footer(text=f"Yêu cầu bởi {interaction.user.display_name}")
                await interaction.followup.send(embed=embed)
            await interaction.edit_original_response(content=f"Đã xử lý xong yêu cầu cho **{keyword_name}**.", view=None)
            queue.task_done()
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong worker: {e}")
            try:
                await interaction.followup.send(f"Rất tiếc {interaction.user.mention}, đã có lỗi hệ thống không mong muốn.")
            except:
                pass

# --- CẤU HÌNH BOT CHÍNH VÀ WEB SERVER ---
class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.synced = False
        self.task_queue = asyncio.Queue()
        self.web_app = web.Application()
        self.web_app.add_routes([web.get('/health', self.health_check)])

    async def health_check(self, request):
        print("Pinged! Bot is alive.")
        return web.Response(text="OK", status=200)

    async def setup_hook(self):
        if not self.synced:
            await tree.sync()
            self.synced = True
        asyncio.create_task(automation_worker(self.task_queue))
        print(f'✅ Bot đã đăng nhập với tên {self.user}.')

client = MyClient()
tree = app_commands.CommandTree(client)

@tree.command(name="yeumoney", description="Chạy kịch bản lấy mã từ một website được chọn")
@app_commands.describe(keyword="Chọn website bạn muốn chạy kịch bản")
@app_commands.choices(keyword=[app_commands.Choice(name=data['name'], value=key) for key, data in KEYWORD_MAP.items()])
async def yeumoney_command(interaction: discord.Interaction, keyword: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=False)
    job = (interaction, keyword.value, keyword.name)
    await client.task_queue.put(job)
    await interaction.edit_original_response(content=f"Đã nhận yêu cầu cho **{keyword.name}** và đưa vào hàng đợi xử lý!")

async def main():
    # Railway tự động cung cấp biến PORT
    port = int(os.environ.get('PORT', 10000))
    runner = web.AppRunner(client.web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    await asyncio.gather(
        client.start(DISCORD_TOKEN),
        site.start()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot đang tắt...")
