import json
import logging
import os
import re
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo
from datetime import date, datetime, timedelta
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import csv
from formulas import formula1, formula2, formula3, formula4, generate_plot, get_time, generate_ph_plot, get_percent, \
    get_recommendation
from io import BytesIO
from aiogram.utils.exceptions import BotBlocked

cards = {}
API_TOKEN = os.getenv('API_TOKEN')
ADMINS = os.getenv('ADMINS').replace(' ', '').split(',')
DOCTORS = os.getenv('DOCTORS').replace(' ', '').split(',')

for i, a in enumerate(ADMINS):
    ADMINS[i] = int(a)

for i, d in enumerate(DOCTORS):
    DOCTORS[i] = int(d)

API_URL = os.getenv('API_URL')
ADMIN_LIST_LIMIT = int(os.getenv('ADMIN_LIST_LIMIT'))

with open('cards.csv') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if not i:
            continue
        n = row[0]
        cards[n] = {
            "id": n,
            "bones": re.findall(r'([CTLS]\d{1,2})', row[1].replace(' ', '')),
            "count": row[2],
            "power": row[3],
            "name": row[4],
            "desc": row[5],
            "EOB": re.findall(r'([А-Я]{2})', row[6].replace(' ', '')),
            "REC_RU": row[-2],
            "REC_EN": row[-1],
        }

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


class Request(StatesGroup):
    tariff = State()
    accept = State()


class Messages(StatesGroup):
    text = State()


class Cast(StatesGroup):
    text = State()


class Tariff(StatesGroup):
    tariff = State()
    amount = State()


async def reset_state(obj):
    state = dp.current_state(user=obj.from_user.id)
    if state:
        await state.finish()


async def setup_bot_commands(args):
    # data = ['1', '2', '3', '4', '5']
    # selected_cards = []
    # for key in data:
    #     selected_cards.append(cards.get(key, {}))
    # img = await get_plot(ADMINS[0])
    # await bot.send_photo(ADMINS[0], photo=img)
    bot_commands = [
        BotCommand(command="/about", description="О проекте"),
        BotCommand(command="/balance", description="Информация о подписке"),
        BotCommand(command="/requests", description="Заявки на пополнение"),
    ]
    await bot.set_my_commands(bot_commands)


@dp.message_handler(commands=['start'], state="*")
async def start(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    if state:
        await state.finish()

    data = {
        'telegram_id': message.from_user.id,
        'name': message.from_user.first_name,
        'username': message.from_user.username
    }
    async with aiohttp.ClientSession(trust_env=True) as session:
        await session.post(f'{API_URL}/registration/', data=data)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton(text="Пройти тест", web_app=WebAppInfo(url='https://bagi4-source.github.io/bot/')))

    await message.answer(f"Привет, {message.from_user.first_name}! Мы рады тебя видеть)", reply_markup=keyboard)


@dp.callback_query_handler(text='admin', state="*")
async def admin(query: types.CallbackQuery):
    await reset_state(query)

    if query.from_user.id not in ADMINS:
        return await query.message.edit_text(f"Неизвестная команда!")

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Заявки", callback_data=f"admin_requests"),
    ).row(
        InlineKeyboardButton(text="О нас", callback_data=f"admin_about"),
        InlineKeyboardButton(text="Реквизиты", callback_data=f"admin_payments"),
    ).row(
        InlineKeyboardButton(text="Рассылка", callback_data=f"admin_cast"),
        InlineKeyboardButton(text="Тарифы", callback_data=f"admin_tariffs"),
    )

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/registration/', params={'limit': 1}) as r:
            if r.ok:
                data = await r.json()
                return await query.message.edit_text(f"Админ-панель:\n"
                                                     f"Ботом пользуется ({data.get('count', 0)}) человек",
                                                     reply_markup=keyboard)
    return await query.message.edit_text(f"Что-то пошло не так!")


