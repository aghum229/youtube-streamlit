# import streamlit as st
# import time

# 固定コンテナコードの始まり
from typing import Literal

import streamlit as st
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
            return st.container(height=height, border=border)

        return st_opaque_container(height=height, border=border, key=f"opaque_{key}")
# 固定コンテナコードの終わり


button_style = """
<style>
div.stButton {
    display: flex;
    justify-content: center;
    width: 100%; /* 必要に応じて調整：ボタンコンテナの幅 */
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

button_css = f"""
<style>
  div.stButton > button:first-child  {{
    font-size: 10px !important; /* 文字サイズを指定 */
    font-weight  : bold ;
    color        : #000;
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background   : #FF0                ;/* 背景色：yellow            */
    width: 200px; /* ボタンの横幅を固定値に設定 */
    max-width: 200px; /* 必要に応じて最大幅も設定 */
    height: 20px;
  }}
</style>
"""
button_style2 = """
<style>
div.stButton {
    display: flex;
    justify-content: center;
    width: 100%; /* 必要に応じて調整：ボタンコンテナの幅 */
}
div.stButton > button {
    font-size: 30px !important; /* 文字サイズを指定 */
    font-weight  : bold ;
    color        : #000;
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background   : #FF0                ;/* 背景色：yellow            */
    width: 150px; /* ボタンの横幅を固定値に設定 */
    max-width: 150px; /* 必要に応じて最大幅も設定 */
    height: 30px;
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

write_css1 = """
<style>
.big-font {
    font-size      :40px !important;
    font-weight    :bold;
    text-align     :center;
    margin-bottom: 0px;
    line-height: 0.5;
}
</style>
"""

# _= '''
write_css2 = """
<style>
.main-font {
    font-size      :40px !important;
    font-weight    :bold;
    color        : #ffff00;
    text-align     :center;
}
</style>
"""
# '''

# _= '''
write_css3 = """
<style>
.small-font {
    font-size      :10px !important;
    text-align     :left;
}
</style>
"""
# '''

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
        <span style='margin-bottom: 0px;line-height: 0.5'>――――――――――――――――――――――――――――――</span> \
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

def display_mainheader():
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='font-size: 40px;font-weight:bold;color:yellow;margin-bottom: 0px;line-height: 0.5'>☆メイン画面☆</span> \
        </p>"
        , unsafe_allow_html=True
    )
    display_line()

def display_footer():
    display_line()
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='font-size: 14px;'>〇〇〇〇〇株式会社&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> \
        <span style='font-size: 10px;'>ver.XX.XXX.XXX</span> \
        </p>"
        , unsafe_allow_html=True
    )

def display_container(color, text):
    with st_fixed_container(mode="fixed", position="top", transparent=True):
        st.markdown(
            f"<p style='text-align:center;'> \
            <span style='font-size: 40px;font-weight:bold;color:{color};margin-bottom: 0px;line-height: 0.5'>{text}</span> \
            </p>",
            unsafe_allow_html=True
        )

def button_set(button_name, button_text, screen_name):
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

return_main = "⏎ ☆メイン画面☆　へ戻る"
return_1 = "⏎ 1.製造関連メニュー　へ戻る"
return_11 = "⏎ 11.製品メニュー　へ戻る"
return_116 = "⏎ 116.在庫管理メニュー　へ戻る"
return_1161 = "⏎ 1161.在庫置き場メニュー　へ戻る"

def show_main_screen():
    _= '''
    with st_fixed_container(mode="fixed", position="bottom", border=True):
        st.markdown(
        "<p style='text-align:left;'> \
        <span style='font-size: 20px;font-weight:bold;color:yellow'>☆メイン画面☆</span> \
        </p>" \
        "<p style='text-align:left;'> \
        <span style='font-size: 20px;font-weight:bold;color:yellow'>☆メイン画面☆</span> \
        </p>"
        , unsafe_allow_html=True
        )
    '''
    _= '''
    with st_fixed_container(mode="fixed", position="top", transparent=True):
        # _, right = st.columns([0.5, 0.5])
        # with right:
        #     with st_opaque_container(border=True):
        # left, right = st.columns([0.4, 0.3, 0.3])
        # with st_opaque_container(border=True):
            st.markdown(
                "<p style='text-align:center;'> \
                <span style='font-size: 40px;font-weight:bold;color:yellow;margin-bottom: 0px;line-height: 0.5'>☆メイン画面☆</span> \
                </p>"
                , unsafe_allow_html=True
            )
            
            
            left, center, right = st.columns([0.3, 0.4, 0.4])
            with left:
                st.markdown(
                "<p style='text-align:right;'> \
                <span style='font-size: 16px;font-weight:bold;color:yellow'>☆メイン画面☆</span> \
                </p>"
                , unsafe_allow_html=True
                )
            with center:
                # st.markdown(button_css, unsafe_allow_html=True)
                btn0 = st.button("⏎ ☆メイン画面☆　へ戻る", use_container_width=True, on_click=set_screen, args=('main',))
            with right:
                # st.markdown(button_css, unsafe_allow_html=True)
                btn1 = st.button("⏎ 1.製造関連メニュー　へ戻る", use_container_width=True, on_click=set_screen, args=('other1',))
            
    '''
    # display_mainheader()
    # st.write('---  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n ---')
    # st.write('---  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n ---')
    # st.write('---  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n  \n ---')
    display_container('yellow', '☆メイン画面☆')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('button1', '1.製造関連', 'other1')
    button_set('button2', '2.ＩＳＯ関連', 'other2')
    button_set('button3', '3.労務関連', 'other3')
    # button1 = st.button("1.製造関連", on_click=set_screen, args=('other1',))
    # button2 = st.button("2.ＩＳＯ関連", on_click=set_screen, args=('other2',))
    # button3 = st.button("3.労務関連", on_click=set_screen, args=('other3',))
    left, center, right = st.columns([0.3, 0.4, 0.3])
    with center:
        st.markdown("""
        <style>
        .centered-selectbox {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        </style>
        """, unsafe_allow_html=True)
        # コンテナで中央配置
        with st.container():
            st.markdown('<div class="centered-selectbox">', unsafe_allow_html=True)
            st.selectbox("選択してください", ["オプション1", "オプション2", "オプション3"])
            st.markdown('</div>', unsafe_allow_html=True)
    # _= '''
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
    # '''
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
    # st.markdown(write_css1, unsafe_allow_html=True)
    # st.markdown('<p class="big-font">1.製造関連メニュー</p>', unsafe_allow_html=True)
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    # btn0 = st.button("⏎ ☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    display_line()
    # st.write('---')
    button_set('button11', '11.製品', 'other11')
    button_set('button12', '12.金型', 'other12')
    button_set('button13', '13.治工具', 'other13')
    button_set('button14', '14.検具', 'other14')
    button_set('button15', '15.設備', 'other15')
    button_set('button16', '16.備品', 'other16')
    # button11 = st.button('11.製品', on_click=set_screen, args=('other11',))
    # button12 = st.button('12.金型', on_click=set_screen, args=('other12',))
    # button13 = st.button('13.治工具', on_click=set_screen, args=('other13',))
    # button14 = st.button('14.検具', on_click=set_screen, args=('other14',))
    # button15 = st.button('15.設備', on_click=set_screen, args=('other15',))
    # button16 = st.button('16.備品', on_click=set_screen, args=('other16',))
    display_footer()

