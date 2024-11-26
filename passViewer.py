import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
from tkinter import ttk

# Función para abrir el archivo SQLite
def open_sqlite_file():
    file_path = filedialog.askopenfilename(filetypes=[("SQLite Files", "*.sqlite"), ("All Files", "*.*")])
    if not file_path:
        return

    # Conectar a la base de datos SQLite
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo SQLite: {e}")
        return

    # Listar todas las tablas en la base de datos
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        messagebox.showerror("Error", "No se encontraron tablas en la base de datos.")
        conn.close()
        return

    # Mostrar las tablas en una ventana
    show_tables_window(tables, conn, cursor)

# Función para mostrar las tablas disponibles
def show_tables_window(tables, conn, cursor):
    window = tk.Toplevel()
    window.title("Tablas de la Base de Datos SQLite")

    # Lista de tablas
    listbox = tk.Listbox(window, selectmode="single", height=10)
    for table in tables:
        listbox.insert(tk.END, table[0])

    listbox.pack(expand=True, fill="both")

    # Botón para mostrar los datos de la tabla seleccionada
    def show_table_data():
        selected_table = listbox.get(tk.ACTIVE)
        if selected_table:
            cursor.execute(f"SELECT * FROM {selected_table}")
            rows = cursor.fetchall()
            show_data_window(selected_table, rows)

    show_button = tk.Button(window, text="Mostrar Datos", command=show_table_data)
    show_button.pack()

    # Botón para cerrar la ventana de tablas
    close_button = tk.Button(window, text="Cerrar", command=window.destroy)
    close_button.pack()

# Función para mostrar los datos de una tabla seleccionada
def show_data_window(table_name, rows):
    window = tk.Toplevel()
    window.title(f"Datos de la tabla: {table_name}")

    # Si no hay datos, mostrar un mensaje
    if not rows:
        messagebox.showinfo("No hay datos", "No se encontraron datos en esta tabla.")
        return

    # Crear la tabla para mostrar los datos
    tree = ttk.Treeview(window, columns=[str(i) for i in range(len(rows[0]))], show="headings")
    
    # Definir los encabezados de columna según los datos
    for i in range(len(rows[0])):
        tree.heading(i, text=f"Columna {i+1}")

    # Agregar las filas de datos
    for row in rows:
        tree.insert("", "end", values=row)

    tree.pack(expand=True, fill="both")

    # Botón para cerrar la ventana de datos
    close_button = tk.Button(window, text="Cerrar", command=window.destroy)
    close_button.pack()

# Crear la ventana principal
root = tk.Tk()
root.title("Visor de Base de Datos SQLite")

# Botón para cargar el archivo SQLite
open_button = tk.Button(root, text="Abrir Archivo SQLite", command=open_sqlite_file)
open_button.pack(pady=20)

# Ejecutar la interfaz gráfica
root.mainloop()
