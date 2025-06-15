import streamlit as st
import requests
import json

# url = "https://raw.githubusercontent.com/ユーザー名/リポジトリ名/ブランチ名/フォルダ名/ファイル名.txt"
# response = requests.get(url)
response = requests.get(st.secrets["text_path"])
if response.status_code == 200:
    text_content = response.text
    st.write(text_content)
else:
    st.write(f"Failed to fetch file: {response.status_code}")

_= '''
token = st.secrets["test_text_access_Token"]
repo = st.secrets["test_repo"]
path = st.secrets["test_path"]
branch = "main"
# repo = "ユーザー名/リポジトリ名"
# path = "フォルダ名/ファイル名.txt"
# branch = "main"
message = "Update text file via API"
new_content = "これは新しいテキストの内容です。"
# new_content = text_content + "  \n" + "これは新しいテキストの内容です。"

# ファイルの現在のSHAを取得
url = f"https://api.github.com/repos/{repo}/contents/{path}"
headers = {"Authorization": f"token {token}"}
response = requests.get(url, headers=headers)

if response.status_code == 200:
    sha = response.json()["sha"]

    # 更新リクエスト
    data = {
        "message": message,
        "content": new_content.encode("utf-8").hex(),  # Base64エンコードが必要
        "sha": sha,
        "branch": branch
    }
    st.write(new_content.encode("utf-8").hex())
    update_response = requests.put(url, headers=headers, data=json.dumps(data))

    if update_response.status_code == 200 or update_response.status_code == 201:
        st.write("ファイルを更新しました!")
    else:
        st.write(f"更新に失敗しました: {update_response.status_code}")
else:
    st.write(f"SHAの取得に失敗しました: {response.status_code}")
'''


_= '''
# Streamlitのシークレットから値を取得
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
username = st.secrets["username"]
password = st.secrets["password"]
token_url = st.secrets["token_url"]

# OAuthリクエストの送信
payload = {
    "grant_type": "password",
    "client_id": client_id,
    "client_secret": client_secret,
    "username": username,
    "password": password
}


try:
    response = requests.post(token_url, data=payload)
    response.raise_for_status()

    auth_response = response.json()
    access_token = auth_response.get("access_token")
    instance_url = auth_response.get("instance_url")

    if access_token:
        st.write("✅ **成功しました！**")
        st.write(f"🔑 Access Token: `{access_token[:40]}...`")
        st.write(f"🌍 Instance URL: `{instance_url}`")
    else:
        st.write("❌ **トークンが受信されませんでした。**")
        st.write(auth_response)
    
    
except requests.exceptions.RequestException as e:
    print("❌ Salesforce への接続エラー：")
    print(e)


def add_button():
    st.session_state.button_count += 1

def remove_button(index):
    st.write(index)
    st.session_state.button_names.pop(index)
    st.session_state.button_count -= 1

if 'button_count' not in st.session_state:
    st.session_state.button_count = 0
    st.session_state.button_names = []

st.button("ボタンを追加", on_click=add_button)

for i in range(st.session_state.button_count):
    col1, col2 = st.columns(2)
    with col1:
        button_name = st.text_input(f"ボタン {i+1} の名前:", key=f"button_name_{i}", value=f"ボタン{i+1}")
        st.session_state.button_names.append(button_name)
    with col2:
        st.button(f"{button_name} を削除", on_click=remove_button, args=(i,), key=f"remove_button_{i}")

    if st.button(st.session_state.button_names[i], key=f"dynamic_button_{i}"):
       st.write(f"{st.session_state.button_names[i]} がクリックされました")
'''
