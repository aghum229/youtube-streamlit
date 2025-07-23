import streamlit as st
import requests

from streamlit_qrcode_scanner import qrcode_scanner
# import firebase_admin
# from firebase_admin import credentials, db
import pandas as pd
import os
from simple_salesforce import Salesforce
from datetime import datetime
import re
import time

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
'''

# Função para carregar credenciais
def carregar_credenciais():
    if os.path.exists('.streamlit/secrets.toml'):
        import toml
        secrets = toml.load('.streamlit/secrets.toml')
    else:
        secrets = st.secrets
    return secrets

# Carregar as credenciais
secrets = carregar_credenciais()

# Função de autenticação do Salesforce usando as credenciais do secrets
def authenticate_salesforce():
    # _= '''
    auth_url = f"{secrets['DOMAIN']}/services/oauth2/token"
    auth_data = {
        'grant_type': 'password',
        'client_id': secrets['CONSUMER_KEY'],
        'client_secret': secrets['CONSUMER_SECRET'],
        'username': secrets['USERNAME'],
        'password': secrets['PASSWORD']
    }
    # '''
    _= '''
    auth_url = st.secrets["token_url"]
    auth_data = {
        'grant_type': 'password',
        'client_id': secrets['client_id'],
        'client_secret': secrets['client_secret'],
        'username': secrets['username'],
        'password': secrets['password']
    }
    '''
    try:
        response = requests.post(auth_url, data=auth_data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data['access_token']
        instance_url = token_data['instance_url']
        return Salesforce(instance_url=instance_url, session_id=access_token)
    except requests.exceptions.RequestException as e:
        st.error(f"認証エラー: {e}")
        st.stop()

# Função para consultar Salesforce
def consultar_salesforce(production_order, sf):
    query = f"""
        SELECT Id, Name, snps_um__ProcessName__c, snps_um__ActualQt__c, snps_um__Item__r.Id, 
               snps_um__Item__r.Name, snps_um__ProcessOrderNo__c, snps_um__ProdOrder__r.Id, 
               snps_um__ProdOrder__r.Name, snps_um__Status__c, snps_um__WorkPlace__r.Id, 
               snps_um__WorkPlace__r.Name, snps_um__StockPlace__r.Name, snps_um__Item__c, 
               snps_um__Process__r.AITC_Acumulated_Price__c, AITC_OrderQt__c, snps_um__EndDateTime__c, 
               snps_um__Item__r.AITC_PrintItemName__c
        FROM snps_um__WorkOrder__c 
        WHERE snps_um__ProdOrder__r.Name = '{production_order}'
    """
    try:
        result = sf.query(query)
        records = result['records']
        if not records:
            st.write("❌00 **データの取り出しに失敗しました。**")
            return pd.DataFrame(), None, None, 0.0

        df = pd.DataFrame(records)
        st.session_state.all_data = df.to_dict(orient="records")
        
        df_done = df[df['snps_um__Status__c'] == 'Done']
        if not df_done.empty:
            last_record = df_done.loc[df_done['snps_um__ProcessOrderNo__c'].idxmax()].to_dict()
            cumulative_cost = last_record.get("snps_um__Process__r", {}).get("AITC_Acumulated_Price__c", 0.0)
            if cumulative_cost is None:
                cumulative_cost = 0.0

            father_id = last_record['snps_um__Item__c']
            composition_query = f"""
                SELECT 
                snps_um__ChildItem__r.Name,
                snps_um__AddQt__c
                FROM snps_um__Composition2__c
                WHERE snps_um__ParentItem2__c = '{father_id}'
            """
            composition_result = sf.query(composition_query)
            composition_records = composition_result['records']
            if composition_records:
                material = composition_records[0].get("snps_um__ChildItem__r", {}).get("Name", "N/A")
                material_weight = composition_records[0].get("snps_um__AddQt__c", 0.0)
            else:
                material = "N/A"
                material_weight = 0.0
            return pd.DataFrame([last_record]), material, material_weight, cumulative_cost
        else:
            st.write("❌01 **データの取り出しに失敗しました。**")
        return pd.DataFrame(), None, None, 0.0
    except Exception as e:
        st.error(f"Salesforceクエリエラー: {e}")
        return pd.DataFrame(), None, None, 0.0

# Função para limpar quantidade e converter para float
def clean_quantity(value):
    if isinstance(value, str):
        num = re.sub(r'[^\d.]', '', value)
        return float(num) if num else 0.0
    return float(value) if value else 0.0

# Função para preparar DataFrame simplificado
def simplify_dataframe(df):
    if df.empty:
        return df
    relevant_columns = [
        'snps_um__ProcessName__c',
        'snps_um__ProcessOrderNo__c',
        'snps_um__Status__c',
        'snps_um__WorkPlace__r.Name',
        'snps_um__ActualQt__c',
        'AITC_OrderQt__c'
    ]
    simplified_df = pd.DataFrame()
    for col in relevant_columns:
        if col in df.columns:
            if col == 'snps_um__WorkPlace__r.Name':
                simplified_df[col] = df[col].apply(lambda x: x.get('Name', '') if isinstance(x, dict) else '' if x is None else str(x))
            elif col in ['snps_um__ActualQt__c', 'AITC_OrderQt__c']:
                simplified_df[col] = df[col].apply(clean_quantity)
            else:
                simplified_df[col] = df[col]
    return simplified_df

def update_process_tanaban(sf, process_id):
    try:
        sf.snps_um__Process__c.update(process_id, {"AITC_tanaban00__c": "OK"})
        st.success("AITC_tanaban00__c フィールドに「OK」を書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")

def encontrar_item_por_nome00(sf, item_name):
    query = f"""
        SELECT snps_um__ItemName__c
        FROM snps_um__Item__c
        WHERE snps_um__ItemName__c LIKE '%{item_name}%'
        LIMIT 1
    """
    try:
        result = sf.query(query)
        records = result.get("records", [])
        if records:
            return records[0]["snps_um__ItemName__c"]
        else:
            st.warning(f"品番 {item_name} に一致する snps_um__Item__c が見つかりませんでした。")
            return None
    except Exception as e:
        st.error(f"Item検索エラー: {e}")
        return None

def atualizar_tanabangou(sf, item_id):
    try:
        # sf.snps_um__Item__c.update(item_id, {"AITC_tanabangou00__c": "OK"})
        sf.snps_um__Process__c.update(item_id, {"AITC_tanaban00__c": "OK"})
        st.success("AITC_tanabangou00__c に「OK」を書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")

# WHERE Name LIKE '%{item_name}%' AND snps_um__ProcessOrderNo__c = 999
def encontrar_item_por_nome(sf, item_name):
    query = f"""
        SELECT AITC_ID18__c, Name, snps_um__ProcessOrderNo__c
        FROM snps_um__Process__c
        WHERE Name LIKE '%{item_name}%'
    """
    try:
        result = sf.query(query)
        records = result.get("records", [])
        if records:
            return records[0].get("AITC_ID18__c")
        else:
            st.warning(f"品番 {item_name} に一致する snps_um__Process__c が見つかりませんでした。")
            return None
    except Exception as e:
        st.error(f"Item検索エラー: {e}")
        return None

def atualizar_tanaban(sf, item_id):
    try:
        sf.snps_um__Item__c.update(item_id, {"AITC_tanaban00__c": "OK"})
        st.success("AITC_tanaban00__c に「OK」を書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")

def descrever_item_fields_completo(sf):
    try:
        # fields = sf.snps_um__Item__c.describe()["fields"]
        fields = sf.snps_um__Process__c.describe()["fields"]
        field_info_list = [
            {
                "ラベル": field["label"],
                "API名": field["name"],
                "型": field["type"]
            }
            for field in fields
        ]
        st.write("📋 snps_um__Item__c のフィールド一覧（ラベル・型つき）:")
        st.dataframe(field_info_list)
        return field_info_list
    except Exception as e:
        st.error(f"describe() API エラー: {e}")
        return []

def descrever_process_fields(sf):
    try:
        fields = sf.snps_um__Process__c.describe()["fields"]
        for field in fields:
            if "referenceTo" in field and field["referenceTo"]:
                st.write(f"📌 関係フィールド候補: {field['name']} → 参照先: {field['referenceTo']}")
    except Exception as e:
        st.error(f"describe() エラー: {e}")


# Autenticar no Salesforce
if "sf" not in st.session_state:
    try:
        st.session_state.sf = authenticate_salesforce()
        st.success("Salesforceに正常に接続しました！")
    except Exception as e:
        st.error(f"認証エラー: {e}")
        st.stop()


_= '''
try:
    response = requests.post(token_url, data=payload)
    response.raise_for_status()

    auth_response = response.json()
    access_token = auth_response.get("access_token")
    instance_url = auth_response.get("instance_url")

    if access_token:
        st.write("✅ **成功しました！**")
        # st.write(f"🔑 Access Token: `{access_token[:40]}...`")
        # st.write(f"🌍 Instance URL: `{instance_url}`")
    else:
        st.write("❌ **トークンが受信されませんでした。**")
        st.write(auth_response)
    
except requests.exceptions.RequestException as e:
    print("❌ Salesforce への接続エラー：")
    print(e)
'''

# Inicializar estados necessários
if "production_order" not in st.session_state:
    st.session_state.production_order = None
# if "sf" not in st.session_state:
#     st.session_state.sf = None  # Salesforceオブジェクトを適切に設定
if "show_camera" not in st.session_state:
    st.session_state.show_camera = True
if "data" not in st.session_state:
    st.session_state.data = None
if "owner" not in st.session_state:
    st.session_state.owner = ""
if "quantity" not in st.session_state:
    st.session_state.quantity = 0.0
if "process_order" not in st.session_state:
    st.session_state.process_order = 0
if "material" not in st.session_state:
    st.session_state.material = None
if "material_weight" not in st.session_state:
    st.session_state.material_weight = None
if "cumulative_cost" not in st.session_state:
    st.session_state.cumulative_cost = 0.0
if "manual_input_value" not in st.session_state:
    st.session_state.manual_input_value = ""

manual_input = st.text_input("品番を入力してください (50桁、例: AAAAA-BBB-CCCC):",
                            value=st.session_state.manual_input_value,
                            max_chars=50,
                            key="manual_input")

_= '''
# Opção de digitação manual do production_order
manual_input = st.text_input("生産オーダー番号を入力してください (6桁、例: 000000):",
                            value=st.session_state.manual_input_value,
                            max_chars=6,
                            key="manual_input")
if manual_input and len(manual_input) == 6 and manual_input.isdigit():
    st.session_state.production_order = f"PO-{manual_input.zfill(6)}"
    st.session_state.manual_input_value = manual_input
    st.session_state.show_camera = False
'''

_= '''
# Exibir câmera apenas se production_order for None e show_camera for True
if not st.session_state.production_order and st.session_state.show_camera:
    st.write("QRコードをスキャンして開始してください:")
    production_order = qrcode_scanner(key="qrcode_scanner_fixed")
    if production_order:
        st.session_state.production_order = production_order
        st.session_state.manual_input_value = ""
        st.session_state.show_camera = False
        st.rerun()

# Botão de reexibição sempre visível
if st.button("カメラを再表示"):
    st.session_state.show_camera = True
    st.session_state.production_order = None
    st.session_state.manual_input_value = ""
    st.rerun()
'''

if st.button("関係フィールド詳細を表示"):
    descrever_process_fields(st.session_state.sf)
    
if st.button("フィールド詳細を表示"):
    descrever_item_fields_completo(st.session_state.sf)

# Formulário sempre renderizado
with st.form(key="registro_form"):
    default_quantity = 0.0
    default_process_order = 0
    default_process_order_name = ""
    # st.write(st.session_state)
    if st.session_state.production_order is not None:
        df, material, material_weight, cumulative_cost = consultar_salesforce(st.session_state.production_order, st.session_state.sf)
        if "all_data" in st.session_state and st.session_state.all_data:
            st.write("Salesforceで発見されたすべての記録:")
            simplified_df = simplify_dataframe(pd.DataFrame(st.session_state.all_data))
            st.dataframe(simplified_df)
        if not df.empty:
            st.session_state.data = df.to_dict(orient="records")
            st.session_state.material = material
            st.session_state.material_weight = material_weight
            st.session_state.cumulative_cost = cumulative_cost
            last_record = st.session_state.data[0]
            default_quantity = clean_quantity(last_record.get("snps_um__ActualQt__c") or last_record.get("AITC_OrderQt__c") or 0.0)
            default_process_order = int(last_record.get("snps_um__ProcessOrderNo__c", 0))
            default_process_order_name = last_record.get("snps_um__ProcessName__c")
        else:
            st.session_state.data = None
            st.session_state.material = None
            st.session_state.material_weight = None
            st.session_state.cumulative_cost = 0.0
            st.warning("生産オーダーに該当する 'Done' ステータスの記録が見つかりませんでした。")

    # Campos de entrada
    owner_value = "" if st.session_state.data is None else st.session_state.owner
    owner = st.text_input("所有者 (工程):", key="owner", value=owner_value)
    if st.session_state.data:
        quantity = st.number_input("数量 (工程):", value=default_quantity, key="quantity")
        process_order = st.number_input("工程順序:", value=default_process_order, step=1, key="process_order")
        process_order_name = st.text_input("工程名:", key="process_order_name", value=default_process_order_name)
    else:
        quantity = st.number_input("数量 (工程):", value=0.0, key="quantity", disabled=True)
        process_order = st.number_input("工程順序:", value=0, key="process_order", disabled=True)
        process_order_name = st.text_input("工程名:", key="process_order_name", value="-")


    # Botão de submissão
    submit_button = st.form_submit_button("データベースに保存")
    
    if submit_button:
        _= '''
        item_name_input = st.session_state.manual_input_value.strip()
        st.write(f"入力された品番: '{item_name_input}'")
        item_id = encontrar_item_por_nome(st.session_state.sf, item_name_input)
        '''
        st.write(f"入力された品番: '{manual_input}'")
        manual_input
        item_id = encontrar_item_por_nome(st.session_state.sf, manual_input)
        st.write(f"検索したID: '{item_id}'")
        if item_id:
            atualizar_tanabangou(st.session_state.sf, item_id)