@dp.message_handler(commands=['admin'], state="*")
async def admin(message: types.Message):
    await reset_state(message)

    if message.from_user.id not in ADMINS:
        return await message.answer(f"Неизвестная команда!")

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Заявки", callback_data=f"admin_requests"),
    ).row(
        InlineKeyboardButton(text="О нас", callback_data=f"admin_about"),
        InlineKeyboardButton(text="Реквизиты", callback_data=f"admin_payments"),
    ).row(
        InlineKeyboardButton(text="Рассылка", callback_data=f"admin_cast"),
        InlineKeyboardButton(text="Тарифы", callback_data=f"admin_tariffs"),
    )

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/registration/', params={'limit': 1}) as r:
            if r.ok:
                data = await r.json()
                return await message.answer(f"Админ-панель:\n"
                                            f"Ботом пользуется ({data.get('count', 0)}) человек",
                                            reply_markup=keyboard)
    return await message.answer(f"Что-то пошло не так!")


@dp.callback_query_handler(text='admin_cast', state="*")
async def admin_about(query: types.CallbackQuery):
    await reset_state(query)
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=f"admin"),
    )
    await query.message.edit_text(f"Введите пост для рассылки", reply_markup=keyboard)
    await Cast.text.set()


@dp.callback_query_handler(text='admin_tariffs', state="*")
async def admin_tariffs(query: types.CallbackQuery):
    await reset_state(query)

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/tariffs/',
                               params={'limit': 20, 'ordering': 'days'}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    result = result.get('results', [{}])
                    for item in result:
                        pk = item.get('pk')
                        keyboard = InlineKeyboardMarkup()
                        keyboard.row(
                            InlineKeyboardButton(text="❌удалить", callback_data=f"delete_tariff_{pk}"),
                        )
                        await query.message.answer(f"{item.get('days')} - {item.get('amount')}₽", reply_markup=keyboard)

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=f"admin"),
        InlineKeyboardButton(text="Добавить", callback_data=f"add_tariff"),
    )
    await query.message.answer(f"Добавить тариф?", reply_markup=keyboard)


@dp.callback_query_handler(text_contains='add_tariff', state="*")
async def add_tariff(query: types.CallbackQuery):
    await reset_state(query)
    await Tariff.tariff.set()
    await query.message.edit_text(f"Введите количество дней")


@dp.message_handler(state=[Tariff.tariff])
async def add_tariff(message: types.Message):
    text = re.sub(r'\D', '', message.text)
    if not text:
        return await message.answer(f"Неправильно ввели данные")

    await Tariff.amount.set()
    state = dp.current_state(user=message.from_user.id)
    async with state.proxy() as data:
        data['days'] = int(text)
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=f"admin"),
    )
    await message.answer(f"Теперь введите сумму оплаты (₽)", reply_markup=keyboard)


@dp.message_handler(state=[Tariff.amount])
async def add_tariff(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    async with state.proxy() as data:
        text = re.sub(r'\D', '', message.text)
        if not text:
            return await message.answer(f"Неправильно ввели данные")
        amount = int(text)
        days = data.get('days')

    async with aiohttp.ClientSession(trust_env=True) as session:
        payload = {
            'days': days,
            'amount': amount
        }
        await session.post(f'{API_URL}/tariffs/', data=payload)
    await message.answer(f"Тариф ({days} - {amount}₽) успешно добавлен")
    await reset_state(message)


@dp.callback_query_handler(text_contains='delete_tariff_', state="*")
async def delete_tariff(query: types.CallbackQuery):
    await reset_state(query)
    pk = query.data.replace("delete_tariff_", "")
    async with aiohttp.ClientSession(trust_env=True) as session:
        await session.delete(f'{API_URL}/tariffs/{pk}')
    await query.message.delete()


@dp.message_handler(state=[Cast.text], content_types=['text'])
async def admin_cast(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    async with state.proxy() as data:
        data['text'] = message.text

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=f"admin"),
        InlineKeyboardButton(text="Подтвердить", callback_data=f"admin_accept_cast"),
    )
    await message.answer(f"Подтвердить рассылку?", reply_markup=keyboard)


