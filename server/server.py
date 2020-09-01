from sanic import Sanic, response
import config
import datetime
import uuid
import models
import qrcode

memory = models.Memory()
app = Sanic(__name__)

@app.route("/")
async def s_index(request):
    return response.text("OK")

@app.route("/t_webhook", methods=["GET", "POST"])
async def s_twebhook(request):
    print(request.json)
    data = request.json
    if "callback_query" in request.json:
        data = request.json["callback_query"]
        user = memory.get_user_by_chat(data["message"]["chat"])
        user.answer_callback(data["id"])
        callback_data = data["data"]
        if callback_data == "timetable_mem":
            if not user.group_id:
                user.send_welcome("⚠️ <b>Нет сохраненной группы</b>\n\nℹ️ <i>Найдите свою группу с помощью кнопок ниже</i>")
                return response.text("OK")
            user.send_timetable(datetime.datetime.now() + datetime.timedelta(hours=3))
        elif "timetable_mem_" in callback_data:
            tstamp = int(callback_data.replace("timetable_mem_", ""))
            user.send_timetable(datetime.datetime.utcfromtimestamp(tstamp) + datetime.timedelta(hours=3))
        elif callback_data == "timetable_search":
            user.action = "timetable_search_input"
            m_id = user.send_message("👉 Введите название Вашей группы", reply_markup=models.get_keyboard([["Отмена"]])).message_id
            user.data = {"msg_ids": [m_id]}
        elif callback_data == "share":
            qr = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10,border=1)
            qr.add_data("https://t.me/mpei_timetable_bot%s" % (("?start=%s" % user.group) if user.group else ""))
            qr_file = "%s" % uuid.uuid4()
            qr.make_image(fill_color="black", back_color="white").save("/data/qr_codes/%s.png" % qr_file)
            user.edit_message("""💎 <b>Поделиться с друзьями</b>

Покажи своему другу QR-код сообщением ниже или перешли ему это сообщение с ссылкой

%s""" % ("https://t.me/mpei_timetable_bot%s" % (("?start=%s" % user.group) if user.group else "")), reply_markup=models.get_inline_keyboard([[{"text": "На главную 🔙", "callback_data": "home"}]]))
            with open("/data/qr_codes/%s.png" % qr_file, "rb") as file: user.send_photo(file)
        elif callback_data == "feedback":
            user.edit_message("""❓ <b>Обратная связь</b>

Кто сделал этого бота? <a href="https://gurov.co/">gurov.co</a>

По всем вопросам обращайтесь к @psylopunk""", \
                reply_markup=models.get_inline_keyboard([ \
                [{"text": "Написать администратору", "url": "https://t.me/psylopunk"}],
                [{"text": "На главную 🔙", "callback_data": "home"}]
            ]))
        elif callback_data == "home": user.send_welcome()
        return response.text("OK")
    elif "message" in data:
        data = data["message"]
        user = memory.get_user_by_chat(data["chat"])
        user.save_message(data["message_id"])
        text = data["text"]
        if user.action:
            if text == "Отмена": user.send_welcome()
            if user.action == "timetable_search_input":
                group_id = models.get_group_id(text)
                if not group_id:
                    user.send_message("⚠️ <b>Группа не найдена</b>\n\n👉 Введите название Вашей группы", reply_markup=models.get_keyboard([["Отмена"]]))
                    return response.text("OK")
                user.set_group_id(text, group_id)
                user.send_welcome(message="✅ <b>Группа сохранена</b>")
            return response.text("OK")
        if text == "/start":
            user.send_welcome()
        else:
            user.send_message("⚠️ <b>Воспользуйтесь кнопками на сообщении выше или нажмите на</b> /start")
        return response.text("OK")
    return response.text("OK")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082)
