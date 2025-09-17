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

import easyocr
import numpy as np
import cv2
from PIL import Image
import glob

# 固定コンテナコードの始まり
from typing import Literal
from streamlit.components.v1 import html

_= '''
"""
st_fixed_container consist of two parts - fixed container and opaque container.
Fixed container is a container that is fixed to the top or bottom of the screen.
When transparent is set to True, the container is typical `st.container`, which is transparent by default.
When transparent is set to False, the container is custom opaque_container, that updates its background color to match the background color of the app.
Opaque container is a helper class, but can be used to create more custom views. See main for examples.
"""
'''
OPAQUE_CONTAINER_CSS = """
:root {{
    --background-color: #ffffff; /* Default background color */
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) div[data-testid="stVerticalBlock"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) > div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: var(--background-color);
    width: 100%;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) div[data-testid="stVerticalBlock"]:has(div.opaque-container-{id}):not(:has(div.not-opaque-container)) > div[data-testid="element-container"] {{
    display: none;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.not-opaque-container):not(:has(div[class^='opaque-container-'])) {{
    display: none;
}}
""".strip()

OPAQUE_CONTAINER_JS = """
const root = parent.document.querySelector('.stApp');
let lastBackgroundColor = null;
function updateContainerBackground(currentBackground) {
    parent.document.documentElement.style.setProperty('--background-color', currentBackground);
    ;
}
function checkForBackgroundColorChange() {
    const style = window.getComputedStyle(root);
    const currentBackgroundColor = style.backgroundColor;
    if (currentBackgroundColor !== lastBackgroundColor) {
        lastBackgroundColor = currentBackgroundColor; // Update the last known value
        updateContainerBackground(lastBackgroundColor);
    }
}
const observerCallback = (mutationsList, observer) => {
    for(let mutation of mutationsList) {
        if (mutation.type === 'attributes' && (mutation.attributeName === 'class' || mutation.attributeName === 'style')) {
            checkForBackgroundColorChange();
        }
    }
};
const main = () => {
    checkForBackgroundColorChange();
    const observer = new MutationObserver(observerCallback);
    observer.observe(root, { attributes: true, childList: false, subtree: false });
}
// main();
document.addEventListener("DOMContentLoaded", main);
""".strip()


def st_opaque_container(
    *,
    height: int | None = None,
    border: bool | None = None,
    key: str | None = None,
):
    global opaque_counter

    opaque_container = st.container()
    non_opaque_container = st.container()
    css = OPAQUE_CONTAINER_CSS.format(id=key)
    with opaque_container:
        html(f"<script>{OPAQUE_CONTAINER_JS}</script>", scrolling=False, height=0)
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='opaque-container-{key}'></div>",
            unsafe_allow_html=True,
        )
    with non_opaque_container:
        st.markdown(
            f"<div class='not-opaque-container'></div>",
            unsafe_allow_html=True,
        )

    return opaque_container.container(height=height, border=border)


FIXED_CONTAINER_CSS = """
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)){{
    background-color: transparent;
    position: {mode};
    width: inherit;
    background-color: inherit;
    {position}: {margin};
    z-index: 999;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)) div[data-testid="stVerticalBlock"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)) > div[data-testid="element-container"] {{
    display: none;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.not-fixed-container):not(:has(div[class^='fixed-container-'])) {{
    display: none;
}}
""".strip()

MARGINS = {
    "top": "2.875rem",
    "bottom": "0",
}


def st_fixed_container(
    *,
    height: int | None = None,
    border: bool | None = None,
    mode: Literal["fixed", "sticky"] = "fixed",
    position: Literal["top", "bottom"] = "top",
    margin: str | None = None,
    transparent: bool = False,
    key: str | None = None,
):
    if margin is None:
        margin = MARGINS[position]
    global fixed_counter
    fixed_container = st.container()
    non_fixed_container = st.container()
    css = FIXED_CONTAINER_CSS.format(
        mode=mode,
        position=position,
        margin=margin,
        id=key,
    )
    with fixed_container:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='fixed-container-{key}'></div>",
            unsafe_allow_html=True,
        )
    with non_fixed_container:
        st.markdown(
            f"<div class='not-fixed-container'></div>",
            unsafe_allow_html=True,
        )

    with fixed_container:
        if transparent:
            # return st.container(height=height, border=border)
            return st.container(border=border)

        return st_opaque_container(height=height, border=border, key=f"opaque_{key}")
# 固定コンテナコードの終わり



def carregar_credenciais():
    if os.path.exists('.streamlit/secrets.toml'):
        import toml
        secrets = toml.load('.streamlit/secrets.toml')
    else:
        secrets = st.secrets
    return secrets

secrets = carregar_credenciais()
jst = pytz.timezone('Asia/Tokyo')

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

