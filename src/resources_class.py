from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from src.resources import resources_standart, resources_coaxial, resources_utp
from time import sleep
import random

FORM_LOAD_DELAY = 0.25  # Затримка
MAX_ATTEMPTS = 3


def get_time_range(time_input: str):
    # замінюємо крапку на кому, якщо треба
    time_input = time_input.replace(".", ",")
    try:
        hours, minutes = map(int, time_input.split(","))
    except ValueError as exc:
        raise ValueError(
            "⛔ Формат часу невірний. Використовуй 'години,хвилини' або 'години.хвилини'"
        ) from exc

    yesterday = datetime.now() - timedelta(days=1)
    base_time = yesterday.replace(hour=hours, minute=minutes, second=0, microsecond=0)

    start_time = base_time - timedelta(minutes=50)
    end_time = base_time + timedelta(minutes=10)

    return [start_time.strftime("%d-%m-%Y %H:%M"), end_time.strftime("%d-%m-%Y %H:%M")]


class Resource:
    def __init__(
        self, work_type, work_kind, resource_type, model, quantity, description=""
    ):
        self.work_type = work_type
        self.work_kind = work_kind
        self.resource_type = resource_type
        self.model = model
        self.quantity = quantity
        self.description = description

    def __str__(self):
        return f"Resource(work_type={self.work_type}, work_kind={self.work_kind}, resource_type={self.resource_type}, model={self.model}, quantity={self.quantity}, description={self.description})"

    def wait_for_option(self, select_element, option_text):
        # Очікуємо, доки потрібний option з’явиться
        for _ in range(10):  # до ~5 секунд
            options = [o.text.strip() for o in Select(select_element).options]
            if option_text in options:
                return
            sleep(FORM_LOAD_DELAY)
        raise Exception(f"❌ Option '{option_text}' not found in select.")

    def fill_form(self, wait, log, attempts: int = 1):
        log("--" * 40)
        log(f"\n📝 Filling form: {self.description}")

        try:
            add_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Добавить"]'))
            )
            print("🔘 Clicking 'Добавить'...")
            add_button.click()
            sleep(FORM_LOAD_DELAY)
        except Exception as e:
            print("❌ Failed to click 'Добавить':", e)
            return
        sleep(FORM_LOAD_DELAY)
        try:
            # Work Type
            type_select = wait.until(EC.element_to_be_clickable((By.NAME, "WorkType")))
            self.wait_for_option(type_select, self.work_type)
            Select(type_select).select_by_visible_text(self.work_type)

            # Work Kind
            kind_select = wait.until(EC.element_to_be_clickable((By.NAME, "WorkKind")))
            self.wait_for_option(kind_select, self.work_kind)
            Select(kind_select).select_by_visible_text(self.work_kind)

            # Resource Type
            resource_select = wait.until(
                EC.element_to_be_clickable((By.NAME, "ResourceType"))
            )
            self.wait_for_option(resource_select, self.resource_type)
            Select(resource_select).select_by_visible_text(self.resource_type)

            # Model
            model_select = wait.until(EC.element_to_be_clickable((By.NAME, "Mark")))
            self.wait_for_option(model_select, self.model)
            Select(model_select).select_by_visible_text(self.model)

            # Quantity
            quantity_input = wait.until(EC.element_to_be_clickable((By.NAME, "Amount")))
            quantity_input.clear()
            quantity_input.send_keys(str(self.quantity))

            log("✅ Form fields filled.")

        except Exception as e:
            print("❌ Error filling form fields:", e)
            cancel_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//button[text()="Сохранить"]/following::button[text()="Отмена"]',
                    )
                )
            )
            print("❌ Clicking 'Отмена'...")
            cancel_button.click()
            sleep(FORM_LOAD_DELAY)
            if attempts <= MAX_ATTEMPTS:
                log("🔁 Retrying to fill the form...")
                self.fill_form(wait, log, attempts + 1)
                return
            print("❌ Max attempts reached. Exiting...")
            return

        try:
            save_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[text()="Сохранить"]'))
            )
            save_button.click()
            log("💾 Data saved successfully.")
        except Exception as e:
            print("❌ Failed to click 'Сохранить':", e)
        sleep(FORM_LOAD_DELAY)


