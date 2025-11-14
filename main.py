import re
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from src.resources_class import Resources

CHROME_PATH = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
USER_DATA_DIR = r"C:\\chrome_debug_temp"
REMOTE_DEBUGGING_PORT = "9222"

SLEEP_DURATION = 0.5


class GuiSeleniumApp:
    def __init__(self, root):
        self.driver = None
        self.wait = None
        self.form_filling_thread = None
        self.stop_flag = False

        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.title("Автозаповнення заявки")

        self.align_right_center(400, 500)

        self.setup_gui()

    def align_right_center(self, width=600, height=500):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - width  # притиснути до правого краю
        y = (screen_height // 2) - (height // 2)  # по центру вертикалі
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def on_close(self):
        self.stop_flag = True
        self.stop_driver()
        self.root.destroy()

    def log(self, message):
        self.console.configure(state="normal")
        self.console.insert(tk.END, message + "\n")
        self.console.configure(state="disabled")
        self.console.yview(tk.END)
        print(message)

    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete(1.0, tk.END)
        self.console.configure(state="disabled")

    def setup_gui(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        tk.Label(frame, text="Час підключення (год,хв):").grid(
            row=0, column=0, sticky="e"
        )
        self.time_entry = tk.Entry(frame)
        self.time_entry.grid(row=0, column=1)

        tk.Label(frame, text="Тип (1 - Інет, 2 - ТБ, 3 - Міграція, 4 - Bandl):").grid(
            row=1, column=0, sticky="e"
        )
        self.type_entry = tk.Entry(frame)
        self.type_entry.grid(row=1, column=1)

        tk.Label(frame, text="Метраж кабелю:").grid(row=2, column=0, sticky="e")
        self.cable_entry = tk.Entry(frame)
        self.cable_entry.grid(row=2, column=1)
        self.cable_entry.bind("<Return>", lambda event: self.fill_form())

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        top_row = tk.Frame(btn_frame)
        top_row.pack()
        tk.Button(top_row, text="🚀 Chrome", command=self.start_chrome, width=10).pack(
            side="left", padx=5, pady=2
        )
        tk.Button(
            top_row, text="🔗 Connect", command=self.connect_driver, width=10
        ).pack(side="left", padx=5, pady=2)
        tk.Button(top_row, text="📋 Fill", command=self.fill_form, width=10).pack(
            side="left", padx=5, pady=2
        )

        # --- Другий ряд кнопок ---
        bottom_row = tk.Frame(btn_frame)
        bottom_row.pack()
        tk.Button(bottom_row, text="✋ Stop", command=self.stop_filling, width=10).pack(
            side="left", padx=5, pady=2
        )
        tk.Button(
            bottom_row, text="🧹 Clear", command=self.clear_console, width=10
        ).pack(side="left", padx=5, pady=2)

        # tk.Button(btn_frame, text="🛑 Зупинити драйвер", command=self.stop_driver).pack(
        #     side="left", padx=5
        # )

        self.console = scrolledtext.ScrolledText(self.root, height=20, state="disabled")
        self.console.pack(fill="both", padx=10, pady=10)

    def start_chrome(self):
        try:
            subprocess.Popen(
                [
                    "start",
                    "",
                    CHROME_PATH,
                    f"--remote-debugging-port={REMOTE_DEBUGGING_PORT}",
                    f"--user-data-dir={USER_DATA_DIR}",
                ],
                shell=True,
            )
            self.log("🚀 Chrome запущено в режимі налагодження.")
        except Exception as e:
            self.log(f"❌ Помилка запуску Chrome: {e}")

    def connect_driver(self):
        try:
            options = Options()
            options.debugger_address = f"127.0.0.1:{REMOTE_DEBUGGING_PORT}"
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 5)
            self.log("🔗 Підключено до драйвера.")
        except Exception as e:
            self.log(f"❌ Не вдалося підключитися до драйвера: {e}")

    def stop_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.log("🛑 Драйвер зупинено.")
            except Exception as e:
                self.log(f"❌ Помилка зупинки драйвера: {e}")
        else:
            self.log("ℹ️ Драйвер ще не запущено або вже зупинено.")

    def stop_filling(self):
        self.stop_flag = True
        self.log("✋ Заповнення форми перервано користувачем.")

    def fill_form(self):
        if not self.driver:
            self.log("⚠️ Спочатку підключіться до драйвера.")
            return

        time_connect = self.time_entry.get().strip()
        type_connect = self.type_entry.get().strip()
        cable_length = self.cable_entry.get().strip()
        self.stop_flag = False

        if not time_connect or not re.match(r"^\d{1,2}[.,]\d{2}$", time_connect):
            messagebox.showerror(
                "Помилка",
                "❗ Введіть час підключення у форматі год:хв (наприклад, 14.30 або 14,30).",
            )
            return

        if type_connect not in ("1", "2", "3", "4"):
            messagebox.showerror(
                "Помилка",
                "❗ Тип підключення має бути 1 (Інтернет), 2 (ТБ) або 3 (міграція).",
            )
            return

        if type_connect != "3" and (
            not cable_length.isdigit()
            or int(cable_length) <= 0
            or int(cable_length) > 45
        ):
            messagebox.showerror("Помилка", "❗ Метраж кабелю має бути в межах 1-45.")
            return

        def task():
            try:
                resources = Resources(type_connect, cable_length)
                resources.fill_base_options(
                    self.driver, self.wait, self.log, time_connect
                )
                for resource in resources.data:
                    if self.stop_flag:
                        break
                    resource.fill_form(self.wait, self.log)
                if not self.stop_flag:
                    self.log("✅ Форму заповнено успішно.")
                else:
                    self.log("⚠️ Заповнення зупинено до завершення.")
            except Exception as e:
                self.log(f"❌ Помилка при заповненні форми: {e}")

        self.form_filling_thread = threading.Thread(target=task)
        self.form_filling_thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    root.wm_attributes("-topmost", 1)
    app = GuiSeleniumApp(root)
    root.mainloop()