def clean_quantity(value):
    if isinstance(value, str):
        num = re.sub(r'[^\d.]', '', value)
        return float(num) if num else 0.0
    return float(value) if value else 0.0

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
    #     完A-1\n完A-2\n完A-3\n完A-4\n完A-5\n完A-6\n完A-7\n完A-8\n完A-9\n完A-10\n完A-11\n完A-12\n完A-13\n完A-14\n完A-15\n完A-16\n完A-17\n完A-18\n完A-19\n完A-20\n完A-21\n完A-22\n完A-23\n完A-24\n完A-25\n完A-26\n完A-27\n完A-28\n完A-29\n完A-30\n完A-31\n完A-32\n完A-33\n完A-34\n完A-35\n完A-36\n完A-37\n完A-38\n完A-39\n完A-40\n完A-41\n完A-42\n完A-43\n完A-44\n完A-45\n完A-46\n完A-47\n完A-48\n完A-49\n完A-50\n
    #     完B-1\n完B-2\n完B-3\n完B-4\n完B-5\n完B-6\n完B-7\n完B-8\n完B-9\n完B-10\n完B-11\n完B-12\n完B-13\n完B-14\n完B-15\n完B-16\n完B-17\n完B-18\n完B-19\n完B-20\n完B-21\n完B-22\n完B-23\n完B-24\n完B-25\n完B-26\n完B-27\n完B-28\n完B-29\n完B-30\n完B-31\n完B-32\n完B-33\n完B-34\n完B-35\n完B-36\n完B-37\n完B-38\n完B-39\n完B-40\n完B-41\n完B-42\n完B-43\n完B-44\n完B-45\n完B-46\n完B-47\n完B-48\n完B-49\n完B-50\n
    #     完C-1\n完C-2\n完C-3\n完C-4\n完C-5\n完C-6\n完C-7\n完C-8\n完C-9\n完C-10\n完C-11\n完C-12\n完C-13\n完C-14\n完C-15\n完C-16\n完C-17\n完C-18\n完C-19\n完C-20\n完C-21\n完C-22\n完C-23\n完C-24\n完C-25\n完C-26\n完C-27\n完C-28\n完C-29\n完C-30\n完C-31\n完C-32\n完C-33\n完C-34\n完C-35\n完C-36\n完C-37\n完C-38\n完C-39\n完C-40\n完C-41\n完C-42\n完C-43\n完C-44\n完C-45\n完C-46\n完C-47\n完C-48\n完C-49\n完C-50\n
    #     完D-1\n完D-2\n完D-3\n完D-4\n完D-5\n完D-6\n完D-7\n完D-8\n完D-9\n完D-10\n完D-11\n完D-12\n完D-13\n完D-14\n完D-15\n完D-16\n完D-17\n完D-18\n完D-19\n完D-20\n完D-21\n完D-22\n完D-23\n完D-24\n完D-25\n完D-26\n完D-27\n完D-28\n完D-29\n完D-30\n完D-31\n完D-32\n完D-33\n完D-34\n完D-35\n完D-36\n完D-37\n完D-38\n完D-39\n完D-40\n完D-41\n完D-42\n完D-43\n完D-44\n完D-45\n完D-46\n完D-47\n完D-48\n完D-49\n完D-50\n
    #     除内-1\n除内-2\n除内-3\n除内-4\n除内-5\n除内-6\n除内-7\n除内-8\n除内-9\n除内-10\n除内-11\n除内-12\n除内-13\n除内-14\n除内-15\n除内-16\n除内-17\n除内-18\n除内-19\n除内-20\n除内-21\n除内-22\n除内-23\n除内-24\n除内-25\n除内-26\n除内-27\n除内-28\n除内-29\n除内-30\n除内-31\n除内-32\n除内-33\n除内-34\n除内-35\n除内-36\n除内-37\n除内-38\n除内-39\n除内-40\n除内-41\n除内-42\n除内-43\n除内-44\n除内-45\n除内-46\n除内-47\n除内-48\n除内-49\n除内-50\n
    #     除外-1\n除外-2\n除外-3\n除外-4\n除外-5\n除外-6\n除外-7\n除外-8\n除外-9\n除外-10\n除外-11\n除外-12\n除外-13\n除外-14\n除外-15\n除外-16\n除外-17\n除外-18\n除外-19\n除外-20\n除外-21\n除外-22\n除外-23\n除外-24\n除外-25\n除外-26\n除外-27\n除外-28\n除外-29\n除外-30\n除外-31\n除外-32\n除外-33\n除外-34\n除外-35\n除外-36\n除外-37\n除外-38\n除外-39\n除外-40\n除外-41\n除外-42\n除外-43\n除外-44\n除外-45\n除外-46\n除外-47\n除外-48\n除外-49\n除外-50\n
    #     A-1\nA-2\nA-3\nA-4\nA-5\nA-6\nA-7\nA-8\nA-9\nA-10\nA-11\nA-12\nA-13\nA-14\nA-15\nA-16\nA-17\nA-18\nA-19\nA-20\nA-21\nA-22\nA-23\nA-24\nA-25\nA-26\nA-27\nA-28\nA-29\nA-30\n
    #     D-1\nD-2\nD-3\nD-4\nD-5\nD-6\nD-7\nD-8\nD-9\nD-10\nD-11\nD-12\nD-13\nD-14\nD-15\nD-16\nD-17\nD-18\nD-19\nD-20\nD-21\nD-22\nD-23\nD-24\nD-25\nD-26\nD-27\nD-28\nD-29\nD-30\n
    #     E-31\nE-32\nE-33\nE-34\nE-35\nE-36\nE-37\nE-38\nE-39\nE-40\nE-41\nE-42\nE-43\nE-44\nE-45\nE-46\nE-47\nE-48\nE-49\nE-50\nE-51\nE-52\nE-53\nE-54\nE-55\nE-56\nE-57\nE-58\nE-59\nE-60\nE-61\nE-62\nE-63\nE-64\nE-65\nE-66\nE-67\nE-68\nE-69\nE-70\n
    #     F-1\nF-2\nF-3\nF-4\nF-5\nF-6\nF-7\nF-8\nF-9\nF-10\nF-11\nF-12\nF-13\nF-14\nF-15\nF-16\nF-17\nF-18\nF-19\nF-20\nF-21\nF-22\nF-23\nF-24\nF-25\nF-26\nF-27\nF-28\nF-29\nF-30\nF-31\nF-32\nF-33\nF-34\nF-35\nF-36\nF-37\nF-38\nF-39\nF-40\n
    #     G-1\nG-2\nG-3\nG-4\nG-5\nG-6\nG-7\nG-8\nG-9\nG-10\nG-11\nG-12\nG-13\nG-14\nG-15\nG-16\nG-17\nG-18\nG-19\nG-20\nG-21\nG-22\nG-23\nG-24\nG-25\nG-26\nG-27\nG-28\nG-29\nG-30\nG-31\nG-32\nG-33\nG-34\nG-35\nG-36\nG-37\nG-38\nG-39\nG-40\n
    #     H-1\nH-2\nH-3\nH-4\nH-5\nH-6\nH-7\nH-8\nH-9\nH-10\nH-11\nH-12\nH-13\nH-14\nH-15\nH-16\nH-17\nH-18\nH-19\nH-20\nH-21\nH-22\nH-23\nH-24\nH-25\nH-26\nH-27\nH-28\nH-29\nH-30\nH-31\nH-32\nH-33\nH-34\nH-35\nH-36\nH-37\nH-38\nH-39\nH-40\n
    #     R-1\nR-2\nR-3\nR-4\nR-5\nR-6\nR-7\nR-8\nR-9\nR-10\nR-11\nR-12\nR-13\nR-14\nR-15\nR-16\nR-17\nR-18\nR-19\nR-20\n
    #     S-1\nS-2\nS-3\nS-4\nS-5\nS-6\nS-7\nS-8\nS-9\nS-10\nS-11\nS-12\nS-13\nS-14\nS-15\nS-16\nS-17\nS-18\nS-19\nS-20
    # """
    zkTana = "完A-1\n完A-2\n完A-3\n完A-4\n完A-5\n完A-6\n完A-7\n完A-8\n完A-9\n完A-10\n完A-11\n完A-12\n完A-13\n完A-14\n完A-15\n完A-16\n完A-17\n完A-18\n完A-19\n完A-20\n完A-21\n完A-22\n完A-23\n完A-24\n完A-25\n完A-26\n完A-27\n完A-28\n完A-29\n完A-30\n完A-31\n完A-32\n完A-33\n完A-34\n完A-35\n完A-36\n完A-37\n完A-38\n完A-39\n完A-40\n完A-41\n完A-42\n完A-43\n完A-44\n完A-45\n完A-46\n完A-47\n完A-48\n完A-49\n完A-50\n完B-1\n完B-2\n完B-3\n完B-4\n完B-5\n完B-6\n完B-7\n完B-8\n完B-9\n完B-10\n完B-11\n完B-12\n完B-13\n完B-14\n完B-15\n完B-16\n完B-17\n完B-18\n完B-19\n完B-20\n完B-21\n完B-22\n完B-23\n完B-24\n完B-25\n完B-26\n完B-27\n完B-28\n完B-29\n完B-30\n完B-31\n完B-32\n完B-33\n完B-34\n完B-35\n完B-36\n完B-37\n完B-38\n完B-39\n完B-40\n完B-41\n完B-42\n完B-43\n完B-44\n完B-45\n完B-46\n完B-47\n完B-48\n完B-49\n完B-50\n完C-1\n完C-2\n完C-3\n完C-4\n完C-5\n完C-6\n完C-7\n完C-8\n完C-9\n完C-10\n完C-11\n完C-12\n完C-13\n完C-14\n完C-15\n完C-16\n完C-17\n完C-18\n完C-19\n完C-20\n完C-21\n完C-22\n完C-23\n完C-24\n完C-25\n完C-26\n完C-27\n完C-28\n完C-29\n完C-30\n完C-31\n完C-32\n完C-33\n完C-34\n完C-35\n完C-36\n完C-37\n完C-38\n完C-39\n完C-40\n完C-41\n完C-42\n完C-43\n完C-44\n完C-45\n完C-46\n完C-47\n完C-48\n完C-49\n完C-50\n完D-1\n完D-2\n完D-3\n完D-4\n完D-5\n完D-6\n完D-7\n完D-8\n完D-9\n完D-10\n完D-11\n完D-12\n完D-13\n完D-14\n完D-15\n完D-16\n完D-17\n完D-18\n完D-19\n完D-20\n完D-21\n完D-22\n完D-23\n完D-24\n完D-25\n完D-26\n完D-27\n完D-28\n完D-29\n完D-30\n完D-31\n完D-32\n完D-33\n完D-34\n完D-35\n完D-36\n完D-37\n完D-38\n完D-39\n完D-40\n完D-41\n完D-42\n完D-43\n完D-44\n完D-45\n完D-46\n完D-47\n完D-48\n完D-49\n完D-50\n除内-1\n除内-2\n除内-3\n除内-4\n除内-5\n除内-6\n除内-7\n除内-8\n除内-9\n除内-10\n除内-11\n除内-12\n除内-13\n除内-14\n除内-15\n除内-16\n除内-17\n除内-18\n除内-19\n除内-20\n除内-21\n除内-22\n除内-23\n除内-24\n除内-25\n除内-26\n除内-27\n除内-28\n除内-29\n除内-30\n除内-31\n除内-32\n除内-33\n除内-34\n除内-35\n除内-36\n除内-37\n除内-38\n除内-39\n除内-40\n除内-41\n除内-42\n除内-43\n除内-44\n除内-45\n除内-46\n除内-47\n除内-48\n除内-49\n除内-50\n除外-1\n除外-2\n除外-3\n除外-4\n除外-5\n除外-6\n除外-7\n除外-8\n除外-9\n除外-10\n除外-11\n除外-12\n除外-13\n除外-14\n除外-15\n除外-16\n除外-17\n除外-18\n除外-19\n除外-20\n除外-21\n除外-22\n除外-23\n除外-24\n除外-25\n除外-26\n除外-27\n除外-28\n除外-29\n除外-30\n除外-31\n除外-32\n除外-33\n除外-34\n除外-35\n除外-36\n除外-37\n除外-38\n除外-39\n除外-40\n除外-41\n除外-42\n除外-43\n除外-44\n除外-45\n除外-46\n除外-47\n除外-48\n除外-49\n除外-50\nA-1\nA-2\nA-3\nA-4\nA-5\nA-6\nA-7\nA-8\nA-9\nA-10\nA-11\nA-12\nA-13\nA-14\nA-15\nA-16\nA-17\nA-18\nA-19\nA-20\nA-21\nA-22\nA-23\nA-24\nA-25\nA-26\nA-27\nA-28\nA-29\nA-30\nD-1\nD-2\nD-3\nD-4\nD-5\nD-6\nD-7\nD-8\nD-9\nD-10\nD-11\nD-12\nD-13\nD-14\nD-15\nD-16\nD-17\nD-18\nD-19\nD-20\nD-21\nD-22\nD-23\nD-24\nD-25\nD-26\nD-27\nD-28\nD-29\nD-30\nE-31\nE-32\nE-33\nE-34\nE-35\nE-36\nE-37\nE-38\nE-39\nE-40\nE-41\nE-42\nE-43\nE-44\nE-45\nE-46\nE-47\nE-48\nE-49\nE-50\nE-51\nE-52\nE-53\nE-54\nE-55\nE-56\nE-57\nE-58\nE-59\nE-60\nE-61\nE-62\nE-63\nE-64\nE-65\nE-66\nE-67\nE-68\nE-69\nE-70\nF-1\nF-2\nF-3\nF-4\nF-5\nF-6\nF-7\nF-8\nF-9\nF-10\nF-11\nF-12\nF-13\nF-14\nF-15\nF-16\nF-17\nF-18\nF-19\nF-20\nF-21\nF-22\nF-23\nF-24\nF-25\nF-26\nF-27\nF-28\nF-29\nF-30\nF-31\nF-32\nF-33\nF-34\nF-35\nF-36\nF-37\nF-38\nF-39\nF-40\nG-1\nG-2\nG-3\nG-4\nG-5\nG-6\nG-7\nG-8\nG-9\nG-10\nG-11\nG-12\nG-13\nG-14\nG-15\nG-16\nG-17\nG-18\nG-19\nG-20\nG-21\nG-22\nG-23\nG-24\nG-25\nG-26\nG-27\nG-28\nG-29\nG-30\nG-31\nG-32\nG-33\nG-34\nG-35\nG-36\nG-37\nG-38\nG-39\nG-40\nH-1\nH-2\nH-3\nH-4\nH-5\nH-6\nH-7\nH-8\nH-9\nH-10\nH-11\nH-12\nH-13\nH-14\nH-15\nH-16\nH-17\nH-18\nH-19\nH-20\nH-21\nH-22\nH-23\nH-24\nH-25\nH-26\nH-27\nH-28\nH-29\nH-30\nH-31\nH-32\nH-33\nH-34\nH-35\nH-36\nH-37\nH-38\nH-39\nH-40\nR-1\nR-2\nR-3\nR-4\nR-5\nR-6\nR-7\nR-8\nR-9\nR-10\nR-11\nR-12\nR-13\nR-14\nR-15\nR-16\nR-17\nR-18\nR-19\nR-20\nS-1\nS-2\nS-3\nS-4\nS-5\nS-6\nS-7\nS-8\nS-9\nS-10\nS-11\nS-12\nS-13\nS-14\nS-15\nS-16\nS-17\nS-18\nS-19\nS-20"
    # zkTana = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n41\n42\n43\n44\n45\n46\n47\n48\n49\n50\n51\n52\n53\n54\n55\n56\n57\n58\n59\n60\n81\n82\n83\n84\n85\n86\n87\n88\n89\n90\n91\n92\n93\n94\n95\n96\n97\n98\n99\n100\n121\n122\n123\n124\n125\n126\n127\n128\n129\n130\n131\n132\n133\n134\n135\n136\n137\n138\n139\n140\n161\n162\n163\n164\n165\n166\n167\n168\n169\n170\n171\n172\n173\n174\n175\n176\n177\n178\n179\n180\n181\n182\n183\n184\n185\n186\n187\n188\n189\n190\n201\n202\n203\n204\n205\n206\n207\n208\n209\n210\n211\n212\n213\n214\n215\n216\n217\n218\n219\n220\n221\n222\n223\n224\n225\n226\n227\n228\n229\n230\n241\n242\n243\n244\n245\n246\n247\n248\n249\n250\n251\n252\n253\n254\n255\n256\n257\n258\n259\n260\n261\n262\n263\n264\n265\n266\n267\n268\n269\n270\n271\n272\n273\n274\n275\n276\n277\n278\n279\n280\n301\n302\n303\n304\n305\n306\n307\n308\n309\n310\n311\n312\n313\n314\n315\n316\n317\n318\n319\n320\n321\n322\n323\n324\n325\n326\n327\n328\n329\n330\n331\n332\n333\n334\n335\n336\n337\n338\n339\n340\n361\n362\n363\n364\n365\n366\n367\n368\n369\n370\n371\n372\n373\n374\n375\n376\n377\n378\n379\n380\n381\n382\n383\n384\n385\n386\n387\n388\n389\n390\n391\n392\n393\n394\n395\n396\n397\n398\n399\n400\n421\n422\n423\n424\n425\n426\n427\n428\n429\n430\n431\n432\n433\n434\n435\n436\n437\n438\n439\n440\n441\n442\n443\n444\n445\n446\n447\n448\n449\n450\n451\n452\n453\n454\n455\n456\n457\n458\n459\n460\n481\n482\n483\n484\n485\n486\n487\n488\n489\n490\n491\n492\n493\n494\n495\n496\n497\n498\n499\n500\n521\n522\n523\n524\n525\n526\n527\n528\n529\n530\n531\n532\n533\n534\n535\n536\n537\n538\n539\n540"
    try:
        # sf.snps_um__Process__c.update(item_id, {"zkTanaban__c": zkTana})
        # st.success("##### 「zk棚番」に書き込みました！")
        sf.snps_um__Process__c.update(item_id, {"zkMapNo__c": zkTana})
        st.success("##### 「zkマップ表示」に書き込みました！")
    except Exception as e:
        st.error(f"更新エラー: {e}")
        # reset_form()
    st.stop()
               
