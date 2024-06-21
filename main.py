import os
import csv
import sqlite3
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from dotenv import load_dotenv
import json
from copy import deepcopy

# 載入.env檔案中的變數
load_dotenv()
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default="true").lower() == "true"
mode = os.getenv("DEFALUT_MODE", default="課程大綱")

app = Flask(__name__)


def parse_main_ui(classListData):
  with open('main_ui//main_ui.json', 'r', encoding='utf-8') as f:
    classInfo = json.load(f)["contents"][0]
    classList = {"type": "carousel", "contents": []}
    for classInfoData in classListData:
      print('classInfoData: ', classInfoData[0])
      # 科目名稱
      classInfo["body"]["contents"][0]["text"] = classInfoData[1]
      # 課程編號
      classInfo["body"]["contents"][1]["contents"][1]["text"] = classInfoData[
          0]
      # 授課教師
      classInfo["body"]["contents"][2]["contents"][1]["text"] = classInfoData[
          4]
      # 必選別
      classInfo["body"]["contents"][3]["contents"][1]["text"] = classInfoData[
          2]
      # 學分
      classInfo["body"]["contents"][4]["contents"][1]["text"] = classInfoData[
          3]
      classInfo["footer"]["contents"][0]["action"]['uri'] = classInfoData[5]
      classInfo["footer"]["contents"][1]["action"]['text'] \
      = f"{classInfo['footer']['contents'][1]['action']['text']}{classInfoData[0]}"
      classList["contents"].append(deepcopy(classInfo))
      classInfo["footer"]["contents"][1]["action"]['text'] = '心得 '
    return classList


def parse_exp_ui(classListData):
  with open('main_ui//exp_ui.json', 'r', encoding='utf-8') as f:
    classInfo = json.load(f)["contents"][0]
    classList = {"type": "carousel", "contents": []}
    for classInfoData in classListData:
      classInfo["body"]["contents"][0]["text"] = classInfoData[5]
      classInfo["body"]["contents"][1]["contents"][0]["contents"][1]['text'] \
      = classInfoData[13]
      exp = \
      f"{classInfo['body']['contents'][3]['contents'][0]['contents'][0]['text']}{classInfoData[15]}"
      classInfo["body"]["contents"][3]["contents"][0]["contents"][0]['text'] \
      = exp
      print(exp)
      classList["contents"].append(deepcopy(classInfo))
  return classList


# def filter_class_outline(sent_msg: str):
#   filtered_data = []

