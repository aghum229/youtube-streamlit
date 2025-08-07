import streamlit as st
import requests

from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd
import os
import pytz
from simple_salesforce import Salesforce
from datetime import datetime as dt
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

def atualizar_tanaban_addkari(sf, item_id, zkTana):
    try:
        # sf.snps_um__Item__c.update(item_id, {"AITC_tanabangou00__c": "OK"})
        # sf.snps_um__Process__c.update(item_id, {"AITC_tanaban00__c": "OK棚番"})
        sf.snps_um__Process__c.update(item_id, {"zkTanaban__c": zkTana})
        _= '''
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
        '''
        st.success("「zk棚番」に書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")
        
def atualizar_tanaban_add(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap):
    try:
        # sf.snps_um__Item__c.update(item_id, {"AITC_tanabangou00__c": "OK"})
        # sf.snps_um__Process__c.update(item_id, {"AITC_tanaban00__c": "OK棚番"})
        # sf.snps_um__Process__c.update(item_id, {"zkHinban__c": zkHin})
        # _= '''
        sf.snps_um__Process__c.update(item_id, {
            "zkIkohyoNo__c": zkIko,
            "zkHinban__c": zkHin,
            "zkKanryoKoutei__c": zkKan,
            "zkSuryo__c": zkSu,
            "zkTuikaDatetime__c": zkTuiDa,
            "zkTuikaSya__c": zkTuiSya,
            "zkMap__c": zkMap
        })
        # '''
        st.success("snps_um__Process__c の棚番 '{zkTana}' に移行票No '{zkIko}' を追加しました。")
    except Exception as e:
        st.error(f"更新エラー: {e}")

def atualizar_tanaban_del(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkDelDa, zkDelIko, zkDelSya):
    try:
        # sf.snps_um__Item__c.update(item_id, {"AITC_tanabangou00__c": "OK"})
        # sf.snps_um__Process__c.update(item_id, {"AITC_tanaban00__c": "OK棚番"})
        sf.snps_um__Process__c.update(item_id, {
            "zkIkohyoNo__c": zkIko,
            "zkHinban__c": zkHin,
            "zkKanryoKoutei__c": zkKan,
            "zkSuryo__c": zkSu,
            "zkTuikaDatetime__c": zkTuiDa,
            "zkTuikaSya__c": zkTuiSya,
            "zkMap__c": zkMap,
            "zkDeleteDatetime__c": zkDelDa,
            "zkDeleteIkohyoNo__c": zkDelIko,
            "zkDeleteSya__c": zkDelSya
        })
        st.success("snps_um__Process__c の棚番 '{zkTana}' から移行票No '{zkIko}' を削除しました。")
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

