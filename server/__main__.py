from storage import db
from config import TELEGRAM_API_KEY
from memory import Memory, User
from functions import get_keyboard, get_group_id, get_inline_keyboard, get_default_inline_keyboard
from datetime import datetime, timedelta
import asyncio
import httpx

memory = Memory()

async def handle_update(update):
    data = update
    if 'callback_query' in data:
        data = data['callback_query']
        user = memory.get_user(data['message']['chat'])
        callback_data = data['data']
        if 'timetable_mem' not in callback_data:
            await user.answer_callback(data['id'])
        if callback_data == 'timetable_mem':
            if not user.group_id:
                await user.send_welcome(message='⚠️ <b>Нет сохраненной группы</b>\n\nℹ️ <i>Найдите свою группу с помощью кнопок ниже</i>')
                return True
            try:
                await user.send_timetable(
                    datetime.now()
                )
            except Exception as e:
                user.log(f'Servers MPEI is offline, error: {e} (caused by send_timetable)')
                await user.answer_callback(
                    data['id'],
                    text='Сервера МЭИ недоступны'
                )
        elif 'timetable_mem_' in callback_data:
            tstamp = int(callback_data.replace('timetable_mem_', ''))
            try:
                await user.send_timetable(datetime.utcfromtimestamp(tstamp) + timedelta(hours=3))
            except Exception as e:
                user.log(f'Servers MPEI is offline, error: {e} (caused by send_timetable)')
                await user.answer_callback(
                    data['id'],
                    text='Сервера МЭИ недоступны'
                )
        elif callback_data == 'timetable_search':
            user.action = 'timetable_search_input'
            await user.send_message(
                '👉 Введите название Вашей группы\n\n<i>Пример:</i> ИЭ-46-20',
                reply_markup=get_keyboard([['Отмена']])
            )
        elif callback_data == 'settings':
            await user.send_settings()
        elif callback_data == 'setting_toggle_lessonNotification_previously':
            if user.settings['lesson_notification_previously']['enabled']:
                user.settings['lesson_notification_previously'] = {
                    'enabled': False
                }
                user.upload_settings()
                await user.send_settings()
            else:
                user.action = 'toggle_lessonNotification_previously'
                await user.send_message(
                    '👉 Введите количество минут (только цифры)\n\n<i>Пример:</i> 15\n\n<i>Уведомление о парах будет приходить за указанное количество минут до начала</i>',
                    get_keyboard([['Отмена']])
                )
        elif callback_data == 'setting_toggle_lessonNotification_beginning':
            if user.settings['lesson_notification_beginning']['enabled']:
                user.settings['lesson_notification_beginning'] = {
                    'enabled': False
                }
            else:
                user.settings['lesson_notification_beginning'] = {
                    'enabled': True
                }
            user.upload_settings()
            await user.send_settings()
            return True
        elif callback_data == 'feedback':
            user.log('Open feedback, yee')
            await user.edit_message(
                f"""❓ <b>О боте</b>

🎓 Нашим ботом пользуется <b>{db.users.count_documents({})} студентов</b>

<i>Донат:</i>
<b>QIWI/BANK</b> +79255549461
<b>BITCOIN</b> (сообщением ниже, для удобства копирования)

По всем вопросам обращайтесь к @psylopunk""",
                reply_markup=get_inline_keyboard([
                    [{'text': 'Написать администратору', 'url': 'https://t.me/psylopunk'}],
                    [{'text': 'Исходный код (репозиторий)', 'url': 'https://github.com/psylopunk/mpei-timetable-bot'}],
                    [{'text': 'На главную 🔙', 'callback_data': 'home'}]
                ])
            )
            await user.send_message('<code>1QDXmdfA7jW3JDewoAvWB5hn66eXrp1aNw</code>')
        elif callback_data == 'home':
            await user.send_welcome()
        return True
    elif 'message' in data:
        data = data['message']
        user = memory.get_user(data['chat'])
        try:
            text = data['text']
        except Exception as e:
            memory.log(f'Invalid message: {data}')
            memory.log(f'|^| ERROR |^|: {e}')
            user.save_message(data['message_id'])

        # if user.telegram_id not in [1748150734]:
        #     await user.send_message('⚠️ <b>Бот будет доступен через пару дней, Вы получите уведомление</b>')
        #     return True

        if text != '/start':
            user.save_message(data['message_id'])

        if text in ['/start', 'Отмена']:
            await user.send_welcome()
            return True

        if user.action:
            if text == 'Отмена':
                await user.send_welcome()
                return True
            if user.action == 'timetable_search_input':
                group_id, group_name = get_group_id(text)
                if not group_id:
                    await user.send_message(
                        '⚠️ <b>Группа не найдена</b>\n\n👉 Введите название Вашей группы',
                        reply_markup=get_keyboard([["Отмена"]])
                    )
                    return True
                user.set_group(group_name, group_id)
                await user.send_welcome(message='✅ <b>Группа сохранена</b>')
                return True
            elif user.action == 'toggle_lessonNotification_previously':
                if not text.isdigit():
                    await user.send_message(
                        '⚠️ <b>Вы ввели текст</b>\n\n👉 Введите количество минут',
                        reply_markup=get_keyboard([['Отмена']])
                    )
                user.settings['lesson_notification_previously'] = {
                    'enabled': True,
                    'minutes': int(text)
                }
                user.clear_action()
                user.upload_settings()
                await user.send_settings()
                return True
            return True
            # return True

        await user.send_message('⚠️ <b>Воспользуйтесь кнопками на сообщении выше или нажмите на</b> /start')



    return True

async def polling():
    if not db.memory.count_documents({
        'key': 'last_timeout_error'
    }):
        db.memory.insert_one({
            'key': 'last_timeout_error',
            'value': datetime.now()
        })

    async with httpx.AsyncClient() as client:
        while True:
            try:
                res = (
                    await client.get(
                        f'https://api.telegram.org/bot{TELEGRAM_API_KEY}/getUpdates?offset={memory.last_update_id + 1}'
                    )
                ).json()
            except Exception as e:
                print(f'Error [{e}] (caused by polling.request)')
                continue

            if not res['ok']:
                memory.log(f'Error from Telegram: {res}')
                continue

            updates = res['result']
            # print(len(updates))
            if updates:
                memory.set_last_update_id(updates[-1]['update_id'])
                for update in updates:
                    await handle_update(update)

            await asyncio.sleep(.01)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(
        polling()
    )
    loop.run_forever()