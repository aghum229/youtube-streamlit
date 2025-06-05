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
        print("✅ 成功した")
        print(f"Access Token: {access_token[:40]}...")
        print(f"Instance URL: {instance_url}")
    else:
        print("❌ トークンが受信されませんでした。")
        print(auth_response)

except requests.exceptions.RequestException as e:
    print("❌ Salesforce への接続エラー：")
    print(e)