@dp.message_handler(state=[Cast.text], content_types=['photo'])
async def admin_cast(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    async with state.proxy() as data:
        data['text'] = message.caption
        data['photo'] = message.photo[-1].file_id

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=f"admin"),
        InlineKeyboardButton(text="Подтвердить", callback_data=f"admin_accept_cast"),
    )
    await message.answer(f"Подтвердить рассылку?", reply_markup=keyboard)


async def cast(url, text, photo=None):
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(url, params={'limit': 1}) as r:
            if r.ok:
                data = await r.json()
                next_url = data.get('next')
                results = data.get('results')
                for user in results:
                    telegram_id = user.get('telegram_id')
                    if photo:
                        try:
                            await bot.send_photo(telegram_id, photo=photo, caption=text)
                        except BotBlocked:
                            pass
                    else:
                        try:
                            await bot.send_message(telegram_id, text)
                        except BotBlocked:
                            pass
                if next_url:
                    await cast(next_url, text)


@dp.callback_query_handler(text='admin_accept_cast', state=[Cast.text])
async def admin_accept_cast(query: types.CallbackQuery):
    state = dp.current_state(user=query.from_user.id)
    async with state.proxy() as data:
        text = data.get('text')
        photo = data.get('photo')

    await reset_state(query)
    await query.message.answer(f"Рассылка запущена")
    await cast(f'{API_URL}/registration/', text, photo)


@dp.callback_query_handler(text='admin_about', state="*")
async def admin_about(query: types.CallbackQuery):
    await reset_state(query)

    async with aiohttp.ClientSession(trust_env=True) as session:
        keyboard = InlineKeyboardMarkup()
        async with session.get(f'{API_URL}/messages/',
                               params={'tag': 'about'}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    result = result.get('results', [])
                    if result:
                        result = result[0]
                        text = result.get('text', '')
                        tag = result.get('tag', '')
                        pk = result.get('pk', 0)
                        keyboard.row(
                            InlineKeyboardButton(text="Назад", callback_data=f"admin"),
                            InlineKeyboardButton(text="Изменить", callback_data=f"admin_edit_message_{pk}::{tag}"),
                        )
                        return await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                    keyboard.row(
                        InlineKeyboardButton(text="Назад", callback_data=f"admin"),
                        InlineKeyboardButton(text="Изменить", callback_data=f"admin_add_message_about"),
                    )
                    return await query.message.edit_text('Текста нет', reply_markup=keyboard)


@dp.callback_query_handler(text='admin_payments', state="*")
async def admin_payments(query: types.CallbackQuery):
    await reset_state(query)

    async with aiohttp.ClientSession(trust_env=True) as session:
        keyboard = InlineKeyboardMarkup()
        async with session.get(f'{API_URL}/messages/',
                               params={'tag': 'payments'}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    result = result.get('results', [])
                    if result:
                        result = result[0]
                        text = result.get('text', '')
                        tag = result.get('tag', '')
                        pk = result.get('pk', 0)
                        keyboard.row(
                            InlineKeyboardButton(text="Назад", callback_data=f"admin"),
                            InlineKeyboardButton(text="Изменить", callback_data=f"admin_edit_message_{pk}::{tag}"),
                        )
                        return await query.message.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
                    keyboard.row(
                        InlineKeyboardButton(text="Назад", callback_data=f"admin"),
                        InlineKeyboardButton(text="Изменить", callback_data=f"admin_add_message_payments"),
                    )
                    return await query.message.edit_text('Текста нет', reply_markup=keyboard)


@dp.callback_query_handler(text_contains='admin_add_message_', state="*")
async def admin_add_message(query: types.CallbackQuery):
    tag = query.data.replace("admin_add_message_", "")
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=f"admin_{tag}"),
    )
    await Messages.text.set()

    state = dp.current_state(user=query.from_user.id)
    async with state.proxy() as data:
        data['tag'] = tag

    await query.message.edit_text('Введите новый текст', reply_markup=keyboard)