#   return filtered_data


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
  global mode
  if event.message.type != "text":
    return

  if event.message.text == "說話":
    working_status = True
    line_bot_api.reply_message(event.reply_token,
                               TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
    return

  if event.message.text == "閉嘴":
    working_status = False
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「說話」 > <"))
    return

  # if working_status:
  # chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
  # reply_msg = chatgpt.get_response().replace("AI:", "", 1)
  # chatgpt.add_msg(f"AI:{reply_msg}\n")
  # 從data.csv讀取資料
  # 學制別,學年度,學期,開課單位,課程編號,科目名稱,上課日,上課時間,上課地點,選別,學分,教師背景,教師職稱,授課教師,授課語言
  # 研究所,112,1,資管碩一,D0F0333541,金融數據分析與智慧交易,Monday 星期一,"D5,D6,D7",SF130,選修,3,專任,助理教授,邱嘉洲,中文
  # 研究所,112,1,資管碩一,G745032133,敏捷式軟體開發,Monday 星期一,"E1,E2,E3",LW210,選修,3,專任,助理教授,吳濟聰,中文

  # sent_msg = event.message.text
  # if sent_msg == "課程大綱":
  #     data = []
  #     with open('data.csv', newline='', encoding='utf-8') as csvfile:
  #         reader = csv.reader(csvfile)
  #         for row in reader:
  #             data.append(row)
  #     reply_msg = ""
  #     for row in data:
  #         reply_msg += f"{row[1]}-{row[2]} {row[5]} {row[13]}\n"
  #     line_bot_api.reply_message(
  #         event.reply_token,
  #         TextSendMessage(text=reply_msg)
  #     )
  # else:
  #     line_bot_api.reply_message(
  #         event.reply_token,
  #         TextSendMessage(text=reply_msg)
  #     )

  if working_status:
    sent_msg = event.message.text
    data = []
    professor_list = []
    # 讀取課程資訊
    with open('data.csv', newline='', encoding='utf-8') as csvfile:
      reader = csv.reader(csvfile)
      for row in reader:
        data.append(row)
        professor_list.append(row[13])
    reply_msg = ""
    sent_msg = event.message.text.split(' ')
    # 可能的輸入
    # 輔大資管課程資訊
    # 吳濟聰 敏捷是軟體開發
    # 查詢課程大綱
    if sent_msg[0] == "輔大資管課程資訊":
      mode = "課程大綱"
      reply_msg = "請輸入教授名稱及課堂名稱"
      line_bot_api.reply_message(event.reply_token,
                                 TextSendMessage(text=reply_msg))
    # 查詢開課資訊
    check_professor = [item for item in professor_list if sent_msg[0] in item]
    if mode == "課程大綱" and len(check_professor) > 0:
      # filter_class_outline(sent_msg)
      connect = sqlite3.connect('data.db')
      cursor = connect.cursor()
      field = [
          'teacher_name', 'course_name', 'course_time', 'course_place',
          'course_class', 'course_credit', 'course_background'
      ]
      condition = []

      for index, keyword in enumerate(sent_msg):
        condition.append(f"{field[index]} like '%{keyword}%'")
      sql = f'''
            SELECT 
                course_id,
                course_name, 
                course_type, 
                course_credit, 
                teacher_name,
                url 
            FROM 
                course_info 
            WHERE 
                {' AND '.join(condition)}
            '''
      print('sql:  ', sql)
      cursor.execute(sql)
      res = cursor.fetchall()
      connect.close()

      res = [[str(item) for item in row] for row in res]
      if len(res) > 0:
        line_bot_api.reply_message(event.reply_token,
                                   messages=FlexSendMessage(
                                       alt_text=json.dumps(res,
                                                           ensure_ascii=False),
                                       contents=parse_main_ui(res),
                                   ))
      else:
        reply_msg = '無教授開課資訊'
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text=reply_msg))

    # 圖書館資訊
    if sent_msg[0] == "輔大圖書資訊":
      mode = "圖書館資訊"
      reply_msg = '請輸入書籍名稱或作者名稱'
      line_bot_api.reply_message(event.reply_token,
                                 TextSendMessage(text=reply_msg))
    # if mode == "圖書館資訊" and sent_msg[0] in book_list:
    if sent_msg[0] == "課程心得":
      mode = "課程心得"
      reply_msg = '請輸入教授名稱及課堂名稱'
      line_bot_api.reply_message(event.reply_token,
                                 TextSendMessage(text=reply_msg))
    if mode == "課程心得" and len(check_professor) > 0:
      connect = sqlite3.connect('data.db')
      cursor = connect.cursor()
      field = [
          'teacher_name', 'course_name', 'course_time', 'course_place',
          'course_class', 'course_credit', 'course_background'
      ]
      condition = []

      for index, keyword in enumerate(sent_msg):
        condition.append(f"{field[index]} like '%{keyword}%'")
      sql = f"SELECT * FROM course_info WHERE {' AND '.join(condition)}"
      cursor.execute(sql)
      res = cursor.fetchall()
      connect.close()

      res = [[str(item) for item in row] for row in res]
      print('res: ', res)
      if len(res) > 0:
        line_bot_api.reply_message(
          event.reply_token,
          messages=FlexSendMessage(
            alt_text=','.join([item[5] for item in res]),
            contents=parse_exp_ui(res),
          )
        )
    if sent_msg[0] == "心得":
      reply_msg = ''
      sql = f"SELECT * FROM course_info WHERE course_id = '{sent_msg[1]}'"
      connect = sqlite3.connect('data.db')
      cursor = connect.cursor()
      cursor.execute(sql)
      res = cursor.fetchall()
      connect.close()

      res = [[str(item) for item in row] for row in res]
      print('res: ', res)
      if len(res) > 0:
        line_bot_api.reply_message(
          event.reply_token,
          messages=FlexSendMessage(
            alt_text=','.join([item[5] for item in res]),
            contents=parse_exp_ui(res),
          )
        )
    # if sent_msg[0] == "意見改善":
    #     reply_msg = ''
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=reply_msg)
    #     )

    #     reply_msg = ''
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=reply_msg)
    #     )


# 連接到 SQLite 資料庫（如果不存在，會自動建立一個新的）
conn = sqlite3.connect('data.db')
# 創建一個遊標物件，用來執行 SQL 指令
cursor = conn.cursor()

# 檢查資料庫中是不是已經建立course_info
res = cursor.execute("SELECT name FROM sqlite_master WHERE name='course_info'")
if res.fetchone() is None:
  # 創建一個資料表來儲存 CSV 檔案的資料
  cursor.execute('''CREATE TABLE IF NOT EXISTS course_info (
                    system TEXT,
                    year INTEGER,
                    semester INTEGER,
                    dept TEXT,
                    course_id TEXT,
                    course_name TEXT,
                    course_day TEXT,
                    course_time TEXT,
                    course_room TEXT,
                    course_type TEXT,
                    course_credit INTEGER,
                    teacher_bg TEXT,
                    teacher_title TEXT,
                    teacher_name TEXT,
                    language TEXT,
                    experence TEXT,
                    url TEXT
                  )''')
  # 讀取 CSV 檔案並插入資料到 SQLite 資料庫
  with open('data.csv', newline='', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    next(csv_reader)  # 跳過標題列
    for row in csv_reader:
      cursor.execute(
          'INSERT INTO course_info  \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', row)

# 提交變更並關閉連接
conn.commit()
conn.close()

if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True)
