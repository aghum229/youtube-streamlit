import streamlit as st
import requests

from streamlit_qrcode_scanner import qrcode_scanner
import pandas as pd
import os
import pytz
from simple_salesforce import Salesforce
from datetime import datetime as dt
import re
# import time
# import gspread
# from google.oauth2.service_account import Credentials
# from gspread_dataframe import set_with_dataframe
import toml
import streamlit.components.v1 as components


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
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Acessar as credenciais do Streamlit secrets
# credentials = secrets["google_service_account"]

_= '''
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
'''

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

def atualizar_tanaban_addkari(sf, item_id):  # 棚番書き込み専用
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
    try:
        sf.snps_um__Process__c.update(item_id, {"zkTanaban__c": zkTana})
        st.success("「zk棚番」に書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")
        # reset_form()
    st.stop()
        
def atualizar_tanaban_add(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap):
    try:
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
        reset_form()
        st.stop()

def atualizar_tanaban_del(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkDelDa, zkDelIko, zkDelSya):
    try:
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
        # reset_form()
        st.stop()

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
            st.warning(f"ID(18桁) '{item_id}' に一致する snps_um__Process__c が見つかりませんでした。")
            return None
            # reset_form()
            st.stop()
    except Exception as e:
        st.error(f"ID(18桁)検索エラー: {e}")
        return None
        # reset_form()
        st.stop()

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
    zkKari = record[dbItem].splitlines()  # 大項目リスト(改行区切り)
    zkSplit = zkKari[listNo].split(",")  # 小項目リスト(カンマ区切り)
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
                    # reset_form()
                    st.stop()  # 以降の処理を止める
            if 0 <= zkSplitNo < len(zkSplit):
                del zkSplit[zkSplitNo]  # 小項目の対象値削除
            else:
                # ログ出力やエラーハンドリング
                # st.write(f"zkSplitNo {zkSplitNo} is out of range for zkSplit of length {len(zkSplit)}")
                st.write(f"❌03 **有効な範囲ではありませんでした。'{zkSplitNo}'**")
                # reset_form()
                st.stop()  # 以降の処理を止める
        else:
            if flag == 3:
                zkSplitNo = 0
            zkSplit[zkSplitNo] = "-"  # 小項目の対象にデフォルト値反映
        zkKari[listNo] = ",".join(zkSplit)  # 大項目に反映
    else:
        if zkKari[listNo] == "-":  # 大項目がデフォルト値の場合
            if flag == -1 and zkSplitFlag == 1:  # マップ座標で2つ目以降の追加の場合
                zkKari[listNo] += "," + update_value
            else:
                zkKari[listNo] = update_value
        else:
            if flag == 1:
                for index, item in enumerate(zkSplit):
                    if item == update_value:
                        st.write(f"❌04 **すでに登録されている移行票Noです。'{update_value}'**")
                        # reset_form()
                        st.stop()  # 以降の処理を止める
                zkSplitFlag = 1
            zkKari[listNo] += "," + update_value
    zkKari = "\n".join(zkKari) if isinstance(zkKari, list) else zkKari
    return zkKari

def reset_form():
    st.session_state.production_order = None
    # st.session_state.data = None
    # st.session_state.material = None
    # st.session_state.material_weight = None
    # st.session_state.cumulative_cost = 0.0
    st.session_state.manual_input_value = ""
    st.rerun()

