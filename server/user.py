from storage import db
from config import TELEGRAM_API_KEY
from aiogram import Bot
from functions import log, get_default_inline_keyboard, get_keyboard, get_inline_keyboard
from datetime import datetime

bot = Bot(token=TELEGRAM_API_KEY)

class User:
    def log(self, text: str):
        log(f'[{self}] {text}')

    def __repr__(self):
        return f'User(telegram_id={self.telegram_id}, first_name={self.first_name}, last_name={self.last_name}, username={self.username})'

    def __init__(self, user_object):
        self._id = user_object['_id'] if '_id' in user_object else None
        self.telegram_id = user_object['tid']
        self.balance = user_object['balance']
        self.message_id = user_object['message_id']
        self.username = user_object['username'] if 'username' in user_object else None
        self.first_name = user_object['first_name'] if 'first_name' in user_object else None
        self.last_name = user_object['last_name'] if 'last_name' in user_object else None
        self.group = user_object['group']
        self.group_id = user_object['group_id']
        self.history_messages_id = user_object['history_messages_id']
        self.settings = user_object['settings']
        self.last_update_id = 0

        db.users.update_one({
            'tid': self.telegram_id
        }, {
            '$set': {
                'last_use': datetime.now()
            }
        })

        self.clear_action()

    async def send_welcome(self, message=None):
        self.clear_action()
        await self.clear_messages()
        if self.message_id:
            await self.delete_message(self.message_id)

        GROUP_NOT_SETTED = '⚠️ <b>Группа не выбрана</b>\n<i>Найдите свою группу с помощью кнопки под сообщением для начала работы</i>'
        m = await self.send_message(
            f"""{message if message else '💎 <b>Привет, здесь ты можешь найти расписание групп МЭИ</b>'}

{f'👥 Ваша группа: <b>{self.group}</b>' if self.group else GROUP_NOT_SETTED}            

Выбери пункт ниже 👇""",
            save=False,
            reply_markup=get_default_inline_keyboard(self)
        )
        if m:
            self.message_id = m.message_id
            db.users.update_one({
                '_id': self._id
            }, {
                '$set': {
                    'message_id': self.message_id
                }
            })


    async def send_message(self, message, save=True, *args, **kwargs):
        try:
            r = await bot.send_message(
                self.telegram_id,
                message,
                parse_mode='html',
                *args,
                **kwargs
            )
            if save:
                self.save_message(r.message_id)
            return r
        except Exception as e:
            self.log(f'Error (cause.sendMessage): {e}')

    async def delete_message(self, message_id):
        try:
            await bot.delete_message(self.telegram_id, message_id)
        except Exception as e:
            self.log(f'Error (cause.deleteMessage): {e}')

    async def edit_message(self, text, *args, **kwargs):
        await self.clear_messages()
        try:
            return await bot.edit_message_text(
                chat_id=self.telegram_id,
                message_id=self.message_id,
                text=text,
                parse_mode='html',
                *args,
                **kwargs
            )
        except Exception as e:
            self.log(f'Error (cause.editMessage): {e}')
            return False

    def clear_action(self):
        self.action = None
        self.data = {}

    def upload_settings(self):
        db.users.update_one({
            '_id': self._id
        }, {
            '$set': {
                'settings': self.settings
            }
        })

    def set_group(self, group, group_id):
        self.group = group.upper()
        self.group_id = group_id
        db.users.update_one({
            '_id': self._id
        }, {
            '$set': {
                'group': self.group,
                'group_id': self.group_id
            }
        })

    async def clear_messages(self):
        for message_id in self.history_messages_id:
            await self.delete_message(message_id)
        self.history_messages_id = []
        db.users.update_one({
            '_id': self._id
        }, {
            '$set': {
                'history_messages_id': []
            }
        })

    async def answer_callback(self, cd_id, text=None):
        try:
            await bot.answer_callback_query(
                callback_query_id=cd_id,
                text=(text or 'Выполнено'),
                show_alert=False
            )
        except Exception as e:
            self.log(f'Error (cause.answerCallback): {e}')

    async def send_settings(self):
        await self.clear_messages()
        print(self._id)
        print(self.settings)
        await self.edit_message(
            """⚙️ <b>Настройки</b>

<b>Уведомления о приближении пары</b>
<i>Вы можете установить время, за сколько перед началом пары, Вам нужно будет прислать сообщение</i>

<b>Уведомления о начале пары</b>
<i>Включив эту настройку, Вы будете получать уведомления при начале каждой пары</i>""",
            reply_markup=get_inline_keyboard([
                [{
                    'text': f"""{'🟢' if self.settings['lesson_notification_previously']['enabled'] else '🔴'} Уведомления о приближении пары""",
                    'callback_data': 'setting_toggle_lessonNotification_previously'
                }],
                [{
                    'text': f"""{'🟢' if self.settings['lesson_notification_beginning']['enabled'] else '🔴'} Уведомления о начале пары""",
                    'callback_data': 'setting_toggle_lessonNotification_beginning'
                }],
                [{
                    'text': 'На главную 🔙',
                    'callback_data': 'home'
                }]
            ])
        )

    def save_message(self, message_id):
        self.history_messages_id.append(message_id)
        db.users.update_one({
            '_id': self._id
        }, {
            '$set': {
                'history_messages_id': self.history_messages_id
            }
        })

    @classmethod
    def from_tid(cls, tid):
        user_object = db.users.find_one({
            'tid': int(tid)
        })
        if not user_object:
            raise Exception('User not found')

        return User(user_object)