import os
import sqlite3
import base64
import json
import shutil
import win32crypt
from Cryptodome.Cipher import AES
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# Función para obtener la clave secreta de Local State
def get_secret_key(local_state_path):
    try:
        with open(local_state_path, "r", encoding='utf-8') as f:
            local_state = f.read()
            local_state = json.loads(local_state)
        secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        secret_key = secret_key[5:]  # Remove suffix DPAPI
        secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
        return secret_key
    except Exception as e:
        print("[ERR] No se pudo obtener la clave secreta:", str(e))
        return None

# Función para generar el cifrador AES
def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

# Función para desencriptar la contraseña
def decrypt_password(ciphertext, secret_key):
    try:
        # Inicialización del vector (IV) para la desencriptación AES
        iv = ciphertext[3:15]
        encrypted_password = ciphertext[15:-16]  # Contraseña cifrada
        cipher = generate_cipher(secret_key, iv)
        decrypted_pass = cipher.decrypt(encrypted_password).decode()  # Desencriptar y convertir a texto
        return decrypted_pass
    except Exception as e:
        print("[ERR] No se pudo desencriptar la contraseña:", str(e))
        return ""

# Función para abrir el archivo SQLite
def open_sqlite_file(local_state_path):
    file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])  # Permite cualquier tipo de archivo
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

    show_tables_window(tables, conn, cursor, local_state_path)

# Función para mostrar las tablas
def show_tables_window(tables, conn, cursor, local_state_path):
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

            secret_key = get_secret_key(local_state_path)
            if not secret_key:
                messagebox.showerror("Error", "No se pudo obtener la clave maestra para descifrar las contraseñas.")
                return

            show_data_window(selected_table, rows, secret_key)

    show_button = tk.Button(window, text="Mostrar Datos", command=show_table_data)
    show_button.pack()

    close_button = tk.Button(window, text="Cerrar", command=window.destroy)
    close_button.pack()

# Función para mostrar los datos de la tabla seleccionada
def show_data_window(table_name, rows, secret_key):
    window = tk.Toplevel()
    window.title(f"Datos de la tabla: {table_name}")

    if not rows:
        messagebox.showinfo("No hay datos", "No se encontraron datos en esta tabla.")
        return

    tree = ttk.Treeview(window, columns=[str(i) for i in range(len(rows[0]))], show="headings")
    
    for i in range(len(rows[0])):
        tree.heading(i, text=f"Columna {i+1}")

    for row in rows:
        if "password" in str(row[1]).lower():  # Verificar si es una columna de contraseña
            decrypted_password = decrypt_password(row[1], secret_key)
            row = row[:2] + (decrypted_password,) + row[3:]
        tree.insert("", "end", values=row)

    tree.pack(expand=True, fill="both")
    
    close_button = tk.Button(window, text="Cerrar", command=window.destroy)
    close_button.pack()

# Crear la ventana principal de Tkinter
def main():
    root = tk.Tk()
    root.title("Visor de Base de Datos SQLite con Desencriptación de Contraseñas")

    # Solicitar al usuario el archivo Local State
    local_state_path = filedialog.askopenfilename(title="Selecciona el archivo Local State", filetypes=[("All Files", "*.*")])
    if not local_state_path:
        messagebox.showerror("Error", "No se seleccionó el archivo Local State.")
        return

    open_button = tk.Button(root, text="Abrir Archivo SQLite", command=lambda: open_sqlite_file(local_state_path))
    open_button.pack(pady=20)

    root.mainloop()

if __name__ == '__main__':
    main()
