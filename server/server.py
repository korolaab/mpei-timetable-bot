from sanic import Sanic, response
from modules import Memory, User
import config

memory = Memory()
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
    elif "message" in data:
        data = data["message"]
        user = memory.get_user_by_chat(data["chat"])
        text = data["text"]
        if text == "/start":
            user.send_welcome()
    return response.text("OK")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082)
