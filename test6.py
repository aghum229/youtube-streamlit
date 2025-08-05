import streamlit as st
import requests

from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd
import os
import pytz
from simple_salesforce import Salesforce
from datetime import datetime
import re
import time
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
import toml


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

# Definir o escopo
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Acessar as credenciais do Streamlit secrets
credentials = secrets["google_service_account"]

service_account_info = secrets["firebase"].copy()
# 改行コードを修復
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
credentials_dict = {
    "type": service_account_info["type"],
    "project_id": service_account_info["project_id"],
    "private_key_id": service_account_info["private_key_id"],
    "private_key": service_account_info["private_key"],
    "client_email": service_account_info["client_email"],
    "client_id": service_account_info["client_id"],
    "auth_uri": service_account_info["auth_uri"],
    "token_uri": service_account_info["token_uri"],
    "auth_provider_x509_cert_url": service_account_info["auth_provider_x509_cert_url"],
    "client_x509_cert_url": service_account_info["client_x509_cert_url"],
    "universe_domain": service_account_info["universe_domain"],
}

# Definir o fuso horário do Japão (JST)
jst = pytz.timezone('Asia/Tokyo')


# Função de autenticação do Salesforce usando as credenciais do secrets
def authenticate_salesforce():
    auth_url = f"{secrets['DOMAIN']}/services/oauth2/token"
    auth_data = {
        'grant_type': 'password',
        'client_id': secrets['CONSUMER_KEY'],
        'client_secret': secrets['CONSUMER_SECRET'],
        'username': secrets['USERNAME'],
        'password': secrets['PASSWORD']
    }
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
               snps_um__Item__r.AITC_PrintItemName__c, snps_um__Process__r.AITC_ID18__c
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

def atualizar_tanaban_add(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap):
    try:
        # sf.snps_um__Item__c.update(item_id, {"AITC_tanabangou00__c": "OK"})
        # sf.snps_um__Process__c.update(item_id, {"AITC_tanaban00__c": "OK棚番"})
        sf.snps_um__Process__c.update(item_id, {
            "zkTanaban__c": zkTana,
            "zkIkohyoNo__c": zkIko,
            "zkHinban__c": zkHin,
            "zkKanryoKoutei__c": zkKan,
            "zkSuryo__c": zkSu,
            "zkTuikaDatetime__c": zkTuiDa,
            "zkTuikaSya__c": zkTuiSya,
            "zkMap__c": zkMap
        })
        st.success("AITC_tanabangou00__c に「OK棚番00」、AITC_hinban00__c に「OK品番00」を書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")

def atualizar_tanaban_del(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkMap, zkDelDa, zkDelIko, zkDelSya):
    try:
        # sf.snps_um__Item__c.update(item_id, {"AITC_tanabangou00__c": "OK"})
        # sf.snps_um__Process__c.update(item_id, {"AITC_tanaban00__c": "OK棚番"})
        sf.snps_um__Process__c.update(item_id, {
            "zkTanaban__c": zkTana,
            "zkIkohyoNo__c": zkIko,
            "zkHinban__c": zkHin,
            "zkKanryoKoutei__c": zkKan,
            "zkSuryo__c": zkSu,
            "zkMap__c": zkMap,
            "zkDeleteDatetime__c": zkDelDa,
            "zkDeleteIkohyoNo__c": zkDelIko,
            "zkDeleteSya__c": zkDelSya
        })
        st.success("AITC_tanabangou00__c に「OK棚番00」、AITC_hinban00__c に「OK品番00」を書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")

