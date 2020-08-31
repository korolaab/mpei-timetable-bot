from telebot import TeleBot, types, apihelper
import requests
import pymongo
import threading
import config

bot = TeleBot(config.TELEGRAM_BOT_KEY)
db = pymongo.MongoClient("mongodb", 27017).mpeitt
lock = threading.Lock()

def get_default_inline_keyboard(user):
    return get_inline_keyboard([ \
        [{"text": "Мое расписание", "callback_data": "timetable_mem"}] if user.group_id else [], \
        [{"text": "Найти группу", "callback_data": "timetable_search"}], \
        [{"text": "Наш репозиторий", "url": "https://github.com/psylopunk/mpei-timetable-bot"}] \
    ], row_width=1)

def get_inline_keyboard(rows, *args, **kwargs):
    keyboard = types.InlineKeyboardMarkup(*args, **kwargs)
    for row in rows:
        keyboard.add(*[types.InlineKeyboardButton(text=btn["text"],  \
            callback_data=(btn["callback_data"] if "callback_data" in btn else None), url=(btn["url"] if "url" in btn else None)) for btn in row if btn])
    return keyboard

def get_keyboard(rows, **kwargs):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, **kwargs)
    for row in rows: keyboard.add(*[types.KeyboardButton(button) for button in row])
    return keyboard

def get_group_id(name):
    r_url = requests.post("https://mpei.ru/Education/timetable/Pages/default.aspx", \
        {
            'MSOWebPartPage_PostbackSource': '',
            'MSOTlPn_SelectedWpId': '',
            'MSOTlPn_View': '0',
            'MSOTlPn_ShowSettings': 'False',
            'MSOGallery_SelectedLibrary': '',
            'MSOGallery_FilterString': '',
            'MSOTlPn_Button': 'none',
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__REQUESTDIGEST': '0x754E29870BD2C554BDB331DDC7A883C1EDA9A365E654B6307AFDCB38F4A37A5A3C550017E868FD8E9DB0834AD7605A501D84AF4EEC0ECEBAC10637986A3AC585,31 Aug 2020 12',
            'MSOSPWebPartManager_DisplayModeName': 'Browse',
            'MSOSPWebPartManager_ExitingDesignMode': 'false',
            'MSOWebPartPage_Shared': '',
            'MSOLayout_LayoutChanges': '',
            'MSOLayout_InDesignMode': '',
            '_wpSelected': '',
            '_wzSelected': '',
            'MSOSPWebPartManager_OldDisplayModeName': 'Browse',
            'MSOSPWebPartManager_StartWebPartEditingName': 'false',
            'MSOSPWebPartManager_EndWebPartEditing': 'false',
            '_maintainWorkspaceScrollPosition': '0',
            '__VIEWSTATE': '/wEPDwUBMA9kFgJmD2QWAgIBD2QWBAIBD2QWBAIJD2QWAmYPZBYCAgEPFgIeE1ByZXZpb3VzQ29udHJvbE1vZGULKYgBTWljcm9zb2Z0LlNoYXJlUG9pbnQuV2ViQ29udHJvbHMuU1BDb250cm9sTW9kZSwgTWljcm9zb2Z0LlNoYXJlUG9pbnQsIFZlcnNpb249MTQuMC4wLjAsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49NzFlOWJjZTExMWU5NDI5YwFkAhgPZBYCAgcPFgIfAAsrBAFkAgMPZBYMAgMPZBYCBSZnXzUwMjYxM2E0X2Q0MDVfNDFiZl9hNDAxXzJjNDJiMmZhNjVjYQ9kFgRmDxYCHgdWaXNpYmxlaGQCAQ8WAh8BaGQCBw9kFgRmD2QWBAIBDxYCHwFoFgJmD2QWBAICD2QWBgIBDxYCHwFoZAIDDxYIHhNDbGllbnRPbkNsaWNrU2NyaXB0BYEBamF2YVNjcmlwdDpDb3JlSW52b2tlKCdUYWtlT2ZmbGluZVRvQ2xpZW50UmVhbCcsMSwgMzksICdodHRwczpcdTAwMmZcdTAwMmZtcGVpLnJ1XHUwMDJmRWR1Y2F0aW9uXHUwMDJmdGltZXRhYmxlJywgLTEsIC0xLCAnJywgJycpHhhDbGllbnRPbkNsaWNrTmF2aWdhdGVVcmxkHihDbGllbnRPbkNsaWNrU2NyaXB0Q29udGFpbmluZ1ByZWZpeGVkVXJsZB4MSGlkZGVuU2NyaXB0BSJUYWtlT2ZmbGluZURpc2FibGVkKDEsIDM5LCAtMSwgLTEpZAIFDxYCHwFoZAIDDw8WCh4JQWNjZXNzS2V5BQEvHg9BcnJvd0ltYWdlV2lkdGgCBR4QQXJyb3dJbWFnZUhlaWdodAIDHhFBcnJvd0ltYWdlT2Zmc2V0WGYeEUFycm93SW1hZ2VPZmZzZXRZAusDZGQCAw9kFgJmD2QWAgIDD2QWAgIDD2QWAgIBDzwrAAUBAA8WAh4PU2l0ZU1hcFByb3ZpZGVyBRFDdXJyZW50TmF2aWdhdGlvbmRkAgEPZBYEAgIPZBYCZg9kFgJmDxQrAANkZGRkAgQPDxYEHgRUZXh0BUvQl9Cw0L/Rg9GB0Log0L/QsNC90LXQu9C4INC80L7QvdC40YLQvtGA0LjQvdCz0LAg0YDQsNC30YDQsNCx0L7RgtGH0LjQutC+0LIfAWhkZAITD2QWAgIBDxAWAh8BaGQUKwEAZAIXD2QWAgIBD2QWAmYPZBYCZg8PZBYGHgVjbGFzcwUibXMtc2J0YWJsZSBtcy1zYnRhYmxlLWV4IHM0LXNlYXJjaB4LY2VsbHBhZGRpbmcFATAeC2NlbGxzcGFjaW5nBQEwZAIZD2QWBAIMD2QWAgIDD2QWAgIBDxYCHwALKwQBZAIQD2QWAgIDD2QWBAIDDxYCHwALKwQBZAIFDxYCHwALKwQBZAIfD2QWAgIBD2QWAmYPZBYCAgMPZBYCAgUPDxYEHgZIZWlnaHQbAAAAAAAAeUABAAAAHgRfIVNCAoABZBYCAgEPPCsACQEADxYEHg1QYXRoU2VwYXJhdG9yBAgeDU5ldmVyRXhwYW5kZWRnZGQYAQUZY3RsMDAkVG9wTmF2aWdhdGlvbk1lbnVWNA8PZAUW0J7QsdGA0LDQt9C+0LLQsNC90LjQtWSgMQgmzHTTQDzzuiEAKKQcyeF62Q==',
            '__VIEWSTATEGENERATOR': 'BAB98CB3',
            '__EVENTVALIDATION': '/wEWBwKhuP7zDgLNrvW5AwKOtvisAQKb+Y7OBAKb+fryCwK3soGRCwK3spXsAwGtAfOd8/pKk9+W++I15dq+fmYQ',
            'InputKeywords': 'Найти',
            'ctl00$PlaceHolderSearchArea$ctl01$ctl03': '0',
            'ctl00$ctl30$g_f0649160_e72e_4671_a36b_743021868df5$ctl03': '%s' % name,
            'ctl00$ctl30$g_f0649160_e72e_4671_a36b_743021868df5$ctl04': '>>',
            'ctl00$ctl30$g_b96f4f86_bef6_432f_8a67_f25ef9a781ae$ctl00': '',
            '__spDummyText1': '',
            '__spDummyText2': '',
            '_wpcmWpid': ''
        }
    ).url
    if "default.aspx" in r_url: return False
    elif "table.aspx" in r_url:
        try: return r_url[r_url.find("=") + 1:r_url.find("&")]
        except Exception as e:
            print("Error: [%s] (caused by get_group_id)" % e)
            return False
    return False