def update_tanaban(sf, item_id, zkTana, zkIko, zkHin, zkKan, zkSu, zkHistory, zkOrder):
    # global add_del_flag  # 0:追加　1:削除
    # global zkScroll_flag  # 初期値0
    # global result_text
    try:
        # sf.snps_um__Process__c.update(item_id, {"zkHinban__c": zkHin})
        # _= '''
        sf.snps_um__Process__c.update(item_id, {
            "zkIkohyoNo__c": zkIko,
            "zkHinban__c": zkHin,
            "zkKanryoKoutei__c": zkKan,
            "zkSuryo__c": zkSu,
            "zkHistory__c": zkHistory
        })
        # '''
        # st.success(f"##### snps_um__Process__c の棚番 '{zkTana}' に移行票No '{zkOrder}' を追加しました。")
        st.session_state.zkScroll_flag = 1
        if st.session_state.add_del_flag == 0: # 追加の場合
            # st.success(f"棚番 '{zkTana}' に、移行票No '{zkOrder}' を追加しました。")
            st.session_state.result_text = f"棚番 '{zkTana}' に、移行票No '{zkOrder}' を追加しました。"
        else:
            # st.success(f"棚番 '{zkTana}' から、移行票No '{zkOrder}' を削除しました。")
            st.session_state.result_text = f"棚番 '{zkTana}' から、移行票No '{zkOrder}' を削除しました。"
    except Exception as e:
        st.error(f"更新エラー: {e}")
        reset_form()
        st.stop()

# WHERE Name LIKE '%{item_name}%' AND snps_um__ProcessOrderNo__c = 999
def data_catch(sf, item_id):
    query = f"""
        SELECT AITC_ID18__c, Name,
            zkTanaban__c, zkIkohyoNo__c ,zkHinban__c, zkKanryoKoutei__c,
            zkSuryo__c, zkHistory__c
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
            st.warning(f"入力文字 '{item_name}' に関連する 品番 が見つかりませんでした。")
            # st.warning(f"品目名称 '{item_name}' に関連する snps_um__Item__c が見つかりませんでした。")
            # return None
            # reset_form()
            st.stop()
    except Exception as e:
        st.error(f"品目名称検索エラー: {e}")
        # return None
        # reset_form()
        st.stop()
       
def list_update_zkKari(record, zkKari, dbItem, listNo, update_value, flag):
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

def tool_tips(text):
    st.markdown(f"<p style='font-size:12px;'>{text}</p>", unsafe_allow_html=True)

def set_flag(flag):
    global add_del_flag
    global button_flag
    add_del_flag = flag
    button_flag = 1

button_style = """
<style>
div.stButton {
    display: flex;
    justify-content: center;
    width: 100%; /* 必要に応じて調整：ボタンコンテナの幅 */
    # width: auto; /* 必要に応じて変更 */
}
div.stButton > button {
    font-size: 12px !important; /* 文字サイズを指定 */
    font-weight  : bold ;
    color        : #000;
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background   : #0FF                ;/* 背景色：aqua            */
    width: 350px; /* ボタンの横幅を固定値に設定 */
    max-width: 350px; /* 必要に応じて最大幅も設定 */
    height: 24px;
}
</style>
"""

selectbox_style = """
    <style>
    .centered-selectbox {
        display: flex;
        justify-content: center;
        width: 200px !important;
    }
    </style>
