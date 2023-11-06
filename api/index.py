from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import os
import csv
from dotenv import load_dotenv

# 載入.env檔案中的變數
load_dotenv()


line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

app = Flask(__name__)

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status
    if event.message.type != "text":
        return

    if event.message.text == "說話":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "閉嘴":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
        return

    if working_status:
        # chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
        # reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        # chatgpt.add_msg(f"AI:{reply_msg}\n")
        sent_msg = event.message.text
        if sent_msg == "課程大綱":
            # 從data.csv讀取資料
            # 學制別,學年度,學期,開課單位,課程編號,科目名稱,上課日,上課時間,上課地點,選別,學分,教師背景,教師職稱,授課教師,授課語言
            # 研究所,112,1,資管碩一,D0F0333541,金融數據分析與智慧交易,Monday 星期一,"D5,D6,D7",SF130,選修,3,專任,助理教授,邱嘉洲,中文
            # 研究所,112,1,資管碩一,G745032133,敏捷式軟體開發,Monday 星期一,"E1,E2,E3",LW210,選修,3,專任,助理教授,吳濟聰,中文
            data = []
            with open('data.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    data.append(row)
            reply_msg = ""
            for row in data:
                reply_msg += f"{row[1]}-{row[2]} {row[5]} {row[13]}\n"
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_msg))


if __name__ == "__main__":
    app.run()