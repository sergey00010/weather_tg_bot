import requests
import telebot
import json
import schedule
import time
import threading
from dotenv import load_dotenv
import os
import re 

load_dotenv()

WEATHERAPI_API_KEY = os.getenv('GEOAPIFY_API_KEY')  
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') 

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
USERS_FILE = 'users.json'

try:
    with open(USERS_FILE, 'r') as file:
        users_data = json.load(file)
except FileNotFoundError:
    users_data = {}

def save_users_data():
    with open(USERS_FILE, 'w') as file:
        json.dump(users_data, file, indent=4)

def get_weather(city_name):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_API_KEY}&q={city_name}&aqi=yes"
        print(url)
        response = requests.get(url)
        data = response.json()
        
        if "error" in data:
            return "Город не найден. Попробуйте еще раз."
        
        location = data["location"]["name"]
        temperature = data["current"]["temp_c"]
        weather_description = data["current"]["condition"]["text"]
        humidity = data["current"]["humidity"]
        wind_speed = data["current"]["wind_kph"]
        
        weather_info = (
            f"Погода в городе {location}:\n"
            f"Описание: {weather_description}\n"
            f"Температура: {temperature}°C\n"
            f"Влажность: {humidity}%\n"
            f"Скорость ветра: {wind_speed} км/ч"
        )
        
        return weather_info
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к API: {e}")
        return "Ошибка при получении данных с сервера. Попробуйте позже."
    except KeyError as e:
        print(f"Ошибка обработки данных: {e}")
        return "Ошибка обработки данных о погоде."
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return "Произошла непредвиденная ошибка. Попробуйте позже."

def send_daily_weather(chat_id, city_name):
    try:
        weather_info = get_weather(city_name)
        bot.send_message(chat_id, weather_info)
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "напиши название города, чтобы погода отправлялась ежедневно, \n то пишите /up название города время, \n чтобы отключить ежедневную отправку, пишите /off")

def is_valid_time(time_str):
    return bool(re.match(r'^[0-9]{2}:[0-9]{2}$', time_str))

@bot.message_handler(commands=['up'])
def set_daily_weather(message):
    try:
        chat_id = message.chat.id
        user_message = message.text.replace('/up', '').strip()

        parts = user_message.split()
        
        if len(parts) < 2:
            bot.reply_to(message, "Пожалуйста, укажите город и время в формате /up Город Время (например, /up Москва 09:00).")
            return
        
        city_name = parts[0]
        time_str = parts[1]

        if not is_valid_time(time_str):
            bot.reply_to(message, "Неверный формат времени. Пожалуйста, укажите время в формате HH:MM.")
            return

        if str(chat_id) not in users_data:
            users_data[str(chat_id)] = {
                "messages": [],
                "daily_weather": False,
                "time": ""
            }

        users_data[str(chat_id)]["messages"].append(city_name) 
        users_data[str(chat_id)]["daily_weather"] = True 
        users_data[str(chat_id)]["time"] = time_str 
        save_users_data()

        bot.reply_to(message, f"Ежедневная погода для города {city_name} будет отправляться в {time_str}.")
        schedule.every().day.at(time_str).do(send_daily_weather, chat_id=chat_id, city_name=city_name)
    except Exception as e:
            print(f"Ошибка в планировщике: {e}")


@bot.message_handler(commands=['off'])
def stop_daily_weather(message):
    try:
        chat_id = message.chat.id
        
        if str(chat_id) in users_data:
            users_data[str(chat_id)]["daily_weather"] = False
            save_users_data()
            bot.reply_to(message, "Ежедневная отправка погоды отключена.")
        else:
            bot.reply_to(message, "Вы еще не активировали ежедневную отправку погоды.")
    except Exception as e:
        print(f"Ошибка в планировщике: {e}")    

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        chat_id = message.chat.id
        user_message = message.text
        
        if str(chat_id) not in users_data:
            users_data[str(chat_id)] = {
                "messages": [], 
                "daily_weather": False
            }
        
        users_data[str(chat_id)]["messages"].append(user_message) 
        save_users_data()
        
        weather_info = get_weather(user_message)
        bot.reply_to(message, weather_info)
    except Exception as e:
        print(f"Ошибка в планировщике: {e}")

def run_scheduler():
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка в планировщике: {e}")

scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

if __name__ == "__main__":
    bot.polling(none_stop=True)