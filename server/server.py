from sanic import Sanic, response
import config
import datetime
import uuid
import models

memory = models.Memory()
app = Sanic(__name__)

@app.route("/")
async def s_index(request):
    return response.text("OK")

@app.route("/t_webhook", methods=["POST"])
async def s_twebhook(request):
    data = request.json
    # print(data)
    if "callback_query" in request.json:
        data = request.json["callback_query"]
        user = memory.get_user_by_chat(data["message"]["chat"])
        if not user.check_update_id(request.json["update_id"]): return response.text("OK")
        user.answer_callback(data["id"])
        callback_data = data["data"]
        print("Callback data: %s" % callback_data)
        if callback_data == "timetable_mem":
            if not user.group_id:
                user.send_welcome("⚠️ <b>Нет сохраненной группы</b>\n\nℹ️ <i>Найдите свою группу с помощью кнопок ниже</i>")
                return response.text("OK")
            user.send_timetable(datetime.datetime.now())
        elif "timetable_mem_" in callback_data:
            tstamp = int(callback_data.replace("timetable_mem_", ""))
            user.send_timetable(datetime.datetime.utcfromtimestamp(tstamp) + datetime.timedelta(hours=3))
        elif callback_data == "timetable_search":
            user.action = "timetable_search_input"
            user.send_message("👉 Введите название Вашей группы\n\n<i>Пример:</i> ИЭ-46-20", reply_markup=models.get_keyboard([["Отмена"]]))
        elif callback_data == "building_locations":
            user.edit_message("""📍 <b>Расположение корпусов</b>

<i>Это тестовая функция, если Вы заметили не точность данных, напишите в обратную связь</i>

<i>Позже на этом месте будет фотография карты корпусов, но пока ее нет в достаточно хорошем оформлении</i>

<i>Если у Вас есть желание помочь с этой фотографией, напишите в обратную связь</i>

👉 Выберите букву корпуса""", \
                reply_markup=models.get_inline_keyboard([ \
                    [{"text": n, "callback_data": "building_location_%s" % n.encode("utf8").hex()} for n in "АБВГДЕЖЗИКЛМНРСТФХ"], \
                    [{"text": "На главную 🔙", "callback_data": "home"}]
            ], row_width=3))
        elif "building_location_" in callback_data:
            if "lmid" in user.data: user.delete_message(user.data["lmid"])
            building_name = bytearray.fromhex(callback_data.replace("building_location_", "").strip()).decode("utf8")
            coordinates = config.BUILDINGS[building_name]
            r = user.send_location(coordinates[0], coordinates[1])
            if r: user.data["lmid"] = r.message_id
        elif callback_data == "bells_sticker":
            user.send_sticker("CAACAgIAAxkBAAIT8V9WLBPE8NxjsDzE_1e0DQNWIs1YAAJqCAACifCwSsu2IvEXtjwzGwQ")
        elif callback_data == "settings":
            user.send_settings()
        elif callback_data == "setting_toggle_lnotification":
            if "lesson_notification" not in user.settings:
                user.settings["lesson_notification"] = {"enabled": False}
                user.upload_settings()
            if user.settings["lesson_notification"]["enabled"]:
                user.settings["lesson_notification"] = {"enabled": False}
                user.upload_settings()
                user.send_settings()
            else:
                user.action = "toggle_lnotification"
                user.send_message("👉 Введите количество минут (только цифры)\n\n<i>Пример:</i> 15\n\n<i>Уведомление о парах будет приходить за указанное количество минут до начала</i>", reply_markup=models.get_keyboard([["Отмена"]]))
        elif callback_data == "share":
            user.send_share()
        elif callback_data == "feedback":
            user.edit_message("""❓ <b>Обратная связь</b>

Кто сделал этого бота? <a href="https://gurov.co/">gurov.co</a>

<i>Донат:</i>
<b>QIWI</b> +79255549461
<b>BITCOIN</b> (сообщением ниже, для удобства копирования)

По всем вопросам обращайтесь к @psylopunk""", \
                disable_web_page_preview=None, \
                reply_markup=models.get_inline_keyboard([ \
                [{"text": "Написать администратору", "url": "https://t.me/psylopunk"}],
                [{"text": "На главную 🔙", "callback_data": "home"}]
            ]))
            user.send_message("<code>1QDXmdfA7jW3JDewoAvWB5hn66eXrp1aNw</code>")
        elif callback_data == "home": user.send_welcome()
        return response.text("OK")
    elif "message" in data:
        data = data["message"]
        user = memory.get_user_by_chat(data["chat"])
        if not user.check_update_id(request.json["update_id"]): return response.text("OK")
        user.save_message(data["message_id"])
        try: text = data["text"]
        except Exception as e:
            print(data)
            print("Error: [%s] (caused by get text by message)" % e)
            return response.text("OK")
        if user.action:
            if text == "Отмена":
                user.send_welcome()
                return response.text("OK")
            if user.action == "timetable_search_input":
                group_id, group_name = models.get_group_id(text)
                if not group_id:
                    user.send_message("⚠️ <b>Группа не найдена</b>\n\n👉 Введите название Вашей группы", reply_markup=models.get_keyboard([["Отмена"]]))
                    return response.text("OK")
                user.set_group(group_name, group_id)
                user.send_welcome(message="✅ <b>Группа сохранена</b>")
            elif user.action == "toggle_lnotification":
                if not text.isdigit():
                    user.send_message("⚠️ <b>Вы ввели текст</b>\n\n👉 Введите количество минут", reply_markup=models.get_keyboard([["Отмена"]]))
                    return response.text("OK")
                user.settings["lesson_notification"] = {"enabled": True, "minutes": int(text)}
                user.upload_settings()
                user.send_settings()
            else: user.send_welcome()
            return response.text("OK")
        if "/start" in text:
            group = text.replace("/start", "").strip()
            try:
                if group:
                    group_id, group_name = models.get_group_id(bytearray.fromhex(group).decode("utf8"))
                    if group_id: user.set_group(group_name, group_id)
            except Exception as e:
                print("Error [%s] (caused by /start)" % e)
            user.send_welcome()
        elif text == "/share":
            user.send_share()
            user.delete_message(data["message_id"])
        else:
            user.send_message("⚠️ <b>Воспользуйтесь кнопками на сообщении выше или нажмите на</b> /start")
        return response.text("OK")
    return response.text("OK")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082)