@dp.callback_query_handler(text_contains='admin_edit_message_', state="*")
async def admin_edit_message(query: types.CallbackQuery):
    params = query.data.replace("admin_edit_message_", "")
    pk, tag = tuple(params.split('::'))
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=f"admin_{tag}"),
    )
    await Messages.text.set()

    state = dp.current_state(user=query.from_user.id)
    async with state.proxy() as data:
        data['pk'] = pk
        data['tag'] = tag

    await query.message.edit_text('Введите новый текст', reply_markup=keyboard)


@dp.message_handler(state=[Messages.text])
async def admin_put_message(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    async with state.proxy() as data:
        pk = data.get('pk')
        tag = data.get('tag')

    async with aiohttp.ClientSession(trust_env=True) as session:
        payload = {
            'tag': tag,
            'text': message.text
        }
        if pk:
            await session.put(f'{API_URL}/messages/{pk}/', data=payload)
        else:
            await session.post(f'{API_URL}/messages/', data=payload)
        await message.delete()
        await admin(message)


@dp.callback_query_handler(text='admin_requests', state="*")
async def admin_requests(query: types.CallbackQuery):
    page = 0
    offset = page * ADMIN_LIST_LIMIT
    await reset_state(query)

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(
                f'{API_URL}/admin-request/?limit={ADMIN_LIST_LIMIT}&offset={offset}') as r:
            if r.ok:
                result = await r.json()
                if result:
                    count = result.get('count', 0)
                    result = result.get('results', [{}])
                    for x in result:
                        keyboard = InlineKeyboardMarkup()
                        keyboard.row(
                            InlineKeyboardButton(text="❌", callback_data=f"admin_requests_discard_{x.get('pk')}"),
                            InlineKeyboardButton(text="✅", callback_data=f"admin_requests_accept_{x.get('pk')}"),
                        )
                        text = f"ID заявки: #{x.get('pk')}\n" \
                               f"Сумма: {x.get('amount')}₽\n" \
                               f"Тариф: {x.get('tariff')} дней\n" \
                               f"Время создания: {get_time(x.get('create_time')).strftime('%H:%M %d-%m-%Y')}"
                        await query.message.answer(text, reply_markup=keyboard)

                    other = max(0, count - (page + 1) * ADMIN_LIST_LIMIT)
                    keyboard = InlineKeyboardMarkup()
                    buttons = []
                    if other:
                        buttons.append(InlineKeyboardButton(text=f"Показать еще ({other})",
                                                            callback_data=f"admin_requests_new_{page + 1}"))
                    buttons.append(InlineKeyboardButton(text="Обновить", callback_data="admin_requests"))
                    keyboard.row(*buttons)
                    keyboard.row(InlineKeyboardButton(text="Назад", callback_data=f"admin"))
                    await query.message.delete()
                    return await query.message.answer(f"Всего заявок {count}", reply_markup=keyboard)
    return await query.message.edit_text("Заявки не найдены!")


@dp.callback_query_handler(text_contains='admin_requests_new_', state="*")
async def admin_requests_accept(query: types.CallbackQuery):
    page = query.data.replace("admin_requests_new_", "")
    page = int(page)
    offset = page * ADMIN_LIST_LIMIT

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(
                f'{API_URL}/admin-request/?limit={ADMIN_LIST_LIMIT}&offset={offset}') as r:
            if r.ok:
                result = await r.json()
                if result:
                    count = result.get('count', 0)
                    result = result.get('results', [{}])
                    for x in result:
                        keyboard = InlineKeyboardMarkup()
                        keyboard.row(
                            InlineKeyboardButton(text="❌", callback_data=f"admin_requests_discard_{x.get('pk')}"),
                            InlineKeyboardButton(text="✅", callback_data=f"admin_requests_accept_{x.get('pk')}"),
                        )
                        text = f"ID заявки: #{x.get('pk')}\n" \
                               f"Сумма: {x.get('amount')}\n" \
                               f"Время создания: {get_time(x.get('create_time')).strftime('%H:%M %d-%m-%Y')}"
                        await query.message.answer(text, reply_markup=keyboard)

                    other = max(0, count - (page + 1) * ADMIN_LIST_LIMIT)
                    keyboard = InlineKeyboardMarkup()
                    buttons = []
                    if other:
                        buttons.append(InlineKeyboardButton(text=f"Показать еще ({other})",
                                                            callback_data=f"admin_requests_new_{page + 1}"))
                    buttons.append(InlineKeyboardButton(text="Обновить", callback_data="admin_requests"))
                    await query.message.delete()
                    return await query.message.answer(f"Всего заявок {count}", reply_markup=keyboard)
    return await query.message.edit_text("Заявки не найдены!")


@dp.callback_query_handler(text_contains='admin_requests_accept_', state="*")
async def admin_requests_accept(query: types.CallbackQuery):
    await query.message.delete()

    pk = query.data.replace("admin_requests_accept_", "")
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/admin-request/{pk}/') as r:
            if r.ok:
                data = await r.json()
                payload = {
                    'telegram_id': data.get('telegram_id'),
                    'amount': data.get('amount'),
                    'tariff': data.get('tariff'),
                    'status': True,
                    'viewed': True
                }
                await session.put(f'{API_URL}/admin-request/{pk}/', data=payload)
                await bot.send_message(
                    data.get('telegram_id'),
                    f"Ваша заявка #{pk} подтверждена!\n"
                    f"Сумма: {data.get('amount')}₽\n"
                    f"Тариф: {data.get('tariff')} дней\n"
                )


@dp.callback_query_handler(text_contains='admin_requests_discard_', state="*")
async def admin_requests_discard(query: types.CallbackQuery):
    await query.message.delete()

    pk = query.data.replace("admin_requests_discard_", "")
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/admin-request/{pk}/') as r:
            if r.ok:
                data = await r.json()
                payload = {
                    'telegram_id': data.get('telegram_id'),
                    'amount': data.get('amount'),
                    'tariff': data.get('tariff'),
                    'status': False,
                    'viewed': True
                }
                await session.put(f'{API_URL}/admin-request/{pk}/', data=payload)
                await bot.send_message(
                    data.get('telegram_id'),
                    f"Ваша заявка #{pk} отклонена!\n"
                    f"Сумма: {data.get('amount')}₽\n"
                    f"Тариф: {data.get('tariff')} дней\n"
                )


@dp.message_handler(state='*', commands=['balance'])
async def balance(message: types.Message):
    await reset_state(message)

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        text="Продлить подписку",
        callback_data=f"add_request")
    )
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/registration/',
                               params={'telegram_id': message.from_user.id}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    result = result.get('results', [{}])
                    result = result[0]
                    subscription = result.get('subscription_end')
                    return await message.answer(
                        f"Дата окончания подписки: {result.get('subscription_end')}",
                        reply_markup=keyboard
                    )
    return await message.answer("Пользователь не найден!")