def styled_text_old(
    text,
    bg_color,
    padding,
    width,
    text_color,
    font_size,
    border_thickness,
    border_color="#000000",
    margin_top="2px",
    margin_bottom="2px"
):
    st.markdown(
        f"""
        <div style="
            background-color:{bg_color};
            padding:{padding};
            border-radius:2px;
            height:30px;
            width:{width};
            margin-top:{margin_top};
            margin-bottom:{margin_bottom};
            border-bottom:{border_thickness} solid {border_color};
            display:inline-block;
        ">
            <p style="color:{text_color}; font-size:{font_size}; margin:0; line-height:1;">{text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
def styled_text(
    text,
    bg_color,
    padding,
    width,
    text_color,
    font_size,
    border_thickness,
    border_color="#000000",
    margin_top="2px",
    margin_bottom="2px"
):
    st.markdown(
        f"""
        <div style="
            background-color:{bg_color};
            padding:{padding};
            border-radius:2px;
            width:{width};
            margin-top:{margin_top};
            margin-bottom:{margin_bottom};
            border-bottom:{border_thickness} solid {border_color};
        ">
            <p style="color:{text_color}; font-size:{font_size}; margin:0; line-height:1;">{text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def styled_input_text():
    st.markdown(
        """
        <style>
        input[type="text"], input[type="password"] {
            font-size: 26px !important;
            padding-top: 16px !important;
            padding-bottom: 16px !important;
            line-height: 2.5 !important;   /* 高さ調整のキモ */
            box-sizing: border-box !important;
        }
        
        /* 親コンテナの余白にも調整を加える */
        div[data-testid="stTextInput"] {
            padding-top: 2px !important;
            padding-bottom: 2px !important
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Autenticar no Salesforce
if "sf" not in st.session_state:
    try:
        st.session_state.sf = authenticate_salesforce()
        # st.success("Salesforceに正常に接続しました！")
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
if "tanaban" not in st.session_state:
    st.session_state.tanaban = ""
if "tanaban_select" not in st.session_state:
    st.session_state.tanaban_select = ""
if "qr_code" not in st.session_state:
    st.session_state.qr_code = None
if "qr_code_tana" not in st.session_state:
    st.session_state.qr_code_tana = False

if "user_code_entered" not in st.session_state:
    st.session_state.user_code_entered = False
    st.session_state.user_code = ""
    
if not st.session_state.user_code_entered:
    styled_input_text()
    st.title("作業者コード？")
    st.session_state['owner'] = st.text_input("作業者コード(社員番号)を入力してください。\n(3～4桁、例: 999)",
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

    manual_input_flag = 0
    if not st.session_state.qr_code_tana:
        tanaban = ""
        if manual_input_flag == 0:
            st.write("棚番のQRコードをスキャンしてください:")
            qr_code_tana = qrcode_scanner(key='qrcode_scanner_tana')  
        
            if qr_code_tana:  
                # st.write(qr_code_tana) 
                tanaban = qr_code_tana.strip()
        else:
            zkTanalist = """
                完A-1,完A-2,完A-3,完A-4,完A-5,完A-6,完A-7,完A-8,完A-9,完A-10,完A-11,完A-12,完A-13,完A-14,完A-15,完A-16,完A-17,完A-18,完A-19,完A-20,
                完B-1,完B-2,完B-3,完B-4,完B-5,完B-6,完B-7,完B-8,完B-9,完B-10,完B-11,完B-12,完B-13,完B-14,完B-15,完B-16,完B-17,完B-18,完B-19,完B-20,
                完C-1,完C-2,完C-3,完C-4,完C-5,完C-6,完C-7,完C-8,完C-9,完C-10,完C-11,完C-12,完C-13,完C-14,完C-15,完C-16,完C-17,完C-18,完C-19,完C-20,
                完D-1,完D-2,完D-3,完D-4,完D-5,完D-6,完D-7,完D-8,完D-9,完D-10,完D-11,完D-12,完D-13,完D-14,完D-15,完D-16,完D-17,完D-18,完D-19,完D-20,
                A-1,A-2,A-3,A-4,A-5,A-6,A-7,A-8,A-9,A-10,A-11,A-12,A-13,A-14,A-15,A-16,A-17,A-18,A-19,A-20,A-21,A-22,A-23,A-24,A-25,A-26,A-27,A-28,A-29,A-30,
                D-1,D-2,D-3,D-4,D-5,D-6,D-7,D-8,D-9,D-10,D-11,D-12,D-13,D-14,D-15,D-16,D-17,D-18,D-19,D-20,D-21,D-22,D-23,D-24,D-25,D-26,D-27,D-28,D-29,D-30,
                E-31,E-32,E-33,E-34,E-35,E-36,E-37,E-38,E-39,E-40,E-41,E-42,E-43,E-44,E-45,E-46,E-47,E-8,E-49,E-50,E-51,E-52,E-53,E-54,E-55,E-56,E-57,E-58,E-59,E-60,E-61,E-62,E-63,E-64,E-65,E-66,E-67,E-68,E-69,E-70,
                F-1,F-2,F-3,F-4,F-5,F-6,F-7,F-8,F-9,F-10,F-11,F-12,F-13,F-14,F-15,F-16,F-17,F-18,F-19,F-20,F-21,F-22,F-23,F-24,F-25,F-26,F-27,F-28,F-29,F-30,F-31,F-32,F-33,F-34,F-35,F-36,F-37,F-38,F-39,F-40,
                G-1,G-2,G-3,G-4,G-5,G-6,G-7,G-8,G-9,G-10,G-11,G-12,G-13,G-14,G-15,G-16,G-17,G-18,G-19,G-20,G-21,G-22,G-23,G-24,G-25,G-26,G-27,G-28,G-29,G-30,G-31,G-32,G-33,G-34,G-35,G-36,G-37,G-38,G-39,G-40,
                H-1,H-2,H-3,H-4,H-5,H-6,H-7,H-8,H-9,H-10,H-11,H-12,H-13,H-14,H-15,H-16,H-17,H-18,H-19,H-20,H-21,H-22,H-23,H-24,H-25,H-26,H-27,H-28,H-29,H-30,H-31,H-32,H-33,H-34,H-35,H-36,H-37,H-38,H-39,H-40,
                R-1,R-2,R-3,R-4,R-5,R-6,R-7,R-8,R-9,R-10,R-11,R-12,R-13,R-14,R-15,R-16,R-17,R-18,R-19,R-20,
                S-1,S-2,S-3,S-4,S-5,S-6,S-7,S-8,S-9,S-10,S-11,S-12,S-13,S-14,S-15,S-16,S-17,S-18,S-19,S-20
                """
            zkTanalistSplit = zkTanalist.split(",")
            options = zkTanalistSplit
            tanaban = st.selectbox("棚番号を選んでください", options, key="tanaban")
            st.write(f"選択された棚番号: {tanaban}")
    
        # tanaban = st.text_input("棚番号を選択または入力してください (例: H-15):",
        #                     max_chars=6,
        #                     key="manual_input_tana")
        if tanaban != "":
            st.session_state.tanaban = tanaban
            st.session_state.tanaban_select = tanaban
            st.session_state.show_camera = False
            st.session_state.qr_code_tana = True
            st.rerun()  # 再描画して次のステップへ
    else:
        st.write(st.session_state.tanaban)
        if st.button("棚番を再選択"):
            st.session_state.qr_code_tana = False
            st.session_state.tanaban = ""
            st.session_state.tanaban_select = ""
            st.session_state.show_camera = True  # 必要に応じてカメラ表示を再開
            st.rerun()
        
        if manual_input_flag == 0:
            qr_code = ""
            if st.button("移行票(製造オーダー)を再選択", key="camera_rerun"):
                st.session_state.show_camera = True
                st.session_state.production_order = None
                # st.session_state.manual_input_value = ""
                st.rerun()
            if qr_code == "":
            # if st.session_state.show_camera:
                st.session_state.show_camera = True
                st.write("移行票(製造オーダー)のQRコードをスキャンしてください:")
                qr_code = qrcode_scanner(key="qrcode_scanner_fixed")
                # st.write(f"読取直後qr_code : {st.session_state.production_order}")
                if qr_code is not None and qr_code.strip() != "":
                # if qr_code:
                    st.session_state.qr_code = qr_code.strip()
                
                # if not st.session_state.production_order and st.session_state.show_camera:
                #     st.write("QRコードをスキャンして開始してください:")
                #     try:
                #         qr_code = qrcode_scanner(key="qrcode_scanner_fixed")
                #     except Exception as e:
                #         st.error(f"表示中にエラー: {type(e).__name__} - {e}")
                #     if isinstance(qr_code, str) and qr_code:
                #         st.session_state.qr_code = qr_code
                #         st.rerun()  # ← ここで明示的に再描画
                if "qr_code" in st.session_state and st.session_state.qr_code != "":
                # if st.session_state.qr_code != "":
                    # st.write("QRコードの型:", type(st.session_state.qr_code))
                    # st.write("QRコードの中身:", repr(st.session_state.qr_code))
                    
                    # production_order = st.session_state.qr_code
                    # st.write(production_order[3:8])
                    # st.write(f"qr_code : {st.session_state.production_order}")
                    st.session_state.production_order = f"{st.session_state.qr_code}"
                    # st.write(f"production_order : {st.session_state.production_order}")
                    # st.session_state.manual_input_value = production_order[3:8]
                    # st.write("カメラONの session_state:", st.session_state)
                    st.session_state.show_camera = False
                    # st.write("カメラOFFの session_state:", st.session_state)
                    # st.session_state.qr_code = None  # 処理済みなのでクリア
                    # st.rerun()
                    # st.session_state.trigger_rerun = True
                # if st.session_state.get("trigger_rerun"):
                    # st.session_state.show_camera = False
                    # st.session_state.trigger_rerun = False
                    # st.rerun()
        else:                   
            styled_input_text()
            with st.form(key="manual_input_form", clear_on_submit=True):
                # manual_input_key = st.session_state.get("manual_input_key", "manual_input_default")
                if manual_input_flag == 1:
                    # Opção de digitação manual do production_order
                    # manual_input = st.text_input("移行票番号を入力してください (6桁、例: 000000):",
                    #                            value=st.session_state.manual_input_value,
                    #                            max_chars=6,
                    #                            key="manual_input")
                    manual_input = st.text_input("移行票番号を入力してください (6桁、例: 000000):",
                                                value="",
                                                max_chars=6,
                                                key="manual_input")
                    if manual_input and manual_input.isdigit():
                        st.session_state.production_order = f"PO-{manual_input.zfill(6)}"
                        # st.session_state.manual_input_value = manual_input
                        st.session_state.show_camera = False
                    
                    # 入力欄の直後に JavaScript を挿入
                    components.html(
                        """
                        <script>
                            setTimeout(() => {
                                const inputs = window.parent.document.querySelectorAll('input');
                                for (let input of inputs) {
                                    if (input.placeholder.includes("移行票番号")) {
                                        input.focus();
                                        break;
                                    }
                                }
                            }, 500);
                        </script>
                        """,
                        height=0,
                    )
                    submit_button_modify = st.form_submit_button("再入力(移行票番号)")  # 送信ボタンを配置しないとエラーになる
        
        st.write(st.session_state.production_order)     
        zkSplitNo = 99
        zkSplitFlag = 0
        # Formulário sempre renderizado
        with st.form(key="registro_form", clear_on_submit=True):
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
                    print("Salesforceで発見されたすべての記録:")
                    # st.write("Salesforceで発見されたすべての記録:")
                    # simplified_df = simplify_dataframe(pd.DataFrame(st.session_state.all_data))
                    # st.dataframe(simplified_df)
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
                    st.session_state.manual_input_value = ""
                    # st.session_state.data = None
                    # st.session_state.material = None
                    # st.session_state.material_weight = None
                    # st.session_state.cumulative_cost = 0.0
                    st.warning("生産オーダーに該当する 'Done' ステータスの記録が見つかりませんでした。")
                    # df, material, material_weight, cumulative_cost = pd.DataFrame(), None, None, 0.0
                    # reset_form()
                    # st.stop()
            else:
                # print("移行票番号が見つかりませんでした。")
                st.warning("移行票番号が見つかりませんでした。")
                # reset_form()
                # st.stop()
            
            # left, right = st.columns([0.5, 0.5])
            # Campos de entrada
            owner_value = st.session_state.owner
            # owner_value = "" if st.session_state.data is None else st.session_state.owner
            # owner = st.text_input("作業者(社員番号):", key="owner", value=owner_value)
            # st.write(f"作業者 (社員番号): {owner_value}")
            # styled_text(f"作業者 (社員番号) : {owner_value}", bg_color="#ffe4e1", text_color="#333333")
            tanaban = st.session_state.tanaban
            # tanaban = "" if st.session_state.tanaban is None else st.session_state.tanaban
            production_order_value = st.session_state.production_order
            # production_order_value = "" if st.session_state.production_order is None else st.session_state.production_order
            # production_order_v = st.text_input("移行票番号 :", key="production_order_v", value=production_order_value)
            # st.write(f"移行票番号: {production_order_value}")
            # styled_text(f"移行票番号 : {production_order_value}", bg_color="#ffe4e1", text_color="#333333")
            # tanaban_select_value = "" if st.session_state.tanaban_select is None else st.session_state.tanaban_select
            # tanaban_select = st.text_input("棚番 :", key="tanaban_select", value=tanaban_select_value)
            # st.write(f"棚番: {tanaban}")
            # styled_text(f"棚番 : {tanaban}", bg_color="#ffe4e1", text_color="#333333")
            # with left:
                # styled_text(f"　項　　目", bg_color="#c0c0c0", padding="9px", width="80px", text_color="#333333", font_size="10px", border_thickness="3px")
                # styled_text(f"　項　　目", bg_color="#c0c0c0", padding="9px", width="80px", text_color="#333333", font_size="10px", border_thickness="3px")
                # styled_text(f"社員番号 :", bg_color="#c0c0c0", padding="10px", width="80px", text_color="#333333", font_size="10px", border_thickness="0px")
                # styled_text(f"棚番 :", bg_color="#c0c0c0", padding="10px", width="80px", text_color="#333333", font_size="10px", border_thickness="0px")
                # styled_text(f"移行票番号 :", bg_color="#c0c0c0", padding="10px", width="80px", text_color="#333333", font_size="10px", border_thickness="0px")
                # styled_text(f"品番 :", bg_color="#c0c0c0", padding="10px", width="80px", text_color="#333333", font_size="10px", border_thickness="0px")
                # styled_text(f"工順 :", bg_color="#c0c0c0", padding="10px", width="80px", text_color="#333333", font_size="10px", border_thickness="0px")
                # styled_text(f"工程名 :", bg_color="#c0c0c0", padding="10px", width="80px", text_color="#333333", font_size="10px", border_thickness="0px")
                # styled_text(f"数量(工程) :", bg_color="#c0c0c0", padding="10px", width="80px", text_color="#333333", font_size="10px", border_thickness="0px")
            # with right:
                # styled_text(f"　追加または削除の対象", bg_color="#c0c0c0", padding="10px", width="120px", text_color="#333333", font_size="10px", border_thickness="3px")
                # styled_text(f"　追加または削除の対象", bg_color="#c0c0c0", padding="10px", width="120px", text_color="#333333", font_size="10px", border_thickness="3px")
                # styled_text(f"{owner_value}", bg_color="#c0c0c0", padding="6px", width="120px", text_color="#333333", font_size="14px", border_thickness="0px")
                # styled_text(f"{tanaban}", bg_color="#FFFF00", padding="6px", width="120px", text_color="#333333", font_size="14px", border_thickness="0px")
                # styled_text(f"{production_order_value}", bg_color="#FFFF00", padding="6px", width="120px", text_color="#333333", font_size="14px", border_thickness="0px")
                # styled_text(f"{default_hinban}", bg_color="#FFFF00", padding="6px", width="120px", text_color="#333333", font_size="14px", border_thickness="0px")
                # styled_text(f"{default_process_order}", bg_color="#FFFF00", padding="6px", width="120px", text_color="#333333", font_size="14px", border_thickness="0px")
                # styled_text(f"{default_process_order_name}", bg_color="#FFFF00", padding="6px", width="120px", text_color="#333333", font_size="14px", border_thickness="0px")
                # styled_text(f"{default_quantity}", bg_color="#FFFF00", padding="6px", width="120px", text_color="#333333", font_size="14px", border_thickness="0px")
            styled_text(f"項　　目　 :　追加または削除の対象", bg_color="#c0c0c0", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="3px")
            styled_text(f"社員番号　 : {owner_value}", bg_color="#c0c0c0", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="0px")
            styled_text(f"棚　　番　 : {tanaban}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="0px")
            styled_text(f"移行票番号 : {production_order_value}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="0px")
            styled_text(f"品　　番　 : {default_hinban}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="0px")
            styled_text(f"工　　順　 : {default_process_order}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="0px")
            styled_text(f"工 程 名　 : {default_process_order_name}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="0px")
            styled_text(f"数量(工程) : {default_quantity}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="14px", border_thickness="0px")
            if st.session_state.data:
                hinban = default_hinban
                process_order = default_process_order
                process_order_name = default_process_order_name
                quantity = default_quantity
                # hinban = st.text_input("品番:", key="hinban", value=default_hinban)
                # process_order = st.number_input("工程順序:", value=default_process_order, step=1, key="process_order")
                # process_order_name = st.text_input("工程名:", key="process_order_name", value=default_process_order_name)
                # quantity = st.number_input("数量 (工程):", value=default_quantity, key="quantity")
                # hinmei = st.text_input("品名:", key="hinmei", value=default_hinmei)
            else:
                hinban = "-"
                process_order = 0
                process_order_name = "-"
                quantity = 0.0
                # hinmei = st.text_input("品名:", key="hinmei", value="-")
            
            add_del_flag = 0  # 0:追加 1:削除
            # HTMLとCSSでボタンを横並びに配置
            st.markdown("""
                <style>
                .button-row {
                    display: flex;
                    gap: 10px;
                }
                .button-row form {
                    margin: 0;
                }
                </style>
                <div class="button-row">
                    <form action="?action=btnAdd" method="post">
                        <button type="submit">追加</button>
                    </form>
                    <form action="?action=btnDel" method="post">
                        <button type="submit">削除</button>
                    </form>
                    <form action="?action=btnCancel" method="post">
                        <button type="submit">取消</button>
                    </form>
                </div>
            """, unsafe_allow_html=True)
            
            # クエリパラメータでどのボタンが押されたか判定
            query_params = st.experimental_get_query_params()
            action = query_params.get("action", [None])[0]
            
            if action == "btnAdd":
                add_del_flag = 0
            elif action == "btnDel":
                add_del_flag = 1
            elif action == "btnCancel":
                add_del_flag = 9

            # left, center, right = st.columns([0.3, 0.4, 0.3])
            # with left:
            #     submit_button_add = st.form_submit_button("追加")
            # with center:
            #     submit_button_del = st.form_submit_button("削除")
            if add_del_flag == 0 or add_del_flag == 1: 
                item_id = "a1ZQ8000000FB4jMAG"  # 工程手配明細マスタの 1-PC9-SW_IZ の ID(18桁) ※限定
                
                # 棚番設定用マスタ(棚番を変更する場合には、下記に追加または削除してからatualizar_tanaban_addkari()を実行の事。尚、棚番は改行区切りである。)
                # atualizar_tanaban_addkari(st.session_state.sf, item_id)
                # st.stop()  # 以降の処理を止める
                
                # tanaban = "完A-3"  # 仮で設定
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
                        st.write(f"❌05 **棚番 '{tanaban}' の追加は許可されてません。**")
                        # reset_form()
                        st.stop()  # 以降の処理を止める
                        # # zkTana = f"{record["zkTanaban__c"]},{tanaban}"
                        # zkTana = record["zkTanaban__c"] + "\n" + tanaban
                        # zkIko = record["zkIkohyoNo__c"] + "\n" + st.session_state.production_order  # zk移行票No
                        # zkHin = record["zkHinban__c"] + "\n" + hinban   # zk品番
                        # zkKan = record["zkKanryoKoutei__c"] + "\n" + process_order_name   # zk完了工程
                        # zkSu = f"{record["zkSuryo__c"]}\n{quantity}"   # zk数量
                        # zkTuiDa = f"{record["zkTuikaDatetime__c"]}\n{datetime_str}"   # zk追加日時
                        # zkTuiSya = record["zkTuikaSya__c"] + "\n" + owner   # zk追加者
                        # zkMap = record["zkMap__c"] + "\n" + "-"   # zkマップ座標
                        # # zkDelDa = record["zkDeleteDatetime__c"] + "," +    # zk直近削除日時
                        # # zkDelIko = record["zkDeleteIkohyoNo__c"] + "," +    # zk直近削除移行票No
                        # # zkDelSya = record["zkDeleteSya__c"] + "," +    # zk直近削除者
                        # # zkShoBu = record["zkShortcutButton__c"] + "\n" +    # zkショートカットボタン
                        # # zkShoU = record["zkShortcutUser__c"] + "\n" +    # zkショートカットユーザー
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
                            st.write(f"❌06 **移行票Noリスト '{zkIko}' の追加は許可されてません。**")
                            # reset_form()
                            st.stop()  # 以降の処理を止める
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
                            elseif add_del_flag == 1: # 削除の場合
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
                            
                        # zkHin = record["zkHinban__c"].splitlines()   # zk品番
                        # zkKan = record["zkKanryoKoutei__c"].splitlines()   # zk完了工程
                        # zkSu = record["zkSuryo__c"].splitlines()   # zk数量
                        # zkTuiDa = record["zkTuikaDatetime__c"].splitlines()   # zk追加日時
                        # zkTuiSya = record["zkTuikaSya__c"].splitlines()   # zk追加者
                        # zkMap = record["zkMap__c"].splitlines()   # zkマップ座標
                        # zkDelDa = record["zkDeleteDatetime__c"].split(",")   # zk直近削除日時
                        # zkDelIko = record["zkDeleteIkohyoNo__c"].split(",")   # zk直近削除移行票No
                        # zkDelSya = record["zkDeleteSya__c"].split(",")   # zk直近削除者
                        # zkShoBu = record["zkShortcutButton__c"].splitlines()   # zkショートカットボタン
                        # zkShoU = record["zkShortcutUser__c"].splitlines()   # zkショートカットユーザー
                                    
                if st.session_state.owner is None:
                    st.write(f"❌07 **作業者コード '{owner}' が未入力です。**")
                    # reset_form()
                    st.stop()  # 以降の処理を止める
                # if "rerun_flag" not in st.session_state:
                #     st.session_state.rerun_flag = False
                if item_id:
                    # atualizar_tanabangou(st.session_state.sf, item_id)
                    # atualizar_tanaban(st.session_state.sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkDelDa, zkDelIko, zkDelSya)
                    # datetime_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    if add_del_flag == 0: # 追加の場合
                        atualizar_tanaban_add(st.session_state.sf, item_id, tanaban, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap)
                    else: # 削除の場合
                        atualizar_tanaban_del(st.session_state.sf, item_id, tanaban, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkDelDa, zkDelIko, zkDelSya)
                    # reset_form()
                    # JavaScriptでフォーカスを当てる
                    if st.session_state.rerun_flag:
                        components.html(
                            """
                            <script>
                                setTimeout(() => {
                                    const inputs = window.parent.document.querySelectorAll('input');
                                    for (let input of inputs) {
                                        if (input.placeholder === "移行票番号を入力してください (6桁、例: 000000):") {
                                            input.focus();
                                            break;
                                        }
                                    }
                                }, 500);
                            </script>
                            """,
                            height=0,
                        )
                        st.session_state.rerun_flag = False
