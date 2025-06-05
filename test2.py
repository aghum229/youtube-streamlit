import requests

client_id = "3MVG9pgcF_Z64XnizvSTCn_ECf.zBBPXh8XwWQ.7yM0TXGAAaJ.WWBMiFiciwfsiUZ2vOswYR7Bg84TdPsTe9"
client_secret = "B2F3EDC33E2F07B57E4C9D45C1FA333EC27FCA789F83AC9F8F01030503F92CFF"
username = "s489@aitech-inc.co.jp.umpm.zaikotest"
password = "Aitech489"

URL= "https://aitech--zaikotest.sandbox.my.salesforce.com"

token_url = "https://test.salesforce.com/services/oauth2/token"

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