@dp.message_handler(state='*', commands=['about'])
async def about(message: types.Message):
    await reset_state(message)

    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/messages/',
                               params={'tag': 'about'}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    result = result.get('results', [{}])
                    result = result[0]
                    text = result.get('text', '')
                    return await message.answer(text, parse_mode="HTML")
    return await message.answer("Пользователь не найден!")


def get_status(status, viewed):
    if status:
        return 'Выполнено'
    if viewed:
        return 'Отклонена'
    return 'В обработке'


@dp.message_handler(commands=['requests'], state="*")
async def requests(message: types.Message):
    await reset_state(message)
    page = 0
    offset = ADMIN_LIST_LIMIT * page
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/request/',
                               params={'telegram_id': message.from_user.id,
                                       'limit': ADMIN_LIST_LIMIT,
                                       'offset': offset,
                                       'ordering': '-pk'}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    count = result.get('count', 0) - (page + 1) * ADMIN_LIST_LIMIT
                    count = max(count, 0)
                    result = result.get('results', [{}])
                    text = "\n\n".join([
                        f"ID заявки: #{x.get('pk')}\n"
                        f"Сумма: {x.get('amount')}\n"
                        f"Статус: {get_status(x.get('status'), x.get('viewed'))}\n"
                        f"Время создания: {get_time(x.get('create_time')).strftime('%H:%M %d-%m-%Y')}"
                        for x in result])
                    keyboard = InlineKeyboardMarkup()
                    buttons = []
                    if offset:
                        buttons.append(
                            InlineKeyboardButton(text=f"Назад ({offset})", callback_data=f"requests_next_{page - 1}"))
                    if count:
                        buttons.append(
                            InlineKeyboardButton(text=f"Далее ({count})", callback_data=f"requests_next_{page + 1}"))

                    keyboard.row(*buttons)
                    return await message.answer(text, reply_markup=keyboard)
    return await message.answer("Заявки не найдены!")


