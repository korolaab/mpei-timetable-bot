from telebot import TeleBot, types, apihelper
import threading
import config

bot = TeleBot(config.TELEGRAM_BOT_KEY)
db = pymongo.MongoClient("mongodb", 27017)
lock = threading.Lock()

def get_default_inline_keyboard():
    return get_inline_keyboard([ \
        [{"text": "Мое расписание", "callback_data": "timetable_mem"}], \
        [{"text": "Найти группу", "callback_data": "timetable_search"}], \
        [{"text": "Наш репозиторий", "url": "https://github.com/psylopunk/mpei-timetable-bot"}] \
    ], row_width=1)

def get_inline_keyboard(rows, *args, **kwargs):
    keyboard = types.InlineKeyboardMarkup(*args, **kwargs)
    for row in rows:
        keyboard.add(*[types.InlineKeyboardButton(text=btn["text"],  \
            callback_data=(btn["callback_data"] if "callback_data" in btn else None), url=(btn["url"] if "url" in btn else None)) for btn in row])
    return keyboard

class Memory:
    def __init__(self):
        self.users = {}

    def get_user_by_chat(self, chat):
        if chat["id"] not in self.users:
            if db.users.count_documents({"tid": chat["id"]}) == 0:
                user_object = {"tid": chat["id"], "balance": 0.0}
                if "first_name" in chat: user_object["first_name"] = chat["first_name"]
                if "last_name" in chat: user_object["last_name"] = chat["last_name"]
                if "username" in chat: user_object["username"] = chat["username"]
                db.users.insert_one(user_object)
                user = User(user_object["tid"])
            else: user = User(chat["id"])
            with lock: self.users[chat["id"]] = user
        else: user = self.users[chat["id"]]
        return user

class User:
    def __init__(self, tid):
        self.tid = tid

    def send_message(self, message, *args, **kwargs):
        try: bot.send_message(self.tid, message, parse_mode="html", *args, **kwargs)
        except apihelper.ApiException as e: self.log("Error: [%s] (caused by send_message)" % e)

    def send_welcome(self):
        self.send_message("""💎 <b>Привет, здесь ты можешь найти расписание групп МЭИ</b>

Выбери пункт ниже 👇""", reply_markup=get_default_inline_keyboard())
