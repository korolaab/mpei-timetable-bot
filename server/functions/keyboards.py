from storage import db
from config import TELEGRAM_API_KEY
from aiogram import types

def get_inline_keyboard(rows, *args, **kwargs):
    keyboard = types.InlineKeyboardMarkup(*args, **kwargs)
    for row in rows:
        keyboard.add(*[types.InlineKeyboardButton(text=btn['text'],  \
            callback_data=(btn['callback_data'] if 'callback_data' in btn else None), url=(btn['url'] if 'url' in btn else None)) for btn in row if btn])
    return keyboard

def get_default_inline_keyboard(user):
    return get_inline_keyboard([ \
        [{"text": "Мое расписание", "callback_data": "timetable_mem"}] if user.group_id else [], \
        # [{"text": "Расположение корпусов", "callback_data": "building_locations"}],
        # [{"text": "Звонки", "callback_data": "bells_sticker"}],
        [{"text": "Найти группу" if not user.group_id else "Изменить группу", "callback_data": "timetable_search"}, {"text": "Настройки", "callback_data": "settings"} if user.group_id else {}],
        # [{"text": "Поделиться с друзьями", "callback_data": "share"},
        [{"text": "О боте", "callback_data": "feedback"}] \
    ], row_width=2)

def get_weekday_name(date_obj): return ["пн", "вт", "ср", "чт", "пт", "сб", "вс"][date_obj.weekday()]

def get_keyboard(rows, **kwargs):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, **kwargs)
    for row in rows: keyboard.add(*[types.KeyboardButton(button) for button in row])
    return keyboard