@dp.callback_query_handler(text_contains="requests_next_", state="*")
async def requests_next(query: types.CallbackQuery):
    page = query.data.replace('requests_next_', '')
    page = int(page)
    if page < 0:
        return
    offset = ADMIN_LIST_LIMIT * page
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/request/',
                               params={'telegram_id': query.from_user.id,
                                       'limit': ADMIN_LIST_LIMIT,
                                       'offset': offset,
                                       'ordering': '-pk'}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    count = result.get('count', 0) - (page + 1) * ADMIN_LIST_LIMIT
                    count = max(count, 0)
                    result = result.get('results', [{}])
                    text = "\n\n".join([
                        f"ID заявки: #{x.get('pk')}\n"
                        f"Сумма: {x.get('amount')}\n"
                        f"Статус: {get_status(x.get('status'), x.get('viewed'))}\n"
                        f"Время создания: {get_time(x.get('create_time')).strftime('%H:%M %d-%m-%Y')}"
                        for x in result])
                    keyboard = InlineKeyboardMarkup()
                    buttons = []
                    if offset:
                        buttons.append(
                            InlineKeyboardButton(text=f"Назад ({offset})", callback_data=f"requests_next_{page - 1}"))
                    if count:
                        buttons.append(
                            InlineKeyboardButton(text=f"Далее ({count})", callback_data=f"requests_next_{page + 1}"))

                    keyboard.row(*buttons)
                    return await query.message.edit_text(text, reply_markup=keyboard)


async def check_sub(message: types.Message):
    await reset_state(message)
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/registration/',
                               params={'telegram_id': message.from_user.id}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    result = result.get('results', [{}])
                    result = result[0]
                    if date.today() >= get_time(result.get('subscription_end', '2000-01-01T08:18:26')).date():
                        return await message.answer("Необходимо продлить подписку!")
    return await message.answer("Пользователь не найден!")


@dp.message_handler(commands=['request'])
@dp.callback_query_handler(text="add_request", state="*")
async def add_request(query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()

    buttons = []
    tariffs = {}
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/tariffs/',
                               params={'limit': 20, 'ordering': 'days'}) as r:
            if r.ok:
                result = await r.json()
                if result:
                    result = result.get('results', [{}])
                    for item in result:
                        tariffs[item.get('days')] = item.get('amount')

    for tariff_key, tariff_price in tariffs.items():
        buttons.append(InlineKeyboardButton(
            text=f"{tariff_key} дней ({tariff_price}₽)",
            callback_data=f"tariff_{tariff_key}::{tariff_price}"
        ))
    for i in range(len(buttons) // 2 + 1):
        keyboard.row(*buttons[i * 2:(i + 1) * 2])

    await query.message.edit_text(f"Выбери тариф из следующего списка:", reply_markup=keyboard)
    await Request.tariff.set()


@dp.callback_query_handler(text_contains="tariff_", state=Request.tariff)
async def tariffs(query: types.CallbackQuery):
    text = ''
    tariff, amount = tuple(query.data.replace("tariff_", "").split("::"))

    state = dp.current_state(user=query.from_user.id)
    async with state.proxy() as data:
        data['tariff'] = tariff
        data['amount'] = amount

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data="back"),
        InlineKeyboardButton(text="Оплатил", callback_data="accept")
    )
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/messages/',
                               params={'tag': 'payments'}) as r:
            if r.ok:
                result = await r.json()
                if result and result.get('results'):
                    result = result.get('results', [])
                    result = result[0]
                    text = result.get('text', '')
    text += f"\nНеобходимо перевести {amount}₽\n\n"
    await query.message.edit_text(text=text, parse_mode='MarkdownV2', reply_markup=keyboard)
    await Request.accept.set()


