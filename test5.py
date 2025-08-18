_= '''
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
'''

# _= '''
import streamlit as st
import easyocr
import numpy as np
import cv2
from PIL import Image
import glob
import os

def preprocess_image(image_np):
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

st.title("複数画像から指定文字を検出して赤い円（○）を描画")

# 🔤 検出したい文字を入力
target_text = st.text_input("検出したい文字を入力してください", value="")
if target_text == "":
    None
else:
    # 📂 同じフォルダ内の画像ファイル一覧を取得（PNG/JPG）
    image_files = sorted(glob.glob("TanaMap*.png") + glob.glob("TanaMap*.jpg") + glob.glob("TanaMap*.jpeg"))
    image_flag = False
    image_search_flag = False
    if not image_files:
        st.warning("画像ファイルが見つかりませんでした。")
    else:
        reader = easyocr.Reader(['ja', 'en'], gpu=False)
        first_char = target_text[0]
        after_hyphen = target_text.split("-")[1]
        
        for image_path in image_files:
            # st.subheader(f"画像ファイル: {os.path.basename(image_path)}")
            if first_char == "完" and os.path.basename(image_path) == "TanaMap20250815_1":
                image_search_flag = True
            elif (first_char == "A" and after_hyphen <= 16) or (first_char == "D" and after_hyphen <= 16) or (first_char == "E" and 51 <= after_hyphen <= 57) or (first_char == "F" and after_hyphen <= 16):
                if os.path.basename(image_path) == "TanaMap20250815_3.png":
                    image_search_flag = True
            elif (first_char == "E" and 31 <= after_hyphen <= 37) or (first_char == "G" and after_hyphen <= 18) or (first_char == "H" and after_hyphen <= 18) or (first_char == "R" and after_hyphen <= 19):
                if os.path.basename(image_path) == "TanaMap20250815_2.png":
                    image_search_flag = True
            elif (first_char == "E" and 38 <= after_hyphen <= 50) or (first_char == "G" and 20 <= after_hyphen <= 33) or (first_char == "H" and 31 <= after_hyphen <= 37):
                if os.path.basename(image_path) == "TanaMap20250815_4.png":
                    image_search_flag = True
            elif (first_char == "A" and 19 <= after_hyphen <= 30) or (first_char == "D" and 18 <= after_hyphen <= 28) or (first_char == "F" and 20 <= after_hyphen <= 32) or (first_char == "H" and 26 <= after_hyphen <= 30) or (first_char == "S" and after_hyphen <= 12):
                if os.path.basename(image_path) == "TanaMap20250815_5.png":
                    image_search_flag = True
            if image_search_flag:
                # 画像読み込みとNumPy変換
                image = Image.open(image_path).convert("RGB")
                image_np = np.array(image)
                # processed = preprocess_image(image_np)
        
                # OCR実行
                results = reader.readtext(image_np)
                target_center = None
        
                for bbox, text, prob in results:
                    if text.strip() == target_text.strip():
                        (tl, tr, br, bl) = bbox
                        center_x = int((tl[0] + br[0]) / 2)
                        center_y = int((tl[1] + br[1]) / 2)
                        target_center = (center_x, center_y)
                        break
        
                # 赤い円（○）を描画
                image_with_circle = image_np.copy()
                if target_center:
                    cv2.circle(image_with_circle, target_center, 50, (255, 0, 0), thickness=8)
                    st.image(image_with_circle, caption=f"{target_text} を検出しました", use_container_width=True)
                    st.success(f"座標: {target_center}")
                    image_flag = True
                    break
                else:
                    None
                    # st.image(image_with_circle, caption=f"{target_text} は検出されませんでした", use_container_width=True)
                    # st.warning(f"{target_text} はこの画像には見つかりませんでした。")
        if image_flag == False:
            st.warning(f"{target_text} はこの画像には見つかりませんでした。")
    st.stop()
# '''
_= '''
import streamlit as st
import easyocr
import numpy as np
import cv2
from PIL import Image
import os

st.title("入力した文字の位置に赤い円（○）を描画")

# 🔤 ユーザー入力欄
target_text = st.text_input("検出したい文字を入力してください", value="368")

image_filename = "TanaMap20250815_2.png"

if not os.path.exists(image_filename):
    st.error(f"画像ファイル '{image_filename}' が見つかりません。")
else:
    image = Image.open(image_filename).convert("RGB")
    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    reader = easyocr.Reader(['ja', 'en'], gpu=False)
    results = reader.readtext(image_np)

    target_center = None

    for bbox, text, prob in results:
        if text.strip() == target_text.strip():
            (tl, tr, br, bl) = bbox
            center_x = int((tl[0] + br[0]) / 2)
            center_y = int((tl[1] + br[1]) / 2)
            target_center = (center_x, center_y)
            break

    if target_center:
        radius_px = 40
        image_with_circle = image_np.copy()
        cv2.circle(image_with_circle, target_center, radius_px, (255, 0, 0), thickness=6)

        st.image(image_with_circle, caption=f"{target_text} の位置に赤い円（○）を描画", use_container_width=True)
        st.success(f"{target_text} を検出しました。座標: {target_center}")
    else:
        st.warning(f"{target_text} は画像内に見つかりませんでした。")

st.stop()
'''




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
