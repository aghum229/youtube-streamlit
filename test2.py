import streamlit as st
import requests

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