"""

_= '''
selectbox_style = """
<style>
div.stSelectbox {
    display: flex;
    justify-content: center;
    width: 100%; /* 必要に応じて調整：ボタンコンテナの幅 */
}
div.stSelectbox > selectbox {
    font-size: 12px !important; /* 文字サイズを指定 */
    font-weight  : bold ;
    color        : #000;
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background   : #0FF                ;/* 背景色：aqua            */
    width: 200px; /* ボタンの横幅を固定値に設定 */
    max-width: 200px; /* 必要に応じて最大幅も設定 */
    height: 24px;
}
</style>
"""
'''


# 画面の状態を管理する変数（初期状態はメイン画面）
if 'current_screen' not in st.session_state:
    st.session_state['current_screen'] = 'main'

# 画面の履歴を管理
if 'history' not in st.session_state:
    st.session_state['history'] = ['main']

def set_screen(screen_name):
    if st.session_state['current_screen'] != screen_name:
        st.session_state['history'].append(st.session_state['current_screen'])
        st.session_state['current_screen'] = screen_name

def go_back():
    if len(st.session_state['history']) > 1:
        st.session_state['current_screen'] = st.session_state['history'].pop()

def display_line():
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='margin-bottom: 0px;line-height: 0.5'>――――――――――――――――――――――――――</span> \
        </p>"
        , unsafe_allow_html=True
    )
    _= '''
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='margin-bottom: 0px;line-height: 1.0'>------------------------------------------------------------</span> \
        </p>"
        , unsafe_allow_html=True
    )
    '''

def display_header(color, text):
    st.markdown(
        f"<p style='text-align:center;'> \
        <span style='font-size: 40px;font-weight:bold;color:{color};margin-bottom: 0px;line-height: 0.5'>{text}</span> \
        </p>"
        , unsafe_allow_html=True
    )
    # display_line()

def display_footer():
    display_line()
    _= '''
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='font-size: 14px;'>〇〇〇〇〇株式会社&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> \
        <span style='font-size: 10px;'>ver.XX.XXX.XXX</span> \
        </p>"
        , unsafe_allow_html=True
    )
    '''
    left, center, right = st.columns([0.35, 0.3, 0.35])
    _= '''
    with center:
        st.markdown(
            "<p style='text-align:center;'> \
            <span style='font-size: 14px;'>アイテック株式会社&nbsp;</span> \
            <span style='font-size: 10px;'>ver.1.0.0</span> \
            </p>"
            , unsafe_allow_html=True
        )
    '''
    # _= '''
    with right:
        st.markdown(
            "<p style='text-align:left;'> \
            <span style='font-size: 10px;'>ver.1.0.0</span> \
            </p>"
            , unsafe_allow_html=True
        )
    # '''

def display_container(color, text):
    with st_fixed_container(mode="sticky", position="top", transparent=True):
        st.markdown(
            f"<p style='text-align:center;'> \
            <span style='font-size: 40px;font-weight:bold;color:{color};margin-bottom: 0px;line-height: 0.5'>{text}</span> \
            </p>"
            , unsafe_allow_html=True
        )


def button_set(button_name, button_text, screen_name):
    left, center, right = st.columns([0.25, 0.5, 0.25])
    with center:
        if button_name == "btn99999":
            button_name = st.button(button_text, on_click=go_back)
        else:
            button_name = st.button(button_text, on_click=set_screen, args=(screen_name,))

def button_make(button_text, screen_name):
    st.markdown("""
        <style>
        .stButton>button { /* Streamlitのボタン要素に直接スタイルを適用 */
            background-color: #FF0;
            color: black;
            font-size: 10px !important;
            text-align: center;
            font-weight: bold;
            border-radius: 5px;
            width: 200px;
            max-width: 200px;
            height: 20px;
            margin: 5px; /* ボタン間の間隔など調整 */
        }
        .stButton>button:hover {
            opacity: 0.8;
        }
        </style>
    """, unsafe_allow_html=True)
    st.button(button_text, key=button_text, on_click=set_screen, args=(screen_name,))
    # if st.button(button_text, key=button_text): # keyを設定して複数のボタンを区別
    #     set_screen(screen_name)

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
        
def pad_to_center(img, target_width, pad_color=(255, 255, 255)):
    h, w = img.shape[:2]
    pad_left = (target_width - w) // 2
    pad_right = target_width - w - pad_left
    return cv2.copyMakeBorder(img, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=pad_color)

def image_viewer(target_text):
    image_files = sorted(glob.glob("TanaMap*.png") + glob.glob("TanaMap*.jpg") + glob.glob("TanaMap*.jpeg"))
    image_flag = False
    image_sub_flag = False
    image_search_flag = False
    if not image_files:
        st.warning("画像ファイルが見つかりませんでした。")
    else:
        reader = easyocr.Reader(['ja', 'en'], gpu=False)
        first_char = target_text[0]
        second_char = target_text[1]
        after_hyphen = target_text.split("-")[1]
        after_hyphen_int = int(after_hyphen)
        # st.write(f"ハイフン以降の数値: {after_hyphen_int}（型: {type(after_hyphen_int)}）")
        # st.write(first_char)
        # st.write(second_char)
        # st.write(f"{after_hyphen_int}")
        image_path_sub2 = "TanaMap20250820-0.png"
        if first_char == "完" and after_hyphen_int <= 9:
            sub_text = "P-1"
            image_path_sub = "TanaMap20250820-P1.png"
            image_path = "TanaMap20250820-1.png"
            image_search_flag = True
        elif (first_char == "完" and 10 <= after_hyphen_int <= 15): 
            sub_text = "P-2"
            image_path_sub = "TanaMap20250820-P2.png"
            image_path = "TanaMap20250820-2.png"
            image_search_flag = True
        elif (first_char == "完" and 16 <= after_hyphen_int <= 40): 
            sub_text = "P-3"
            image_path_sub = "TanaMap20250820-P3.png"
            # image_path = "TanaMap20250820-2.png"
            image_search_flag = True
        elif ((first_char == "E" and 31 <= after_hyphen_int <= 37) 
            or (first_char == "G" and after_hyphen_int <= 18) 
            or (first_char == "H" and after_hyphen_int <= 18) 
            or (first_char == "R" and after_hyphen_int <= 19)):
            sub_text = "P-4"
            image_path_sub = "TanaMap20250820-P4.png"
            image_path = "TanaMap20250820-3.png"
            image_search_flag = True
        elif ((first_char == "A" and after_hyphen_int <= 16) 
            or (first_char == "D" and after_hyphen_int <= 16) 
            or (first_char == "E" and 51 <= after_hyphen_int <= 57) 
            or (first_char == "F" and after_hyphen_int <= 18)):
            sub_text = "P-5"
            image_path_sub = "TanaMap20250820-P5.png"
            image_path = "TanaMap20250820-4.png"
            image_search_flag = True
        elif ((first_char == "E" and 38 <= after_hyphen_int <= 50) 
            or (first_char == "G" and 20 <= after_hyphen_int <= 33) 
            or (first_char == "H" and 31 <= after_hyphen_int <= 37)):
            sub_text = "P-6"
            image_path_sub = "TanaMap20250820-P6.png"
            image_path = "TanaMap20250820-5.png"
            image_search_flag = True
        elif ((first_char == "A" and 19 <= after_hyphen_int <= 30) 
            or (first_char == "D" and 18 <= after_hyphen_int <= 28) 
            or (first_char == "E" and 58 <= after_hyphen_int <= 64) 
            or (first_char == "F" and 20 <= after_hyphen_int <= 32) 
            or (first_char == "H" and 26 <= after_hyphen_int <= 30) 
            or (first_char == "S" and after_hyphen_int <= 12)):
            sub_text = "P-7"
            image_path_sub = "TanaMap20250820-P7.png"
            image_path = "TanaMap20250820-6.png"
            image_search_flag = True
        elif (first_char == "除" and second_char == "内" and 1 <= after_hyphen_int <= 50): 
            sub_text = "P-8"
            image_path_sub = "TanaMap20250820-P8.png"
            # image_path = "TanaMap20250820-2.png"
            image_search_flag = True
        elif (first_char == "除" and second_char == "外" and 1 <= after_hyphen_int <= 50): 
            sub_text = "P-9"
            image_path_sub = "TanaMap20250820-P9.png"
            # image_path = "TanaMap20250820-2.png"
            image_search_flag = True
        if image_search_flag:
            # OCR実行   r"完.?[ABC][-–—]?(1[0-5]|[1-9])"
            
            image_sub = Image.open(image_path_sub).convert("RGB")
            image_sub_np = np.array(image_sub)
            if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                if os.path.exists(image_path):
                    image = Image.open(image_path).convert("RGB")
                    image_np = np.array(image)
                else:
                    st.error(f"画像ファイルが見つかりません: {image_path}")
                    st.stop()
            _= '''
            results_sub = reader.readtext(image_sub_np)
            target_center = None
            target_pattern = re.compile(fr"{sub_text}")
            target_pattern_b = re.compile(fr"{sub_text}_")
            # st.write(target_pattern)
            for bbox, text, prob in results_sub:
                cleaned = text.replace(" ", "")
                # st.write(cleaned)
                if target_pattern.search(cleaned):
                    (tl, tr, br, bl) = bbox
                    center_x = int((tl[0] + br[0]) / 2)
                    center_y = int((tl[1] + br[1]) / 2)
                    target_center = (center_x, center_y)
                    break
                else:
                    if target_pattern_b.search(cleaned):
                        (tl, tr, br, bl) = bbox
                        center_x = int((tl[0] + br[0]) / 2)
                        center_y = int((tl[1] + br[1]) / 2)
                        if second_char == "B" or second_char == "D":
                            center_x += 10
                        else:
                            center_x -= 10
                        target_center = (center_x, center_y)
                        break
            # 赤い円（○）を描画
            image_with_circle_a = image_sub_np.copy()
            if target_center:
                cv2.circle(image_with_circle_a, target_center, 60, (255, 0, 0), thickness=8)
                # 画像サイズに合わせて矩形を描画
                h, w = image_with_circle_a.shape[:2]
                cv2.rectangle(image_with_circle_a, (0, 0), (w - 1, h - 1), (0, 0, 0), 20)
                # st.image(image_with_circle_a, caption=f"{sub_text} を検出しました", use_container_width=True)
                st.success(f"座標: {target_center}")
                image_sub_flag = True
            else:
                None
                # st.image(image_with_circle_a, caption=f"{sub_text} は検出されませんでした", use_container_width=True)
                # st.warning(f"{sub_text} はこの画像には見つかりませんでした。")
            if image_sub_flag == False:
                st.warning(f"{sub_text} はこの画像には見つかりませんでした。")
            '''
            
            image_with_circle_a = image_sub_np.copy()
            h, w = image_with_circle_a.shape[:2]
            cv2.rectangle(image_with_circle_a, (0, 0), (w - 1, h - 1), (0, 0, 0), 40)
            image_sub2 = Image.open(image_path_sub2).convert("RGB")
            image_sub2_np = np.array(image_sub2)
            image_with_circle_b = image_sub2_np.copy()

            if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                results = reader.readtext(image_np)
                target_center = None
                if first_char == "完":
                    target_pattern = re.compile(fr"完{second_char}-{after_hyphen_int}")
                    target_pattern_b = re.compile(fr"{second_char}-{after_hyphen_int}")
                    # st.write(target_pattern)
                    for bbox, text, prob in results:
                        cleaned = text.replace(" ", "")
                        # st.write(cleaned)
                        if target_pattern.search(cleaned):
                            (tl, tr, br, bl) = bbox
                            center_x = int((tl[0] + br[0]) / 2)
                            center_y = int((tl[1] + br[1]) / 2)
                            target_center = (center_x, center_y)
                            break
                        else:
                            if target_pattern_b.search(cleaned):
                                (tl, tr, br, bl) = bbox
                                center_x = int((tl[0] + br[0]) / 2)
                                center_y = int((tl[1] + br[1]) / 2)
                                if second_char == "B" or second_char == "D":
                                    center_x += 10
                                else:
                                    center_x -= 10
                                target_center = (center_x, center_y)
                                break
                else:
                    for bbox, text, prob in results:
                        # st.write(text)
                        if text.strip() == target_text.strip():
                            (tl, tr, br, bl) = bbox
                            center_x = int((tl[0] + br[0]) / 2)
                            center_y = int((tl[1] + br[1]) / 2)
                            target_center = (center_x, center_y)
                            break
                        elif ((text.strip() == "R-g" and target_text.strip() == "R-9")
                            or (text.strip() == "6-5" and target_text.strip() == "G-5") 
                            or (text.strip() == "6-6" and target_text.strip() == "G-6") 
                            or (text.strip() == "6-17" and target_text.strip() == "G-17")):
                            (tl, tr, br, bl) = bbox
                            center_x = int((tl[0] + br[0]) / 2)
                            center_y = int((tl[1] + br[1]) / 2)
                            target_center = (center_x, center_y)
                            break
            else:
                target_center = (1, 1)
            # 赤い円（○）を描画
            if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                image_with_circle_c = image_np.copy()
            if target_center:
                if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                    # cv2.circle(image_with_circle_c, target_center, 50, (255, 0, 0), thickness=8)
                    if first_char == "E":
                        axes = (90, 50) 
                    else:
                        axes = (65, 35)  # 横長：横65、縦35
                    angle = 0         # 回転なし
                    cv2.ellipse(image_with_circle_c, target_center, axes, angle, 0, 360, (255, 0, 0), thickness=8)
                    # st.image(image_with_circle_c, caption=f"{target_text} を検出しました", use_container_width=True)
    
                    # 画像サイズに合わせて矩形を描画
                    h, w = image_with_circle_c.shape[:2]
                    cv2.rectangle(image_with_circle_c, (0, 0), (w - 1, h - 1), (0, 0, 255), 20)
                    # cv2.rectangle(image_with_circle_c, (0, 0), (w - 1, h - 1), (255, 0, 255), 20)
                img1 = image_with_circle_a
                img2 = image_with_circle_b
                if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                    img3 = image_with_circle_c
                
                # 最大横幅を取得
                if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                    max_width = max(img1.shape[1], img2.shape[1], img3.shape[1])
                else:
                    max_width = max(img1.shape[1], img2.shape[1])
                # 中央揃えでパディング
                img1_padded = pad_to_center(img1, max_width)
                img2_padded = pad_to_center(img2, max_width)
                if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                    img3_padded = pad_to_center(img3, max_width)
                
                # 縦に結合
                if sub_text != "P-3" and sub_text != "P-8" and sub_text != "P-9":
                    combined = np.vstack([img1_padded, img2_padded, img3_padded])
                    st.image(combined, channels="RGB", use_container_width=True)
                else:
                    st.image(img1_padded, channels="RGB", use_container_width=True)
                # st.image(combined, channels="RGB", caption=f"画像を結合しました", use_container_width=True)
                # st.success(f"座標: {target_center}")
                image_flag = True
            else:
                None
                # st.image(image_with_circle, caption=f"{target_text} は検出されませんでした", use_container_width=True)
                # st.warning(f"{target_text} はこの画像には見つかりませんでした。")
        if image_flag == False:
            st.warning(f"{target_text} はこの画像には見つかりませんでした。")
    # st.stop()

if "sf" not in st.session_state:
    try:
        st.session_state.sf = authenticate_salesforce()
        # st.success("Salesforceに正常に接続しました！")
    except Exception as e:
        st.error(f"認証エラー: {e}")
        st.stop()
        
def zaiko_place():
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
    if "manual_input_info_flag" not in st.session_state:
        st.session_state.manual_input_info_flag = 0
    if "manual_input_hinban" not in st.session_state:
        st.session_state.manual_input_hinban = ""
    if "manual_input_hinban_entered" not in st.session_state:
        st.session_state.manual_input_hinban_entered = False
    # if "tanaban" not in st.session_state:
    #     st.session_state.tanaban = ""
    if "tanaban_select_input" not in st.session_state:
        st.session_state.tanaban_select_input = False
    if "tanaban_select" not in st.session_state:
        st.session_state.tanaban_select = ""
    if "selected_tanaban_key" not in st.session_state:
        st.session_state.selected_tanaban_key = ""
    if "tanaban_select_info" not in st.session_state:
        st.session_state.tanaban_select_info = ""
    if "tanaban_select_temp" not in st.session_state:
        st.session_state.tanaban_select_temp = ""
    if "tanaban_select_temp_info" not in st.session_state:
        st.session_state.tanaban_select_temp_info = ""
    if "tanaban_select_value" not in st.session_state:
        st.session_state.tanaban_select_value = ""
    if "tanaban_select_flag" not in st.session_state:
        st.session_state.tanaban_select_flag = False
    if "tanaban_record" not in st.session_state:
        st.session_state.tanaban_select_value = ""
    if "tanaban_record_flag" not in st.session_state:
        st.session_state.tanaban_select_flag = False
    if "qr_code" not in st.session_state:
        st.session_state.qr_code = None
    if "qr_code_tana" not in st.session_state:
        st.session_state.qr_code_tana = False
    if "qr_code_tana_info" not in st.session_state:
        st.session_state.qr_code_tana_info = False
    if "hinban_select_value" not in st.session_state:
        st.session_state.hinban_select_value = ""
    if "hinban_select_flag" not in st.session_state:
        st.session_state.hinban_select_flag = False
    if "list_flag" not in st.session_state:
        st.session_state.list_flag = 0
    if "record" not in st.session_state:
        st.session_state.record = ""
    if "records" not in st.session_state:
        st.session_state.records = ""
    if "df_search_result" not in st.session_state:
        st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
    if "df" not in st.session_state:
        st.session_state.df = None
    if "selected_row" not in st.session_state:
        st.session_state.selected_row = None
    if "button_key" not in st.session_state:
        st.session_state.button_key = ""
    if "add_del_flag" not in st.session_state: # 0:追加　1:削除
        st.session_state.add_del_flag = 0
    if "zkScroll_flag" not in st.session_state: # 初期値0
        st.session_state.zkScroll_flag = 0
    if "result_text" not in st.session_state:
        st.session_state.result_text = ""
    
    if "user_code_entered" not in st.session_state:
        st.session_state.user_code_entered = False
        st.session_state.user_code = ""
    
    item_id = "a1ZQ8000000FB4jMAG"  # 工程手配明細マスタの 1-PC9-SW_IZ の ID(18桁) ※変更禁止
    zkTanalist = """
        ---,完A-1,完A-2,完A-3,完A-4,完A-5,完A-6,完A-7,完A-8,完A-9,完A-10,完A-11,完A-12,完A-13,完A-14,完A-15,完A-16,完A-17,完A-18,完A-19,完A-20,完A-21,完A-22,完A-23,完A-24,完A-25,完A-26,完A-27,完A-28,完A-29,完A-30,完A-31,完A-32,完A-33,完A-34,完A-35,完A-36,完A-37,完A-38,完A-39,完A-40,完A-41,完A-42,完A-43,完A-44,完A-45,完A-46,完A-47,完A-48,完A-49,完A-50,
        完B-1,完B-2,完B-3,完B-4,完B-5,完B-6,完B-7,完B-8,完B-9,完B-10,完B-11,完B-12,完B-13,完B-14,完B-15,完B-16,完B-17,完B-18,完B-19,完B-20,完B-21,完B-22,完B-23,完B-24,完B-25,完B-26,完B-27,完B-28,完B-29,完B-30,完B-31,完B-32,完B-33,完B-34,完B-35,完B-36,完B-37,完B-38,完B-39,完B-40,完B-41,完B-42,完B-43,完B-44,完B-45,完B-46,完B-47,完B-48,完B-49,完B-50,
        完C-1,完C-2,完C-3,完C-4,完C-5,完C-6,完C-7,完C-8,完C-9,完C-10,完C-11,完C-12,完C-13,完C-14,完C-15,完C-16,完C-17,完C-18,完C-19,完C-20,完C-21,完C-22,完C-23,完C-24,完C-25,完C-26,完C-27,完C-28,完C-29,完C-30,完C-31,完C-32,完C-33,完C-34,完C-35,完C-36,完C-37,完C-38,完C-39,完C-40,完C-41,完C-42,完C-43,完C-44,完C-45,完C-46,完C-47,完C-48,完C-49,完C-50,
        完D-1,完D-2,完D-3,完D-4,完D-5,完D-6,完D-7,完D-8,完D-9,完D-10,完D-11,完D-12,完D-13,完D-14,完D-15,完D-16,完D-17,完D-18,完D-19,完D-20,完D-21,完D-22,完D-23,完D-24,完D-25,完D-26,完D-27,完D-28,完D-29,完D-30,完D-31,完D-32,完D-33,完D-34,完D-35,完D-36,完D-37,完D-38,完D-39,完D-40,完D-41,完D-42,完D-43,完D-44,完D-45,完D-46,完D-47,完D-48,完D-49,完D-50,
        除内-1,除内-2,除内-3,除内-4,除内-5,除内-6,除内-7,除内-8,除内-9,除内-10,除内-11,除内-12,除内-13,除内-14,除内-15,除内-16,除内-17,除内-18,除内-19,除内-20,除内-21,除内-22,除内-23,除内-24,除内-25,除内-26,除内-27,除内-28,除内-29,除内-30,除内-31,除内-32,除内-33,除内-34,除内-35,除内-36,除内-37,除内-38,除内-39,除内-40,除内-41,除内-42,除内-43,除内-44,除内-45,除内-46,除内-47,除内-48,除内-49,除内-50,
        除外-1,除外-2,除外-3,除外-4,除外-5,除外-6,除外-7,除外-8,除外-9,除外-10,除外-11,除外-12,除外-13,除外-14,除外-15,除外-16,除外-17,除外-18,除外-19,除外-20,除外-21,除外-22,除外-23,除外-24,除外-25,除外-26,除外-27,除外-28,除外-29,除外-30,除外-31,除外-32,除外-33,除外-34,除外-35,除外-36,除外-37,除外-38,除外-39,除外-40,除外-41,除外-42,除外-43,除外-44,除外-45,除外-46,除外-47,除外-48,除外-49,除外-50,
        A-1,A-2,A-3,A-4,A-5,A-6,A-7,A-8,A-9,A-10,A-11,A-12,A-13,A-14,A-15,A-16,A-17,A-18,A-19,A-20,A-21,A-22,A-23,A-24,A-25,A-26,A-27,A-28,A-29,A-30,
        D-1,D-2,D-3,D-4,D-5,D-6,D-7,D-8,D-9,D-10,D-11,D-12,D-13,D-14,D-15,D-16,D-17,D-18,D-19,D-20,D-21,D-22,D-23,D-24,D-25,D-26,D-27,D-28,D-29,D-30,
        E-31,E-32,E-33,E-34,E-35,E-36,E-37,E-38,E-39,E-40,E-41,E-42,E-43,E-44,E-45,E-46,E-47,E-48,E-49,E-50,E-51,E-52,E-53,E-54,E-55,E-56,E-57,E-58,E-59,E-60,E-61,E-62,E-63,E-64,E-65,E-66,E-67,E-68,E-69,E-70,
        F-1,F-2,F-3,F-4,F-5,F-6,F-7,F-8,F-9,F-10,F-11,F-12,F-13,F-14,F-15,F-16,F-17,F-18,F-19,F-20,F-21,F-22,F-23,F-24,F-25,F-26,F-27,F-28,F-29,F-30,F-31,F-32,F-33,F-34,F-35,F-36,F-37,F-38,F-39,F-40,
        G-1,G-2,G-3,G-4,G-5,G-6,G-7,G-8,G-9,G-10,G-11,G-12,G-13,G-14,G-15,G-16,G-17,G-18,G-19,G-20,G-21,G-22,G-23,G-24,G-25,G-26,G-27,G-28,G-29,G-30,G-31,G-32,G-33,G-34,G-35,G-36,G-37,G-38,G-39,G-40,
        H-1,H-2,H-3,H-4,H-5,H-6,H-7,H-8,H-9,H-10,H-11,H-12,H-13,H-14,H-15,H-16,H-17,H-18,H-19,H-20,H-21,H-22,H-23,H-24,H-25,H-26,H-27,H-28,H-29,H-30,H-31,H-32,H-33,H-34,H-35,H-36,H-37,H-38,H-39,H-40,
        R-1,R-2,R-3,R-4,R-5,R-6,R-7,R-8,R-9,R-10,R-11,R-12,R-13,R-14,R-15,R-16,R-17,R-18,R-19,R-20,
        S-1,S-2,S-3,S-4,S-5,S-6,S-7,S-8,S-9,S-10,S-11,S-12,S-13,S-14,S-15,S-16,S-17,S-18,S-19,S-20
        """
    
    if not st.session_state.manual_input_check:
        left, center, right = st.columns([0.25, 0.5, 0.25])
        with center:
            st.title("入力方法　選択")
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
            tool_tips("(品番から棚番を検索)")
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
        left, center, right = st.columns([0.25, 0.5, 0.25])
        with center:
            if st.button("入力方法を再選択"):
                st.session_state.manual_input_check = False
                st.session_state.manual_input_flag = 0
                st.session_state.manual_input_check_select = False
                st.session_state.manual_input_check_flag = 0
                st.session_state.manual_input_info_flag = 0
                st.session_state.manual_input_hinban_entered = False
                st.session_state.hinban_select_flag = False
                st.session_state.tanaban_select_flag  = False
                st.session_state.tanaban_select_input = False
                st.session_state.qr_code_tana_info = False
                st.session_state.tanaban_select_temp_info = ""
                st.session_state.records  = None
                st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                st.session_state.record  = None
                st.rerun()
        if st.session_state.manual_input_flag == 9:
            if not st.session_state.manual_input_check_select:
                left, center, right = st.columns([0.25, 0.5, 0.25])
                with center:
                    st.title("参照方法　選択")
                left, center1, center2, right = st.columns(4)
                with center1:
                    button_manual_Hinban = st.button("品番(入力)で検索")
                    tool_tips("(品番を手動で入力し検索(曖昧検索可))")
                with center2:
                    button_manual_Tanaban = st.button("棚番で検索")
                    tool_tips("(棚番をQRコード入力または手動選択で検索)")
                # with right:
                #     button_qr_Ikohyo = st.button("移行票番号で検索")
                #     tool_tips("(移行票番号をQRコードまたは手動入力で検索)")
                # if button_manual_Hinban or button_manual_Tanaban or button_qr_Ikohyo : 
                if button_manual_Hinban or button_manual_Tanaban: 
                    if button_manual_Hinban:
                        st.session_state.manual_input_check_flag = 0
                    elif button_manual_Tanaban:
                        st.session_state.manual_input_check_flag = 1
                    # else:
                    #     st.session_state.manual_input_check_flag = 2
                    st.session_state.manual_input_check_select = True
                    st.rerun()
            else:
                left, center, right = st.columns([0.25, 0.5, 0.25])
                with center:
                    if st.button("参照方法を再選択"):
                        st.session_state.manual_input_check_select = False
                        st.session_state.manual_input_check_flag = 0
                        st.session_state.manual_input_info_flag = 0
                        st.session_state.manual_input_hinban_entered = False
                        st.session_state.hinban_select_flag = False
                        st.session_state.tanaban_select_flag  = False
                        st.session_state.tanaban_select_input = False
                        st.session_state.qr_code_tana_info = False
                        st.session_state.tanaban_select_temp_info = ""
                        st.session_state.records  = None
                        st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                        st.session_state.record  = None
                        st.rerun()
                if st.session_state.manual_input_check_flag == 0:
                    left, center, right = st.columns([0.25, 0.5, 0.25])
                    with center:
                        st.title("品番(入力)で検索")
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
                        left, center, right = st.columns([0.25, 0.5, 0.25])
                        with center:
                            if st.button("品番を再入力"):
                                st.session_state.manual_input_hinban_entered = False
                                st.session_state.hinban_select_flag = False
                                st.session_state.tanaban_select_flag  = False
                                st.session_state.records  = None
                                st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                                st.session_state.record  = None
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
                            left, center, right = st.columns([0.25, 0.5, 0.25])
                            with center:
                                if st.button("品番を再選択"):
                                    st.session_state.hinban_select_flag = False
                                    st.session_state.tanaban_select_flag  = False
                                    st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                                    st.session_state.record  = None
                                    st.rerun()
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
                                listCount = len(zkTana_list)
                                # listCount = len(zkHin_list)
                                zkHin_Search = st.session_state.hinban_select_value
                                if listCount > 1:
                                    for index, item in enumerate(zkTana_list):
                                        # st.write(f"for文で検索した棚番: '{item}'") 
                                        # st.write(f"検索させる棚番: '{tanaban_select}'")
                                        zkIko = zkIko_list[index].split(",")
                                        zkHin = zkHin_list[index].split(",")
                                        zkKan = zkKan_list[index].split(",")
                                        zkSu = zkSu_list[index].split(",")
                                        if zkHin_Search in zkHin:
                                            for index_2, item_2 in enumerate(zkHin):
                                                if item_2 == zkHin_Search:
                                                    st.session_state.df_search_result.loc[len(st.session_state.df_search_result)] = [item, zkIko[index_2], zkHin[index_2], zkKan[index_2], zkSu[index_2]]
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
                                    st.write("棚番が１データしか存在しません。至急、システム担当者に連絡してください！")
                                    st.stop()
                                    # st.session_state.df_search_result.loc[len(st.session_state.df_search_result)] = [zkTana_list[0], zkIko[0], zkHin[0], zkKan[0], zkSu[0]]
                            else:
                                st.write("'item_id'　が存在しません。至急、システム担当者に連絡してください！")
                                st.stop()
                            # tanban_list = ["---"] + sorted(st.session_state.df_search_result.iloc[:, 0].dropna().unique())
                            tanban_list = ["---"] + st.session_state.df_search_result.iloc[:, 0].dropna().tolist()
                            selected_tanaban = ""
                            selected_tanaban = st.selectbox("棚番を選択してください　(クリックするとリストが開きます)", tanban_list, key="selected_tanaban_key")
                            # selected_tanaban = st.selectbox("棚番を選択してください　(クリックするとリストが開きます)", st.session_state.df_search_result["棚番"])
                            st.session_state.tanaban_select_value = selected_tanaban
                            if st.session_state.tanaban_select_value != "" and st.session_state.tanaban_select_value != "---":
                                left, center, right = st.columns([0.25, 0.5, 0.25])
                                with center:
                                    if st.button("棚番を再選択"):
                                        st.session_state.tanaban_select_flag  = False
                                        st.session_state.tanaban_select_value = ""
                                        st.rerun()
                                st.write(f"選択された棚番： {st.session_state.tanaban_select_value}")
                                image_viewer(st.session_state.tanaban_select_value)
                                st.stop()
                            _= '''
                            if not st.session_state.tanaban_select_flag:
                                selected_tanaban = ""
                                selected_tanaban = st.selectbox("棚番を選択してください　(クリックするとリストが開きます)", tanban_list, key="selected_tanaban_key")
                                # selected_tanaban = st.selectbox("棚番を選択してください　(クリックするとリストが開きます)", st.session_state.df_search_result["棚番"])
                                st.session_state.tanaban_select_value = selected_tanaban
                                if st.session_state.tanaban_select_value != "" and st.session_state.tanaban_select_value != "---":
                                    st.session_state.tanaban_select_flag = True
                                    st.write(f"{st.session_state.tanaban_select_value}  ←描画直前の棚番")
                                    st.rerun()  # 再描画して次のステップへ
                                else:
                                    st.write(f"{st.session_state.tanaban_select_value}  ←現在の棚番")
                            else:
                                if st.button("棚番を再選択"):
                                    st.session_state.tanaban_select_flag  = False
                                    st.session_state.tanaban_select_value = ""
                                    st.rerun()
                                st.write(f"選択された棚番： {st.session_state.tanaban_select_value}")
                                # image_viewer(st.session_state.tanaban_select_value)
                                st.stop()
                            '''
                elif st.session_state.manual_input_check_flag == 1:
                    left, center, right = st.columns([0.25, 0.5, 0.25])
                    with center:
                        st.title("棚番で検索")
                    if not st.session_state.tanaban_select_input:
                        left, right = st.columns(2)
                        with left:
                            button_qr_tana = st.button("QRコード(棚番)")
                            tool_tips("(棚番をQRコードで検索)")
                        with right:
                            button_manual_tana = st.button("手動入力(棚番)")
                            tool_tips("(棚番を手動選択で検索)")
                        if button_qr_tana or button_manual_tana: 
                            if button_qr_tana:
                                st.session_state.manual_input_info_flag = 0
                            else:
                                st.session_state.manual_input_info_flag = 1
                            # st.session_state.manual_input_check = True
                            # st.session_state.manual_input_check_select = False
                            st.session_state.tanaban_select_input = True
                            st.rerun()
                    else:
                        left, center, right = st.columns([0.25, 0.5, 0.25])
                        with center:
                            if st.button("棚番入力を再選択"):
                                st.session_state.tanaban_select_input = False
                                st.session_state.qr_code_tana_info = False
                                st.session_state.tanaban_select_temp_info = ""
                                st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                                st.session_state.record_2  = None
                                st.rerun()
                        if not st.session_state.qr_code_tana_info:
                            tanaban_select_info = ""
                            if st.session_state.manual_input_info_flag == 0:
                                st.write("棚番のQRコードをスキャンしてください:")
                                qr_code_tana_info = qrcode_scanner(key='qrcode_scanner_tana_info')  
                                if qr_code_tana_info:  
                                    # st.write(qr_code_tana_info) 
                                    tanaban_select_info = qr_code_tana_info.strip()
                            else:
                                zkTanalistSplit = zkTanalist.split(",")
                                tanaban_select_info = st.selectbox(
                                    "棚番号を選んでください", zkTanalistSplit, key="tanaban_select_info"
                                )
                            st.session_state.tanaban_select_temp_info = tanaban_select_info
                            if st.session_state.tanaban_select_temp_info != "" and st.session_state.tanaban_select_temp_info != "---":
                                st.session_state.show_camera = False
                                st.session_state.qr_code_tana_info = True
                                # st.session_state.qr_code = ""
                                # st.session_state.production_order = ""
                                # st.session_state.production_order_flag = False
                                st.rerun()  # 再描画して次のステップへ
                        else:
                            left, center, right = st.columns([0.25, 0.5, 0.25])
                            with center:
                                if st.button("棚番を再選択(参照)"):
                                    st.session_state.qr_code_tana_info = False
                                    st.session_state.tanaban_select_temp_info = ""
                                    st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                                    st.session_state.record_2  = None
                                    st.rerun()
                            st.write(f"選択された棚番： {st.session_state.tanaban_select_temp_info}　にある品番一覧")
                            st.session_state.df_search_result = pd.DataFrame(columns=["棚番", "移行票番号", "品番", "完了工程", "数量"])
                            listCount = 0
                            listCount2 = 0
                            zkTana = ""
                            zkIko = ""
                            zkHin = ""
                            zkKan = ""
                            zkSu = ""
                            zkHistory = ""
                            record_2 = data_catch(st.session_state.sf, item_id)
                            if record_2:
                                # zkHistory = record_2["zkHistory__c"]  # zk履歴
                                zkTana_list = record_2["zkTanaban__c"].splitlines()  # 改行区切り　UM「新規 工程手配明細マスタ レポート」で見易くする為
                                zkIko_list = record_2["zkIkohyoNo__c"].splitlines() 
                                zkHin_list = record_2["zkHinban__c"].splitlines() 
                                zkKan_list = record_2["zkKanryoKoutei__c"].splitlines() 
                                zkSu_list = record_2["zkSuryo__c"].splitlines() 
                                listCount = len(zkTana_list)
                                # listCount = len(zkHin_list)
                                zkTana_Search = st.session_state.tanaban_select_temp_info
                                if listCount > 1:
                                    for index, item in enumerate(zkTana_list):
                                        zkIko = zkIko_list[index].split(",")
                                        zkHin = zkHin_list[index].split(",")
                                        zkKan = zkKan_list[index].split(",")
                                        zkSu = zkSu_list[index].split(",")
                                        listCount2 = len(zkIko)
                                        if item == zkTana_Search:
                                            if listCount2 > 1:
                                                for index_2, item_2 in enumerate(zkIko):
                                                    st.session_state.df_search_result.loc[len(st.session_state.df_search_result)] = [item, zkIko[index_2], zkHin[index_2], zkKan[index_2], zkSu[index_2]]
                                            else:
                                                st.session_state.df_search_result.loc[len(st.session_state.df_search_result)] = [item, zkIko[0], zkHin[0], zkKan[0], zkSu[0]]
                                    # st.write(st.session_state.df_search_result)
                                    st.dataframe(st.session_state.df_search_result)
                                    # edited_df = st.data_editor(
                                    #     st.session_state.df_search_result,
                                    #    num_rows="dynamic",
                                    #     use_container_width=True,
                                    #     key="editable_table"
                                    # )
                                else:
                                    st.write("棚番が１データしか存在しません。至急、システム担当者に連絡してください！")
                                    st.stop()
                            else:
                                st.write("'item_id'　が存在しません。至急、システム担当者に連絡してください！")
                                st.stop()
                            
                            # st.write(f"選択された棚番： {st.session_state.tanaban_select_temp_info}")
                            image_viewer(st.session_state.tanaban_select_temp_info)
                            st.stop()
                _= '''
                else:
                    st.title("移行票番号で検索")
                    st.stop()
                    if not st.session_state.production_order_flag:
                        st.write(f"#### 現在選択されている棚番 : {st.session_state.tanaban_select_temp}")
                        if st.session_state.manual_input_flag == 0:
                            qr_code_kari = ""
                            if st.button("移行票番号(製造オーダー)を再選択", key="camera_rerun"):
                                st.session_state.show_camera = True
                                st.session_state.qr_code = ""
                                st.session_state.production_order = None
                                st.session_state.production_order_flag = False
                                st.rerun()
                            if qr_code_kari == "":
                                st.session_state.show_camera = True
                                st.write("移行票番号(製造オーダー)のQRコードをスキャンしてください:")
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
                            
           
                        # st.write(f"#### 現在選択されている棚番 : {st.session_state.tanaban_select_temp}")
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
                '''
        else:  # st.session_state.manual_input_flag が 0 or 1 の場合
            # st.write(st.session_state.qr_code_tana)
            # st.session_state.manual_input_flag = 1
            if not st.session_state.qr_code_tana:
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
                
                if tanaban_select != "" and tanaban_select != "---":
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
                left, center, right = st.columns([0.25, 0.5, 0.25])
                with center:
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
                    st.write(f"#### 現在選択されている棚番 :   {st.session_state.tanaban_select_temp}")  
                    if st.session_state.manual_input_flag == 0:
                        qr_code_kari = ""
                        left, center, right = st.columns([0.25, 0.5, 0.25])
                        with center:
                            if st.button("移行票番号(製造オーダー)を再選択", key="camera_rerun"):
                                st.session_state.show_camera = True
                                st.session_state.qr_code = ""
                                st.session_state.production_order = None
                                st.session_state.production_order_flag = False
                                st.rerun()
                        if qr_code_kari == "":
                            st.session_state.show_camera = True
                            st.write("移行票番号(製造オーダー)のQRコードをスキャンしてください:")
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
                        
                    # st.write(f"#### 現在選択されている棚番 :   {st.session_state.tanaban_select_temp}")                   
                    button_key = "check_ok"
                    # st.session_state[button_key] = False
                    if st.session_state.production_order != "" and button_key not in st.session_state:
                    # if st.session_state.production_order != "" and st.session_state[button_key] == False:
                        # if st.button("棚番と移行票番号確認"):
                        @st.dialog("棚番と移行票番号確認")
                        def dialog_button(button_key):
                            global message_text
                            # global button_key
                            message_text = f"""
                            #### 現在選択されている棚番 : {st.session_state.tanaban_select_temp}
                            #### 移行票番号(製造オーダー)は、
                            ## 「 {st.session_state.production_order} 」
                            #### でよろしいですか？
                            """
                            result_flag = approve_button(message_text, button_key)
                        dialog_button(button_key)

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
                    left, center, right = st.columns([0.25, 0.5, 0.25])
                    with center:
                        if st.button("移行票番号を再入力"):
                            st.session_state.df = None
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
                            
                        st.session_state.list_flag = 0 # 0:移行票番号が無い  1:有る
                        record = data_catch(st.session_state.sf, item_id)
                        if record:
                            zkTana_list = ""
                            listCount = 0
                            listCount2 = 0
                            zkIko_kari = ""
                            zkTana_list = record["zkTanaban__c"].splitlines()  # 改行区切り　UM「新規 工程手配明細マスタ レポート」で見易くする為
                            listCount = len(zkTana_list)
                            if listCount > 2:
                                for index, item in enumerate(zkTana_list):
                                    if item == tanaban_select:
                                        zkIko_list = record["zkIkohyoNo__c"].splitlines()
                                        zkIko_kari = zkIko_list[index].split(",")
                                        listCount2 = len(zkIko_kari)
                                        if listCount2 > 1:
                                            for index, item in enumerate(zkIko_kari):
                                                if item == st.session_state.production_order:
                                                    st.session_state.list_flag = 1 # 移行票番号が有る
                                                    break
                                        else:
                                            print("-  のみ")
                        st.session_state.record = ""
                        st.session_state.add_del_flag = 0  # 0:追加 1:削除 9:取消     
                        left, center, right = st.columns(3)
                        with left:
                            if st.session_state.list_flag == 0: # 移行票番号が無い場合のみ
                                submit_button_add = st.form_submit_button("追加")
                        with center:
                            if st.session_state.list_flag == 1: # 移行票番号が有る場合のみ
                                submit_button_del = st.form_submit_button("削除")
                        with right:
                            submit_button_cancel = st.form_submit_button("取消")
                        submit_button_flag = 0
                        if st.session_state.list_flag == 0:
                            if submit_button_add:
                                st.session_state.add_del_flag = 0
                                submit_button_flag = 1
                        if st.session_state.list_flag == 1:
                            if submit_button_del:
                                st.session_state.add_del_flag = 1
                                submit_button_flag = 1
                        if submit_button_cancel:
                            st.session_state.add_del_flag = 9
                            submit_button_flag = 1
                        if submit_button_flag == 1:
                        # if submit_button_add or submit_button_del or submit_button_cancel: 
                        #     if submit_button_add:
                        #         st.session_state.add_del_flag = 0
                        #     elif submit_button_del:
                        #         st.session_state.add_del_flag = 1
                        #     elif submit_button_cancel:
                        #         st.session_state.add_del_flag = 9
                            if st.session_state.add_del_flag == 9:
                                st.session_state.qr_code_tana = False
                                st.session_state.tanaban_select_temp = ""
                                if st.session_state.manual_input_flag == 0:
                                    st.session_state.show_camera = True  # 必要に応じて棚番再選択
                                st.session_state.qr_code = ""
                                st.session_state.production_order = ""
                                st.session_state.production_order_flag = False
                                st.session_state.add_del_flag = 0
                                st.session_state.df = None
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
                            zkTana_list = ""
                            zkTana = ""
                            zkIko = ""
                            zkHin = ""
                            zkKan = ""
                            zkSu = ""
                            # zkMap = ""
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
                                    # list_flag = 0 # 移行票番号が無い
                                    # zkIko_kari = zkIko[listNumber].split(",")
                                    # listCount2 = len(zkIko_kari)
                                    # if listCount2 > 1:
                                    #     for index, item in enumerate(zkIko_kari):
                                    #         if item == st.session_state.production_order:
                                    #             list_flag = 1 # 移行票番号が有る
                                    #             break
                                    # else:
                                    #     print("-  のみ")
                                    # if list_flag == 1 and st.session_state.add_del_flag == 0:
                                    #     st.write(f"❌06 **移行票番号は登録済みですので、追加できません。　取消ボタンを押して下さい。**")
                                    #     st.stop()  # 以降の処理を止める
                                    # if list_flag == 0 and st.session_state.add_del_flag == 1:
                                    #     st.write(f"❌07 **移行票番号の登録はありませんので、削除できません。　取消ボタンを押して下さい。**")
                                    #     st.stop()  # 以降の処理を止める
                                    if listCountEtc != listCount: # 棚番が追加されない限り、あり得ない分岐(初期設定時のみ使用)
                                        st.write(f"❌08 **移行票Noリスト '{zkIko}' の追加は許可されてません。**")
                                        st.stop()  # 以降の処理を止める
                                        zkKari = "-"
                                        separator = "\n"
                                        zkIko = f"{separator.join([zkKari] * listCount)}"
                                        zkHin = zkIko
                                        zkKan = zkIko
                                        zkSu = zkIko
                                        # zkMap = zkIko
                                        zkHistory = zkIko
                                    else:
                                        zkOrder = st.session_state.production_order
                                        zkHistory_value = f"{tanaban_select},{zkOrder},{hinban},{process_order_name},{quantity},{datetime_str},{owner_value}"
                                        if st.session_state.add_del_flag == 0: # 追加の場合
                                            zkIko = list_update_zkKari(record, zkIko, "zkIkohyoNo__c", listNumber, zkOrder, 1)   # zk移行票No
                                            zkHin = list_update_zkKari(record, zkHin, "zkHinban__c", listNumber, hinban, 0)   # zk品番
                                            zkKan = list_update_zkKari(record, zkKan, "zkKanryoKoutei__c", listNumber, process_order_name, 0)   # zk完了工程
                                            zkSu = list_update_zkKari(record, zkSu, "zkSuryo__c", listNumber, f"{quantity}", 0)   # zk数量
                                            # zkMap = list_update_zkKari(zkMap, "zkMap__c", listNumber, "-", -1)   # zkマップ座標
                                            zkHistory_value = f"{zkHistory_value},add"
                                        elif st.session_state.add_del_flag == 1: # 削除の場合
                                            zkIko = list_update_zkKari(record, zkIko, "zkIkohyoNo__c", listNumber, zkOrder, 3)   # zk移行票No
                                            zkHin = list_update_zkKari(record, zkHin, "zkHinban__c", listNumber, hinban, 2)   # zk品番
                                            zkKan = list_update_zkKari(record, zkKan, "zkKanryoKoutei__c", listNumber, process_order_name, 2)   # zk完了工程
                                            zkSu = list_update_zkKari(record, zkSu, "zkSuryo__c", listNumber, f"{quantity}", 2)   # zk数量
                                            # zkMap = list_update_zkKari(zkMap, "zkMap__c", listNumber, "-", 2)   # zkマップ座標
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
                                st.write(f"❌09 **作業者コード '{owner}' が未入力です。**")
                                st.stop()  # 以降の処理を止める
                            st.session_state.zkScroll_flag = 0
                            if item_id:
                                update_tanaban(st.session_state.sf, item_id, tanaban_select, zkIko, zkHin, zkKan, zkSu, zkHistory, zkOrder)
                                button_key = "check_ok_2"
                                if st.session_state.zkScroll_flag == 1 and button_key not in st.session_state:
                                    @st.dialog("処理結果通知")
                                    def dialog_button_2(button_key):
                                        global dialog_ok_flag
                                        # st.session_state["dialog_closed"] = True
                                        st.write(st.session_state.result_text)
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
                                            st.session_state.zkScroll_flag = 0
                                            st.session_state["dialog_closed"] = True
                                            st.session_state.df = None
                                            st.rerun()
                                    dialog_button_2(button_key)


return_main = "⏎ ☆メイン画面☆　へ戻る"
return_1 = "⏎ 1.製造関連メニュー　へ戻る"
return_11 = "⏎ 11.製品メニュー　へ戻る"
return_116 = "⏎ 116.在庫管理メニュー　へ戻る"
return_1161 = "⏎ 1161.在庫置き場メニュー　へ戻る"

def show_main_screen():
    left, center, right = st.columns([0.2, 0.6, 0.2])
    with center:
        st.image("aitech_logo_E1.png", use_container_width=True)
    #     st.image("aitech_logo_D.png", use_container_width=True)
    # with right:
    #     st.write('(仮)')
    
    # display_container('yellow', '☆メイン画面☆')
    # display_container('yellow', '☆在庫置場管理システム☆')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    styled_input_text()
    zaiko_place()
    # button_set('button0', '0.ショートカット', 'other0')
    # button_set('button31', '1161.在庫置場', 'other1161')
    # st.write('  ')
    # st.write('  ')
    # button_set('button1', '1.製造関連', 'other1')
    # button_set('button2', '2.ＩＳＯ関連', 'other2')
    # button_set('button3', '3.労務関連', 'other3')
    _= '''
    button11 = st.button('11.製品', on_click=set_screen, args=('other11',))
    button12 = st.button('12.金型', on_click=set_screen, args=('other12',))
    button13 = st.button('13.治工具', on_click=set_screen, args=('other13',))
    button14 = st.button('14.検具', on_click=set_screen, args=('other14',))
    button15 = st.button('15.設備', on_click=set_screen, args=('other15',))
    button16 = st.button('16.備品', on_click=set_screen, args=('other16',))
    button21 = st.button('21.品質・環境マニュアル', on_click=set_screen, args=('other21',))
    button22 = st.button('22.規定', on_click=set_screen, args=('other22',))
    button23 = st.button('23.要領', on_click=set_screen, args=('other23',))
    button24 = st.button('24.外部文書', on_click=set_screen, args=('other24',))
    button25 = st.button('25.マネジメントレビュー', on_click=set_screen, args=('other25',))
    button26 = st.button('26.内部監査', on_click=set_screen, args=('other26',))
    button27 = st.button('27.外部監査', on_click=set_screen, args=('other27',))
    button111 = st.button('111.図面', on_click=set_screen, args=('other111',))
    button112 = st.button('112.検査基準書', on_click=set_screen, args=('other112',))
    button113 = st.button('113.ＱＣ表', on_click=set_screen, args=('other113',))
    button114 = st.button('114.作業標準', on_click=set_screen, args=('other114',))
    button115 = st.button('115.検査表', on_click=set_screen, args=('other115',))
    button116 = st.button('116.在庫管理', on_click=set_screen, args=('other116',))
    '''
    display_footer()

def show_other0_screen():
    display_container('yellow', '0.ショートカット')
    # display_header('blue', '0.ショートカット')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    display_line()
    button_set('button31', '1161.在庫置場', 'other1161')
    # button_set('btn11611', '11611.在庫置場 追加', 'other11611')
    # button_set('btn11612', '11612.在庫置場 削除', 'other11612')
    # button_set('btn11613', '11613.在庫置場 参照', 'other11613')
    display_footer()


def show_other1_screen():
    _= '''
    with st_fixed_container(mode="fixed", position="bottom", border=True):
        st.markdown(
        "<p style='text-align:left;'> \
        <span style='font-size: 20px;font-weight:bold;margin-bottom: 0px;line-height: 0.5'>1.製造関連メニュー</span> \
        </p>"
        , unsafe_allow_html=True
        )
    with st_fixed_container(mode="fixed", position="bottom", transparent=True):
        _, right = st.columns([0.5, 0.5])
        with right:
            with st_opaque_container(border=True):
                button_make("⏎☆メイン画面☆　へ戻る",'main')
                # btn0 = st.button("⏎☆メイン画面☆　へ戻る", use_container_width=True, on_click=set_screen, args=('main',))
                # btn1 = st.button("⏎1.製造関連メニュー　へ戻る", use_container_width=True, on_click=set_screen, args=('other1',))
    '''
    _= '''
    with st_fixed_container(mode="fixed", position="top", transparent=True):
        st.markdown(
            "<p style='text-align:center;'> \
            <span style='font-size: 40px;font-weight:bold;color:aqua;margin-bottom: 0px;line-height: 0.5'>1.製造関連メニュー</span> \
            </p>"
            , unsafe_allow_html=True
        )
    '''
    display_container('blue', '1.製造関連メニュー')
    # display_header('blue', '1.製造関連メニュー')
    # st.markdown(write_css1, unsafe_allow_html=True)
    # st.markdown('<p class="big-font">1.製造関連メニュー</p>', unsafe_allow_html=True)
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    # btn0 = st.button("⏎ ☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    display_line()
    # st.write('---')
    button_set('btn11', '11.製品', 'other11')
    button_set('btn12', '12.金型', 'other12')
    button_set('btn13', '13.治工具', 'other13')
    button_set('btn14', '14.検具', 'other14')
    button_set('btn15', '15.設備', 'other15')
    button_set('btn16', '16.備品', 'other16')
    # button11 = st.button('11.製品', on_click=set_screen, args=('other11',))
    # button12 = st.button('12.金型', on_click=set_screen, args=('other12',))
    # button13 = st.button('13.治工具', on_click=set_screen, args=('other13',))
    # button14 = st.button('14.検具', on_click=set_screen, args=('other14',))
    # button15 = st.button('15.設備', on_click=set_screen, args=('other15',))
    # button16 = st.button('16.備品', on_click=set_screen, args=('other16',))
    display_footer()

def show_other2_screen():
    display_container('blue', '2.ＩＳＯメニュー')
    # display_header('blue', '2.ＩＳＯメニュー')
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    display_line()
    button_set('btn21', '21.品質・環境マニュアル', 'other21')
    button_set('btn22', '22.規定', 'other22')
    button_set('btn23', '23.要領', 'other23')
    button_set('btn24', '24.外部文書', 'other24')
    button_set('btn25', '25.マネジメントレビュー', 'other25')
    button_set('btn26', '26.内部監査', 'other26')
    button_set('btn27', '27.外部監査', 'other27')
    # button21 = st.button('21.品質・環境マニュアル', on_click=set_screen, args=('other21',))
    # button22 = st.button('22.規定', on_click=set_screen, args=('other22',))
    # button23 = st.button('23.要領', on_click=set_screen, args=('other23',))
    # button24 = st.button('24.外部文書', on_click=set_screen, args=('other24',))
    # button25 = st.button('25.マネジメントレビュー', on_click=set_screen, args=('other25',))
    # button26 = st.button('26.内部監査', on_click=set_screen, args=('other26',))
    # button27 = st.button('27.外部監査', on_click=set_screen, args=('other27',))
    display_footer()

def show_other3_screen():
    display_container('blue', '3.労務メニュー')
    # display_header('blue', '3.労務メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    display_line()
    button_set('btn31', '31.就業規則', 'other31')
    button_set('btn32', '32.規定', 'other32')
    button_set('btn33', '33.外部監査', 'other33')
    display_footer()

def show_other11_screen():
    display_container('blue', '11.製品メニュー')
    # display_header('blue', '11.製品メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    display_line()
    button_set('btn111', '111.図面', 'other111')
    button_set('btn112', '112.検査基準書', 'other112')
    button_set('btn113', '113.ＱＣ表', 'other113')
    button_set('btn114', '114.作業標準', 'other114')
    button_set('btn115', '115.検査表', 'other115')
    button_set('btn116', '116.在庫管理', 'other116')
    display_footer()

def show_other116_screen():
    display_container('blue', '116.在庫管理メニュー')
    # display_header('blue', '116.在庫管理メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    display_line()
    button_set('btn1161', '1161.在庫置場', 'other1161')
    button_set('btn1162', '1162.棚卸', 'other1162')
    display_footer()

def show_other1161_screen():
    display_container('blue', '1161.在庫置場メニュー')
    # display_header('blue', '1161.在庫置場メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    button_set('btn116', return_116, 'other116')
    display_line()
    zaiko_place()
    # button_set('btn11611', '11611.在庫置場 追加', 'other11611')
    # button_set('btn11612', '11612.在庫置場 削除', 'other11612')
    # button_set('btn11613', '11613.在庫置場 参照', 'other11613')
    display_footer()

def show_other11613_screen():
    display_container('blue', '11613.在庫置場 参照メニュー')
    # display_header('blue', '11613.在庫置場 参照メニュー')
    _= '''
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='font-size: 40px;font-weight:bold;color:blue;margin-bottom: 0px;line-height: 0.5'>11613.在庫置場 参照メニュー</span> \
        </p>",
        unsafe_allow_html=True
    )
    '''
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    button_set('btn116', return_116, 'other116')
    button_set('btn1161', return_1161, 'other1161')
    display_line()
    st.write("こ")
    st.write("こ")
    st.write("に")
    st.write("参")
    st.write("照")
    st.write("メ")
    st.write("ニ")
    st.write("ュ")
    st.write("ー")
    st.write("を")
    st.write("表")
    st.write("示")
    st.write("予")
    st.write("定")
    # button_set('btn11611', '11611.在庫置場 参照', 'other11611')
    # button_set('btn11612', '11612.在庫置場 追加', 'other11612')
    display_footer()
    
def show_other11611_screen():
    display_container('blue', '11611.在庫置場 追加・削除メニュー')
    # display_header('blue', '11612.在庫置場 追加メニュー')
    # with st_fixed_container(mode="fixed", position="top", transparent=True):
    _= '''
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='font-size: 40px;font-weight:bold;color:blue;margin-bottom: 0px;line-height: 0.5'>11612.在庫置場 追加メニュー</span> \
        </p>",
        unsafe_allow_html=True
    )
    '''
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    button_set('btn116', return_116, 'other116')
    button_set('btn1161', return_1161, 'other1161')
    display_line()
    # st.markdown(selectbox_style, unsafe_allow_html=True)
    # okiba = st.selectbox("在庫置場を選択", ["E40", "E41", "E42", "E43", "E44", "E45"], placeholder="E40")
    left, center, right = st.columns([0.25, 0.5, 0.25])
    with center:
        # okiba = st.selectbox("在庫置場を選択", ["E40", "E41", "E42", "E43", "E44", "E45"], placeholder="F56")
        # seiban = st.text_input("移行票No", placeholder="PP-012345")
        # hinban = st.text_input("品番 (品名)", placeholder="123-45H67-890 (PPPPP,QQQQQ RRRRR)")
        # koutei = st.text_input("完了済工程", placeholder="20 GSN")
        # suryo = st.text_input("数量", placeholder="3000")
        left, center, right = st.columns([0.3, 0,3, 0.4])
        with left:
            button_set('btn116121', '追加', 'other11621')
        with center:
            button_set('btn116122', '削除', 'other11622')
        with right:
            button_set('btn116123', '取消', 'other11623')
    # button_set('btn11611', '11611.在庫置場 参照', 'other11611')
    # button_set('btn11612', '11612.在庫置場 追加', 'other11612')
    display_footer()
    
# 不明な画面の場合の処理
def unknown_screen():
    display_container('red', '現在、準備中です。')
    # display_header('red', '現在、メンテナンス中です。')
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    # btnKari = button_set('btn99999', '前の画面に戻る', 'other99999')
    if len(st.session_state['history']) > 1:
        button_set('btn99999', '前の画面に戻る', 'other99999')
        # if st.button("前の画面に戻る", on_click=go_back, key="back_button"):
        # if btnKari:
        #     pass
    display_footer()



if "sf" not in st.session_state:
    try:
        st.session_state.sf = authenticate_salesforce()
        # st.success("Salesforceに正常に接続しました！")
    except Exception as e:
        st.error(f"認証エラー: {e}")
        st.stop()

if "user_code_entered" not in st.session_state:
    st.session_state.user_code_entered = False
    st.session_state.user_code = ""
    
if not st.session_state.user_code_entered:
    styled_input_text()
    st.title("作業者コード入力")
    st.session_state['owner'] = st.text_input("作業者コード(社員番号)を入力してください (3～4桁、例: 999)",
                                              max_chars=4,
                                              key="owner_input")
    
    if st.session_state['owner']:  # 入力があれば保存して完了フラグを立てる
        st.session_state.user_code = st.session_state['owner']
        st.session_state.user_code_entered = True
        st.rerun()  # 再描画して次のステップへ
else:
    # _= '''
    # 画面の切り替え
    # メイン画面
    if st.session_state['current_screen'] == 'main':
        show_main_screen()
    # ショートカットボタンメニュー
    elif st.session_state['current_screen'] == 'other0':
        show_other0_screen()
    # 製造関連メニュー
    elif st.session_state['current_screen'] == 'other1':
        show_other1_screen()
    # ISO関連メニュー
    elif st.session_state['current_screen'] == 'other2':
        show_other2_screen()
    # 労務関連メニュー
    elif st.session_state['current_screen'] == 'other3':
        show_other3_screen()
    # 製品メニュー
    elif st.session_state['current_screen'] == 'other11':
        show_other11_screen()
    # 金型メニュー
    elif st.session_state['current_screen'] == 'other12':
        # show_other12_screen()
        unknown_screen()
    # 治工具メニュー
    elif st.session_state['current_screen'] == 'other13':
        # show_other13_screen()
        unknown_screen()
    # 検具メニュー
    elif st.session_state['current_screen'] == 'other14':
        # show_other14_screen()
        unknown_screen()
    # 設備メニュー
    elif st.session_state['current_screen'] == 'other15':
        # show_other15_screen()
        unknown_screen()
    # 備品メニュー
    elif st.session_state['current_screen'] == 'other16':
        # show_other16_screen()
        unknown_screen()
    # 在庫管理メニュー
    elif st.session_state['current_screen'] == 'other116':
        show_other116_screen()
    # 在庫置場メニュー
    elif st.session_state['current_screen'] == 'other1161':
        show_other1161_screen()
    # 在庫置場 参照メニュー
    # elif st.session_state['current_screen'] == 'other11611':
    #    show_other11611_screen()
    # 在庫置場 追加削除メニュー
    # elif st.session_state['current_screen'] == 'other11612':
    #     show_other11612_screen()
    else:
        unknown_screen()
    # '''
