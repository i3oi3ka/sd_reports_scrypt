import re
import time
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
        x = screen_width - width
        y = (screen_height // 2) - (height // 2)
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

        tk.Label(frame, text="Тип (1-Інет, 2-ТБ, 3-Мігр, 4-Bandl):").grid(
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

        # --- ЗМІНА: Збережено посилання на кнопку для зміни кольору ---
        self.connect_btn = tk.Button(
            top_row, text="🔗 Connect", command=self.connect_driver, width=10
        )
        self.connect_btn.pack(side="left", padx=5, pady=2)

        tk.Button(top_row, text="📋 Fill", command=self.fill_form, width=10).pack(
            side="left", padx=5, pady=2
        )

        bottom_row = tk.Frame(btn_frame)
        bottom_row.pack()

        tk.Button(bottom_row, text="✋ Stop", command=self.stop_filling, width=10).pack(
            side="left", padx=5, pady=2
        )
        tk.Button(
            bottom_row, text="🧹 Clear", command=self.clear_console, width=10
        ).pack(side="left", padx=5, pady=2)

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
            self.log("🚀 Chrome запущено. Зачекайте завантаження сторінки.")
        except Exception as e:
            self.log(f"❌ Помилка запуску Chrome: {e}")

    # --- ЗМІНА: Повністю переписаний метод connect_driver ---
    def connect_driver(self):
        self.connect_btn.configure(bg="SystemButtonFace")  # Скидаємо колір
        try:
            options = Options()
            options.debugger_address = f"127.0.0.1:{REMOTE_DEBUGGING_PORT}"

            self.log("🔍 Спроба підключення до браузера...")
            self.driver = webdriver.Chrome(options=options)

            target_found = False
            max_attempts = 5

            for attempt in range(max_attempts):
                self.log(f"🔎 Пошук вкладки (спроба {attempt + 1})...")
                handles = self.driver.window_handles

                for handle in handles:
                    try:
                        self.driver.switch_to.window(handle)
                        url = self.driver.current_url.lower()
                        title = self.driver.title.lower()

                        if "pdamaster" in url or "интерфейс мастера" in title:
                            self.log(f"✅ Знайдено: {self.driver.title}")
                            target_found = True
                            break
                    except:
                        continue

                if target_found:
                    break
                time.sleep(1)

            if target_found:
                self.wait = WebDriverWait(self.driver, 5)
                self.connect_btn.configure(bg="#90EE90")  # ЗЕЛЕНИЙ КОЛІР
                self.log("🔗 Драйвер успішно підключено.")
            else:
                self.log("⚠️ Вкладку не знайдено. Відкрийте pdamaster вручну.")
                self.connect_btn.configure(bg="#FFCCCB")  # ЧЕРВОНУВАТИЙ
                self.driver = None

        except Exception as e:
            self.log(f"❌ Помилка: Переконайтеся, що Chrome запущено кнопкою вище.")
            self.connect_btn.configure(bg="#FFCCCB")
            self.driver = None

    def stop_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.connect_btn.configure(bg="SystemButtonFace")
                self.log("🛑 Драйвер зупинено.")
            except Exception as e:
                self.log(f"❌ Помилка зупинки: {e}")

    def stop_filling(self):
        self.stop_flag = True
        self.log("✋ Заповнення перервано.")

    def fill_form(self):
        if not self.driver:
            self.log("⚠️ Спочатку натисніть Connect.")
            return

        time_connect = self.time_entry.get().strip()
        type_connect = self.type_entry.get().strip()
        cable_length = self.cable_entry.get().strip()
        self.stop_flag = False

        # Валідація даних
        if not time_connect or not re.match(r"^\d{1,2}[.,]\d{2}$", time_connect):
            messagebox.showerror("Помилка", "❗ Формат часу: 14.30")
            return

        if type_connect not in ("1", "2", "3", "4"):
            messagebox.showerror("Помилка", "❗ Тип: 1, 2, 3 або 4")
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
                    self.log("✅ Готово!")
            except Exception as e:
                self.log(f"❌ Помилка: {e}")

        threading.Thread(target=task).start()


if __name__ == "__main__":
    root = tk.Tk()
    root.wm_attributes("-topmost", 1)
    app = GuiSeleniumApp(root)
    root.mainloop()
