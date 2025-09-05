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
    # zkTana = """
    #     完A-1\n完A-2\n完A-3\n完A-4\n完A-5\n完A-6\n完A-7\n完A-8\n完A-9\n完A-10\n完A-11\n完A-12\n完A-13\n完A-14\n完A-15\n完A-16\n完A-17\n完A-18\n完A-19\n完A-20\n
    #     完B-1\n完B-2\n完B-3\n完B-4\n完B-5\n完B-6\n完B-7\n完B-8\n完B-9\n完B-10\n完B-11\n完B-12\n完B-13\n完B-14\n完B-15\n完B-16\n完B-17\n完B-18\n完B-19\n完B-20\n
    #     完C-1\n完C-2\n完C-3\n完C-4\n完C-5\n完C-6\n完C-7\n完C-8\n完C-9\n完C-10\n完C-11\n完C-12\n完C-13\n完C-14\n完C-15\n完C-16\n完C-17\n完C-18\n完C-19\n完C-20\n
    #     完D-1\n完D-2\n完D-3\n完D-4\n完D-5\n完D-6\n完D-7\n完D-8\n完D-9\n完D-10\n完D-11\n完D-12\n完D-13\n完D-14\n完D-15\n完D-16\n完D-17\n完D-18\n完D-19\n完D-20\n
    #     A-1\nA-2\nA-3\nA-4\nA-5\nA-6\nA-7\nA-8\nA-9\nA-10\nA-11\nA-12\nA-13\nA-14\nA-15\nA-16\nA-17\nA-18\nA-19\nA-20\nA-21\nA-22\nA-23\nA-24\nA-25\nA-26\nA-27\nA-28\nA-29\nA-30\n
    #     D-1\nD-2\nD-3\nD-4\nD-5\nD-6\nD-7\nD-8\nD-9\nD-10\nD-11\nD-12\nD-13\nD-14\nD-15\nD-16\nD-17\nD-18\nD-19\nD-20\nD-21\nD-22\nD-23\nD-24\nD-25\nD-26\nD-27\nD-28\nD-29\nD-30\n
    #     E-31\nE-32\nE-33\nE-34\nE-35\nE-36\nE-37\nE-38\nE-39\nE-40\nE-41\nE-42\nE-43\nE-44\nE-45\nE-46\nE-47\nE-48\nE-49\nE-50\nE-51\nE-52\nE-53\nE-54\nE-55\nE-56\nE-57\nE-58\nE-59\nE-60\nE-61\nE-62\nE-63\nE-64\nE-65\nE-66\nE-67\nE-68\nE-69\nE-70\n
    #     F-1\nF-2\nF-3\nF-4\nF-5\nF-6\nF-7\nF-8\nF-9\nF-10\nF-11\nF-12\nF-13\nF-14\nF-15\nF-16\nF-17\nF-18\nF-19\nF-20\nF-21\nF-22\nF-23\nF-24\nF-25\nF-26\nF-27\nF-28\nF-29\nF-30\nF-31\nF-32\nF-33\nF-34\nF-35\nF-36\nF-37\nF-38\nF-39\nF-40\n
    #     G-1\nG-2\nG-3\nG-4\nG-5\nG-6\nG-7\nG-8\nG-9\nG-10\nG-11\nG-12\nG-13\nG-14\nG-15\nG-16\nG-17\nG-18\nG-19\nG-20\nG-21\nG-22\nG-23\nG-24\nG-25\nG-26\nG-27\nG-28\nG-29\nG-30\nG-31\nG-32\nG-33\nG-34\nG-35\nG-36\nG-37\nG-38\nG-39\nG-40\n
    #     H-1\nH-2\nH-3\nH-4\nH-5\nH-6\nH-7\nH-8\nH-9\nH-10\nH-11\nH-12\nH-13\nH-14\nH-15\nH-16\nH-17\nH-18\nH-19\nH-20\nH-21\nH-22\nH-23\nH-24\nH-25\nH-26\nH-27\nH-28\nH-29\nH-30\nH-31\nH-32\nH-33\nH-34\nH-35\nH-36\nH-37\nH-38\nH-39\nH-40\n
    #     R-1\nR-2\nR-3\nR-4\nR-5\nR-6\nR-7\nR-8\nR-9\nR-10\nR-11\nR-12\nR-13\nR-14\nR-15\nR-16\nR-17\nR-18\nR-19\nR-20\n
    #     S-1\nS-2\nS-3\nS-4\nS-5\nS-6\nS-7\nS-8\nS-9\nS-10\nS-11\nS-12\nS-13\nS-14\nS-15\nS-16\nS-17\nS-18\nS-19\nS-20
    # """
    zkTana = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n41\n42\n43\n44\n45\n46\n47\n48\n49\n50\n51\n52\n53\n54\n55\n56\n57\n58\n59\n60\n81\n82\n83\n84\n85\n86\n87\n88\n89\n90\n91\n92\n93\n94\n95\n96\n97\n98\n99\n100\n121\n122\n123\n124\n125\n126\n127\n128\n129\n130\n131\n132\n133\n134\n135\n136\n137\n138\n139\n140\n161\n162\n163\n164\n165\n166\n167\n168\n169\n170\n171\n172\n173\n174\n175\n176\n177\n178\n179\n180\n181\n182\n183\n184\n185\n186\n187\n188\n189\n190\n201\n202\n203\n204\n205\n206\n207\n208\n209\n210\n211\n212\n213\n214\n215\n216\n217\n218\n219\n220\n221\n222\n223\n224\n225\n226\n227\n228\n229\n230\n241\n242\n243\n244\n245\n246\n247\n248\n249\n250\n251\n252\n253\n254\n255\n256\n257\n258\n259\n260\n261\n262\n263\n264\n265\n266\n267\n268\n269\n270\n271\n272\n273\n274\n275\n276\n277\n278\n279\n280\n301\n302\n303\n304\n305\n306\n307\n308\n309\n310\n311\n312\n313\n314\n315\n316\n317\n318\n319\n320\n321\n322\n323\n324\n325\n326\n327\n328\n329\n330\n331\n332\n333\n334\n335\n336\n337\n338\n339\n340\n361\n362\n363\n364\n365\n366\n367\n368\n369\n370\n371\n372\n373\n374\n375\n376\n377\n378\n379\n380\n381\n382\n383\n384\n385\n386\n387\n388\n389\n390\n391\n392\n393\n394\n395\n396\n397\n398\n399\n400\n421\n422\n423\n424\n425\n426\n427\n428\n429\n430\n431\n432\n433\n434\n435\n436\n437\n438\n439\n440\n441\n442\n443\n444\n445\n446\n447\n448\n449\n450\n451\n452\n453\n454\n455\n456\n457\n458\n459\n460\n481\n482\n483\n484\n485\n486\n487\n488\n489\n490\n491\n492\n493\n494\n495\n496\n497\n498\n499\n500\n521\n522\n523\n524\n525\n526\n527\n528\n529\n530\n531\n532\n533\n534\n535\n536\n537\n538\n539\n540"
    try:
        # sf.snps_um__Process__c.update(item_id, {"zkTanaban__c": zkTana})
        # st.success("##### 「zk棚番」に書き込みました！")
        sf.snps_um__Process__c.update(item_id, {"zkMapNo__c": zkTana})
        st.success("##### 「zkマップ表示」に書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")
        # reset_form()
    st.stop()
        