def show_other2_screen():
    display_container('blue', '2.ＩＳＯメニュー')
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    display_line()
    button_set('button21', '21.品質・環境マニュアル', 'other21')
    button_set('button22', '22.規定', 'other22')
    button_set('button23', '23.要領', 'other23')
    button_set('button24', '24.外部文書', 'other24')
    button_set('button25', '25.マネジメントレビュー', 'other25')
    button_set('button26', '26.内部監査', 'other26')
    button_set('button27', '27.外部監査', 'other27')
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
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    display_line()
    button_set('button31', '31.就業規則', 'other31')
    button_set('button32', '32.規定', 'other32')
    button_set('button33', '33.外部監査', 'other33')
    display_footer()

def show_other11_screen():
    display_container('blue', '11.製品メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    display_line()
    button_set('button111', '111.図面', 'other111')
    button_set('button112', '112.検査基準書', 'other112')
    button_set('button113', '113.ＱＣ表', 'other113')
    button_set('button114', '114.作業標準', 'other114')
    button_set('button115', '115.検査表', 'other115')
    button_set('button116', '116.在庫管理', 'other116')
    display_footer()

def show_other116_screen():
    display_container('blue', '116.在庫管理メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    display_line()
    button_set('button1161', '1161.在庫置き場', 'other1161')
    button_set('button1162', '1162.棚卸', 'other1162')
    display_footer()

def show_other1161_screen():
    display_container('blue', '1161.在庫置き場メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    button_set('btn116', return_116, 'other116')
    display_line()
    button_set('button11611', '11611.在庫置き場参照', 'other11611')
    button_set('button11612', '11612.在庫置き場入力', 'other11612')
    display_footer()

def show_other11611_screen():
    display_container('blue', '11611.在庫置き場参照メニュー')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    button_set('btn116', return_116, 'other116')
    button_set('btn1161', return_1161, 'other1161')
    display_line()
    # button_set('button11611', '11611.在庫置き場参照', 'other11611')
    # button_set('button11612', '11612.在庫置き場入力', 'other11612')
    display_footer()
    
def show_other11612_screen():
    display_container('blue', '11612.在庫置き場入力画面')
    display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button_set('btn0', return_main, 'main')
    button_set('btn1', return_1, 'other1')
    button_set('btn11', return_11, 'other11')
    button_set('btn116', return_116, 'other116')
    button_set('btn1161', return_1161, 'other1161')
    display_line()
    # st.markdown(selectbox_style, unsafe_allow_html=True)
    # okiba = st.selectbox("在庫置き場を選択", ["E40", "E41", "E42", "E43", "E44", "E45"])
    left, center, right = st.columns([0.3, 0.4, 0.3])
    with center:
        okiba = st.selectbox("在庫置き場を選択", ["E40", "E41", "E42", "E43", "E44", "E45"])
        seiban = st.text_input("移行票No")
        hinban = st.text_input("品番と品名")
        koutei = st.text_input("完了工程")
        suryo = st.text_input("数量")
    # button_set('button11611', '11611.在庫置き場参照', 'other11611')
    # button_set('button11612', '11612.在庫置き場入力', 'other11612')
    display_footer()
    
# 不明な画面の場合の処理
def unknown_screen():
    display_container('red', '現在、メンテナンス中です。')
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    if len(st.session_state['history']) > 1:
        if st.button("前の画面に戻る", on_click=go_back, key="back_button"):
            pass
    display_footer()

# _= '''
# 画面の切り替え
# メイン画面
if st.session_state['current_screen'] == 'main':
    show_main_screen()
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
# 在庫置き場メニュー
elif st.session_state['current_screen'] == 'other1161':
    show_other1161_screen()
# 在庫置き場参照メニュー
elif st.session_state['current_screen'] == 'other11611':
    show_other11611_screen()
# 在庫置き場入力画面
elif st.session_state['current_screen'] == 'other11612':
    show_other11612_screen()
else:
    unknown_screen()
# '''
