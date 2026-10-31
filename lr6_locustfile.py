"""
Лабораторная работа 6: Нагрузочное тестирование с Locust
Вариант 20
"""
from locust import HttpUser, task, between
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BMC_URL = "https://192.168.163.153:2443"
BMC_USER = "root"
BMC_PASS = "0penBmc"


class OpenBMCUser(HttpUser):
    """Класс 1: нагрузка на OpenBMC API (Redfish)"""
    host = BMC_URL
    wait_time = between(1, 3)

    def on_start(self):
        self.client.verify = False
        self.client.auth = (BMC_USER, BMC_PASS)

    @task(2)
    def get_system_info(self):
        """GET /Systems/system — информация о системе"""
        with self.client.get(
            "/redfish/v1/Systems/system",
            name="/redfish/v1/Systems/system",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "PowerState" in data:
                    response.success()
                else:
                    response.failure("PowerState отсутствует")
            else:
                response.failure(f"Код {response.status_code}")

    @task(1)
    def get_power_state(self):
        """Получение PowerState"""
        with self.client.get(
            "/redfish/v1/Systems/system",
            name="/redfish/v1/Systems/system (PowerState)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                power_state = data.get("PowerState", "Unknown")
                if power_state:
                    response.success()
                else:
                    response.failure("PowerState пуст")
            else:
                response.failure(f"Код {response.status_code}")


class PublicAPIUser(HttpUser):
    """Класс 2: нагрузка на публичные API"""
    wait_time = between(1, 3)

    @task(1)
    def jsonplaceholder_posts(self):
        """GET JSONPlaceholder /posts"""
        with self.client.get(
            "https://jsonplaceholder.typicode.com/posts",
            name="JSONPlaceholder /posts",
            catch_response=True,
            timeout=15,
        ) as response:
            if response.status_code == 200:
                if len(response.json()) > 0:
                    response.success()
                else:
                    response.failure("Пустой список постов")
            else:
                response.failure(f"Код {response.status_code}")

    @task(1)
    def wttr_in_weather(self):
        """GET wttr.in — погода в Новосибирске"""
        with self.client.get(
            "https://wttr.in/Novosibirsk?format=j1",
            name="wttr.in Novosibirsk",
            catch_response=True,
            timeout=15,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Код {response.status_code}")