class Memory:
    def __init__(self):
        self.users = {}

    def hard_update_user(self, user): return User(user.tid)

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
        user_object = db.users.find({"tid": tid})[0]
        self.db_id = user_object["_id"]
        self.tid = user_object["tid"]
        self.group_id = user_object["group_id"] if "group_id" in user_object else None
        self.message_id = user_object["message_id"] if "message_id" in user_object else None

        self.clear_action()

    def clear_action(self):
        self.action = None
        self.data = None

    def send_message(self, message, *args, **kwargs):
        try: return bot.send_message(self.tid, message, parse_mode="html", *args, **kwargs)
        except apihelper.ApiException as e: print("Error: [%s] (caused by send_message)" % e); return False

    def delete_message(self, message_id):
        try: bot.delete_message(self.tid, message_id)
        except apihelper.ApiException as e: print("Error: [%s] (caused by delete_message)" % e)

    def edit_message(self, text, *args, **kwargs):
        try: bot.edit_message_text(chat_id=self.tid, message_id=self.message_id, \
            text=text, *args, **kwargs)
        except apihelper.ApiException as e: print("Error: [%s] (caused by edit_message)" % e)

    def send_welcome(self, message=None):
        if self.message_id: self.delete_message(self.message_id)
        m = self.send_message("""%s

Выбери пункт ниже 👇""" % ( \
                message if message else "💎 <b>Привет, здесь ты можешь найти расписание групп МЭИ</b>" \
             ), reply_markup=get_default_inline_keyboard(self))
        if m:
            self.message_id = m.message_id
            self.db.users.update_one({"_id": self.db_id}, {"$set": {"message_id": m.message_id}})
