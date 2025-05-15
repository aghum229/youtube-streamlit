import streamlit as st

# 共通CSS
common_css = """
<style>
.big-font { font-size: 40px !important; font-weight: bold; text-align: center; }
.vertical-button-container {
    display: flex;
    justify-content: center;
    width: 100%; /* 親要素の幅いっぱいに広げる */
}
.vertical-button-container > div.stButton > button { /* button 要素をターゲット */
    font-size: 30px !important;
    font-weight: bold;
    color: #000;
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background-color: #0FF !important; /* 背景色を #0FF に設定 */
    width: 200px !important; /* ボタンの固定幅 */
    max-width: 200px !important; /* 最大幅も固定 */
    margin-bottom: 10px; /* ボタン間の余白 */
    padding: 10px 20px;
}
.footer-text-center { font-size: 14px !important; text-align: center; }
.footer-text-left { font-size: 10px !important; text-align: left; }
</style>
"""
st.markdown(common_css, unsafe_allow_html=True)

# 画面の状態を管理
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

def display_header(title):
    st.markdown(f'<p class="big-font">{title}</p>', unsafe_allow_html=True)
    st.write('---')

def display_footer():
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    center_column.markdown('<p class="footer-text-center">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    right_column.markdown('<p class="footer-text-left">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def vertical_button(label, target_screen):
    st.button(label, on_click=set_screen, args=(target_screen,), key=label, use_container_width=False)

# 画面定義
screens = {
    'main': lambda: (
        display_header("メイン画面"),
        st.markdown('<div class="vertical-button-container">', unsafe_allow_html=True),
        vertical_button("製造関連", 'other1'),
        vertical_button("ＩＳＯ関連", 'other2'),
        vertical_button("労務関連", 'other3'),
        st.markdown('</div>', unsafe_allow_html=True),
        display_footer()
    ),
    'other1': lambda: (
        display_header("製造関連メニュー"),
        st.markdown('<div class="vertical-button-container">', unsafe_allow_html=True),
        vertical_button("⏎メイン画面へ戻る", 'main'),
        vertical_button('製品', 'other4'),
        vertical_button('金型', 'other5'),
        vertical_button('治工具', 'other6'),
        vertical_button('検具', 'other7'),
        vertical_button('設備', 'other8'),
        vertical_button('備品', 'other9'),
        st.markdown('</div>', unsafe_allow_html=True),
        display_footer()
    ),
    'other2': lambda: (
        display_header("ＩＳＯメニュー"),
        st.markdown('<div class="vertical-button-container">', unsafe_allow_html=True),
        vertical_button("⏎メイン画面へ戻る", 'main'),
        vertical_button('品質・環境マニュアル', 'other10'),
        vertical_button('規定', 'other11'),
        vertical_button('要領', 'other12'),
        vertical_button('外部文書', 'other13'),
        vertical_button('マネジメントレビュー', 'other14'),
        vertical_button('内部監査', 'other15'),
        vertical_button('外部監査', 'other16'),
        st.markdown('</div>', unsafe_allow_html=True),
        display_footer()
    ),
    'other3': lambda: (
        display_header("労務メニュー"),
        st.markdown('<div class="vertical-button-container">', unsafe_allow_html=True),
        vertical_button("⏎メイン画面へ戻る", 'main'),
        vertical_button('就業規則', 'other17'),
        vertical_button('規定', 'other18'),
        vertical_button('外部監査', 'other19'),
        st.markdown('</div>', unsafe_allow_html=True),
        display_footer()
    ),
    'other4': lambda: (
        display_header("製品メニュー"),
        st.markdown('<div class="vertical-button-container">', unsafe_allow_html=True),
        vertical_button("⏎メイン画面へ戻る", 'main'),
        vertical_button("⏎製造関連メニューへ戻る", 'other1'),
        vertical_button('図面', 'other20'),
        vertical_button('検査基準書', 'other21'),
        vertical_button('ＱＣ表', 'other22'),
        vertical_button('作業標準', 'other23'),
        vertical_button('検査表', 'other24'),
        vertical_button('在庫管理', 'other25'),
        st.markdown('</div>', unsafe_allow_html=True),
        display_footer()
    ),
    'other25': lambda: (
        display_header("在庫管理メニュー"),
        st.markdown('<div class="vertical-button-container">', unsafe_allow_html=True),
        vertical_button("⏎メイン画面へ戻る", 'main'),
        vertical_button("⏎製造関連メニューへ戻る", 'other1'),
        vertical_button("⏎製品メニューへ戻る", 'other4'),
        vertical_button('在庫管理', 'other26'),
        vertical_button('棚卸', 'other27'),
        st.markdown('</div>', unsafe_allow_html=True),
        display_footer()
    ),
    # 他の画面定義も同様に追加
}

# 不明な画面の場合の処理
def unknown_screen():
    st.error("不明な画面です")
    if len(st.session_state['history']) > 1:
        if st.button("前の画面に戻る", on_click=go_back, key="back_button"):
            pass

# 画面の切り替え
if st.session_state['current_screen'] in screens:
    screens[st.session_state['current_screen']]()
else:
    unknown_screen()