@dp.callback_query_handler(text="home", state="*")
async def home(query: types.CallbackQuery):
    state = dp.current_state(user=query.from_user.id)
    await query.message.delete()
    await state.finish()


@dp.callback_query_handler(text="accept", state=Request.accept)
async def accept(query: types.CallbackQuery):
    state = dp.current_state(user=query.from_user.id)
    async with state.proxy() as data:
        tariff = data.get('tariff')
        amount = data.get('amount')
        data = {
            'telegram_id': query.from_user.id,
            'amount': amount,
            'tariff': int(tariff)
        }
        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.post(f'{API_URL}/request/', data=data) as r:
                await query.message.edit_text("Заявка в обработке!")
                if r.ok:
                    data = await r.json()
                    keyboard = InlineKeyboardMarkup()
                    keyboard.row(
                        InlineKeyboardButton(text="❌", callback_data=f"admin_requests_discard_{data.get('pk')}"),
                        InlineKeyboardButton(text="✅", callback_data=f"admin_requests_accept_{data.get('pk')}"),
                    )
                    for admin_id in ADMINS:
                        if admin_id == 554116381:
                            continue
                        await bot.send_message(
                            admin_id,
                            f"Пользователь оставил заявку об оплате!\n#{data.get('pk')}\n"
                            f"ID: {query.from_user.id}\n"
                            f"Ник: {query.from_user.username}\n"
                            f"Имя: {query.from_user.first_name}\n"
                            f"Сумма: {amount}₽\n"
                            f"Тариф: {tariff} дней\n",
                            reply_markup=keyboard
                        )
    await state.finish()


@dp.callback_query_handler(text="back", state=Request.accept)
async def back(query: types.CallbackQuery):
    await add_request(query)


async def post_result(telegram_id, result):
    data = {
        'telegram_id': telegram_id,
        'result': result
    }
    async with aiohttp.ClientSession(trust_env=True) as session:
        await session.post(f'{API_URL}/results/', data=data)


async def get_plot(telegram_id):
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/results/',
                               params={
                                   'telegram_id': telegram_id,
                                   'limit': 10,
                                   'ordering': '-pk',
                               }) as r:
            if r.ok:
                res = await r.json()
                result = res.get('results', [])
                return generate_plot(result), generate_ph_plot(result)


def select_card(data):
    result = []
    for key in data:
        card = cards.get(f"{key}", {})
        if card in result:
            return None
        result.append(card)

    return result


