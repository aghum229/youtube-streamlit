import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# スコープ設定：SheetsとDrive両方
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

# 認証処理
creds = None
if os.path.exists('credentials.json'):
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

# APIクライアントを作成
sheets_service = build('sheets', 'v4', credentials=creds)
drive_service = build('drive', 'v3', credentials=creds)

# スプレッドシート作成
spreadsheet_body = {
    'properties': {'title': 'My Test Spreadsheet'}
}
spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet_body,
                                                   fields='spreadsheetId').execute()
spreadsheet_id = spreadsheet['spreadsheetId']
# print(f'作成されたスプレッドシートのID: {spreadsheet_id}')
st.write(f'作成されたスプレッドシートのID: {spreadsheet_id}')

# 📥 データの書き込み
data = [
    ['名前', 'スコア'],
    ['鈴木', '100'],
    ['伊藤', '90'],
    ['齋藤', '55']
]
sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range='Sheet1!A1',
    valueInputOption='RAW',
    body={'values': data}
).execute()

# 📤 データの読み込み
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range='Sheet1!A1:B3'
).execute()

print('読み込まれたデータ:')
for row in result.get('values', []):
    print(row)

