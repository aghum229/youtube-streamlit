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
import easyocr
import numpy as np
import cv2
from PIL import Image
import os

st.title("数字265の位置に赤丸を描画")

image_filename = "TanaMap20250815_2.png"

if not os.path.exists(image_filename):
    st.error(f"画像ファイル '{image_filename}' が見つかりません。")
else:
    image = Image.open(image_filename).convert("RGB")
    image_np = np.array(image)

    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(image_np)

    target_text = "265"
    target_center = None

    for bbox, text, prob in results:
        if text == target_text:
            (tl, tr, br, bl) = bbox
            center_x = int((tl[0] + br[0]) / 2)
            center_y = int((tl[1] + br[1]) / 2)
            target_center = (center_x, center_y)
            break

    if target_center:
        # 赤丸描画（直径5mm ≒ 半径9〜10px）
        radius_px = 20
        image_with_circle = image_np.copy()
        cv2.circle(image_with_circle, target_center, radius_px, (255, 0, 0), thickness=2)

        st.image(image_with_circle, caption="167の位置に赤丸を描画", use_column_width=True)
        st.success(f"167 を検出しました。座標: {target_center}")
    else:
        st.warning("167 は画像内に見つかりませんでした。")

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
