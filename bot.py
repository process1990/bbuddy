#D2Buddy
TELEGRAM_API_TOKEN = '6034407389:AAENp7_dSV8elFvTlVAm0UJjnh91PKezQGs'
FEEDBACK_CHAT_ID = 'FEEDBACK_CHAT_ID'

import telebot
from telebot import types
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import logging
from collections import defaultdict

from google.cloud import vision
from google.oauth2 import service_account
import requests
import os
import logging
import csv

logging.basicConfig(level=logging.DEBUG)

nltk.download('stopwords')
nltk.download('punkt')

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "liquid-anchor-383805-da17f74a4cfb.json"

stop_words = set(stopwords.words('russian'))
user_states = {}
ratingMenu = ["👎🏻 Плохой ответ", "👍🏻 Это то, что я искал!"]

credentials = service_account.Credentials.from_service_account_file('liquid-anchor-383805-da17f74a4cfb.json')
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

# Введите ваш токен бота

bot = telebot.TeleBot(TELEGRAM_API_TOKEN)

DOCUMENTATION = {"Как получить ключ PayControl для подписания платежных документов?": "Для получения своего ключа PayControl, при помощи которого вы сможете осуществлять подписание платёжных документов, вам необходимо обратиться в банк с просьбой о выпуске ключа PayControl.",
"Где отобразится ключ PayControl после его получения в банке?": """После того, как банк выпустит для вас ключ PayControl и заведет соответствующее
средство подписи, данный ключ отобразится в списке ключей PayControl, доступном
в разделе Безопасность меню настроек профиля (Настройки → Безопасность → PayControl → Ключи)""",
"зарегистрировать ключ PayControl на своем устройстве?": "Если при создании ключа был выбран способ доставки ключа раздельно двумя частями, в мобильном приложении после первого сканирования QR-кода потребуется ввести вторую часть ключа – код активации.",
"продлить срок действия ключа PayControl?": "Ключи PayControl, как и любое средство подписи, имеют свой срок действия. Для его продления вы можете отправить в банк заявление на продление срока действия ключа PayControl",
"найти список заявлений на продление ключей PayControl?" :"Перейдите к списку заявлений на продление ключей (Настройки → Безопасность → PayControl → Продление ключей).",
"сертификаты могут использовать физические лица, действующие без доверенности от юридического лица": "Физические лица, действующие без доверенности (к примеру, ген. директор юр. лица), имеют возможность по прежнему использовать сертификаты, выданные на юридическое лицо.",
"открыть список всех зарегистрированных сертификатов электронной подписи?": "На главной панели инструментов выберите элемент Настройки → Безопасность → Сертификаты → Сертификаты",
"просмотреть детальную информацию по конкретному сертификату?": "Для просмотра детальной информации по сертификату выберите нужную запись в списке и выполните двойной щелчок левой кнопкой мыши.",
"создать запрос на отзыв сертификата": """Для создания запроса на отзыв сертификата выполните следующие действия:
Откройте панель настроек профиля, нажав Настройки
На правой панели выберите пункт Безопасность.
Перейдите в подраздел Сертификаты → Запросы
В выпадающем списке выберите пункт Запросы на добавление сертификата:
и нажмите кнопку + справа.""",
# old texts
    "открыть форму пролонгация депозита на странице размещение средств?": """Выберите в главном меню раздел Депозиты.
Будет открыта вкладка Мои продукты → Текущие продукты страницы Размещение средств (см. Страница Размещение средств (вкладка Мои продукты)).
Нажмите кнопку в правом верхнем углу карточки депозита, который требуется продлить, и в открывшемся меню выберите пункт Пролонгировать.
Будет отображена экранная форма Пролонгация депозита.""",

    "предварительно просмотреть печатную форму заявления на выдачу средств по кредиту?": """Для предварительного просмотра печатной формы / печати документа нажмите кнопку Просмотр. При необходимости обратитесь к Печать документа из страницы создания / редактирования.""",

    "информация содержится в записях по сделкам на учете в банке?": "Записи по сделкам, поставленным на учёт в банке, содержат основную информацию по данным сделкам – номера УНК, ссылки на обосновывающие документы, суммы и даты исполнения обязательств.",

    "содержит вкладка Платежи в карточке сделки на учете в банке?": "Вкладка Платежи содержит – в соответствующих вкладках-подразделах – списки платёжных документов (рублёвых платежей, валютных переводов и списаний с транзитных счетов), связанных с выбранной сделкой.",

    "можно указать данные контактного лица при пролонгации депозита?": """Если на форме отображается поле выбора Добавить данные исполнителя, при необходимости укажите данные контактного лица:
Заполните поле выбора Добавить данные исполнителя.
Будут отображены дополнительные поля ФИО и Телефон (см. Форма Пополнение депозита с дополнительными полями).
Укажите в данных полях, соответственно, ФИО и номер телефона контактного лица."""
}

# Настройка логирования
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR)

def find_best_match(query, documents):
    stop_words = set(stopwords.words('russian'))
    query_words = word_tokenize(query)

    filtered_query = [w.lower() for w in query_words if w.lower() not in stop_words]

    best_score = 5
    best_match = None

    for key, value in documents.items():
        value_words = word_tokenize(value)
        filtered_value = [w.lower() for w in value_words if w.lower() not in stop_words]

        score = 0
        for word in filtered_query:
            score += filtered_value.count(word)

        if score > best_score:
            print(f"score: {score}, best_score: {best_score}")
            best_score = score
            best_match = (key, value)
    return best_match

def get_response(query):
    response = find_best_match(query, DOCUMENTATION)
    if response:
        return response[1]
    return "Извините, я не нашел информацию по вашему запросу."

