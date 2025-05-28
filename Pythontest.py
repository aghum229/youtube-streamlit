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
    font-size: 50px !important; /* 文字サイズを指定 */
    font-weight  : bold ;
    color        : #000;
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background   : #0FF                ;/* 背景色：aqua            */
    width: 250px; /* ボタンの横幅を固定値に設定 */
    max-width: 250px; /* 必要に応じて最大幅も設定 */
    height: 50px;
}
</style>
"""

button_css = f"""
<style>
  div.stButton > button:first-child  {{
    font-size: 18px !important; /* 文字サイズを指定 */
    font-weight  : bold ;
    color        : #000;
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background   : #FF0                ;/* 背景色：yellow            */
    width: 150px; /* ボタンの横幅を固定値に設定 */
    max-width: 150px; /* 必要に応じて最大幅も設定 */
    height: 25px;
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

def show_main_screen():
    with st_fixed_container(mode="fixed", position="bottom", border=True):
        st.markdown(
        "<p style='text-align:left;'> \
        <span style='font-size: 20px;font-weight:bold;color:yellow'>☆メイン画面☆</span> \
        </p>"
        , unsafe_allow_html=True
        )
    with st_fixed_container(mode="fixed", position="bottom", transparent=True):
        _, right = st.columns([0.5, 0.5])
        with right:
            with st_opaque_container(border=True):
                st.markdown(button_style, unsafe_allow_html=True)
                btn0 = st.button("⏎☆メイン画面☆　へ戻る", use_container_width=True, on_click=set_screen, args=('main',))
                btn1 = st.button("⏎1.製造関連メニュー　へ戻る", use_container_width=True, on_click=set_screen, args=('other1',))
    display_mainheader()
    # display_line()
    st.markdown(button_style, unsafe_allow_html=True)
    button1 = st.button("1.製造関連", on_click=set_screen, args=('other1',))
    button2 = st.button("2.ＩＳＯ関連", on_click=set_screen, args=('other2',))
    button3 = st.button("3.労務関連", on_click=set_screen, args=('other3',))
    display_footer()

def show_other1_screen():
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
                btn0 = st.markdown("""
                    <style> \
                    .custom-button { \
                       background-color: #FF0; \
                       color: black; \
                       font-size: 12px !important; \
                       text-align     :center; \
                       font-weight  : bold ; \
                       border-radius: 5px 5px 5px 5px ; \
                       width: 200px; \
                       max-width: 200px; \
                       height: 30px; \
                       on_click: set_screen, args=('main',); \
                    } \
                    .custom-button:hover { \
                       opacity: 0.8; \
                    } \
                    </style> \
                    <button class="custom-button">⏎☆メイン画面☆　へ戻る</button>
                """, unsafe_allow_html=True)
                btn0(, on_click=set_screen, args=('main',))
                # btn0 = st.button("⏎☆メイン画面☆　へ戻る", use_container_width=True, on_click=set_screen, args=('main',))
                # btn1 = st.button("⏎1.製造関連メニュー　へ戻る", use_container_width=True, on_click=set_screen, args=('other1',))
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">1.製造関連メニュー</p>', unsafe_allow_html=True)
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    # btn0 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    # display_line()
    # st.write('---')
    button11 = st.button('11.製品', on_click=set_screen, args=('other11',))
    button12 = st.button('12.金型', on_click=set_screen, args=('other12',))
    button13 = st.button('13.治工具', on_click=set_screen, args=('other13',))
    button14 = st.button('14.検具', on_click=set_screen, args=('other14',))
    button15 = st.button('15.設備', on_click=set_screen, args=('other15',))
    button16 = st.button('16.備品', on_click=set_screen, args=('other16',))
    display_footer()

def show_other2_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">2.ＩＳＯメニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn0 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    st.write('---')
    button21 = st.button('21.品質・環境マニュアル', on_click=set_screen, args=('other21',))
    button22 = st.button('22.規定', on_click=set_screen, args=('other22',))
    button23 = st.button('23.要領', on_click=set_screen, args=('other23',))
    button24 = st.button('24.外部文書', on_click=set_screen, args=('other24',))
    button25 = st.button('25.マネジメントレビュー', on_click=set_screen, args=('other25',))
    button26 = st.button('26.内部監査', on_click=set_screen, args=('other26',))
    button27 = st.button('27.外部監査', on_click=set_screen, args=('other27',))
    display_footer()

def show_other3_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">3.労務メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn0 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    st.write('---')
    button31 = st.button('31.就業規則', on_click=set_screen, args=('other31',))
    button32 = st.button('32.規定', on_click=set_screen, args=('other32',))
    button33 = st.button('33.外部監査', on_click=set_screen, args=('other33',))
    display_footer()

def show_other11_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">11.製品メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn0 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    btn1 = st.button("⏎1.製造関連メニュー　へ戻る", on_click=set_screen, args=('other1',))
    st.write('---')
    button111 = st.button('111.図面', on_click=set_screen, args=('other111',))
    button112 = st.button('112.検査基準書', on_click=set_screen, args=('other112',))
    button113 = st.button('113.ＱＣ表', on_click=set_screen, args=('other113',))
    button114 = st.button('114.作業標準', on_click=set_screen, args=('other114',))
    button115 = st.button('115.検査表', on_click=set_screen, args=('other115',))
    button116 = st.button('116.在庫管理', on_click=set_screen, args=('other116',))
    display_footer()

def show_other116_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">116.在庫管理メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn0 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    btn1 = st.button("⏎1.製造関連メニュー　へ戻る", on_click=set_screen, args=('other1',))
    btn11 = st.button("⏎11.製品メニュー　へ戻る", on_click=set_screen, args=('other11',))
    st.write('---')
    button1161 = st.button('1161.在庫置き場', on_click=set_screen, args=('other1161',))
    button1162 = st.button('1162.棚卸', on_click=set_screen, args=('other1162',))
    display_footer()

# 不明な画面の場合の処理
def unknown_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">現在、メンテナンス中です。</p>', unsafe_allow_html=True)
    # st.error("不明な画面です")
    st.write('---')
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
else:
    unknown_screen()
# '''
