import sys
import psutil
import os.path
import urllib.request
from json import dump as json_dump, load as json_load, loads as json_loads
from shutil import move as shutil_move, rmtree as shutil_rmtree
from zipfile import ZipFile
from tqdm import tqdm


__location__ = os.getcwd()


VERSION_FILE = os.path.join(__location__, "version.json")
TEMP_DIR = os.path.join(__location__, "temp")
UPDATE_URL = "https://judedm.github.io/"


def is_process_running(exe_path):
    for process in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if process.info['exe'] and process.info['exe'].lower() == exe_path.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def get_latest_update_info():
    response = urllib.request.urlopen(UPDATE_URL, timeout=10)
    data = json_loads(response.read().decode('utf-8'))
    return data[-1] if isinstance(data, list) and data else None


def get_local_version():
    return json_load(open(VERSION_FILE, "r", encoding="utf-8"))["version"] if os.path.exists(VERSION_FILE) else {}


def is_last_version(latest_update: dict):
    return get_local_version() == latest_update.get("version", "")


def download_and_extract_update(url):
    os.makedirs(TEMP_DIR, exist_ok=True)
    zip_path = os.path.join(TEMP_DIR, "update.zip")

    response = urllib.request.urlopen(url)
    bytes_length = int(response.headers.get("content-length"))
    CHUNK = 16 * 1024

    with open(zip_path, "wb") as out_file, tqdm(desc=os.path.split(zip_path)[-1], colour="#00ff00", total=bytes_length, unit="iB", unit_scale=True, unit_divisor=1024) as bar:
        while True:
            chunk = response.read(CHUNK)
            if not chunk:
                break
            size = out_file.write(chunk)
            bar.update(size)

    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(TEMP_DIR)

    files = [f for f in os.listdir(TEMP_DIR) if not (f.endswith("update.zip"))]

    for file in files:
        src_path = os.path.join(TEMP_DIR, file)
        dest_path = os.path.join(__location__, file)

        if not os.path.isdir(dest_path) or not dest_path.endswith("data"):
            shutil_move(src_path, dest_path)

    shutil_rmtree(TEMP_DIR)


def update_app():
    latest_update = get_latest_update_info()
    if is_process_running(os.path.join(__location__, "Binder.exe")):
        return print("Необходимо закрыть биндер.")
    if is_last_version(latest_update):
        return print("У Вас установлена последняя версия биндера.")
    try:
        download_and_extract_update(latest_update["url"])
        json_dump({"version": latest_update["version"]}, open(VERSION_FILE, "w", encoding="utf-8"), indent=2)
        print(f"Успешно обновлено до версии {latest_update['version']}!")
    except PermissionError:
        print("Необходимо закрыть биндер.")
    except Exception as e:
        print(f"Произошла ошибка при выполнении обновления: {e}")


update_app()
os.system("pause")