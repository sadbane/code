import telebot
import sqlite3
import datetime
import threading
import random
import config
import time
import datetime
import json

user_tokens = {}

# Создаем словарь для хранения времени последнего использования команды для каждого пользователя
last_command_time = {}

# использование переменной
bot = telebot.TeleBot(config.TOKEN)

# Здесь config.channel_id устанавливается равным переменной channel_id
channel_id = config.channel_id

admin_ids = [629025283, 886070687]

# Инициализируем бота с помощью токена


# Создаем базу данных и таблицу для хранения статистики
conn = sqlite3.connect('bot_stats.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        luna INTEGER,
        primogems INTEGER,
        tokens INTEGER
    )
''')
conn.commit()

# Создаем мьютекс для защиты базы данных
db_lock = threading.Lock()

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    # Добавляем пользователя в базу данных, если его там еще нет
    user_id = message.chat.id
    with db_lock:
        cursor.execute('SELECT user_id FROM user_stats WHERE user_id=?', (user_id,))
        if cursor.fetchone() is None:
            cursor.execute('INSERT INTO user_stats (user_id, luna, primogems, tokens) VALUES (?, 0, 0, 1)', (user_id,))
            conn.commit()

    # Отправляем приветственное сообщение и клавиатуру
    bot.send_message(user_id, 'Как ты можешь использовать меня (краткая инструкция):\n\n- Нажми "Моя статистика 📈" чтобы узнать статистику своего аккаунта;\n- Нажми "Крутить Автомат! 🎰" чтобы испытать свою удачу!', reply_markup=get_main_keyboard())

def process_start_command(message):
    # Обрабатываем команду /start повторно
    start_command(message)


# Обработчик команды /mystats
@bot.message_handler(func=lambda message: message.text.lower() == 'моя статистика 📈')
def my_stats_command(message):
    user_id = message.chat.id
    with db_lock:
        cursor.execute('SELECT luna, primogems, tokens FROM user_stats WHERE user_id=?', (user_id,))
        stats = cursor.fetchone()

    # Формируем сообщение со статистикой и отправляем его
    message = f'Статистика Вашего аккаунта:\n'
    message += f'――――――――――――――\n'
    message += f'- ID аккаунта: {user_id}\n'
    message += f'- Луна: {stats[0]}\n'
    message += f'- Примогемы: {stats[1]}\n'
    message += f'- Количество жетонов: {stats[2]}\n'
    message += f'――――――――――――――'
    bot.send_message(user_id, message)


from datetime import datetime, timedelta

# Словарь для хранения времени последнего использования команды
last_command_time = {}


@bot.message_handler(func=lambda message: message.text == 'Крутить Автомат! 🎰')
def play_slot_machine(message):
    user_id = message.chat.id

    # Проверяем, прошло ли достаточно времени с момента последнего использования команды
    if user_id in last_command_time and datetime.now() - last_command_time[user_id] < timedelta(seconds=10):
        bot.send_message(user_id, 'Данную команду можно использовать только раз в 10 секунд\nПожалуйста подождите!')
        return

    with db_lock:
        cursor.execute('SELECT tokens FROM user_stats WHERE user_id=?', (user_id,))
        tokens = cursor.fetchone()[0]
        if tokens < 1:
            bot.send_message(user_id, 'У вас недостаточно жетонов для игры в автомат')
            return
        cursor.execute('UPDATE user_stats SET tokens=tokens-1 WHERE user_id=?', (user_id,))
        conn.commit()

    # Выбираем случайную гифку
    gifs = ['win_luna.gif.gif', 'win_primogems.gif.gif', 'lose_1.gif.gif', 'lose_2.gif.gif', 'lose_3.gif.gif', 'lose_4.gif.gif']
    win_probability = 0.00001 # 0.001%
    if random.random() < win_probability:
        animation = gifs[0]
        with db_lock:
            cursor.execute('UPDATE user_stats SET luna=luna+1 WHERE user_id=?', (user_id,))
            conn.commit()
        message_text = f'Вы выиграли луну!'
    elif random.random() < win_probability:
        animation = gifs[1]
        with db_lock:
            cursor.execute('UPDATE user_stats SET primogems=primogems+10 WHERE user_id=?', (user_id,))
            conn.commit()
        message_text = f'Вы выиграли примогемы!'
    else:
        animation = random.choice(gifs[2:])
        message_text = 'Я сожалею, но Вы проиграли 🥺\n\nПриходите завтра или можете получить ещё жетоны в разделе "Получить жетоны 🎟"'

    # Отправляем сообщение с гифкой и текстом
    animation_message = bot.send_animation(user_id, open(animation, 'rb'), caption='Крутим автомат! 🎰')

    # Запоминаем время последнего использования команды
    last_command_time[user_id] = datetime.now()

    # Ждем 10 секунд
    time.sleep(10)

    # Удаляем сообщение с гифкой
    bot.delete_message(user_id, animation_message.message_id)

    # Отправляем сообщение с результатами игры
    bot.send_message(user_id, message_text)

@bot.message_handler(commands=['astats'])
def stats_command(message):
    # Проверяем, является ли отправитель команды администратором
    if message.chat.id not in admin_ids:
        bot.send_message(message.chat.id, 'Команда доступна только администраторам')
        return

    with db_lock:
        cursor.execute('SELECT COUNT(*) FROM user_stats')
        count = cursor.fetchone()[0]

    bot.send_message(message.chat.id, f'Количество зарегистрированных пользователей: {count}')
    
# добавление жетонов
@bot.message_handler(commands=['addtokens'])
def add_tokens_command(message):
    # Проверяем, является ли отправитель команды администратором
    if message.chat.id not in admin_ids:
        bot.send_message(message.chat.id, 'Команда доступна только администраторам')
        return

    # Получаем аргументы команды
    args = message.text.split()[1:]
    if len(args) != 2:
        bot.send_message(message.chat.id, 'Использование: /addtokens <user_id> <amount>')
        return
    try:
        user_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        bot.send_message(message.chat.id, 'Использование: /addtokens <user_id> <amount>')
        return

    # Обновляем количество жетонов пользователя в базе данных
    with db_lock:
        cursor.execute('UPDATE user_stats SET tokens=tokens+? WHERE user_id=?', (amount, user_id))
        conn.commit()

    # Получаем chat_id пользователя
    user_chat_id = get_user_chat_id(user_id)
    # Отправляем уведомление пользователю
    bot.send_message(user_chat_id, f'Администратор добавил вам {amount} жетонов. Скорей крути рулетку!')
    # Отправляем уведомление администратору
    bot.send_message(message.chat.id, f'У пользователя с ID {user_id} теперь {amount} жетонов')


# Обработчик команды для отправки сообщения всем пользователям бота
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    # Проверяем, является ли отправитель команды администратором
    if message.chat.id not in admin_ids:
        bot.send_message(message.chat.id, 'Команда доступна только администраторам')
        return

    # Получаем текст сообщения, которое нужно отправить всем пользователям
    message_text = message.text[11:]

    # Получаем список id всех пользователей бота
    with db_lock:
        cursor.execute('SELECT user_id FROM user_stats')
        user_ids = [row[0] for row in cursor.fetchall()]

    # Отправляем сообщение каждому пользователю бота
    for user_id in user_ids:
        bot.send_message(user_id, message_text)

# Функция для получения клавиатуры со списком каналов
def get_channels_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        keyboard.add(telebot.types.InlineKeyboardButton(text=channel, callback_data=f'channel_{channel}'))
    return keyboard


channels = [
    {'name': 'Live Genshin Impact', 'username': '@LiveGenshinImpact'},
    {'name': 'Kanal2', 'username': '@onlinegenshinimpact'},
    {'name': 'svegak', 'username': '@ccddcssdc'}
]


# Обработчик команды "Получить жетоны"
@bot.message_handler(func=lambda message: message.text == 'Получить жетоны 💰')
def handle_get_tokens(message):
    channels_keyboard = get_channels_keyboard()
    bot.send_message(message.chat.id, 'Выберите канал:', reply_markup=channels_keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('channel_'))
def handle_channel(call):
    channel_name = call.data.split('_')[1]
    for channel in channels:
        if channel['username'] == channel_name:
            channel_title = channel['name']
            break

    # Проверяем, подписан ли пользователь на канал
    chat_member = bot.get_chat_member(channel_name, call.message.chat.id)
    if chat_member.status == 'member' or chat_member.status == 'creator':
        subscribed = True
    else:
        subscribed = False

    channel_menu_keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    if subscribed:
        check_subscription_button = telebot.types.InlineKeyboardButton(text='Проверить подписку ✅', callback_data='check_subscription')
    else:
        subscribe_button = telebot.types.InlineKeyboardButton(text='Подписаться 🔔', url='https://t.me/' + channel_name[1:])
        check_subscription_button = telebot.types.InlineKeyboardButton(text='Проверить подписку ❌', callback_data='check_subscription')
        channel_menu_keyboard.add(subscribe_button)
    back_button = telebot.types.InlineKeyboardButton(text='Назад', callback_data='back')
    channel_menu_keyboard.add(check_subscription_button, back_button)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f'Вы выбрали канал {channel_title}. Что вы хотите сделать?', reply_markup=channel_menu_keyboard)


# Обработчик кнопки "Назад" в меню канала
@bot.callback_query_handler(func=lambda call: call.data == 'back')
def handle_back_button(call):
    channels_keyboard = get_channels_keyboard()
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text='Выберите канал:', reply_markup=channels_keyboard)

# Функция для получения основной клавиатуры
def get_main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Моя статистика 📈', 'Крутить Автомат! 🎰')
    keyboard.row('Подпишись на каналы')
    return keyboard



# ДЛЯ ОБРАТНОГО СМС
def get_user_chat_id(user_id):
    # Получаем объект пользователя по его user_id
    user = bot.get_chat_member(config.channel_name, user_id).user
    # Возвращаем id пользователя
    return user.id

# Запускаем бота
bot.polling()