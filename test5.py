_= '''
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
'''
_= '''
import numpy as np 
from PIL import Image, ImageDraw
import easyocr
import streamlit as st

reader = easyocr.Reader(['ja','en'])
# selected_image = st.file_uploader('TanaMap20250814', type='png')
selected_image = 'TanaMap20250814.png'

original_image = st.empty()
result_image = st.empty()

if (selected_image != None):
    original_image.image(selected_image)
    pil = Image.open(selected_image)
    result = reader.readtext(np.array(pil))
    draw = ImageDraw.Draw(pil)
    for each_result in result:
        draw.rectangle(tuple(each_result[0][0] + each_result[0][2]), outline=(0, 0, 255), width=3)
        st.write(each_result[1])
    result_image.image(pil)
st.stop()
'''

import streamlit as st
from PIL import Image
import easyocr
import cv2
import numpy as np

# 画像読み込み
img = Image.open("TanaMap20250814.png")
st.image(img, caption="画像", use_container_width=True)

# 座標入力
x = st.number_input("x座標", min_value=0)
y = st.number_input("y座標", min_value=0)
w = st.number_input("幅 (w)", min_value=1)
h = st.number_input("高さ (h)", min_value=1)

if st.button("OCR実行"):
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    roi = img_cv[int(y):int(y+h), int(x):int(x+w)]
    rotated = cv2.rotate(roi, cv2.ROTATE_90_CLOCKWISE)

    reader = easyocr.Reader(['ja', 'en'])
    results = reader.readtext(rotated)

    for _, text, conf in results:
        st.write(f"認識結果: {text}（信頼度: {conf:.2f}）")


st.stop()

# 画像読み込み
img = cv2.imread('TanaMap20250814.png')

# R-1の位置（例：手動で指定）
x, y, w, h = 300, 400, 50, 150  # 適宜調整
roi = img[y:y+h, x:x+w]

# 回転して横向きに
rotated = cv2.rotate(roi, cv2.ROTATE_90_CLOCKWISE)

# OCR実行
reader = easyocr.Reader(['ja', 'en'])
results = reader.readtext(rotated)

# 結果表示
for bbox, text, conf in results:
    st.write(f"認識結果: {text}（信頼度: {conf:.2f}）")
st.stop()



_= '''
def authenticate():
    # Secretsからサービスアカウント情報を取得
    credentials_dict = st.secrets["service_account"]
    
    # Credentialsオブジェクト作成
    creds = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    
    return creds

def create_spreadsheet(service):
    spreadsheet_body = {'properties': {'title': 'Streamlit連携テスト'}}
    spreadsheet = service.spreadsheets().create(body=spreadsheet_body,
                                                fields='spreadsheetId').execute()
    return spreadsheet['spreadsheetId']

def write_data(service, spreadsheet_id):
    values = [['名前', 'スコア'], ['鈴木', '95'], ['伊藤', '90'], ['齋藤', '55']]
    body = {'values': values}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

def share_spreadsheet(drive_service, spreadsheet_id, email):
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': email
    }
    drive_service.permissions().create(
        fileId=spreadsheet_id,
        body=permission,
        fields='id'
    ).execute()

# Streamlit UI
st.title("Google Sheets作成＆共有")

if st.button("認証＆スプレッドシート作成"):
    creds = authenticate()
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    spreadsheet_id = "1Zn6StEq2yveZ_ypCV2CXGs8SUPXgLmh3YsMDCNIKdLY"
    # st.success(f"スプレッドシート作成成功！ID: {spreadsheet_id}")
    
    write_data(sheets_service, spreadsheet_id)
    st.info("初期データ書き込み完了。")

    email = st.text_input("共有相手のメールアドレスを入力")
    if email:
        share_spreadsheet(drive_service, spreadsheet_id, email)
        st.success(f"{email} と共有しました！")

'''
