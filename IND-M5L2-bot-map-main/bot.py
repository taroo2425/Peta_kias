from config import *
from logic import *
import discord
from discord.ext import commands
from config import TOKEN

# Menginisiasi pengelola database
manager = DB_Map("database.db")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("Bot started")

@bot.command()
async def start(ctx: commands.Context):
    await ctx.send(f"Halo, {ctx.author.name}. Masukkan !help_me untuk mengeksplorasi daftar perintah yang tersedia")

@bot.command(name="help_me")
async def help_me(ctx: commands.Context):
    help_text = (
        "**Daftar Perintah Bot Peta Kota**\n\n"
        "`!start` - Menyapa dan menampilkan instruksi awal.\n"
        "`!help_me` - Menampilkan daftar perintah yang tersedia.\n"
        "`!show_city <nama_kota>` - Menampilkan peta dengan kota yang ditentukan.\n"
        "`!remember_city <nama_kota>` - Menyimpan kota ke daftar kota favorit Anda.\n"
        "`!show_my_cities` - Menampilkan peta berisi semua kota yang sudah Anda simpan.\n\n"
        "_Contoh:_\n"
        "`!show_city London`\n"
        "`!remember_city Jakarta`\n"
        "`!show_my_cities`"
    )
    await ctx.send(help_text)

@bot.command()
async def show_city(ctx: commands.Context, *, city_name: str = ""):
    if not city_name.strip():
        await ctx.send("Silakan tulis nama kota setelah perintah, misalnya: `!show_city London`")
        return

    coordinates = manager.get_coordinates(city_name)
    if not coordinates:
        await ctx.send(
            f"Kota **{city_name}** tidak ditemukan di database. "
            "Pastikan penulisan dalam bahasa Inggris dan sudah ada di tabel `cities`."
        )
        return

    image_path = f"map_{ctx.author.id}.png"
    success = manager.create_graph(image_path, [city_name])

    if not success:
        await ctx.send("Terjadi masalah saat menggambar peta. Coba lagi nanti.")
        return

    file = discord.File(image_path, filename="city_map.png")
    await ctx.send(
        content=f"Berikut peta untuk kota **{city_name}**:",
        file=file
    )

@bot.command()
async def show_my_cities(ctx: commands.Context):
    cities = manager.select_cities(ctx.author.id)  # Mengambil daftar kota yang diingat oleh pengguna

    if not cities:
        await ctx.send(
            "Anda belum menyimpan kota apa pun.\n"
            "Gunakan perintah `!remember_city <nama_kota>` untuk menyimpan kota terlebih dahulu."
        )
        return

    image_path = f"map_user_{ctx.author.id}.png"
    success = manager.create_graph(image_path, cities)

    if not success:
        await ctx.send("Tidak ada koordinat kota yang valid untuk digambar. Coba simpan kota lain.")
        return

    file = discord.File(image_path, filename="my_cities_map.png")
    city_list = ", ".join(cities)
    await ctx.send(
        content=f"Berikut peta kota-kota yang Anda simpan: **{city_list}**",
        file=file
    )

@bot.command()
async def remember_city(ctx: commands.Context, *, city_name=""):
    if manager.add_city(ctx.author.id, city_name):  # Memeriksa apakah kota ada dalam database; jika ya, menambahkannya ke memori pengguna
        await ctx.send(f'Kota {city_name} telah berhasil disimpan!')
    else:
        await ctx.send("Format tidak benar. Silakan masukkan nama kota dalam bahasa Inggris, dengan spasi setelah perintah.")

if __name__ == "__main__":
    bot.run(TOKEN)