def send_keyboard(chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    search_button = types.KeyboardButton("❓ Задать вопрос")
    help_button = types.KeyboardButton("ℹ Помощь")
    feedback_button = types.KeyboardButton("💬 Обратная связь")
    keyboard.add(search_button)
    keyboard.add(help_button, feedback_button)
    bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def start(message):
    try:
        start_text = '''
        🤖 Привет! Я бот Bbuddy, который поможет тебе найти информацию из документации. Воспользуйся командой ❓ Задать вопрос.
        '''
        bot.send_message(message.chat.id, start_text)
        send_keyboard(message.chat.id)
    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, "Ошибка соединения с сервером API. Пожалуйста, попробуйте позже.")
        logging.error(f"Ошибка: {e}")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        logging.error(f"Ошибка: {e}")

@bot.message_handler(func=lambda message: message.text == "❓ Задать вопрос")
def search(message):
    try:
        search_text = '''
🔍 Напишите текстом свой вопрос. Например:
<b>Как открыть форму Пролонгация депозита на странице Размещение средств?</b>
        '''
        bot.send_message(message.chat.id, search_text, parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        logging.error(f"Ошибка: {e}")

@bot.message_handler(func=lambda message: message.text == "ℹ Помощь")
def help_text(message):
    help_text = '''
🚀 Привет! Я бот, который поможет тебе найти информацию из документации. Вот список доступных команд и функций:

/start - начать взаимодействие с ботом

❓ Задать вопрос - просто напишите свой запрос в чате, и я найду информацию для вас.

ℹ Помощь - получить список доступных команд и функций

💬 Обратная связь - оставить отзыв или предложение по работе бота
    Напишите "💬 Обратная связь" и отправьте ваше сообщение с отзывом или предложением.
    '''
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: message.text == "💬 Обратная связь")
def handle_feedback(message):
    user_id = message.from_user.id
    user_states[user_id] = 'waiting_for_feedback'
    msg = bot.send_message(message.chat.id, "📝 Вы можете оставить свой отзыв или предложение по работе бота. Отправьте ваше сообщение.")
    bot.register_next_step_handler(msg, send_feedback)
        
def send_feedback(message):
    user_id = message.from_user.id
    if user_states[user_id] == 'waiting_for_feedback':
        try:
            user_states[user_id] = ''
            feedback_text = f"{message.text}"
            save_feedback_to_file(message.from_user.username, feedback_text) # Добавьте эту строку
            bot.send_message(message.chat.id, "Спасибо за ваш отзыв! 😊")
            send_keyboard(message.chat.id)
        except Exception as e:
            bot.send_message(message.chat.id, "Произошла ошибка при отправке вашего отзыва. Пожалуйста, попробуйте позже.")
            logging.error(f"Ошибка: {e}")
            send_keyboard(message.chat.id)

def send_rating_menu(chat_id):
    rating_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bad_rating_button = types.KeyboardButton(ratingMenu[0])
    good_rating_button = types.KeyboardButton(ratingMenu[1])
    rating_keyboard.add(bad_rating_button, good_rating_button)
    bot.send_message(chat_id, "Оцените пожалуйста мою работу.", reply_markup=rating_keyboard)

@bot.message_handler(func=lambda message: message.text in ratingMenu)
def handle_rating(message):
    if message.text == ratingMenu[0]:
        bot.send_message(message.chat.id, "😔 Спасибо за вашу оценку. Мы постоянно работаем над улучшением качества поиска.")
        save_bad_answer(message.from_user.username, message.text) # Добавьте эту строку
    elif message.text == ratingMenu[1]:
        bot.send_message(message.chat.id, "😄 Спасибо за вашу оценку! Мы рады, что смогли помочь вам.")
    send_keyboard(message.chat.id)

# Modify the handle_text_message function
@bot.message_handler(func=lambda message: True)
def handle_text_message(message):
    try:
        query = message.text
        response = get_response(query)
        if response:
            bot.send_message(message.chat.id, response)
            send_rating_menu(message.chat.id) # Add this line
        else:
            bot.send_message(message.chat.id, "Извините, я не нашел информацию по вашему запросу. Попробуйте другой запрос или воспользуйтесь инлайн-поиском.")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, попробуйте снова.")
        logging.error(f"Ошибка: {e}")

# PHOTO VISION
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        image_id = message.photo[-1].file_id
        image_url = bot.get_file_url(image_id)
        image_bytes = download_image(image_url)
        if image_bytes:
            recognized_text = recognize_text_with_google_vision(image_bytes)
            if recognized_text:
                response = get_response(recognized_text)
                bot.send_message(message.chat.id, response)
            else:
                bot.send_message(message.chat.id, "На изображении не был распознан текст.")
        else:
            bot.send_message(message.chat.id, "Не удалось загрузить изображение. Пожалуйста, попробуйте снова.")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка при обработке изображения. Пожалуйста, попробуйте снова.")
        logging.error(f"Ошибка: {e}")
        print(f"Ошибка: {e}")

def download_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при скачивании изображения: {e}")
        return None
        
def recognize_text_with_google_vision(image_bytes):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        return texts[0].description
    else:
        return ""

def save_feedback_to_file(username, feedback):
    file_name = "feedback.csv"
    file_exists = os.path.isfile(file_name)

    with open(file_name, "a", newline="", encoding="utf-8") as file:
        fieldnames = ["Username", "Feedback"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        writer.writerow({"Username": username, "Feedback": feedback})

def save_bad_answer(username, question):
    file_name = "bad_answers.csv"
    file_exists = os.path.isfile(file_name)

    with open(file_name, "a", newline="", encoding="utf-8") as file:
        fieldnames = ["Username", "Question"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        writer.writerow({"Username": username, "Question": question})

if __name__ == "__main__":
    bot.polling(none_stop=True)
