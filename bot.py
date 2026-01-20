import json
import time
import requests
from threading import Thread

TOKEN = "8206500144:AAE0d33TCI3hXtDqfIU-Msi17n5Kr760vfs"
GROUP_ID = -1002720457461
DATA_FILE = "data.json"

CONSTRUCTIONS = {"Высокая": 400_000, "Средняя": 250_000}

# --- Загрузка данных ---
try:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
except:
    data = {"users": {}}

# --- Функции для Telegram ---
def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=payload)

def send_photo(chat_id, file_id, caption=None):
    payload = {"chat_id": chat_id, "photo": file_id}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data=payload)

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def create_report(uid):
    u = data["users"][uid]
    salary = CONSTRUCTIONS.get(u.get("construction_type","-"), 0)
    total_bank = u.get("total_bank", 0)
    report = f"""🟩🟩🟩 <b>СК SAMOGON — Отчёт</b> 🟩🟩🟩

👤 Nick_Name: {u.get("nick_name","-")}
🏗 Вид стройки: {u.get("construction_type","-")}
💰 Банк: {u.get("bank","-")}
⏱ Время КД: {u.get("cd_time","-")}
💵 Заработок: {salary:,} вирт
🏦 Общий банк: {total_bank:,} вирт
"""
    return report

# --- Обработка сообщений ---
def handle_message(msg):
    uid = msg["from"]["id"]
    text = msg.get("text")
    photo = msg.get("photo")

    # Инициализация пользователя
    if uid not in data["users"]:
        data["users"][uid] = {"step":"start","total_bank":0,"high_count":0,"medium_count":0}
    user = data["users"][uid]

    # Старт
    if text == "/start":
        user["step"]="start"
        kb = {"inline_keyboard":[
            [{"text":"🟩 Сдать отчёт","callback_data":"report"}],
            [{"text":"🟪 Взять стройку","callback_data":"take"}],
            [{"text":"🟨 Рейтинг","callback_data":"rating"}]
        ]}
        send_message(uid,"🏗 Добро пожаловать в СК SAMOGON!", kb)
        save_data()
        return

    # Ввод Nick_Name
    if user.get("step")=="waiting_nick" and text:
        user["nick_name"]=text
        user["step"]="waiting_construction"
        kb = {"inline_keyboard":[
            [{"text":"Высокая","callback_data":"high_report"}],
            [{"text":"Средняя","callback_data":"medium_report"}],
            [{"text":"⬅️ Назад","callback_data":"back"}]
        ]}
        send_message(uid,"Выберите вид стройки:", kb)
        save_data()
        return

    # Ввод банка
    if user.get("step")=="waiting_bank" and text:
        user["bank"]=text
        user["step"]="waiting_cd"
        send_message(uid,"Введите время КД:")
        save_data()
        return

    # Ввод времени КД
    if user.get("step")=="waiting_cd" and text:
        user["cd_time"]=text
        user["step"]="waiting_photo"
        send_message(uid,"Пришлите скриншот доказательства:")
        save_data()
        return

    # Обработка фото
    if user.get("step")=="waiting_photo" and photo:
        file_id = photo[-1]["file_id"]
        user["step"]="start"
        salary = CONSTRUCTIONS.get(user.get("construction_type",""),0)
        user["total_bank"] += salary
        if user.get("construction_type")=="Высокая":
            user["high_count"]=user.get("high_count",0)+1
        else:
            user["medium_count"]=user.get("medium_count",0)+1
        save_data()

        report = create_report(uid)
        send_message(uid, report)         # пользователю
        send_message(GROUP_ID, report)    # в группу
        send_photo(uid, file_id, caption="📸 Скриншот")
        return

# --- Обработка колбеков (кнопки) ---
def handle_callback(cb):
    uid = cb["from"]["id"]
    data_cb = cb["data"]

    if uid not in data["users"]:
        data["users"][uid] = {"step":"start","total_bank":0,"high_count":0,"medium_count":0}
    user = data["users"][uid]

    # Назад
    if data_cb=="back":
        user["step"]="start"
        kb = {"inline_keyboard":[
            [{"text":"🟩 Сдать отчёт","callback_data":"report"}],
            [{"text":"🟪 Взять стройку","callback_data":"take"}],
            [{"text":"🟨 Рейтинг","callback_data":"rating"}]
        ]}
        send_message(uid,"Главное меню", kb)
        save_data()
        return

    # Сдать отчёт
    if data_cb=="report":
        user["step"]="waiting_nick"
        send_message(uid,"Введите ваш Nick_Name:")
        save_data()
        return

    # Взятие строек (пример)
    if data_cb=="take":
        kb = {"inline_keyboard":[
            [{"text":"Высокая","callback_data":"take_high"}],
            [{"text":"Средняя","callback_data":"take_medium"}],
            [{"text":"⬅️ Назад","callback_data":"back"}]
        ]}
        send_message(uid,"Выберите тип стройки:", kb)
        save_data()
        return

    if data_cb=="take_high":
        kb = {"inline_keyboard":[
            [{"text":"Арзамас","callback_data":"gps_7_3_1"}],
            [{"text":"Лыткарино","callback_data":"gps_7_3_2"}],
            [{"text":"Южный","callback_data":"gps_7_3_3"}],
            [{"text":"Нижегородск","callback_data":"gps_7_3_4"}],
            [{"text":"⬅️ Назад","callback_data":"back"}]
        ]}
        send_message(uid,"Выберите город:", kb)
        save_data()
        return

    if data_cb=="take_medium":
        kb = {"inline_keyboard":[
            [{"text":"Гарель 1","callback_data":"gps_7_2_3"}],
            [{"text":"Гарель 2","callback_data":"gps_7_2_4"}],
            [{"text":"Батырево 1","callback_data":"gps_7_2_1"}],
            [{"text":"Батырево 2","callback_data":"gps_7_2_2"}],
            [{"text":"⬅️ Назад","callback_data":"back"}]
        ]}
        send_message(uid,"Выберите город:", kb)
        save_data()
        return

    # Рейтинг
    if data_cb=="rating":
        # Формируем топ-3
        top = sorted(data["users"].items(), key=lambda x: x[1].get("total_bank",0), reverse=True)[:3]
        text = "🏆 <b>Рейтинг за неделю</b> 🏆\n\n"
        for i,u in enumerate(top,1):
            text += f"{i}. {u[1].get('nick_name','-')} — 🏗Высокие: {u[1].get('high_count',0)}, Средние: {u[1].get('medium_count',0)}, 💰Банк: {u[1].get('total_bank',0):,} вирт\n"
        send_message(uid,text)
        save_data()
        return

# --- Основной цикл (polling) для Background Worker ---
def main_loop():
    offset = 0
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30")
            result = r.json()["result"]
            for u in result:
                offset = u["update_id"]+1
                if "message" in u:
                    handle_message(u["message"])
                if "callback_query" in u:
                    handle_callback(u["callback_query"])
        except Exception as e:
            print("Ошибка:", e)
            time.sleep(5)

# --- Запуск ---
if __name__=="__main__":
    print("✅ Бот запущен")
    main_loop()