# WHERE Name LIKE '%{item_name}%' AND snps_um__ProcessOrderNo__c = 999
def encontrar_item_por_nome(sf, item_id):
    query = f"""
        SELECT AITC_ID18__c, Name, zkShortcutButton__c, zkShortcutUser__c,
            zkTanaban__c, zkIkohyoNo__c ,zkHinban__c, zkKanryoKoutei__c,
            zkSuryo__c, zkTuikaDatetime__c, zkTuikaSya__c, zkMap__c,
            zkDeleteDatetime__c, zkDeleteIkohyoNo__c, zkDeleteSya__c
        FROM snps_um__Process__c
        WHERE AITC_ID18__c = '{item_id}'
    """
    try:
        result = sf.query(query)
        records = result.get("records", [])
        if records:
            return records[0]
        else:
            st.warning(f"ID(18桁) {item_id} に一致する snps_um__Process__c が見つかりませんでした。")
            return None
    except Exception as e:
        st.error(f"ID(18桁)検索エラー: {e}")
        return None

def encontrar_item_por_nome(sf, item_name):
    query = f"""
        SELECT Name, snps_um__ProcessOrderNo__c
        FROM snps_um__Process__c
        WHERE Name LIKE '%{item_name}%'
    """
    try:
        result = sf.query(query)
        records = result['records']
        # records = result.get("records", [])
        if records:
            return records[0].get("Name")
        else:
            st.warning(f"品番 {item_name} に一致する snps_um__Process__c が見つかりませんでした。")
            return None
    except Exception as e:
        st.error(f"Item検索エラー: {e}")
        return None

        # WHERE snps_um__ItemName__c LIKE '%{item_name}%'
def encontrar_item_por_nome00(sf, item_name):
    query = f"""
        SELECT snps_um__ItemName__c
        FROM snps_um__Item__c
        LIMIT 10
    """
    try:
        result = sf.query(query)
        records = result['records']
        # records = result.get("records", [])
        if records:
            return records[0]["snps_um__ItemName__c"]
        else:
            st.warning(f"品番 {item_name} に一致する snps_um__Item__c が見つかりませんでした。")
            return None
    except Exception as e:
        st.error(f"Item検索エラー: {e}")
        return None

# Autenticar no Salesforce
if "sf" not in st.session_state:
    try:
        st.session_state.sf = authenticate_salesforce()
        st.success("Salesforceに正常に接続しました！")
    except Exception as e:
        st.error(f"認証エラー: {e}")
        st.stop()


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
if 'update' not in st.session_state:
    st.session_state['update'] = False
if 'mostrar_sucesso' not in st.session_state:
    st.session_state['mostrar_sucesso'] = False
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

if "user_code_entered" not in st.session_state:
    st.session_state.user_code_entered = False
    st.session_state.user_code = ""
    