def atualizar_tanaban_add(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkHistory, zkOrder):
    global zkScroll_flag  # 初期値0
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
            "zkMap__c": zkMap,
            "zkHistory__c": zkHistory
        })
        # '''
        # st.success(f"##### snps_um__Process__c の棚番 '{zkTana}' に移行票No '{zkOrder}' を追加しました。")
        zkScroll_flag = 1
        st.success(f"棚番 '{zkTana}' に、移行票No '{zkOrder}' を追加しました。")
    except Exception as e:
        st.error(f"更新エラー: {e}")
        reset_form()
        st.stop()

# def atualizar_tanaban_del(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkHistory, zkDelDa, zkDelTana, zkDelIko, zkDelSya, zkOrder):
def atualizar_tanaban_del(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkTuiDa, zkTuiSya, zkMap, zkHistory, zkOrder):
    global zkScroll_flag  # 初期値0
    try:
        sf.snps_um__Process__c.update(item_id, {
            "zkIkohyoNo__c": zkIko,
            "zkHinban__c": zkHin,
            "zkKanryoKoutei__c": zkKan,
            "zkSuryo__c": zkSu,
            "zkTuikaDatetime__c": zkTuiDa,
            "zkTuikaSya__c": zkTuiSya,
            "zkMap__c": zkMap,
            "zkHistory__c": zkHistory
            # "zkDeleteDatetime__c": zkDelDa,
            # "zkDeleteTanaban__c": zkDelTana,
            # "zkDeleteIkohyoNo__c": zkDelIko,
            # "zkDeleteSya__c": zkDelSya
        })
        # st.success(f"##### snps_um__Process__c の棚番 '{zkTana}' から移行票No '{zkOrder}' を削除しました。")
        zkScroll_flag = 1
        st.success(f"棚番 '{zkTana}' から、移行票No '{zkOrder}' を削除しました。")
    except Exception as e:
        st.error(f"更新エラー: {e}")
        # reset_form()
        st.stop()
        
def update_tanaban(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkMap, zkHistory, zkOrder):
    global add_del_flag  # 0:追加　1:削除
    global zkScroll_flag  # 初期値0
    global result_text
    try:
        # sf.snps_um__Process__c.update(item_id, {"zkHinban__c": zkHin})
        # _= '''
        sf.snps_um__Process__c.update(item_id, {
            "zkIkohyoNo__c": zkIko,
            "zkHinban__c": zkHin,
            "zkKanryoKoutei__c": zkKan,
            "zkSuryo__c": zkSu,
            "zkMap__c": zkMap,
            "zkHistory__c": zkHistory
        })
        # '''
        # st.success(f"##### snps_um__Process__c の棚番 '{zkTana}' に移行票No '{zkOrder}' を追加しました。")
        zkScroll_flag = 1
        if add_del_flag == 0: # 追加の場合
            # st.success(f"棚番 '{zkTana}' に、移行票No '{zkOrder}' を追加しました。")
            result_text = f"棚番 '{zkTana}' に、移行票No '{zkOrder}' を追加しました。"
        else:
            # st.success(f"棚番 '{zkTana}' から、移行票No '{zkOrder}' を削除しました。")
            result_text = f"棚番 '{zkTana}' から、移行票No '{zkOrder}' を削除しました。"
    except Exception as e:
        st.error(f"更新エラー: {e}")
        reset_form()
        st.stop()

# WHERE Name LIKE '%{item_name}%' AND snps_um__ProcessOrderNo__c = 999
def data_catch(sf, item_id):
    query = f"""
        SELECT AITC_ID18__c, Name, zkShortcutButton__c, zkShortcutUser__c,
            zkTanaban__c, zkMapNo__c, zkIkohyoNo__c ,zkHinban__c, zkKanryoKoutei__c,
            zkSuryo__c, zkTuikaDatetime__c, zkTuikaSya__c, zkMap__c, zkHistory__c,
            zkDeleteDatetime__c, zkDeleteTanaban__c, zkDeleteIkohyoNo__c, zkDeleteSya__c
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

def data_catch_hinmoku(sf, item_name):
    query = f"""
        SELECT AITC_ID18__c, snps_um__ItemName__c, AITC_PrintItemName__c
        FROM snps_um__Item__c
        WHERE snps_um__ItemName__c LIKE '%{item_name}%'
    """
    try:
        result = sf.query(query)
        records = result.get("records", [])
        if records:
            return records
        else:
            st.warning(f"品目名称 '{item_name}' に関連する snps_um__Item__c が見つかりませんでした。")
            # return None
            # reset_form()
            st.stop()
    except Exception as e:
        st.error(f"品目名称検索エラー: {e}")
        # return None
        # reset_form()
        st.stop()

def list_update_zkKari(zkKari, dbItem, listNo, update_value, flag):
    """
    指定されたlistNoの値を更新する関数。
    "-"の場合はupdate_valueで上書き、それ以外はカンマ区切りで追加。

    Parameters:
    - zkKari: dict or list形式のデータ(注記.zkIko, zkHin, zkKan, zkSu, zkMapの順で処理の事)
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