class Resources:
    def __init__(self, type_connect: str = None, cable_length: str = None):
        self.data = []
        self.type_connect = type_connect
        self.add_ftth_resource(cable_length)
        self.add_standard_resource()
        self.add_sleeve_resource_random(int(cable_length) * 2)

        if type_connect == "1":
            self.add_utp_resource()
        elif type_connect == "2":
            self.add_coaxial_resource()

    def fill_base_options(self, driver, wait, log, time_connect, attempts: int = 1):
        try:
            # Час: вхід/вихід
            if time_connect:
                try:
                    start_time, end_time = get_time_range(time_connect)

                    time_in = wait.until(
                        EC.presence_of_element_located((By.NAME, "timeInPDA"))
                    )
                    time_in.clear()
                    time_in.send_keys(start_time)

                    time_out = wait.until(
                        EC.presence_of_element_located((By.NAME, "timeOutPDA"))
                    )
                    time_out.clear()
                    time_out.send_keys(end_time)

                    log("⏰ Час підключення успішно заповнено.")
                except Exception as e:
                    log(f"❌ Не вдалося заповнити час: {e}")

            # Тип послуги (Інтернет/ЦТБ)
            if self.type_connect:
                service_elements = driver.find_elements(By.NAME, "servicePDA")
                if service_elements:
                    try:
                        Select(service_elements[0]).select_by_visible_text(
                            "Инет" if self.type_connect == "1" else "ЦТВ"
                        )
                        log(
                            f"🌐 Тип послуги встановлено: {'Инет' if self.type_connect == '1' else 'ЦТВ'}"
                        )
                    except Exception as e:
                        log(f"❌ Не вдалося вибрати тип послуги: {e}")
                else:
                    log("⚠️ Поле 'servicePDA' не знайдено, пропущено.")

            # Тип транспорту
            transport = wait.until(
                EC.presence_of_element_located((By.NAME, "routeNumber2"))
            )
            Select(transport).select_by_visible_text("Автомобиль личный")

            # Виконано підрядником
            contractor_done = wait.until(
                EC.presence_of_element_located((By.NAME, "completedContractor"))
            )
            Select(contractor_done).select_by_visible_text("Да")

            # Регіон
            region = wait.until(EC.presence_of_element_located((By.NAME, "pdaRegion")))
            Select(region).select_by_visible_text("ПОДІЛЛЯ")

            # Підрядна організація
            contractor = wait.until(
                EC.presence_of_element_located((By.NAME, "pdaContractor"))
            )
            Select(contractor).select_by_visible_text('ТОВ "Сервіс Сістем" (Вінниця)')

            # Коментарій до заявки
            comment_input = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "gwt-TextArea"))
            )
            comment_input.clear()
            comment_input.send_keys(
                "Виконано підрядною організацією ТОВ 'Сервіс Сістем'"
            )

            log("✅ Основні поля заявки заповнено.")

        except Exception as e:
            log(f"❌ Загальна помилка при заповненні форми: {e}")
            sleep(FORM_LOAD_DELAY)
            if attempts <= MAX_ATTEMPTS:
                self.fill_base_options(driver, wait, log, time_connect, attempts + 1)
                log("🔁 Retrying to fill base options...")
            else:
                print("❌ Max attempts reached. Exiting...")

    # def fill_resources(self, wait):
    #     try:
    #         for resource in self.data:
    #             resource.fill_form(wait)
    #             sleep(FORM_LOAD_DELAY)
    #     except Exception as e:
    #         self.log(f"❌ Помилка при заповненні ресурсів: {e}")

    def add_resource(self, resource: Resource):
        self.data.append(resource)

    def add_ftth_resource(self, cable_length: str):
        self.data.append(
            Resource(
                work_type="Подключение",
                work_kind="Монтаж",
                resource_type="Кабель оптический",
                model="(FTTH) F 1 (з склопрутком)",
                quantity=cable_length,
                description="Кабель оптичний FTTH",
            )
        )

    # def add_sleeve_resource(self, quantity: int = 50):
    #     self.data.append(
    #         Resource(
    #             work_type="Подключение",
    #             work_kind="Монтаж",
    #             resource_type="Расходный материал",
    #             model="Клипса 3",
    #             quantity=quantity,
    #             description="Clip 3mm for fastening",
    #         )
    #     )

    def add_sleeve_resource_random(self, quantity: int = 50) -> None:
        """Додає випадковий ресурс для кріплення з заданими ймовірностями.

        Args:
            quantity: Кількість одиниць ресурсу (за замовчуванням 50)
        """
        # Створюємо словник для зручного вибору ресурсів
        RESOURCE_OPTIONS = {
            "Клипса 3": {"chance": 80, "description": "Клипса 3"},
            "Клипса 5": {"chance": 10, "description": "Клипса 5"},
            "Стяжка хомут": {"chance": 10, "description": "Стяжка хомут"},
        }

        # Генеруємо випадкове число
        rand_val = random.randint(1, 100)
        cumulative_chance = 0

        # Вибираємо ресурс на основі ймовірностей
        for model, params in RESOURCE_OPTIONS.items():
            cumulative_chance += params["chance"]
            if rand_val <= cumulative_chance:
                self.data.append(
                    Resource(
                        work_type="Подключение",
                        work_kind="Монтаж",
                        resource_type="Расходный материал",
                        model=model,
                        quantity=quantity,
                        description=params["description"],
                    )
                )
                break

    def add_standard_resource(self):
        for resource in resources_standart:
            self.data.append(Resource(**resource))

    def add_utp_resource(self):
        for resource in resources_utp:
            self.data.append(Resource(**resource))

    def add_coaxial_resource(self):
        for resource in resources_coaxial:
            self.data.append(Resource(**resource))
