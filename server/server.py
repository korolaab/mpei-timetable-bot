from sanic import Sanic, response
from telebot import TeleBot, types, apihelper
import config

app = Sanic(__name__)
bot = TeleBot(config.TELEGRAM_BOT_KEY)

@app.route("/")
def s_index(request):
    return response.text("OK")

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8082)
