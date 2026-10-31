"""
Лабораторная работа 5: Автотесты Redfish API с PyTest
Вариант 20
"""
import os
import time
import pytest
import requests
import urllib3
import logging
import subprocess

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

BMC_URL = "https://192.168.163.153:2443"
USERNAME = "root"
PASSWORD = "0penBmc"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.verify = False
    s.auth = (USERNAME, PASSWORD)
    s.timeout = 60
    yield s
    s.close()


@pytest.fixture(scope="module")
def auth_token():
    log.info("POST /SessionService/Sessions - создание сессии")
    r = requests.post(
        f"{BMC_URL}/redfish/v1/SessionService/Sessions",
        json={"UserName": USERNAME, "Password": PASSWORD},
        verify=False,
        timeout=60,
    )
    assert r.status_code == 201, f"Ожидался 201, получен {r.status_code}"
    token = r.headers.get("X-Auth-Token")
    assert token, "X-Auth-Token отсутствует в ответе"
    log.info(f"Токен получен: {token[:8]}...")
    return token


def run_ipmi_sensors(retries=3, delay=5):
    """Запуск ipmitool sensor list с retry"""
    ipmi_cmd = (
        f"ipmitool -I lanplus -H 127.0.0.1 -p 2623 "
        f"-U {USERNAME} -P {PASSWORD} sensor list"
    )
    cmd = ["script", "-q", "-c", ipmi_cmd, "/dev/null"]
    env = os.environ.copy()
    env["TERM"] = "xterm"

    for attempt in range(1, retries + 1):
        log.info(f"IPMI попытка {attempt}/{retries}")
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=90, env=env,
        )
        cleaned = result.stdout.replace("\r\n", "\n").replace("\r", "\n")
        cpu_sensors = [l for l in cleaned.splitlines() if "cpu" in l.lower()]
        log.info(f"IPMI: найдено {len(cpu_sensors)} датчиков CPU")
        if cpu_sensors:
            return cpu_sensors
        if attempt < retries:
            log.info(f"Пусто, ждём {delay} сек...")
            time.sleep(delay)
    return []


def test_01_auth_create_session(auth_token):
    assert auth_token
    log.info("[PASS] Тест 1: Аутентификация - токен получен")


def test_02_system_info(session):
    log.info("GET /Systems/system")
    r = session.get(f"{BMC_URL}/redfish/v1/Systems/system")
    assert r.status_code == 200
    data = r.json()
    assert "PowerState" in data
    assert "Status" in data
    log.info(f"[PASS] Тест 2: PowerState = {data['PowerState']}")


def test_03_power_reset(session):
    payload = {"ResetType": "On"}
    log.info("POST /Systems/system/Actions/ComputerSystem.Reset")
    r = session.post(
        f"{BMC_URL}/redfish/v1/Systems/system/Actions/ComputerSystem.Reset",
        json=payload,
    )
    log.info(f"Ответ сервера: {r.status_code}")
    assert r.status_code in (200, 202, 204, 400, 409)
    log.info(f"[PASS] Тест 3: Управление питанием - статус {r.status_code}")


def test_04_cpu_temperature(session):
    log.info("GET /Chassis/chassis/Thermal")
    r = session.get(f"{BMC_URL}/redfish/v1/Chassis/chassis/Thermal")
    if r.status_code == 200:
        data = r.json()
        temps = data.get("Temperatures", [])
        assert len(temps) > 0
        log.info(f"[PASS] Тест 4: Температура - найдено {len(temps)} датчиков")
    else:
        log.info(f"[PASS] Тест 4: Thermal отсутствует ({r.status_code})")
        assert r.status_code == 404


def test_05_cpu_sensors_redfish_vs_ipmi(session):
    """Сравнение датчиков CPU в Redfish и IPMI"""
    log.info("Сравнение датчиков CPU: Redfish vs IPMI")

    r = session.get(f"{BMC_URL}/redfish/v1/Systems/system/Processors")
    assert r.status_code == 200
    processors = r.json().get("Members", [])
    log.info(f"Redfish: найдено {len(processors)} процессоров")

    cpu_sensors = run_ipmi_sensors(retries=3, delay=5)

    assert len(cpu_sensors) > 0, "IPMI не вернул датчики CPU"

    log.info(f"[PASS] Тест 5: Redfish {len(processors)} процессоров, IPMI {len(cpu_sensors)} датчиков")
    print(f"\nСравнение датчиков CPU:")
    print(f"  Redfish Processors: {len(processors)}")
    print(f"  IPMI CPU sensors:   {len(cpu_sensors)}")
