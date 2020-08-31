from sanic import Sanic, response
from telebot import TeleBot, types, apihelper
import config

app = Sanic(__name__)
bot = TeleBot(config.TELEGRAM_BOT_KEY)

@app.route("/")
def s_index(request):
    return response.text("OK")

@app.route("/t_webhook", methods=["GET", "POST"])
def s_twebhook(request):
    print(request.json)
    data = request.json
    if "message" in data:
        data = data["message"]
    return response.text("OK")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082)
