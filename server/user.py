from storage import db
from config import TELEGRAM_API_KEY
from aiogram import Bot
from functions import log, get_default_inline_keyboard, get_keyboard, get_inline_keyboard, get_weekday_name, get_timetable_json
from datetime import datetime, timedelta

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

    async def send_timetable(self, date_obj):
        day = await get_timetable_json(self, date_obj)
        lessons_message = ''
        time_now = datetime.now()
        for lesson in day:
            if time_now < lesson['begin_lesson']:
                lessons_message += '⚪️ '
            elif time_now > lesson['begin_lesson'] and time_now < lesson['end_lesson']:
                lessons_message += '🟡 '
            elif time_now > lesson['end_lesson']:
                lessons_message += '🟢 '
            else:
                lessons_message += 'ERR!'

            _two_endl = '\n\n'
            lessons_message += f"""<b>{lesson['name']}</b>
      <i>{lesson['begin_lesson'].strftime('%H:%M')} - {lesson['end_lesson'].strftime('%H:%M')}</i>
      📍 {lesson['place']}
      👨‍🏫 {lesson['lecturer'] if '!' not in lesson['lecturer'] else '<i>Нет информации</i>'}
      <code>{lesson['type']}</code>

"""
        return await self.edit_message(
                f"""🔰 <b>Расписание на {date_obj.strftime('%d.%m')}, {get_weekday_name(date_obj)}</b>
<i>Информация обновлена {time_now.strftime('%H:%M')}</i>

{lessons_message if lessons_message else f'🌀 <b>В этот день нет занятий</b>{_two_endl}'}🟡 <b>Пара идет</b>
🟢 <b>Пара закончилась</b>""",
                reply_markup=get_inline_keyboard([
                    [
                        {
                            'text': f'◀️ {(date_obj - timedelta(days=1)).strftime("%d.%m")}, {get_weekday_name(date_obj - timedelta(days=1))}',
                            'callback_data': f'timetable_mem_{int((date_obj - timedelta(days=1)).timestamp())}'
                        },
                        {
                            'text': f'Обновить',
                            'callback_data': f'timetable_mem_{int(date_obj.timestamp())}'
                        },
                        {
                            'text': f'{(date_obj + timedelta(days=1)).strftime("%d.%m")}, {get_weekday_name(date_obj + timedelta(days=1))} ▶️',
                            'callback_data': f'timetable_mem_{int((date_obj + timedelta(days=1)).timestamp())}'
                        }
                    ],
                    [
                        {
                            'text': f'⏪ {(date_obj - timedelta(days=7)).strftime("%d.%m")}, {get_weekday_name(date_obj - timedelta(days=7))}',
                            'callback_data': f'timetable_mem_{int((date_obj - timedelta(days=7)).timestamp())}'
                        },
                        {
                            'text': f'Сегодня',
                            'callback_data': f'timetable_mem_{int(datetime.now().timestamp())}'
                        } if datetime.now().strftime('%d.%m.%Y') != date_obj.strftime('%d.%m.%Y') else {},
                        {
                            'text': f'{(date_obj + timedelta(days=7)).strftime("%d.%m")}, {get_weekday_name(date_obj + timedelta(days=7))} ⏩',
                            'callback_data': f'timetable_mem_{int((date_obj + timedelta(days=7)).timestamp())}'
                        }
                    ],
                    [{'text': 'На главную 🔙', 'callback_data': 'home'}]
                ])
            )

    @classmethod
    def from_tid(cls, tid):
        user_object = db.users.find_one({
            'tid': int(tid)
        })
        if not user_object:
            raise Exception('User not found')

        return User(user_object)