def tool_tips(text):
    st.markdown(f"<p style='font-size:12px;'>{text}</p>", unsafe_allow_html=True)

def set_flag(flag):
    global add_del_flag
    global button_flag
    add_del_flag = flag
    button_flag = 1

def button_make(button_text, flag):
    st.markdown("""
        <style>
        .stButton>button { /* Streamlitのボタン要素に直接スタイルを適用 */
            background-color: #FF0;
            color: black;
            font-size: 10px !important;
            text-align: center;
            font-weight: bold;
            border-radius: 5px;
            width: 50px;
            max-width: 50px;
            height: 20px;
            margin: 5px; /* ボタン間の間隔など調整 */
        }
        .stButton>button:hover {
            opacity: 0.8;
        }
        </style>
    """, unsafe_allow_html=True)
    st.button(button_text, key=button_text, on_click=set_flag, args=(flag,))

def approve_button(message, button_key):
    st.write(message)
    left, right = st.columns(2)
    with left:
        dialog_check_ok_flag = st.button("OK", key="dialog_check_ok")
    with right:
        dialog_check_ng_flag = st.button("NG", key="dialog_check_ng")
    if dialog_check_ok_flag:
        st.session_state[button_key] = True
        st.rerun()
    elif dialog_check_ng_flag:
        st.session_state[button_key] = False
        st.rerun()

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
if "production_order_flag" not in st.session_state:
    st.session_state.production_order_flag = False
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
if "manual_input_check" not in st.session_state:
    st.session_state.manual_input_check = False
if "manual_input_check_select" not in st.session_state:
    st.session_state.manual_input_check_select = False
if "manual_input_flag" not in st.session_state:
    st.session_state.manual_input_flag = 0
if "manual_input_check_flag" not in st.session_state:
    st.session_state.manual_input_check_flag = 0
if "manual_input_hinban" not in st.session_state:
    st.session_state.manual_input_hinban = ""
if "manual_input_hinban_entered" not in st.session_state:
    st.session_state.manual_input_hinban_entered = False
# if "tanaban" not in st.session_state:
#     st.session_state.tanaban = ""
if "tanaban_select" not in st.session_state:
    st.session_state.tanaban_select = ""
if "tanaban_select_temp" not in st.session_state:
    st.session_state.tanaban_select_temp = ""
if "tanaban_select_value" not in st.session_state:
    st.session_state.tanaban_select_value = ""
if "tanaban_select_flag" not in st.session_state:
    st.session_state.tanaban_select_flag = False
if "qr_code" not in st.session_state:
    st.session_state.qr_code = None
if "qr_code_tana" not in st.session_state:
    st.session_state.qr_code_tana = False
if "hinban_select_value" not in st.session_state:
    st.session_state.hinban_select_value = ""
if "hinban_select_flag" not in st.session_state:
    st.session_state.hinban_select_flag = False
if "df_search_result" not in st.session_state:
    st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None

if "user_code_entered" not in st.session_state:
    st.session_state.user_code_entered = False
    st.session_state.user_code = ""

item_id = "a1ZQ8000000FB4jMAG"  # 工程手配明細マスタの 1-PC9-SW_IZ の ID(18桁) ※変更禁止
zkTanalist = """
    完A-0,完A-1,完A-2,完A-3,完A-4,完A-5,完A-6,完A-7,完A-8,完A-9,完A-10,完A-11,完A-12,完A-13,完A-14,完A-15,完A-16,完A-17,完A-18,完A-19,完A-20,
    完B-1,完B-2,完B-3,完B-4,完B-5,完B-6,完B-7,完B-8,完B-9,完B-10,完B-11,完B-12,完B-13,完B-14,完B-15,完B-16,完B-17,完B-18,完B-19,完B-20,
    完C-1,完C-2,完C-3,完C-4,完C-5,完C-6,完C-7,完C-8,完C-9,完C-10,完C-11,完C-12,完C-13,完C-14,完C-15,完C-16,完C-17,完C-18,完C-19,完C-20,
    完D-1,完D-2,完D-3,完D-4,完D-5,完D-6,完D-7,完D-8,完D-9,完D-10,完D-11,完D-12,完D-13,完D-14,完D-15,完D-16,完D-17,完D-18,完D-19,完D-20,
    A-1,A-2,A-3,A-4,A-5,A-6,A-7,A-8,A-9,A-10,A-11,A-12,A-13,A-14,A-15,A-16,A-17,A-18,A-19,A-20,A-21,A-22,A-23,A-24,A-25,A-26,A-27,A-28,A-29,A-30,
    D-1,D-2,D-3,D-4,D-5,D-6,D-7,D-8,D-9,D-10,D-11,D-12,D-13,D-14,D-15,D-16,D-17,D-18,D-19,D-20,D-21,D-22,D-23,D-24,D-25,D-26,D-27,D-28,D-29,D-30,
    E-31,E-32,E-33,E-34,E-35,E-36,E-37,E-38,E-39,E-40,E-41,E-42,E-43,E-44,E-45,E-46,E-47,E-48,E-49,E-50,E-51,E-52,E-53,E-54,E-55,E-56,E-57,E-58,E-59,E-60,E-61,E-62,E-63,E-64,E-65,E-66,E-67,E-68,E-69,E-70,
    F-1,F-2,F-3,F-4,F-5,F-6,F-7,F-8,F-9,F-10,F-11,F-12,F-13,F-14,F-15,F-16,F-17,F-18,F-19,F-20,F-21,F-22,F-23,F-24,F-25,F-26,F-27,F-28,F-29,F-30,F-31,F-32,F-33,F-34,F-35,F-36,F-37,F-38,F-39,F-40,
    G-1,G-2,G-3,G-4,G-5,G-6,G-7,G-8,G-9,G-10,G-11,G-12,G-13,G-14,G-15,G-16,G-17,G-18,G-19,G-20,G-21,G-22,G-23,G-24,G-25,G-26,G-27,G-28,G-29,G-30,G-31,G-32,G-33,G-34,G-35,G-36,G-37,G-38,G-39,G-40,
    H-1,H-2,H-3,H-4,H-5,H-6,H-7,H-8,H-9,H-10,H-11,H-12,H-13,H-14,H-15,H-16,H-17,H-18,H-19,H-20,H-21,H-22,H-23,H-24,H-25,H-26,H-27,H-28,H-29,H-30,H-31,H-32,H-33,H-34,H-35,H-36,H-37,H-38,H-39,H-40,
    R-1,R-2,R-3,R-4,R-5,R-6,R-7,R-8,R-9,R-10,R-11,R-12,R-13,R-14,R-15,R-16,R-17,R-18,R-19,R-20,
    S-1,S-2,S-3,S-4,S-5,S-6,S-7,S-8,S-9,S-10,S-11,S-12,S-13,S-14,S-15,S-16,S-17,S-18,S-19,S-20
    """

