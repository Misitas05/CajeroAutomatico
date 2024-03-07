import tkinter as tk
from tkinter import messagebox
import pyodbc
import tkinter.simpledialog as simpledialog

class CajeroAutomatico:
    def __init__(self, root):
        self.root = root
        self.root.title("Cajero Automático")
        
        self.username_label = tk.Label(root, text="Nombre de Usuario:")
        self.username_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.username_entry = tk.Entry(root)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        self.password_label = tk.Label(root, text="Contraseña:")
        self.password_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        self.login_button = tk.Button(root, text="Iniciar Sesión", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        self.create_account_button = tk.Button(root, text="Crear Cuenta", command=self.create_account)
        self.create_account_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        self.db_connection = pyodbc.connect('DRIVER={SQL Server};SERVER=308PC21;DATABASE=CAJERO;UID=usuario1;PWD=1234')
        self.cursor = self.db_connection.cursor()
        self.create_tables()
        self.update_account_numbers()
        self.update_table()

    def update_account_numbers(self):
        self.cursor.execute("SELECT id FROM usuarios WHERE accountNumber IS NULL")
        null_accounts = self.cursor.fetchall()
        for user_id in null_accounts:
            self.cursor.execute("UPDATE usuarios SET accountNumber = ? WHERE id = ?", (user_id[0], user_id[0]))
        self.db_connection.commit()

    def create_tables(self):
        # Crear tabla de usuarios si no existe
        self.cursor.execute("IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'usuarios') CREATE TABLE usuarios (id INT IDENTITY(1,1) PRIMARY KEY, username VARCHAR(255) UNIQUE, password VARCHAR(255), balance FLOAT, accountNumber INT)")

        # Crear tabla de movimientos si no existe
        self.cursor.execute("IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'movimientos') CREATE TABLE movimientos (id INT IDENTITY(1,1) PRIMARY KEY, userId INT, tipoMovimiento VARCHAR(50), valorMovimiento FLOAT, FOREIGN KEY (userId) REFERENCES usuarios(id))")

    def update_table(self):
        self.cursor.execute("UPDATE usuarios SET accountNumber = id")

    def create_account(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        self.cursor.execute("SELECT * FROM usuarios WHERE username=?", (username,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "El nombre de usuario ya está en uso.")
        else:
            self.cursor.execute("INSERT INTO usuarios (username, password, balance) VALUES (?, ?, 0)", (username, password))
            self.db_connection.commit()
            messagebox.showinfo("Éxito", "Cuenta creada exitosamente.")

            self.cursor.execute("SELECT id FROM usuarios WHERE username=?", (username,))
            user_id = self.cursor.fetchone()[0]

            self.cursor.execute("UPDATE usuarios SET accountNumber = ? WHERE id = ?", (user_id, user_id))

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        self.cursor.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (username, password))
        if self.cursor.fetchone():
            messagebox.showinfo("Éxito", "Inicio de sesión exitoso.")
            self.show_menu()
        else:
            messagebox.showerror("Error", "Nombre de usuario o contraseña incorrectos.")
          
    def show_menu(self):
        self.root.withdraw()

        self.menu_window = tk.Toplevel(self.root)
        self.menu_window.title("Menú Cajero Automático")

        self.balance_label = tk.Label(self.menu_window, text="Saldo actual:")
        self.balance_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.balance_display = tk.Label(self.menu_window, text="")
        self.balance_display.grid(row=0, column=1, padx=10, pady=5)

        self.account_label = tk.Label(self.menu_window, text="Número de Cuenta:")
        self.account_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.account_display = tk.Label(self.menu_window, text="")
        self.account_display.grid(row=1, column=1, padx=10, pady=5)

        self.deposit_button = tk.Button(self.menu_window, text="Depositar", command=self.deposit)
        self.deposit_button.grid(row=2, column=0, padx=10, pady=5)

        self.withdraw_button = tk.Button(self.menu_window, text="Retirar", command=self.withdraw)
        self.withdraw_button.grid(row=2, column=1, padx=10, pady=5)

        self.update_balance_display()

    def update_balance_display(self):
        username = self.username_entry.get()
        self.cursor.execute("SELECT balance, accountNumber FROM usuarios WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        current_balance = result[0]
        account_number = result[1]
        self.balance_display.config(text=current_balance)
        self.account_display.config(text=account_number)

    def deposit(self):
        amount = float(tk.simpledialog.askstring("Depositar", "Ingrese la cantidad a depositar:"))
        if amount > 0:
            self.cursor.execute("UPDATE usuarios SET balance = balance + ? WHERE username = ?", (amount, self.username_entry.get()))
            self.cursor.execute("INSERT INTO movimientos (userId, tipoMovimiento, valorMovimiento) VALUES ((SELECT id FROM usuarios WHERE username = ?), ?, ?)", (self.username_entry.get(), 'Depósito', amount))
            self.db_connection.commit()
            messagebox.showinfo("Éxito", f"Se han depositado {amount} unidades.")
            self.update_balance_display()
        else:
            messagebox.showerror("Error", "La cantidad ingresada no es válida.")

    def withdraw(self):
        amount = float(tk.simpledialog.askstring("Retirar", "Ingrese la cantidad a retirar:"))
        if amount > 0:
            self.cursor.execute("SELECT balance FROM usuarios WHERE username = ?", (self.username_entry.get(),))
            balance_row = self.cursor.fetchone()
            if balance_row:
                current_balance = balance_row[0]
                if current_balance >= amount:
                    self.cursor.execute("UPDATE usuarios SET balance = balance - ? WHERE username = ?", (amount, self.username_entry.get()))
                    self.cursor.execute("INSERT INTO movimientos (userId, tipoMovimiento, valorMovimiento) VALUES ((SELECT id FROM usuarios WHERE username = ?), ?, ?)", (self.username_entry.get(), 'Retiro', amount))
                    self.db_connection.commit()
                    messagebox.showinfo("Éxito", f"Se han retirado {amount} unidades.")
                    self.update_balance_display()
                else:
                    messagebox.showerror("Error", "Saldo insuficiente.")
            else:
                messagebox.showerror("Error", "Nombre de usuario incorrecto.")
        else:
            messagebox.showerror("Error", "La cantidad ingresada no es válida.")

root = tk.Tk()
cajero = CajeroAutomatico(root)
root.mainloop()