def list_update_zkKari(zkKari, dbItem, listNo, update_value, flag):
    """
    指定されたlistNoの値を更新する関数。
    "-"の場合はupdate_valueで上書き、それ以外はカンマ区切りで追加。

    Parameters:
    - zkKari: dict or list形式のデータ(注記.zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMapの順で処理の事)
    - dbItem: データベースの項目名(注記.表示ラベルではない)
    - listNo: 対象のインデックスまたはキー
    - update_value: 追加する値
    - flag: -1(追加 マップ座標の場合), 0(追加 移行票No以外), 1(追加 移行票Noの場合), 2(削除 移行票No以外), 3(削除 移行票Noの場合)

    Returns:
    - 更新後のzkKari
    """
    global zkSplitNo  # 初期値99
    global zkSplitFlag  # 0:マップ座標以外  1;マップ座標
    zkKari = record[dbItem].splitlines()
    zkSplit = zkKari[listNo].split(",")
    # st.write(f"zkSplitのリスト数：'{len(zkSplit)}'")
    # st.write(f"追加削除フラグ：'{flag}'")
    if flag >= 2:
        if len(zkSplit) > 1:
            if flag == 3:
                for index, item in enumerate(zkSplit):
                    if item == update_value:
                        zkSplitNo = index
                        break  # 条件を満たしたらループを終了
                if zkSplitNo == 99:
                    st.write(f"❌02 **対象の移行票Noはありませんでした。'{update_value}'**")
                    st.stop()  # 以降の処理を止める
            # del zkSplit[zkSplitNo]
            if 0 <= zkSplitNo < len(zkSplit):
                del zkSplit[zkSplitNo]
            else:
                # ログ出力やエラーハンドリング
                st.write(f"zkSplitNo {zkSplitNo} is out of range for zkSplit of length {len(zkSplit)}")
                st.write(f"❌02 **対象の移行票Noはありませんでした。'{update_value}'**")
                st.stop()  # 以降の処理を止める
        else:
            if flag == 3:
                zkSplitNo = 0
            zkSplit[zkSplitNo] = "-"
        zkKari[listNo] = ",".join(zkSplit)
    else:
        if zkKari[listNo] == "-":
            if flag == -1 and zkSplitFlag == 1:
                zkKari[listNo] += "," + update_value
            else:
                zkKari[listNo] = update_value
        else:
            if flag == 1:
                for index, item in enumerate(zkSplit):
                    if item == update_value:
                        st.write(f"❌03 **すでに登録されている移行票Noです。'{update_value}'**")
                        st.stop()  # 以降の処理を止める
                zkSplitFlag = 1
            zkKari[listNo] += "," + update_value
    zkKari = "\n".join(zkKari) if isinstance(zkKari, list) else zkKari
    return zkKari

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
if "manual_input" not in st.session_state:
    st.session_state.manual_input = ""

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
    st.title("作業者コード入力画面")
    st.session_state['owner'] = st.text_input("作業者コード(社員番号)を入力してください (3～4桁、例: 999:",
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

    zkSplitNo = 99
    zkSplitFlag = 0
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
                st.session_state.production_order = None
                # st.session_state.data = None
                # st.session_state.material = None
                # st.session_state.material_weight = None
                # st.session_state.cumulative_cost = 0.0
                st.warning("生産オーダーに該当する 'Done' ステータスの記録が見つかりませんでした。")
                # st.stop()  # 以降の処理を止める
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

        add_del_flag = 0  # 0:追加 1:削除
        left, right = st.columns([0.5, 0.5])
        with left:
            submit_button_add = st.form_submit_button("追加")
        with right:
            submit_button_del = st.form_submit_button("削除")
        if submit_button_add or submit_button_del:
            if submit_button_add:
                add_del_flag = 0
            elif submit_button_del:
                add_del_flag = 1
            _= '''
            item_name_input = st.session_state.manual_input_value.strip()
            st.write(f"入力された品番: '{item_name_input}'")
            item_id = encontrar_item_por_nome(st.session_state.sf, item_name_input)
            '''
            # st.write(f"入力された品番: '{manual_input}'")
            # manual_input
            # item_id = encontrar_item_por_nome00(st.session_state.sf, manual_input)
            # st.write(f"取得した品番: '{item_id}'")
            # if item_id:
                # atualizar_tanabangou(st.session_state.sf, item_id)
            # st.write(f"検索したid: '{default_id}'")        
            item_id = "a1ZQ8000000FB4jMAG"
            # st.write(f"検索したID: '{item_id}'")
            _= '''
            zkTana = """
                完A-1\n完A-2\n完A-3\n完A-4\n完A-5\n完A-6\n完A-7\n完A-8\n完A-9\n完A-10\n完A-11\n完A-12\n完A-13\n完A-14\n完A-15\n完A-16\n完A-17\n完A-18\n完A-19\n完A-20\n
                完B-1\n完B-2\n完B-3\n完B-4\n完B-5\n完B-6\n完B-7\n完B-8\n完B-9\n完B-10\n完B-11\n完B-12\n完B-13\n完B-14\n完B-15\n完B-16\n完B-17\n完B-18\n完B-19\n完B-20\n
                完C-1\n完C-2\n完C-3\n完C-4\n完C-5\n完C-6\n完C-7\n完C-8\n完C-9\n完C-10\n完C-11\n完C-12\n完C-13\n完C-14\n完C-15\n完C-16\n完C-17\n完C-18\n完C-19\n完C-20\n
                完D-1\n完D-2\n完D-3\n完D-4\n完D-5\n完D-6\n完D-7\n完D-8\n完D-9\n完D-10\n完D-11\n完D-12\n完D-13\n完D-14\n完D-15\n完D-16\n完D-17\n完D-18\n完D-19\n完D-20\n
                A-1\nA-2\nA-3\nA-4\nA-5\nA-6\nA-7\nA-8\nA-9\nA-10\nA-11\nA-12\nA-13\nA-14\nA-15\nA-16\nA-17\nA-18\nA-19\nA-20\nA-21\nA-22\nA-23\nA-24\nA-25\nA-26\nA-27\nA-28\nA-29\nA-30\n
                D-1\nD-2\nD-3\nD-4\nD-5\nD-6\nD-7\nD-8\nD-9\nD-10\nD-11\nD-12\nD-13\nD-14\nD-15\nD-16\nD-17\nD-18\nD-19\nD-20\nD-21\nD-22\nD-23\nD-24\nD-25\nD-26\nD-27\nD-28\nD-29\nD-30\n
                E-31\nE-32\nE-33\nE-34\nE-35\nE-36\nE-37\nE-38\nE-39\nE-40\nE-41\nE-42\nE-43\nE-44\nE-45\nE-46\nE-47\nE-8\nE-49\nE-50\nE-51\nE-52\nE-53\nE-54\nE-55\nE-56\nE-57\nE-58\nE-59\nE-60\nE-61\nE-62\nE-63\nE-64\nE-65\nE-66\nE-67\nE-68\nE-69\nE-70\n
                F-1\nF-2\nF-3\nF-4\nF-5\nF-6\nF-7\nF-8\nF-9\nF-10\nF-11\nF-12\nF-13\nF-14\nF-15\nF-16\nF-17\nF-18\nF-19\nF-20\nF-21\nF-22\nF-23\nF-24\nF-25\nF-26\nF-27\nF-28\nF-29\nF-30\nF-31\nF-32\nF-33\nF-34\nF-35\nF-36\nF-37\nF-38\nF-39\nF-40\n
                G-1\nG-2\nG-3\nG-4\nG-5\nG-6\nG-7\nG-8\nG-9\nG-10\nG-11\nG-12\nG-13\nG-14\nG-15\nG-16\nG-17\nG-18\nG-19\nG-20\nG-21\nG-22\nG-23\nG-24\nG-25\nG-26\nG-27\nG-28\nG-29\nG-30\nG-31\nG-32\nG-33\nG-34\nG-35\nG-36\nG-37\nG-38\nG-39\nG-40\n
                H-1\nH-2\nH-3\nH-4\nH-5\nH-6\nH-7\nH-8\nH-9\nH-10\nH-11\nH-12\nH-13\nH-14\nH-15\nH-16\nH-17\nH-18\nH-19\nH-20\nH-21\nH-22\nH-23\nH-24\nH-25\nH-26\nH-27\nH-28\nH-29\nH-30\nH-31\nH-32\nH-33\nH-34\nH-35\nH-36\nH-37\nH-38\nH-39\nH-40\n
                R-1\nR-2\nR-3\nR-4\nR-5\nR-6\nR-7\nR-8\nR-9\nR-10\nR-11\nR-12\nR-13\nR-14\nR-15\nR-16\nR-17\nR-18\nR-19\nR-20\n
                S-1\nS-2\nS-3\nS-4\nS-5\nS-6\nS-7\nS-8\nS-9\nS-10\nS-11\nS-12\nS-13\nS-14\nS-15\nS-16\nS-17\nS-18\nS-19\nS-20
                """
            '''
            # atualizar_tanaban_addkari(st.session_state.sf, item_id, zkTana)
            # st.stop()  # 以降の処理を止める
            
            tanaban = "完A-3"  # 仮で設定
            listCount = 0
            listCountEtc = 0
            listAdd = 0  # リストに追加する場合は 1 
            listNumber = 0
            zkTana = ""
            zkIko = ""
            zkHin = ""
            zkKan = ""
            zkSu = ""
            zkTuiDa = ""
            zkTuiSya = ""
            zkMap = ""
            zkDelDa = ""
            zkDelIko = ""
            zkDelSya = ""
            zkShoBu = ""
            zkShoU = ""
            record = encontrar_item_por_nome(st.session_state.sf, item_id)
            if record:
                # zkTana = record["zkTanaban__c"].split(",")   # zk棚番
                # listCount = len(zkTana)
                zkTana_list = record["zkTanaban__c"].splitlines()
                listCount = len(zkTana_list)
                if listCount > 2:
                    for index, item in enumerate(zkTana_list):
                        # st.write(f"for文で検索した棚番: '{item}'") 
                        # st.write(f"検索させる棚番: '{tanaban}'")  
                        if item == tanaban:
                            listNumber = index
                            listAdd = 0
                            break  # 条件を満たしたらループを終了
                        else:
                            listAdd = 1
                else:
                    if listCount == 1:
                        if zkTana_list != tanaban:
                            listAdd = 1
                        else:
                            listNumber = 0
                    else:
                        if zkTana_list[0] != tanaban and zkTana_list[1] != tanaban:
                            listAdd = 1
                        elif zkTana_list[0] == tanaban:
                            listNumber = 0
                        else:
                            listNumber = 1
                datetime_str = dt.now(jst).strftime("%Y/%m/%d %H:%M:%S")
                # tdatetime = dt.strptime(datetime_str, '%Y/%m/%d %H:%M:%S')
                if listAdd == 1: # 棚番が無い場合
                    st.write(f"❌04 **棚番 '{tanaban}' の追加は許可されてません。**")
                    st.stop()  # 以降の処理を止める
                    _= '''
                    # zkTana = f"{record["zkTanaban__c"]},{tanaban}"
                    zkTana = record["zkTanaban__c"] + "\n" + tanaban
                    zkIko = record["zkIkohyoNo__c"] + "\n" + st.session_state.production_order  # zk移行票No
                    zkHin = record["zkHinban__c"] + "\n" + hinban   # zk品番
                    zkKan = record["zkKanryoKoutei__c"] + "\n" + process_order_name   # zk完了工程
                    zkSu = f"{record["zkSuryo__c"]}\n{quantity}"   # zk数量
                    zkTuiDa = f"{record["zkTuikaDatetime__c"]}\n{datetime_str}"   # zk追加日時
                    zkTuiSya = record["zkTuikaSya__c"] + "\n" + owner   # zk追加者
                    zkMap = record["zkMap__c"] + "\n" + "-"   # zkマップ座標
                    # zkDelDa = record["zkDeleteDatetime__c"] + "," +    # zk直近削除日時
                    # zkDelIko = record["zkDeleteIkohyoNo__c"] + "," +    # zk直近削除移行票No
                    # zkDelSya = record["zkDeleteSya__c"] + "," +    # zk直近削除者
                    # zkShoBu = record["zkShortcutButton__c"] + "\n" +    # zkショートカットボタン
                    # zkShoU = record["zkShortcutUser__c"] + "\n" +    # zkショートカットユーザー
                    '''
                else:
                    # print(f"zkIkohyoNo__c の型: {type(record.get('zkIkohyoNo__c'))}")
                    # print(f"値: {record.get('zkIkohyoNo__c')}")
                    # zkIko = record["zkIkohyoNo__c"].splitlines()   # zk移行票No
                    zkIko_raw = record.get("zkIkohyoNo__c", "")
                    if isinstance(zkIko_raw, str):
                        zkIko = zkIko_raw.splitlines()
                    else:
                        zkIko = []
                    listCountEtc = len(zkIko)
                    st.write(listCountEtc)
                    st.write(listCount)
                    if listCountEtc != listCount: # 棚番が追加されない限り、あり得ない分岐(初期設定時のみ使用)
                        st.write(f"❌05 **移行票Noリスト '{zkIko}' の追加は許可されてません。**")
                        st.stop()  # 以降の処理を止める
                        # _= '''
                        zkKari = "-"
                        separator = "\n"
                        zkIko = f"{separator.join([zkKari] * listCount)}"
                        # st.write(zkIko)
                        zkHin = zkIko
                        zkKan = zkIko
                        zkSu = zkIko
                        zkTuiDa = zkIko
                        zkTuiSya = zkIko
                        zkMap = zkIko
                        # zkDelDa = zkDelDa
                        # zkDelIko = zkDelDa
                        # zkDelSya = zkDelDa
                        # zkShoBu = zkIko
                        # zkShoU = zkIko
                        # '''
                    else:
                        st.write(f"Index: '{listNumber}'") 
                        if add_del_flag == 0: # 追加の場合
                            zkIko = list_update_zkKari(zkIko, "zkIkohyoNo__c", listNumber, st.session_state.production_order, 1)   # zk棚番
                            zkHin = list_update_zkKari(zkHin, "zkHinban__c", listNumber, hinban, 0)   # zk品番
                            zkKan = list_update_zkKari(zkKan, "zkKanryoKoutei__c", listNumber, process_order_name, 0)   # zk完了工程
                            zkSu = list_update_zkKari(zkSu, "zkSuryo__c", listNumber, f"{quantity}", 0)   # zk数量
                            zkTuiDa = list_update_zkKari(zkTuiDa, "zkTuikaDatetime__c", listNumber, datetime_str, 0)   # zk追加日時
                            zkTuiSya = list_update_zkKari(zkTuiSya, "zkTuikaSya__c", listNumber, owner, 0)   # zk追加者
                            zkMap = list_update_zkKari(zkMap, "zkMap__c", listNumber, "-", -1)   # zkマップ座標
                        else: # 削除の場合
                            zkIko = list_update_zkKari(zkIko, "zkIkohyoNo__c", listNumber, st.session_state.production_order, 3)   # zk棚番
                            zkHin = list_update_zkKari(zkHin, "zkHinban__c", listNumber, hinban, 2)   # zk品番
                            zkKan = list_update_zkKari(zkKan, "zkKanryoKoutei__c", listNumber, process_order_name, 2)   # zk完了工程
                            zkSu = list_update_zkKari(zkSu, "zkSuryo__c", listNumber, f"{quantity}", 2)   # zk数量
                            zkTuiDa = list_update_zkKari(zkTuiDa, "zkTuikaDatetime__c", listNumber, datetime_str, 2)   # zk追加日時
                            zkTuiSya = list_update_zkKari(zkTuiSya, "zkTuikaSya__c", listNumber, owner, 2)   # zk追加者
                            zkMap = list_update_zkKari(zkMap, "zkMap__c", listNumber, "-", 2)   # zkマップ座標
                            zkDelDa = datetime_str   # zk直近削除日時
                            zkDelIko = st.session_state.production_order   # zk直近削除移行票No
                            zkDelSya = owner   # zk直近削除者
                        _= '''
                        zkHin = record["zkHinban__c"].splitlines()   # zk品番
                        zkKan = record["zkKanryoKoutei__c"].splitlines()   # zk完了工程
                        zkSu = record["zkSuryo__c"].splitlines()   # zk数量
                        zkTuiDa = record["zkTuikaDatetime__c"].splitlines()   # zk追加日時
                        zkTuiSya = record["zkTuikaSya__c"].splitlines()   # zk追加者
                        zkMap = record["zkMap__c"].splitlines()   # zkマップ座標
                        '''
                        _= '''
                        if zkIko[listNumber] == "-":
                            zkIko[listNumber] = st.session_state.production_order   # zk棚番
                        else:
                            zkIko[listNumber] = zkIko[listNumber] + "," + st.session_state.production_order   # zk棚番
                        if zkHin[listNumber] == "-":
                            zkHin[listNumber] = hinban   # zk品番
                        else:
                            zkHin[listNumber] = zkHin[listNumber] + "," + hinban   # zk品番
                        if zkKan[listNumber] == "-":
                            zkKan[listNumber] = process_order_name   # zk完了工程
                        else:
                            zkKan[listNumber] = zkKan[listNumber] + "," + process_order_name   # zk完了工程
                        zkSu[listNumber] = f"{quantity}"   # zk数量
                        zkTuiDa[listNumber] = datetime_str   # zk追加日時
                        zkTuiSya[listNumber] = owner   # zk追加者
                        zkMap[listNumber] = "-"   # zkマップ座標
                        '''
                        _= '''
                        zkIko = "\n".join(zkIko) if isinstance(zkIko, list) else zkIko
                        zkHin = "\n".join(zkHin) if isinstance(zkHin, list) else zkHin
                        zkKan = "\n".join(zkKan) if isinstance(zkKan, list) else zkKan
                        zkSu = "\n".join(zkSu) if isinstance(zkSu, list) else zkSu
                        # if isinstance(zkSu, list):
                        #     zkSu = "\n".join(str(item) for item in zkSu)
                        zkTuiDa = "\n".join(zkTuiDa) if isinstance(zkTuiDa, list) else zkTuiDa
                        zkTuiSya = "\n".join(zkTuiSya) if isinstance(zkTuiSya, list) else zkTuiSya
                        zkMap = "\n".join(zkMap) if isinstance(zkMap, list) else zkMap
                        '''
                    _= '''
                    zkHin = record["zkHinban__c"].splitlines()   # zk品番
                    zkKan = record["zkKanryoKoutei__c"].splitlines()   # zk完了工程
                    zkSu = record["zkSuryo__c"].splitlines()   # zk数量
                    zkTuiDa = record["zkTuikaDatetime__c"].splitlines()   # zk追加日時
                    zkTuiSya = record["zkTuikaSya__c"].splitlines()   # zk追加者
                    zkMap = record["zkMap__c"].splitlines()   # zkマップ座標
                    zkDelDa = record["zkDeleteDatetime__c"].split(",")   # zk直近削除日時
                    zkDelIko = record["zkDeleteIkohyoNo__c"].split(",")   # zk直近削除移行票No
                    zkDelSya = record["zkDeleteSya__c"].split(",")   # zk直近削除者
                    zkShoBu = record["zkShortcutButton__c"].splitlines()   # zkショートカットボタン
                    zkShoU = record["zkShortcutUser__c"].splitlines()   # zkショートカットユーザー
                    '''
            
            if st.session_state.owner is None:
                st.write(f"❌06 **作業者コード '{owner}' が未入力です。**")
                st.stop()  # 以降の処理を止める
            # st.session_state.should_rerun = True
            # _= '''
            if item_id:
                # atualizar_tanabangou(st.session_state.sf, item_id)
                # atualizar_tanaban(st.session_state.sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkDelDa, zkDelIko, zkDelSya)
                # datetime_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                if add_del_flag == 0: # 追加の場合
                    atualizar_tanaban_add(st.session_state.sf, item_id, tanaban, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap)
                else: # 削除の場合
                    atualizar_tanaban_del(st.session_state.sf, item_id, tanaban, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkDelDa, zkDelIko, zkDelSya)
                # _= '''
                st.session_state.production_order = None
                # st.session_state.data = None
                # st.session_state.material = None
                # st.session_state.material_weight = None
                # st.session_state.cumulative_cost = 0.0
                st.session_state.manual_input_value = ""
                # st.session_state.manual_input = ""  # セッション状態を空にする
                # if st.session_state.get("should_rerun"):
                #     st.session_state.should_rerun = False
                #     st.experimental_rerun()
                # '''
                _= '''
                reset_keys = {
                    "production_order": None,
                    "data": None,
                    "material": None,
                    "material_weight": None,
                    "cumulative_cost": 0.0,
                    "manual_input_value": ""
                }
                for key, value in reset_keys.items():
                    st.session_state[key] = value
                st.experimental_rerun()
                '''
            # '''