if not st.session_state.user_code_entered:
    styled_input_text()
    st.title("作業者コード？")
    st.session_state['owner'] = st.text_input("作業者コード(社員番号)を入力し、Enterを押してください。\n(3～4桁、例: 999)",
                                              max_chars=4,
                                              key="owner_input")
    
    if st.session_state['owner']:  # 入力があれば保存して完了フラグを立てる
        st.session_state.user_code = st.session_state['owner']
        st.session_state.user_code_entered = True
        st.session_state.qr_code_tana = False
        st.rerun()  # 再描画して次のステップへ
else:
    if not st.session_state.manual_input_check:
        st.title("入力方法選択画面")
        left, center, right = st.columns(3)
        with left:
            button_qr = st.button("QRコード")
            tool_tips("(棚番と移行票番号をQRコードで入力)")
            # st.markdown('<p style="font-size:12px;">(棚番と移行票番号をQRコードで入力)</p>', unsafe_allow_html=True)
            # st.write("###### (棚番と移行票番号をQRコードで入力)")
        with center:
            button_manual = st.button("手動入力")
            tool_tips("(棚番と移行票番号を手動で入力)")
        with right:
            button_reference = st.button("参照")
            tool_tips("(品番や移行票番号から棚番を検索)")
        if button_qr or button_manual or button_reference: 
            if button_qr:
                st.session_state.manual_input_flag = 0
            elif button_manual:
                st.session_state.manual_input_flag = 1
            else:
                st.session_state.manual_input_flag = 9
            st.session_state.manual_input_check = True
            st.session_state.manual_input_check_select = False
            st.rerun()
    else:
        if st.button("入力方法を再選択"):
            st.session_state.manual_input_check = False
            st.session_state.manual_input_flag = 0
            st.session_state.qr_code_tana = False
            st.session_state.tanaban_select_temp = ""
            st.rerun()
        if st.session_state.manual_input_flag == 9:
            # st.session_state.manual_input_check = False
            # st.session_state.manual_input_flag = 0
            # st.session_state.qr_code_tana = False
            # st.session_state.tanaban_select_temp = ""
            # st.rerun()
            if not st.session_state.manual_input_check_select:
                st.title("参照方法選択画面")
                left, center, right = st.columns(3)
                with left:
                    button_qr_Ikohyo = st.button("移行票番号(QRコード)")
                    st.write("移行票番号をQRコードで検索")
                with center:
                    button_manual_Hinban = st.button("品番(手動入力)")
                    st.write("品番を手動で入力し検索(曖昧検索可)")
                with right:
                    button_manual_Tanaban = st.button("棚番(手動入力)")
                    st.write("棚番を手動で選択し検索")
                if button_qr_Ikohyo or button_manual_Hinban or button_manual_Tanaban: 
                    if button_qr_Ikohyo:
                        st.session_state.manual_input_check_flag = 0
                    elif button_manual_Hinban:
                        st.session_state.manual_input_check_flag = 1
                    else:
                        st.session_state.manual_input_check_flag = 2
                    st.session_state.manual_input_check_select = True
                    st.rerun()
            else:
                if st.button("参照方法を再選択"):
                    st.session_state.manual_input_check_select = False
                    st.rerun()
                if st.session_state.manual_input_check_flag == 0:
                    if not st.session_state.production_order_flag:
                        if st.session_state.manual_input_flag == 0:
                            st.title("移行票番号をQRコードで検索")
                            qr_code_kari = ""
                            if st.button("移行票(製造オーダー)を再選択", key="camera_rerun"):
                                st.session_state.show_camera = True
                                st.session_state.qr_code = ""
                                st.session_state.production_order = None
                                st.session_state.production_order_flag = False
                                st.rerun()
                            if qr_code_kari == "":
                                st.session_state.show_camera = True
                                st.write("移行票(製造オーダー)のQRコードをスキャンしてください:")
                                qr_code_kari = qrcode_scanner(key="qrcode_scanner_fixed")
                                if qr_code_kari is not None and qr_code_kari.strip() != "":
                                    st.session_state.qr_code = qr_code_kari.strip()
                                
                                if "qr_code" in st.session_state and st.session_state.qr_code != "":
                                    st.session_state.production_order = f"{st.session_state.qr_code}"
                                    st.session_state.show_camera = False
                                    
                        else:                   
                            st.title("移行票番号を手動入力で検索")
                            styled_input_text()
                            manual_input = st.text_input("移行票番号を入力し、Enterを押してください。 (1～6桁、例: 12345):",
                                                        value="",
                                                        max_chars=6,
                                                        key="manual_input")
                            if manual_input and manual_input.isdigit():
                                st.session_state.production_order = f"PO-{manual_input.zfill(6)}"
                                # st.session_state.manual_input_value = manual_input
                                st.session_state.show_camera = False
                            
           
                        st.write(f"#### 現在選択されている棚番 : {st.session_state.tanaban_select_temp}")
                        # st.write(f"移行票番号 : {st.session_state.production_order}") 
                        st.write(f"下欄に移行票番号が表示されるまで、お待ちください。。。")
                        st.write(f"""
                            ###### 移行票番号(製造オーダー)は、
                            ## 「 {st.session_state.production_order} 」
                            ###### でよろしいですか？
                            """)
                        left, right = st.columns(2)
                        with left:
                            check_button_ok = st.button("ＯＫ", key="check_ok")
                        with right:
                            check_button_ng = st.button("ＮＧ", key="check_ng")
                        if check_button_ok:
                            st.session_state.show_camera = False
                            st.session_state.production_order_flag = True
                            st.rerun()
                        else:
                            if st.session_state.manual_input_flag == 0:
                                st.session_state.show_camera = True
                            st.session_state.production_order_flag = False
                            st.session_state.qr_code = None
                            st.session_state.production_order = None
                            # st.rerun()
                    else:
                        if st.button("移行票番号を再入力"):
                            st.session_state.data = None
                            st.session_state.material = None
                            st.session_state.material_weight = None
                            st.session_state.cumulative_cost = 0.0
                            st.session_state.production_order_flag = False
                            st.session_state.qr_code = ""
                            st.session_state.production_order = ""
                            if st.session_state.manual_input_flag == 0:
                                st.session_state.show_camera = True  # 必要に応じてカメラ表示を再開
                            st.rerun() 
                elif st.session_state.manual_input_check_flag == 1:
                    st.title("品番入力で検索")
                    if not st.session_state.manual_input_hinban_entered:
                        styled_input_text()
                        manual_input_hinban_kari = st.text_input("品番を入力し、Enterを押してください。",
                                                    value="",
                                                    key="manual_input_hinban_00")
                        if manual_input_hinban_kari:
                            st.session_state.manual_input_hinban = manual_input_hinban_kari
                            st.session_state.manual_input_hinban_entered = True
                            st.session_state.show_camera = False
                            st.rerun() 
                    else:
                        # if "hinban_select" not in st.session_state:
                        #     st.session_state.hinban_select = "---"
                        if st.button("品番を再入力"):
                            st.session_state.manual_input_hinban_entered = False
                            st.session_state.hinban_select_flag = False
                            st.session_state.tanaban_select_flag  = False
                            st.rerun()
                        if not st.session_state.hinban_select_flag:
                            records = data_catch_hinmoku(st.session_state.sf, st.session_state["manual_input_hinban"])
                            if records:
                                hinban_list = ["---"] + sorted([r["snps_um__ItemName__c"] for r in records])  # ID: AITC_ID18__c, 品番: snps_um__ItemName__c, 品名: AITC_PrintItemName__c
                                hinban_select = st.selectbox(
                                    "品番を選択してください　(クリックするとリストが開きます)", hinban_list, key="hinban_select"
                                )
                                st.session_state.hinban_select_value = hinban_select
                                if st.session_state.hinban_select_value != "" and st.session_state.hinban_select_value != "---":
                                    st.session_state.hinban_select_flag = True
                                    st.rerun()  # 再描画して次のステップへ
                                _= '''
                                '''
                        else:
                            # st.write(f"選択された品番：{st.session_state.hinban_select_value}")
                            # st.stop()
                            if st.button("品番を再選択"):
                                st.session_state.hinban_select_flag = False
                                st.session_state.tanaban_select_flag  = False
                                st.rerun()
                            if not st.session_state.tanaban_select_flag:
                                st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                                listCount = 0
                                zkTana = ""
                                zkIko = ""
                                zkHin = ""
                                zkKan = ""
                                zkSu = ""
                                zkHistory = ""
                                record = data_catch(st.session_state.sf, item_id)
                                if record:
                                    # zkHistory = record["zkHistory__c"]  # zk履歴
                                    zkTana_list = record["zkTanaban__c"].splitlines()  # 改行区切り　UM「新規 工程手配明細マスタ レポート」で見易くする為
                                    zkIko_list = record["zkIkohyoNo__c"].splitlines() 
                                    zkHin_list = record["zkHinban__c"].splitlines() 
                                    zkKan_list = record["zkKanryoKoutei__c"].splitlines() 
                                    zkSu_list = record["zkSuryo__c"].splitlines() 
                                    # listCount = len(zkTana_list)
                                    listCount = len(zkHin_list)
                                    zkHin_Search = st.session_state.hinban_select_value
                                    if listCount > 1:
                                        for index, item in enumerate(zkHin_list):
                                            # st.write(f"for文で検索した棚番: '{item}'") 
                                            # st.write(f"検索させる棚番: '{tanaban_select}'")
                                            zkIko = zkIko_list[index].split(",")
                                            zkHin = item.split(",")
                                            zkKan = zkKan_list[index].split(",")
                                            zkSu = zkSu_list[index].split(",")
                                            if zkHin_Search in zkHin:
                                                for index_2, item_2 in enumerate(zkHin):
                                                    if item_2 == zkHin_Search:
                                                        st.session_state.df_search_result.loc[len(st.session_state.df_search_result)] = [zkTana_list[index], zkIko[index_2], zkHin[index_2], zkKan[index_2], zkSu[index_2]]
                                                        # st.write("zkHin_list:", zkHin_list)
                                                        # st.write("df_search_result:", st.session_state.df_search_result)
                                        # st.write(st.session_state.df_search_result)
                                        st.dataframe(st.session_state.df_search_result)
                                        # edited_df = st.data_editor(
                                        #     st.session_state.df_search_result,
                                        #    num_rows="dynamic",
                                        #     use_container_width=True,
                                        #     key="editable_table"
                                        # )
                                    else:
                                        st.session_state.df_search_result.loc[len(st.session_state.df_search_result)] = [zkTana_list[0], zkIko[0], zkHin[0], zkKan[0], zkSu[0]]
                                else:
                                    st.write("'item_id'　が存在しません。至急、システム担当者に連絡してください！")
                                    st.stop()
                                # tanban_list = ["---"] + sorted(st.session_state.df_search_result.iloc[:, 0].dropna().unique())
                                tanban_list = ["---"] + st.session_state.df_search_result.iloc[:, 0].dropna().tolist()
                                selected_tanaban = st.selectbox("棚番を選択してください", tanban_list)
                                # selected_tanaban = st.selectbox("棚番を選択してください　(クリックするとリストが開きます)", st.session_state.df_search_result["棚番"])
                                st.session_state.tanaban_select_value = selected_tanaban
                                if st.session_state.tanaban_select_value != "---":
                                    st.session_state.tanaban_select_flag = True
                                    st.rerun()  # 再描画して次のステップへ
                                # else:
                                # datetime_str = dt.now(jst).strftime("%Y/%m/%d %H:%M:%S")
                            else:
                                if st.button("棚番を再選択"):
                                    st.session_state.tanaban_select_flag  = False
                                    st.rerun()
                                st.write(f"選択された棚番： {st.session_state.tanaban_select_value}")
                                st.stop()
                else:
                    if not st.session_state.qr_code_tana:
                        st.title("棚番を手動で選択し検索")
                        if st.button("入力方法を再選択"):
                            st.session_state.manual_input_check = False
                            st.session_state.manual_input_flag = 0
                            st.session_state.qr_code_tana = False
                            st.session_state.tanaban_select_temp = ""
                            st.rerun()
                        tanaban_select = ""
                        if st.session_state.manual_input_flag == 0:
                            st.write("棚番のQRコードをスキャンしてください:")
                            qr_code_tana = qrcode_scanner(key='qrcode_scanner_tana')  
                        
                            if qr_code_tana:  
                                # st.write(qr_code_tana) 
                                tanaban_select = qr_code_tana.strip()
                        else:
                            zkTanalistSplit = zkTanalist.split(",")
                            tanaban_select = st.selectbox(
                                "棚番号を選んでください", zkTanalistSplit, key="tanaban_select"
                            )
                        
                        if tanaban_select != "" and tanaban_select != "完A-0": # 完A-0は存在しない置き場(変更前提の初期値としてのみ利用)
                            st.session_state.tanaban_select_temp = tanaban_select
                            st.session_state.show_camera = False
                            st.session_state.qr_code_tana = True
                            st.session_state.qr_code = ""
                            st.session_state.production_order = ""
                            st.session_state.production_order_flag = False
                            st.rerun()  # 再描画して次のステップへ
                    else:
                        None
        else:  # st.session_state.manual_input_flag が 0 or 1 の場合
            # st.write(st.session_state.qr_code_tana)
            # st.session_state.manual_input_flag = 1
            if not st.session_state.qr_code_tana:
                if st.button("入力方法を再選択"):
                    st.session_state.manual_input_check = False
                    st.session_state.manual_input_flag = 0
                    st.session_state.qr_code_tana = False
                    st.session_state.tanaban_select_temp = ""
                    st.rerun()
                tanaban_select = ""
                if st.session_state.manual_input_flag == 0:
                    st.write("棚番のQRコードをスキャンしてください:")
                    qr_code_tana = qrcode_scanner(key='qrcode_scanner_tana')  
                
                    if qr_code_tana:  
                        # st.write(qr_code_tana) 
                        tanaban_select = qr_code_tana.strip()
                else:
                    zkTanalistSplit = zkTanalist.split(",")
                    # st.write(f"選択前棚番号: {tanaban_select}")
                    tanaban_select = st.selectbox(
                        "棚番号を選んでください", zkTanalistSplit, key="tanaban_select"
                    )
                    # options = zkTanalistSplit
                    # st.session_state.tanaban_select = st.selectbox("棚番号を選んでください", options, key="tanaban_select")
                    # st.write(f"選択された棚番号: {st.session_state.tanaban_select}")
                
                if tanaban_select != "" and tanaban_select != "完A-0": # 完A-0は存在しない置き場(変更前提の初期値としてのみ利用)
                    # st.session_state.tanaban = tanaban_select
                    st.session_state.tanaban_select_temp = tanaban_select
                    st.session_state.show_camera = False
                    st.session_state.qr_code_tana = True
                    # st.write(st.session_state.qr_code_tana)
                    st.session_state.qr_code = ""
                    st.session_state.production_order = ""
                    st.session_state.production_order_flag = False
                    st.rerun()  # 再描画して次のステップへ
            else:
                if st.button("棚番を再選択"):
                    st.session_state.qr_code_tana = False
                    st.session_state.tanaban_select_temp = ""
                    if st.session_state.manual_input_flag == 0:
                        st.session_state.show_camera = True  # 必要に応じてカメラ表示を再開
                    st.session_state.qr_code = ""
                    st.session_state.production_order = ""
                    st.session_state.production_order_flag = False
                    st.rerun()
                
                if not st.session_state.production_order_flag:
                    if st.session_state.manual_input_flag == 0:
                        qr_code_kari = ""
                        if st.button("移行票(製造オーダー)を再選択", key="camera_rerun"):
                            st.session_state.show_camera = True
                            st.session_state.qr_code = ""
                            st.session_state.production_order = None
                            st.session_state.production_order_flag = False
                            st.rerun()
                        if qr_code_kari == "":
                            st.session_state.show_camera = True
                            st.write("移行票(製造オーダー)のQRコードをスキャンしてください:")
                            qr_code_kari = qrcode_scanner(key="qrcode_scanner_fixed")
                            if qr_code_kari is not None and qr_code_kari.strip() != "":
                                st.session_state.qr_code = qr_code_kari.strip()
                            
                            if "qr_code" in st.session_state and st.session_state.qr_code != "":
                                st.session_state.production_order = f"{st.session_state.qr_code}"
                                st.session_state.show_camera = False
                                
                    else:                   
                        styled_input_text()
                        manual_input = st.text_input("移行票番号を入力し、Enterを押してください。 (1～6桁、例: 12345):",
                                                    value="",
                                                    max_chars=6,
                                                    key="manual_input")
                        if manual_input and manual_input.isdigit():
                            st.session_state.production_order = f"PO-{manual_input.zfill(6)}"
                            # st.session_state.manual_input_value = manual_input
                            st.session_state.show_camera = False
                        
                    st.write(f"#### 現在選択されている棚番 :   {st.session_state.tanaban_select_temp}")                   
                    button_key = "check_ok"
                    # st.session_state[button_key] = False
                    if st.session_state.production_order != "" and button_key not in st.session_state:
                    # if st.session_state.production_order != "" and st.session_state[button_key] == False:
                        # if st.button("棚番と移行票番号確認"):
                        message_text = f"""
                        #### 現在選択されている棚番 : {st.session_state.tanaban_select_temp}
                        #### 移行票番号(製造オーダー)は、
                        ## 「 {st.session_state.production_order} 」
                        #### でよろしいですか？
                        """
                        @st.dialog("棚番と移行票番号確認")
                        def dialog_button():
                            global message_text
                            global button_key
                            result_flag = approve_button(message_text, button_key)
                        dialog_button()

                    if st.session_state.get(button_key, False):
                        st.session_state.show_camera = False
                        st.session_state.production_order_flag = True
                        st.session_state[button_key] = False
                        del st.session_state[button_key]
                        st.rerun()
                    else:
                        if st.session_state.manual_input_flag == 0:
                            st.session_state.show_camera = True
                        st.session_state.production_order_flag = False
                        st.session_state.qr_code = None
                        st.session_state.production_order = None
                        if button_key in st.session_state:
                            del st.session_state[button_key]
                        # st.rerun()
                else:
                    if st.button("移行票番号を再入力"):
                        st.session_state.data = None
                        st.session_state.material = None
                        st.session_state.material_weight = None
                        st.session_state.cumulative_cost = 0.0
                        st.session_state.production_order_flag = False
                        st.session_state.qr_code = ""
                        st.session_state.production_order = ""
                        if st.session_state.manual_input_flag == 0:
                            st.session_state.show_camera = True  # 必要に応じてカメラ表示を再開
                        st.rerun()
                    
                    zkSplitNo = 99
                    zkSplitFlag = 0
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
                                default_quantity = clean_quantity(last_record.get("snps_um__ActualQt__c") or last_record.get("AITC_OrderQt__c") or 0.0)
                                default_process_order = int(last_record.get("snps_um__ProcessOrderNo__c", 0))
                                default_process_order_name = last_record.get("snps_um__ProcessName__c")
                                default_id = last_record.get("snps_um__Process__r", {}).get("AITC_ID18__c", "")
                                default_hinban = last_record.get("snps_um__Item__r", {}).get("Name", "")
                            else:
                                st.session_state.production_order = None
                                st.session_state.production_order_flag = False
                                st.warning("生産オーダーに該当する 'Done' ステータスの記録が見つかりませんでした。")
                                # st.stop()
                        else:
                            st.warning("移行票番号が見つかりませんでした。")
                            # st.stop()
                        
                        owner_value = st.session_state.owner
                        tanaban_select = st.session_state.tanaban_select_temp
                        production_order_value = st.session_state.production_order
                        styled_text(f"項　　目　 :　追加または削除の対象", bg_color="#c0c0c0", padding="7px", width="100%", text_color="#333333", font_size="16px", border_thickness="3px")
                        styled_text(f"社員番号　 : {owner_value}", bg_color="#c0c0c0", padding="7px", width="100%", text_color="#333333", font_size="20px", border_thickness="0px")
                        styled_text(f"棚　　番　 : {tanaban_select}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="20px", border_thickness="0px")
                        styled_text(f"移行票番号 : {production_order_value}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="20px", border_thickness="0px")
                        styled_text(f"品　　番　 : {default_hinban}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="20px", border_thickness="0px")
                        styled_text(f"工　　順　 : {default_process_order}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="20px", border_thickness="0px")
                        styled_text(f"工 程 名　 : {default_process_order_name}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="20px", border_thickness="0px")
                        styled_text(f"数量(工程) : {default_quantity}", bg_color="#FFFF00", padding="7px", width="100%", text_color="#333333", font_size="20px", border_thickness="0px")
                        if st.session_state.data:
                            hinban = default_hinban
                            process_order = default_process_order
                            process_order_name = default_process_order_name
                            quantity = default_quantity
                        else:
                            hinban = "-"
                            process_order = 0
                            process_order_name = "-"
                            quantity = 0.0
                                                    
                        add_del_flag = 0  # 0:追加 1:削除 9:取消     
                        left, center, right = st.columns(3)
                        with left:
                            submit_button_add = st.form_submit_button("追加")
                        with center:
                            submit_button_del = st.form_submit_button("削除")
                        with right:
                            submit_button_cancel = st.form_submit_button("取消")
                        if submit_button_add or submit_button_del or submit_button_cancel: 
                            if submit_button_add:
                                add_del_flag = 0
                            elif submit_button_del:
                                add_del_flag = 1
                            elif submit_button_cancel:
                                add_del_flag = 9
                            if add_del_flag == 9:
                                st.session_state.qr_code_tana = False
                                st.session_state.tanaban_select_temp = ""
                                if st.session_state.manual_input_flag == 0:
                                    st.session_state.show_camera = True  # 必要に応じて棚番再選択
                                st.session_state.qr_code = ""
                                st.session_state.production_order = ""
                                st.session_state.production_order_flag = False
                                st.rerun()
                                
                            # item_id = "a1ZQ8000000FB4jMAG"  # 工程手配明細マスタの 1-PC9-SW_IZ の ID(18桁) ※変更禁止
                            
                            # 棚番設定用マスタ(棚番を変更する場合には、下記に追加または削除してからatualizar_tanaban_addkari()を実行の事。尚、棚番は改行区切りである。)
                            #atualizar_tanaban_addkari(st.session_state.sf, item_id)
                            #st.stop()  # 以降の処理を止める
                            
                            # tanaban_select = "完A-3"  # 仮で設定
                            listCount = 0
                            listCountEtc = 0
                            listAdd = 0  # リストに追加する場合は 1 
                            listNumber = 0
                            zkTana = ""
                            zkIko = ""
                            zkHin = ""
                            zkKan = ""
                            zkSu = ""
                            zkMap = ""
                            zkOrder = ""
                            zkHistory = ""
                            record = data_catch(st.session_state.sf, item_id)
                            if record:
                                zkHistory = record["zkHistory__c"]  # zk履歴
                                zkTana_list = record["zkTanaban__c"].splitlines()  # 改行区切り　UM「新規 工程手配明細マスタ レポート」で見易くする為
                                listCount = len(zkTana_list)
                                if listCount > 2:
                                    for index, item in enumerate(zkTana_list):
                                        if item == tanaban_select:
                                            listNumber = index
                                            listAdd = 0
                                            break  # 条件を満たしたらループを終了
                                        else:
                                            listAdd = 1
                                else:
                                    if listCount == 1:
                                        if zkTana_list != tanaban_select:
                                            listAdd = 1
                                        else:
                                            listNumber = 0
                                    else:
                                        if zkTana_list[0] != tanaban_select and zkTana_list[1] != tanaban_select:
                                            listAdd = 1
                                        elif zkTana_list[0] == tanaban_select:
                                            listNumber = 0
                                        else:
                                            listNumber = 1
                                datetime_str = dt.now(jst).strftime("%Y/%m/%d %H:%M:%S")
                                zkHistory_value = ""
                                if listAdd == 1: # 棚番が無い場合
                                    st.write(f"❌05 **棚番 '{tanaban_select}' の追加は許可されてません。**")
                                    st.stop()  # 以降の処理を止める
                                else:
                                    zkIko_raw = record.get("zkIkohyoNo__c", "")
                                    if isinstance(zkIko_raw, str):
                                        zkIko = zkIko_raw.splitlines()
                                    else:
                                        zkIko = []
                                    listCountEtc = len(zkIko)
                                    if zkIko[listNumber] == "-" and add_del_flag == 1:
                                        st.write(f"❌06 **移行票番号の登録はありませんので、処理を中止します。**")
                                        st.stop()  # 以降の処理を止める
                                    if listCountEtc != listCount: # 棚番が追加されない限り、あり得ない分岐(初期設定時のみ使用)
                                        st.write(f"❌07 **移行票Noリスト '{zkIko}' の追加は許可されてません。**")
                                        st.stop()  # 以降の処理を止める
                                        zkKari = "-"
                                        separator = "\n"
                                        zkIko = f"{separator.join([zkKari] * listCount)}"
                                        zkHin = zkIko
                                        zkKan = zkIko
                                        zkSu = zkIko
                                        zkMap = zkIko
                                        zkHistory = zkIko
                                    else:
                                        zkOrder = st.session_state.production_order
                                        zkHistory_value = f"{tanaban_select},{zkOrder},{hinban},{process_order_name},{quantity},{datetime_str},{owner_value}"
                                        if add_del_flag == 0: # 追加の場合
                                            zkIko = list_update_zkKari(zkIko, "zkIkohyoNo__c", listNumber, zkOrder, 1)   # zk移行票No
                                            zkHin = list_update_zkKari(zkHin, "zkHinban__c", listNumber, hinban, 0)   # zk品番
                                            zkKan = list_update_zkKari(zkKan, "zkKanryoKoutei__c", listNumber, process_order_name, 0)   # zk完了工程
                                            zkSu = list_update_zkKari(zkSu, "zkSuryo__c", listNumber, f"{quantity}", 0)   # zk数量
                                            zkMap = list_update_zkKari(zkMap, "zkMap__c", listNumber, "-", -1)   # zkマップ座標
                                            zkHistory_value = f"{zkHistory_value},add"
                                        elif add_del_flag == 1: # 削除の場合
                                            zkIko = list_update_zkKari(zkIko, "zkIkohyoNo__c", listNumber, zkOrder, 3)   # zk移行票No
                                            zkHin = list_update_zkKari(zkHin, "zkHinban__c", listNumber, hinban, 2)   # zk品番
                                            zkKan = list_update_zkKari(zkKan, "zkKanryoKoutei__c", listNumber, process_order_name, 2)   # zk完了工程
                                            zkSu = list_update_zkKari(zkSu, "zkSuryo__c", listNumber, f"{quantity}", 2)   # zk数量
                                            zkMap = list_update_zkKari(zkMap, "zkMap__c", listNumber, "-", 2)   # zkマップ座標
                                            zkHistory_value = f"{zkHistory_value},del"
                                        zkHistory  = zkHistory_value + "\n" + str(zkHistory)   # zk履歴
                                        
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
                                st.write(f"❌08 **作業者コード '{owner}' が未入力です。**")
                                st.stop()  # 以降の処理を止める
                            zkScroll_flag = 0
                            if item_id:
                                update_tanaban(st.session_state.sf, item_id, tanaban_select, zkIko, zkHin, zkKan, zkSu, zkMap, zkHistory, zkOrder)
                                button_key = "check_ok_2"
                                if zkScroll_flag == 1 and button_key not in st.session_state:
                                    @st.dialog("処理結果通知")
                                    def dialog_button_2():
                                        global dialog_ok_flag
                                        # st.session_state["dialog_closed"] = True
                                        st.write(result_text)
                                        dialog_ok_flag = st.button("OK", key="dialog_ok")
                                        if dialog_ok_flag:
                                            st.session_state.qr_code_tana = False
                                            st.session_state.tanaban_select_temp = ""
                                            if st.session_state.manual_input_flag == 0:
                                                st.session_state.show_camera = True  # 必要に応じて棚番再選択
                                            st.session_state.qr_code = ""
                                            st.session_state.production_order = ""
                                            st.session_state.production_order_flag = False
                                            st.session_state[button_key] = False
                                            del st.session_state[button_key]
                                            zkScroll_flag = 0
                                            st.session_state["dialog_closed"] = True
                                            st.rerun()
                                    dialog_button_2()


