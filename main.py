from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


from src.resources_class import Resources

# Підключення до відкритого Chrome
options = Options()
options.debugger_address = "127.0.0.1:9222"
driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 5)

time_connect = input("Введіть час підключення (XX,YY): ")
type_connect = input(
    "Введіть тип підключення (1 - Інтернет, 2 - ТБ, ' ' - пропустити): "
)
cable_length = input("Enter cable length: ").strip()

# fill_base_options(wait, time_connect, type_connect)
# process_all_resources(wait)

resources = Resources(type_connect, cable_length=cable_length)
resources.fill_base_options(wait, time_connect)
resources.fill_resources(wait)

input("Press Enter to close window...")
driver.quit()