if not st.session_state.user_code_entered:
    st.markdown(
        """
        <style>
        input[type="text"], input[type="password"] {
            font-size: 40px !important;
            padding-top: 16px !important;
            padding-bottom: 16px !important;
            line-height: 2.5 !important;   /* 高さ調整のキモ */
            box-sizing: border-box !important;
        }
        
        /* 親コンテナの余白にも調整を加える */
        div[data-testid="stTextInput"] {
            padding-top: 8px !important;
            padding-bottom: 8px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.session_state['owner'] = st.text_input("担当者コードを入力してください (3～4桁、例: 999:",
                                              max_chars=4,
                                              key="owner_input")
    
    if st.session_state['owner']:  # 入力があれば保存して完了フラグを立てる
        st.session_state.user_code = st.session_state['owner']
        st.session_state.user_code_entered = True
        st.rerun()  # 再描画して次のステップへ
else:
    _= '''
    # 入力完了後はメイン処理を表示
    st.title("メイン画面")
    st.write(f"入力されたコード: {st.session_state.user_code}")

    # ここに本処理を記述
    st.success("ここからメイン処理を開始します！")
    '''
    
    _= '''
    # Controle de exibição: sucesso ou formulário
    if st.session_state['mostrar_sucesso']:
        if st.session_state['update']:
            st.success("登録が正常に更新されました！")
        else:
            st.success("登録が正常に完了しました！")
    '''

    st.markdown(
        """
        <style>
        input[type="text"], input[type="number"] {
            font-size: 40px !important;
            padding-top: 16px !important;
            padding-bottom: 16px !important;
            line-height: 2.5 !important;   /* 高さ調整のキモ */
            box-sizing: border-box !important;
        }
        
        /* 親コンテナの余白にも調整を加える */
        div[data-testid="stTextInput"] {
            padding-top: 8px !important;
            padding-bottom: 8px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    _= '''
    manual_input = st.text_input("品番を入力してください (50桁、例: AAAAA-BBB-CCCC):",
                                value=st.session_state.manual_input_value,
                                max_chars=50,
                                key="manual_input")
    '''
    
    # _= '''
    # Opção de digitação manual do production_order
    manual_input = st.text_input("生産オーダー番号を入力してください (6桁、例: 000000):",
                                value=st.session_state.manual_input_value,
                                max_chars=6,
                                key="manual_input")
    if manual_input and len(manual_input) == 6 and manual_input.isdigit():
        st.session_state.production_order = f"PO-{manual_input.zfill(6)}"
        st.session_state.manual_input_value = manual_input
        st.session_state.show_camera = False
    # '''
    
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
    
    # Formulário sempre renderizado
    with st.form(key="registro_form"):
        default_quantity = 0.0
        default_process_order = 0
        default_process_order_name = ""
        default_id = ""
        default_hinban = ""
        default_hinmei = ""
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
                # st.write(last_record)
                default_quantity = clean_quantity(last_record.get("snps_um__ActualQt__c") or last_record.get("AITC_OrderQt__c") or 0.0)
                default_process_order = int(last_record.get("snps_um__ProcessOrderNo__c", 0))
                default_process_order_name = last_record.get("snps_um__ProcessName__c")
                default_id = last_record.get("snps_um__Process__r", {}).get("AITC_ID18__c", "")
                default_hinban = last_record.get("snps_um__Item__r", {}).get("Name", "")
                default_hinmei = last_record.get("snps_um__Item__r", {}).get("AITC_PrintItemName__c", "")
            else:
                st.session_state.data = None
                st.session_state.material = None
                st.session_state.material_weight = None
                st.session_state.cumulative_cost = 0.0
                st.warning("生産オーダーに該当する 'Done' ステータスの記録が見つかりませんでした。")
        else:
            st.warning("データが見つかりませんでした。")
    
        # Campos de entrada
        owner_value = "" if st.session_state.data is None else st.session_state.owner
        owner = st.text_input("所有者 (工程):", key="owner", value=owner_value)
        if st.session_state.data:
            quantity = st.number_input("数量 (工程):", value=default_quantity, key="quantity")
            process_order = st.number_input("工程順序:", value=default_process_order, step=1, key="process_order")
            process_order_name = st.text_input("工程名:", key="process_order_name", value=default_process_order_name)
            hinban = st.text_input("品番:", key="hinban", value=default_hinban)
            hinmei = st.text_input("品名:", key="hinmei", value=default_hinmei)
        else:
            quantity = st.number_input("数量 (工程):", value=0.0, key="quantity", disabled=True)
            process_order = st.number_input("工程順序:", value=0, key="process_order", disabled=True)
            process_order_name = st.text_input("工程名:", key="process_order_name", value="-")
            hinban = st.text_input("品番:", key="hinban", value="-")
            hinmei = st.text_input("品名:", key="hinmei", value="-")
    
        submit_button = st.form_submit_button("データベースに保存")
        
        if submit_button:
            _= '''
            item_name_input = st.session_state.manual_input_value.strip()
            st.write(f"入力された品番: '{item_name_input}'")
            item_id = encontrar_item_por_nome(st.session_state.sf, item_name_input)
            '''
            #st.write(f"入力された品番: '{manual_input}'")
            # manual_input
            #item_id = encontrar_item_por_nome00(st.session_state.sf, manual_input)
            #st.write(f"取得した品番: '{item_id}'")
            # if item_id:
                # atualizar_tanabangou(st.session_state.sf, item_id)
            # st.write(f"検索したid: '{default_id}'")        
            item_id = "a1ZQ8000000FB4jMAG"
            # st.write(f"検索したID: '{item_id}'")
            
            record = encontrar_item_por_nome(st.session_state.sf, item_id)
            if record:
                st.write("名称:", record["Name"])
                st.write("追加者:", record["zkTuikaSya__c"])
                st.write("削除日時:", record["zkDeleteDatetime__c"])
                # 他にも必要な項目を好きな順に表示可能
            
            if item_id:
                # atualizar_tanabangou(st.session_state.sf, item_id)
                # atualizar_tanaban(st.session_state.sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkDelDa, zkDelIko, zkDelSya)
                datetime_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                atualizar_tanaban_add(st.session_state.sf, item_id, "H-1", st.session_state.production_order, hinban, process_order_name, quantity, datetime_str, owner, "-")
                # atualizar_tanaban_del(st.session_state.sf, item_id, "H-1", st.session_state.production_order, hinban, process_order_name, quantity, "-", datetime_str, st.session_state.production_order, owner)

    _= '''
    # Botão de submissão
    submit_button = st.form_submit_button("Firebaseに保存")

    # Lógica de gravação
    if submit_button and st.session_state.data is not None:
        owner_input = st.session_state.get("owner", "").strip()
        if not owner_input:
            st.error("'所有者' フィールドを入力してください。")
        else:
            st.write("ボタンが押されました。")

            quantity_value = st.session_state["quantity"]
            process_order_value = int(st.session_state["process_order"])
            record = st.session_state.data[0]
            datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            date_only = datetime.now().strftime("%Y-%m-%d")

            work_place = record.get("snps_um__WorkPlace__r", {}).get("Name", "")

            data_to_save = {
                "datetime": datetime_str,
                "production_order": st.session_state.production_order,
                "quantity": quantity_value,
                "owner": owner_input,
                "product_code": record.get("snps_um__Item__r", {}).get("Name", "N/A"),
                "process_name": record.get("snps_um__ProcessName__c", ""),
                "process_order": process_order_value,
                "work_place": work_place,
                "cumulative_cost": st.session_state.cumulative_cost,
                "material": st.session_state.material if st.session_state.material is not None else "N/A",
                "material_provision_type": "Manual",
                "material_weight": st.session_state.material_weight if st.session_state.material_weight is not None else 0.0
            }

            exists, existing_key = check_existing_record_with_date(st.session_state.production_order, date_only, data_to_save)
            if exists:
                st.warning("この記録は既に存在します。")
                st.session_state.production_order = None
                st.session_state.manual_input_value = ""
                st.session_state.data = None
                st.session_state.all_data = None
                st.session_state.material = None
                st.session_state.material_weight = None
                st.session_state.cumulative_cost = 0.0
                st.session_state.show_camera = True
                st.rerun()
            else:
                update_exists, update_key = check_for_update(st.session_state.production_order, date_only)
                if update_exists:
                    update_firebase(update_key, data_to_save)
                    st.success("更新が成功しました。")
                else:
                    record_id = gravar_firebase(data_to_save)
                    st.success(f"ID {record_id} の記録が保存されました")
                time.sleep(2)
                verified_record = verify_last_record(record_id if not update_exists else update_key)
                if verified_record:
                    st.write(f"確認: ID {record_id if not update_exists else update_key} の記録がFirebaseに正常に保存されました。")
                else:
                    st.error(f"エラー: ID {record_id if not update_exists else update_key} の記録の確認に失敗しました。")
                
                st.session_state.production_order = None
                st.session_state.manual_input_value = ""
                st.session_state.data = None
                st.session_state.all_data = None
                st.session_state.material = None
                st.session_state.material_weight = None
                st.session_state.cumulative_cost = 0.0
                st.session_state.show_camera = True
                st.rerun()

    '''
