import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build


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

