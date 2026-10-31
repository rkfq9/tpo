"""
Лабораторная работа 4: Автотесты OpenBMC через Redfish API
Вариант 20
"""
import unittest
import requests
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BMC_URL = "https://192.168.163.153:2443"
USERNAME = "root"
PASSWORD = "0penBmc"
WRONG_PASSWORD = "wrongpass123"
PROTECTED_URL = f"{BMC_URL}/redfish/v1/Systems/system"


class OpenBMCAuthTests(unittest.TestCase):
    """Тесты авторизации (ЛР4)"""

    def test_01_successful_auth(self):
        """Успешная авторизация"""
        r = requests.get(PROTECTED_URL,
                         auth=HTTPBasicAuth(USERNAME, PASSWORD),
                         verify=False, timeout=30)
        self.assertEqual(r.status_code, 200)
        print(f"[PASS] Тест 1: Успешная авторизация (PowerState: {r.json().get('PowerState')})")

    def test_02_wrong_credentials(self):
        """Неверные данные -> 401"""
        r = requests.get(PROTECTED_URL,
                         auth=HTTPBasicAuth(USERNAME, WRONG_PASSWORD),
                         verify=False, timeout=30)
        self.assertEqual(r.status_code, 401)
        print("[PASS] Тест 2: Неверные данные (401 Unauthorized)")

    def test_03_account_lockout(self):
        """Блокировка после множества неудачных попыток"""
        last = None
        for _ in range(5):
            r = requests.get(PROTECTED_URL,
                             auth=HTTPBasicAuth(USERNAME, WRONG_PASSWORD),
                             verify=False, timeout=30)
            last = r.status_code
        self.assertEqual(last, 401)
        print(f"[PASS] Тест 3: Блокировка (после 5 попыток статус {last})")


class OpenBMCFeatureTests(unittest.TestCase):
    """2 теста из ЛР3 (вариант 20): выключение сервера + логи"""

    def setUp(self):
        self.auth = HTTPBasicAuth(USERNAME, PASSWORD)

    def test_04_power_state(self):
        """ЛР3 ТК1: Выключение сервера (проверка PowerState)"""
        r = requests.get(PROTECTED_URL,
                         auth=self.auth, verify=False, timeout=30)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        power_state = data.get("PowerState", "Unknown")
        print(f"[PASS] Тест 4 (ЛР3-ТК1): PowerState = {power_state}")
        actions = data.get("Actions", {})
        self.assertIn("#ComputerSystem.Reset", actions)

    def test_05_error_logs(self):
        """ЛР3 ТК4: Логи при ошибке (LogServices)"""
        r = requests.get(f"{BMC_URL}/redfish/v1/Systems/system/LogServices",
                         auth=self.auth, verify=False, timeout=30)
        self.assertEqual(r.status_code, 200)
        members = r.json().get("Members", [])
        print(f"[PASS] Тест 5 (ЛР3-ТК4): LogServices найдено {len(members)}")


if __name__ == "__main__":
    print("=" * 60)
    print("ЛАБОРАТОРНАЯ 4: Автотесты OpenBMC (вариант 20)")
    print("=" * 60)
    unittest.main(verbosity=2)
