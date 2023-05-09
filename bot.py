from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import sqlite3
import datetime
import threading
import random
import config
import time
from datetime import timedelta
from aiogram.utils.exceptions import BotBlocked
import asyncio



class Form(StatesGroup):
    image = State()
    caption = State()
    photo = State()


def get_name_channel(link):
    with sqlite3.connect("channels/Channels_for_jetons.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT name FROM Channels_for_jetons WHERE link = ?", [link])
        return cursor.fetchall()[0][0]

def get_id_channel(link):
    with sqlite3.connect("channels/Channels_for_jetons.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT id_channel FROM Channels_for_jetons WHERE link = ?", [link])
        return cursor.fetchall()[0][0]


async def on_startup(_):
    print("Бот онлайн")
    start_db_stats()
    print("БД со статами онлайн")
    start_db_channels()
    print("Бд с каналами онлайн")
    list_channels()
    print("Бд для добавлений и удалений каналов онлайн")


def start_db_stats():
    # Создаем базу данных и таблицу для хранения статистики
    global cursor, conn
    with sqlite3.connect('db_files/bot_stats.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('''
CREATE TABLE IF NOT EXISTS user_stats (
user_id INTEGER PRIMARY KEY,
luna INTEGER,
primogems INTEGER,
tokens INTEGER,
slots_count INTEGER,
shans_win_luna,
shans_win_primogem
)
''')


def start_db_channels():
    global conn_channels, cursor_channels
    with sqlite3.connect('db_files/channels.db', check_same_thread=False) as conn_channels:
        cursor_channels = conn_channels.cursor()
        cursor_channels.execute('''
CREATE TABLE IF NOT EXISTS channels (
user_id INTEGER,
channel_id INTEGER,
last_taked INTEGER
)
''')


def list_channels():
    global conn_list_channels, cursor_list_channels
    with sqlite3.connect('channels/Channels_for_jetons.db', check_same_thread=False) as conn_list_channels:
        cursor_list_channels = conn_list_channels.cursor()
        cursor_list_channels.execute('''
CREATE TABLE IF NOT EXISTS Channels_for_jetons (
name TEXT,
link TEXT, 
id_channel INTEGER UNIQUENESS
)
''')


# Создаем мьютекс для защиты базы данных
db_lock = threading.Lock()
user_tokens = {}

# Создаем словарь для хранения времени последнего использования команды для каждого пользователя
last_command_time = {}

# использование переменной
bot = Bot(config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Здесь config.channel_id устанавливается равным переменной channel_id


admin_ids = [629025283, 886070687]


# Инициализируем бота с помощью токена


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_command(msg: types.message):
    # Добавляем пользователя в базу данных, если его там еще нет
    user_id = msg.chat.id
    with db_lock:
        cursor.execute('SELECT user_id FROM user_stats WHERE user_id=?', (user_id,))
        print(cursor.fetchone())
        if cursor.fetchone() is None:
            cursor.execute('INSERT OR IGNORE INTO user_stats (user_id, luna, primogems, tokens, slots_count, shans_win_luna, shans_win_primogem) VALUES (?, 0, 0, 1, 0, 1, 1)',
                           (user_id,))
            conn.commit()

    # Отправляем приветственное сообщение и клавиатуру
    await msg.answer(
        'Как ты можешь использовать меня (краткая инструкция):\n\n- Нажми "Моя статистика 📈" чтобы узнать статистику своего аккаунта;\n- Нажми "Крутить Автомат! 🎰" чтобы испытать свою удачу!\n- Нажми "Получить жетоны 🎟" чтобы получить бесплатные жетоны;\n- Нажми "О боте 🤖" чтобы узнать информацию о Нашем боте;\n- Нажми на кнопку "Реклама 💰" чтобы узнать всю инофрмацию о рекламе в Нашем боте;\n- Нажми на кнопку "Поддержка 💻" чтобы обратиться в техническую поддержку бота.',
        reply_markup=get_main_keyboard())


async def process_start_command(msg: types.message):
    # Обрабатываем команду /start повторно
    await start_command(msg)


@dp.message_handler(commands=['astats'])
async def stats_command(msg: types.message):
    # Проверяем, является ли отправитель команды администратором
    if msg.chat.id not in admin_ids:
        await msg.answer('Команда доступна только администраторам')
        return

    with db_lock:
        cursor.execute('SELECT COUNT(*) FROM user_stats')
        count = cursor.fetchone()[0]

    await msg.answer(f'Количество зарегистрированных пользователей: {count}')


# добавление жетонов
@dp.message_handler(commands=['addtokens'])
async def add_tokens_command(msg: types.message):
    # Проверяем, является ли отправитель команды администратором
    if msg.chat.id not in admin_ids:
        await msg.answer('Команда доступна только администраторам')
        return
    print(msg.text)
    # Получаем аргументы команды
    args = msg.text.split()[1:]
    if len(args) != 2:
        await msg.answer('Использование: /addtokens <user_id> <amount>')
        return
    try:
        user_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        await msg.answer('Использование: /addtokens <user_id> <amount>')
        return

    # Обновляем количество жетонов пользователя в базе данных
    with db_lock:
        cursor.execute('UPDATE OR IGNORE user_stats SET tokens=tokens+? WHERE user_id=?', (amount, user_id))
        conn.commit()

    # Отправляем уведомление пользователю
    await msg.answer(f'Администратор добавил вам {amount} жетонов. Скорей крути рулетку!')
    # Отправляем уведомление администратору
    await msg.answer(f'У пользователя с ID {user_id} теперь {amount} жетонов')


@dp.message_handler(commands=["delete_channel"])
async def add_channels_for_bot(msg: types.message):
    if msg.chat.id not in admin_ids:
        await msg.answer('Команда доступна только администраторам')
        return
    else:
        try:
            with db_lock:
                mes = msg.text[16:]
                cursor_list_channels.execute("DELETE FROM Channels_for_jetons WHERE link = ?", [str(mes)])
                conn_list_channels.commit()
                await msg.answer(
                    f"Канал по ссылке {mes} был удален")
        except Exception:
            await msg.answer(
                "Чтобы удалить канал введите ссылку на канал:\n/delete_channel <ссылка>")
@dp.message_handler(commands=["add_channel"])
async def add_channels_for_bot(msg: types.message):
    if msg.chat.id not in admin_ids:
        await msg.answer('Команда доступна только администраторам')
        return
    else:
        try:
            with db_lock:
                mes = msg.text[13:]
                name, link, id_channel = mes.split("*")[0], mes.split("*")[1], mes.split("*", 2)[2]
                cursor_list_channels.execute("INSERT OR IGNORE INTO Channels_for_jetons(name, link, id_channel) VALUES(?, ?, ?)",
                                             [str(name), str(link), str(id_channel)])
                conn_list_channels.commit()
                await msg.answer(
                    f"Канал {name} (ссылка: {link}) был успешно добавлен!")
        except Exception:
            await msg.answer(
                "Чтобы добавить канал введите его имя и ссылку на него:\n/add_channel <имя канала>*<ссылка на канал>*<ID чата канала>")


# Обработчик команды для рассылки пользователям бота
@dp.message_handler(commands=["post"])
async def mailing_message(msg: types.message):
    if msg.chat.id not in admin_ids:
        return await msg.answer('Команда доступна только администраторам')
    else:
        try:
            caption = msg.text[6:]
            if str(caption) == "":
                return await msg.answer(
                "Не коректно введена команда. Образец команды:\n/post <текст для рассылки>\n\nПосле этого вам откроется меню, где вы сможете вставить гифку и фото или отправить как есть")
            Form.caption = str(caption)
            markup = InlineKeyboardMarkup(resize_keyboard=True, row_width=1)
            b1 = InlineKeyboardButton("Добавить фото и выложить", callback_data="add_photo")
            b2 = InlineKeyboardButton("Выложить", callback_data="public_post")
            b3 = InlineKeyboardButton("Отмена", callback_data="dont_public")
            markup.add(b1, b2, b3)
            await msg.answer(f"Ваш пост:\n{caption}", reply_markup=markup)
        except Exception:
            await msg.answer(
                "Не коректно введена команда. Образец команды:\n/post <текст для рассылки>\nПосле этого вам откроется меню, где вы сможете вставить гифку и фото или отправить как есть")


# Обработчик команды для отправки сообщения всем пользователям бота
@dp.message_handler(commands=['broadcast'])
async def broadcast_message(msg: types.message):
    # Проверяем, является ли отправитель команды администратором
    if msg.chat.id not in admin_ids:
        await msg.answer('Команда доступна только администраторам')
        return

    # Получаем текст сообщения, которое нужно отправить всем пользователям
    message_text = msg.text[11:]

    # Получаем список id всех пользователей бота
    with db_lock:
        cursor.execute('SELECT user_id FROM user_stats')
        user_ids = [row[0] for row in cursor.fetchall()]

    # Отправляем сообщение каждому пользователю бота
    for user_id in user_ids:
        await msg.answer(user_id, message_text)


@dp.callback_query_handler(text="dont_public")
async def dont_public_text(query: CallbackQuery):
    print("yea")
    await query.message.edit_text("Рассылка была отменена", reply_markup=None)


@dp.callback_query_handler(text='add_photo')
async def photo_add(query: CallbackQuery):
    await query.message.answer("Пришлите фото или гиф для поста")
    await Form.photo.set()


@dp.callback_query_handler(text="public_post")
async def public_post(query: CallbackQuery):
    with db_lock:
        cursor.execute("SELECT user_id FROM user_stats")
        records = cursor.fetchall()
        conn.commit()
    for i in records:
        try:
            await bot.send_message(chat_id=i[0], text=f"{str(Form.caption)}")
        except BotBlocked as E:
            print(f"Пользователей с id {i[0]} заблокировал бота, поэтому сообщение к нему не пришлется\n=====================================================\n{E}")
            continue
    return await query.message.answer("Бот успешно разослал сообщения!")

# Получить жетоны c канала
@dp.callback_query_handler()
async def channel_1(query: CallbackQuery):
    if query.data.split("|")[0] == "channel":
        # создает клавиатуру
        markup = InlineKeyboardMarkup(row_width=1)
        sub = InlineKeyboardButton(url=f"{query.data.split('|')[1]}", text="Подписаться")
        get = InlineKeyboardButton(text="Получить жетоны", callback_data=f"get_chan|{query.data.split('|')[2]}")
        markup.add(sub, get)
        # изменяет отправленное сообщение
        await query.message.edit_text(text='Держи, халявщик)', reply_markup=markup)
    elif query.data.split("|")[0] == "get_chan":
        # получает сегодняшнюю дату
        now = datetime.datetime.now()
        # получает user_id
        user_id = query.message.chat.id

        # Проверка на наличие записи об последнем получении жетона с указанного канала, если записи нет - создание новой.
        with db_lock:
            # берет запись с базы данных, в которой user_id и channel_id соответствуют указанным
            cursor_channels.execute('SELECT user_id FROM channels WHERE user_id=? AND channel_id=?',
                                    (user_id, int(query.data.split("|")[1])))
            # если таких записей нет, то:
            if cursor_channels.fetchone() is None:
                # создает новую запись, записывая user_id, channel_id и last_taked. последнее хранит какого числа были получены жетоны
                cursor_channels.execute(
                    f'INSERT INTO channels(user_id, channel_id, last_taked) VALUES(?, ?, 0)', [user_id, int(query.data.split("|")[1])])
            cursor_channels.execute("SELECT last_taked FROM channels WHERE user_id=? AND channel_id=?",
                                           (user_id, int(query.data.split("|")[1])))

            last = cursor_channels.fetchone()
            conn_channels.commit()
        # Проверка на то, сегодняшенго числа пользователь получил жетон или нет
        if last[0] == now.day:
            # создание клавиатуры
            markup = InlineKeyboardMarkup(row_width=1)
            get = InlineKeyboardButton(text="Назад", callback_data="channels")
            markup.add(get)
            # изменяет отправленное сообщение
            await query.message.edit_text(
                text='Похоже вы уже получили жетон от этого канала. Может стоит получить от других?',
                reply_markup=markup)
            return

        user_channel_status = await bot.get_chat_member(chat_id=int(query.data.split("|")[1]), user_id=user_id)

        # Проверка является человек подписанным на указанный канал
        if user_channel_status["status"] != 'left':
            with db_lock:
                # в бд обновляется запись, записывается сегодняшнее число(если сегодня 22 марта, запишется 22)
                cursor_channels.execute('UPDATE channels SET last_taked=? WHERE user_id=? AND channel_id=?',
                                        (now.day, int(user_id), int(query.data.split("|")[1])))
                conn_channels.commit()
                # в бд обновляется запись, добавляется один жетон
                cursor.execute(f'UPDATE user_stats SET tokens=tokens+?  WHERE user_id=?', (1, user_id))
                conn.commit()
            # создает клавиатуру
            markup = InlineKeyboardMarkup(row_width=1)
            get = InlineKeyboardButton(text="Назад", callback_data="channels")
            markup.add(get)
            # изменяет отправленное сообщение
            await query.message.edit_text(text='Жетон зачислен. Может стоит собрать еще один?', reply_markup=markup)
        else:
            # изменяет отправленное сообщение
            await bot.answer_callback_query(callback_query_id=query.id, show_alert=True,
                                            text="Сперва нужно подписаться!")
    elif query.data == 'channels':
        # создает клавиатуру
        with db_lock:
            cursor_list_channels.execute("SELECT link FROM Channels_for_jetons")
            records = cursor_list_channels.fetchall()
            conn_list_channels.commit()
            # создает клавиатуру
            markup = InlineKeyboardMarkup(row_width=3)
            for i in records:
                name = get_name_channel(i[0])
                id_channel = get_id_channel(i[0])
                button_channel = InlineKeyboardButton(text=f"{name}", callback_data=f"channel|{i[0]}|{id_channel}")
                markup.add(button_channel)
            conn_channels.commit()
        # изменяет отправленное сообщение
        await query.message.edit_text("Жетоны можно получить от следующих каналов:", reply_markup=markup)
    else:
        return


# Вывод всех доступных для получения жетонов каналов
@dp.callback_query_handler(text='channels')
async def get_channels(query: CallbackQuery):
    # генерация каналов из файла
    with db_lock:
        cursor_list_channels.execute("SELECT link FROM channels_name_and_link")
        records = cursor_list_channels.fetchall()
        conn_list_channels.commit()
        # создает клавиатуру
        markup = InlineKeyboardMarkup(row_width=3)
        for i in records:
            name = get_name_channel(i[0])
            id_channel = get_id_channel(i[0])
            button_channel = InlineKeyboardButton(text=f"{name}", callback_data=f"channel|{i[0]}|{id_channel}")
            markup.add(button_channel)
    # изменяет отправленное сообщение
    await query.message.edit_text("Жетоны можно получить от следующих каналов:", reply_markup=markup)


# Обработчик команды /mystats
@dp.message_handler(text=['Моя статистика 📈'])
async def my_stats_command(msg: types.message):
    user_id = msg.chat.id
    with db_lock:
        cursor.execute('SELECT luna, primogems, tokens, slots_count, shans_win_luna, shans_win_primogem FROM user_stats WHERE user_id=?', (user_id,))
        stats = cursor.fetchone()
    await msg.answer(f'<b>Статистика Вашего аккаунта:</b>\n' +
                     f'―――――――――――――――――\n' +
                     f'- ID аккаунта: {user_id}\n' +
                     f'- Луна: {stats[0]}\n' +
                     f'- Примогемы: {stats[1]}\n' +
                     f'- Количество жетонов: {stats[2]}\n' +
                     f'- Количество игр в "Лунный автомат": {stats[3]}\n' +  
                     f'\n' +      
                     f'<b>Вероятность победы:</b>\n' + 
                     f'―――――――――――――――――\n' + 
                     f'- Приз "Луна 30 дней": {round(stats[4], 1)}%\n' +  
                     f'- Приз "Примогемы 120 штук": {round(stats[5], 1)}%\n' +   
                     f'\n' +  
                     f'Чтобы узнать как увеличить шанс на победу: перейди в раздел бота <b>"О боте 🤖"</b>\n' +           
                     f'', parse_mode='HTML')

    # Формируем сообщение со статистикой и отправляем его

# Словарь для хранения времени последнего использования команды


@dp.message_handler(text=['Крутить Автомат! 🎰'])
async def play_slot_machine(msg: types.message):
    user_id = msg.chat.id

    # Проверяем, прошло ли достаточно времени с момента последнего использования команды
    if user_id in last_command_time and datetime.datetime.now() - last_command_time[user_id] < timedelta(seconds=10):
        await msg.answer('Данную команду можно использовать только раз в 10 секунд\nПожалуйста подождите!')
        return

    with db_lock:
        cursor.execute('SELECT tokens FROM user_stats WHERE user_id=?', (user_id,))
        tokens = cursor.fetchone()[0]
        if tokens < 1:
            await msg.answer('У вас недостаточно жетонов для игры в автомат')
            return
        cursor.execute('UPDATE user_stats SET tokens=tokens-1, slots_count=slots_count+1, shans_win_luna=shans_win_luna+0.1, shans_win_primogem=shans_win_primogem+0.2 WHERE user_id=?', (user_id,))
        conn.commit()

    # Выбираем случайное видео
    videos = ['win_luna.mp4', 'win_primogems.mp4', 'lose_1.mp4', 'lose_2.mp4', 'lose_3.mp4', 'lose_4.mp4']
    win_probability = 0.00001  # 0.001%
    if random.random() < win_probability:
        video = videos[0]
        with db_lock:
            cursor.execute('UPDATE user_stats SET luna=luna+1 WHERE user_id=?', (user_id,))
            conn.commit()
        message_text = f'Вы выиграли луну!'
    elif random.random() < win_probability:
        video = videos[1]
        with db_lock:
            cursor.execute('UPDATE user_stats SET primogems=primogems+10 WHERE user_id=?', (user_id,))
            conn.commit()
        message_text = f'Вы выиграли примогемы!'
    else:
        video = random.choice([videos[-1], videos[-2]])
        message_text = 'Я сожалею, но Вы проиграли 🥺\n\nПриходите завтра или можете получить ещё жетоны в разделе ' \
                       '"Получить жетоны 🎟".'

    # # Отправляем сообщение с видео и текстом
    with open(f"{video}", "rb") as video_file:
        video_message = await bot.send_video(user_id, caption='Крутим автомат! 🎰', video=video_file)

    # # Запоминаем время последнего использования команды
    last_command_time[user_id] = datetime.datetime.now()

    await asyncio.sleep(11)

    # # Удаляем сообщение с видео
    await bot.delete_message(chat_id=user_id, message_id=video_message.message_id)
    await msg.answer(message_text)


    # Отправляем сообщение с результатами игры

@dp.message_handler(text=['Получить жетоны 🎟'])
async def get_spins(msg: types.message):
    # создает клавиатуру
    with db_lock:
        cursor_list_channels.execute("SELECT link FROM Channels_for_jetons")
        records = cursor_list_channels.fetchall()
        conn_list_channels.commit()
        # создает клавиатуру
        markup = InlineKeyboardMarkup(row_width=3)
        for i in records:
            name = get_name_channel(i[0])
            id_channel = get_id_channel(i[0])
            button_channel = InlineKeyboardButton(text=f"{name}", callback_data=f"channel|{i[0]}|{id_channel}")
            markup.add(button_channel)
    # изменяет отправленное сообщение
    await msg.answer("Жетоны можно получить от следующих каналов:", reply_markup=markup)


@dp.message_handler(text=['О боте 🤖'])
async def get_inform(msg: types.message):
    await msg.answer("Информация о боте Лунный автомат:\n\nЛунный автомат - телеграм бот от канала Live Genshin Impact (@livegenshinimpact) в котором возможно бесплатно получить Луну или Примогемы крутя автомат (/start → Крутить Автомат! 🎰).\n\nЧтобы увеличить шанс на победу и получить Луну или Примогемы - играйте в автомат. За каждую игру в лунный автомат ваш шанс на получение Луны увеличивается на 0.1%, а шанс на получение Примогемов на 0.2%.\nШанс можно посмотретреть в разделе ''Моя статистика 📈'' (/start → ''Моя статистика 📈'').\n\nБот Лунный автомат постоянно оптимизируется и не стоит на месте!")


@dp.message_handler(text=['Реклама 💰'])
async def get_reklama(msg: types.message):
    keyboard = InlineKeyboardMarkup()
    text = "Реклама в боте"
    url = "https://t.me/+jTCKqLE6ADQ0NTQy"
    button = InlineKeyboardButton(text=text, url=url)
    keyboard.add(button)
    await msg.answer(
        "Информация о рекламе в боте Лунный автомат\n- Всю иноформацию вы можете найти перейдя по ссылке ниже.\n- В этой группе будет опубликована инофрмация о места в боте, также различные скидки, отзывы и так далее :)",
        reply_markup=keyboard)


@dp.message_handler(text=['Поддержка 💻'])
async def get_helme(msg: types.message):
    await msg.answer("Бот поддержки скоро будет добавлен!\nПока обращайтесь с вопросами/предложениями в личные сообщения: @sad_bane")


# Функция для получения основной клавиатуры
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Моя статистика 📈', 'Крутить Автомат! 🎰')
    keyboard.row('Получить жетоны 🎟', 'О боте 🤖')
    keyboard.row('Реклама 💰', 'Поддержка 💻')
    return keyboard

#Здесь происходит сама рассылка сообщений
@dp.message_handler(content_types=['photo', 'text', 'animation'], state=Form.photo)
async def photo_and_post(msg: types.Message, state: FSMContext):
    async with state.proxy() as data:
        with db_lock:
            cursor.execute("SELECT user_id FROM user_stats")
            records = cursor.fetchall()
            conn.commit()
        if msg.content_type == "photo":
            file_id = msg.photo[-1].file_id
            for i in records:
                try:
                    await bot.send_photo(chat_id=i[0], caption=str(Form.caption), photo=file_id)
                except BotBlocked as E:
                    print(
                        f"Пользователей с id {i[0]} заблокировал бота, поэтому сообщение к нему не пришлется\n=====================================================\n{E}")
                    continue
            await state.finish()
            return await msg.answer("Бот успешно разослал сообщения!")
        if msg.content_type == "animation":
            file_id = msg.animation.file_id
            for i in records:
                try:
                    await bot.send_animation(chat_id=i[0], caption=str(Form.caption), animation=file_id)
                except BotBlocked as E:
                    print(
                        f"Пользователей с id {i[0]} заблокировал бота, поэтому сообщение к нему не пришлется\n=====================================================\n{E}")
                    continue
            await state.finish()
            return await msg.answer("Бот успешно разослал сообщения!")
        else:
            await state.finish()
            return await msg.answer("Это не фото и не гиф")


# ЗАПУСКАЕМ БОТА
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
