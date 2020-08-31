from sanic import Sanic, response
import config
import models

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
        callback_data = data["data"]
        # if callback_data == "timetable_mem":
        #     if group_id[]
        if callback_data == "timetable_search":
            user.action = "timetable_search_input"
            m_id = user.send_message("👉 Введите название Вашей группы", reply_markup=models.get_keyboard([["Отмена"]])).message_id
            user.data = {"msg_ids": [m_id]}
        return response.text("OK")
    elif "message" in data:
        data = data["message"]
        user = memory.get_user_by_chat(data["chat"])
        text = data["text"]
        if user.action:
            if text == "Отмена":
                user.data["msg_ids"].append(data["message_id"])
                for m_id in user.data["msg_ids"]: user.delete_message(m_id)
                user.show_welcome()
            return response.text("OK")
        if text == "/start":
            user.delete_message(data["message_id"])
            user.send_welcome()
        return response.text("OK")
    return response.text("OK")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082)