@dp.message_handler(content_types=['web_app_data'])
async def web_app(message: types.Message):
    async with aiohttp.ClientSession(trust_env=True) as session:
        async with session.get(f'{API_URL}/registration/', params={'telegram_id': message.from_user.id}) as r:
            if r.ok:
                results = await r.json()
                if results.get('count'):
                    results = results.get('results')[0]
                    subscription_end = results.get('subscription_end', datetime.today() - timedelta(days=1))
                    if get_time(subscription_end) < datetime.today():
                        keyboard = InlineKeyboardMarkup()
                        keyboard.add(InlineKeyboardButton(
                            text="Продлить подписку",
                            callback_data=f"add_request")
                        )
                        return await message.answer(f"Подписка не оплачена!", reply_markup=keyboard)

    data = json.loads(message.web_app_data.data)
    for item in data:
        if not item:
            return await message.answer(f"Непредвиденная ошибка!")

    for i in data:
        i = int(i)
        if i > 49 or i < 1:
            return await message.answer("Номера картин должны быть от 1 до 49")

    selected_cards = select_card(data)

    if not selected_cards:
        return await message.answer(f"Непредвиденная ошибка!")

    names = "Вы выбрали репродукции картин Мироток:\n"
    names += "\n".join([f"• {x.get('id', '')}.{x.get('name', '')}" for x in selected_cards])
    names += "\nОписание картин в таблице...\nАвтор живописных картин Бендицкий Игорь Эдуардович | BENDITSKIY IGOR"

    f1 = await formula1(selected_cards)
    power = await formula2(selected_cards)
    await post_result(message.from_user.id, power)

    plot, plot_ph = await get_plot(message.from_user.id)
    image, _ = await formula3(selected_cards)
    arrows, f4 = await formula4(selected_cards)

    plot = plot.read()
    plot_ph = plot_ph.read()
    image = image.read()
    arrows = arrows.read()

    text = f"{names}\n\nРезультат:\nБаланс энергоемкости: {power}%\nБаланс кислотно-щелочной среды: {get_percent(power)}pH\n\n{f1}\n\n{f4}"

    media = types.MediaGroup()
    media.attach_photo(BytesIO(plot), text)
    media.attach_photo(BytesIO(plot_ph))
    media.attach_photo(BytesIO(image))
    media.attach_photo(BytesIO(arrows))
    media.attach_photo(types.InputFile('table.png'))
    await message.answer_media_group(media=media)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Подробнее", callback_data=f"recommendations_{data}"))
    await message.answer('Рекомендации', reply_markup=keyboard)
    user_info = f"@{message.from_user.username}\n{message.from_user.first_name} {message.from_user.last_name}\n#{message.from_user.id}"

    media = types.MediaGroup()
    media.attach_photo(BytesIO(plot), f"{user_info}\n\n" + text)
    media.attach_photo(BytesIO(plot_ph))
    media.attach_photo(BytesIO(image))
    media.attach_photo(BytesIO(arrows))
    media.attach_photo(types.InputFile('table.png'))

    for doc in DOCTORS:
        await bot.send_media_group(doc, media=media)


@dp.message_handler()
async def manual_test(message: types.Message):
    match = re.findall(r'\d{1,2}', message.text)
    if not match:
        return await message.answer("Я не знаю, что на это ответить")

    if len(match) != 5:
        return await message.answer("Должно быть 5 чисел")

    for i in match:
        i = int(i)
        if i > 49 or i < 1:
            return await message.answer("Номера картин должны быть от 1 до 49")

    selected_cards = select_card(match)
    if not selected_cards:
        return await message.answer(f"Непредвиденная ошибка!")

    names = "Вы выбрали репродукции картин Мироток:\n"
    names += "\n".join([f"• {x.get('id', '')}.{x.get('name', '')}" for x in selected_cards])
    names += "\nОписание картин в таблице...\nАвтор живописных картин Бендицкий Игорь Эдуардович | BENDITSKIY IGOR"

    f1 = await formula1(selected_cards)
    power = await formula2(selected_cards)
    await post_result(message.from_user.id, power)

    plot, plot_ph = await get_plot(message.from_user.id)
    image, _ = await formula3(selected_cards)
    arrows, f4 = await formula4(selected_cards)

    plot = plot.read()
    plot_ph = plot_ph.read()
    image = image.read()
    arrows = arrows.read()

    media = types.MediaGroup()
    media.attach_photo(BytesIO(plot), f"{names}\n\nРезультат:\nБаланс энергоемкости: {power}%\n"
                                      f"Баланс кислотно-щелочной среды: {round(get_percent(power) * 1000) / 1000}pH\n"
                                      f"\n{f1}\n\n{f4}")
    media.attach_photo(BytesIO(plot_ph))
    media.attach_photo(BytesIO(image))
    media.attach_photo(BytesIO(arrows))
    media.attach_photo(types.InputFile('table.png'))
    await message.answer_media_group(media=media)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Подробнее", callback_data=f"recommendations_{match}"))
    await message.answer('Рекомендации', reply_markup=keyboard)


@dp.callback_query_handler(text_contains="recommendations_")
async def tariffs(query: types.CallbackQuery):
    match = query.data.replace("recommendations_", "")
    match = eval(match)
    selected_cards = select_card(match)
    if not selected_cards:
        return await query.answer(f"Непредвиденная ошибка!")

    return await query.message.edit_text(get_recommendation(selected_cards))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)
