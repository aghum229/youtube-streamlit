import streamlit as st
import time

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
    width: 200px; /* ボタンの横幅を固定値に設定 */
    max-width: 200px; /* 必要に応じて最大幅も設定 */
    height: 50px;
}
</style>
"""
# st.markdown(button_style, unsafe_allow_html=True)

write_css1 = """
<style>
.big-font {
    font-size      :40px !important;
    font-weight    :bold;
    text-align     :center;
}
</style>
"""

# _= '''
write_css2 = """
<style>
.right-font {
    font-size      :14px !important;
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

def show_main_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">メイン画面</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    button1 = st.button("製造関連", on_click=set_screen, args=('other1',))
    button2 = st.button("ＩＳＯ関連", on_click=set_screen, args=('other2',))
    button3 = st.button("労務関連", on_click=set_screen, args=('other3',))
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other1_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">製造関連メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎メイン画面へ戻る", on_click=set_screen, args=('main',))
    st.write('---')
    button4 = st.button('製品', on_click=set_screen, args=('other4',))
    button5 = st.button('金型', on_click=set_screen, args=('other5',))
    button6 = st.button('治工具', on_click=set_screen, args=('other6',))
    button7 = st.button('検具', on_click=set_screen, args=('other7',))
    button8 = st.button('設備', on_click=set_screen, args=('other8',))
    button9 = st.button('備品', on_click=set_screen, args=('other9',))
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other2_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">ＩＳＯメニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎メイン画面へ戻る", on_click=set_screen, args=('main',))
    st.write('---')
    button10 = st.button('品質・環境マニュアル', on_click=set_screen, args=('other10',))
    button11 = st.button('規定', on_click=set_screen, args=('other11',))
    button12 = st.button('要領', on_click=set_screen, args=('other12',))
    button13 = st.button('外部文書', on_click=set_screen, args=('other13',))
    button14 = st.button('マネジメントレビュー', on_click=set_screen, args=('other14',))
    button15 = st.button('内部監査', on_click=set_screen, args=('other15',))
    button16 = st.button('外部監査', on_click=set_screen, args=('other16',))
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other3_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">労務メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎メイン画面へ戻る", on_click=set_screen, args=('main',))
    st.write('---')
    button17 = st.button('就業規則', on_click=set_screen, args=('other17',))
    button18 = st.button('規定', on_click=set_screen, args=('other18',))
    button19 = st.button('外部監査', on_click=set_screen, args=('other19',))
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other4_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">製品メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎メイン画面へ戻る", on_click=set_screen, args=('main',))
    btn2 = st.button("⏎製造関連メニューへ戻る", on_click=set_screen, args=('other1',))
    st.write('---')
    button20 = st.button('図面', on_click=set_screen, args=('other20',))
    button21 = st.button('検査基準書', on_click=set_screen, args=('other21',))
    button22 = st.button('ＱＣ表', on_click=set_screen, args=('other22',))
    button23 = st.button('作業標準', on_click=set_screen, args=('other23',))
    button24 = st.button('検査表', on_click=set_screen, args=('other24',))
    button25 = st.button('在庫管理', on_click=set_screen, args=('other25',))
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other25_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">在庫管理メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎メイン画面へ戻る", on_click=set_screen, args=('main',))
    btn2 = st.button("⏎製造関連メニューへ戻る", on_click=set_screen, args=('other1',))
    btn3 = st.button("⏎製品メニューへ戻る", on_click=set_screen, args=('other4',))
    st.write('---')
    button26 = st.button('在庫管理', on_click=set_screen, args=('other26',))
    button27 = st.button('棚卸', on_click=set_screen, args=('other27',))
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

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

_= '''
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
elif st.session_state['current_screen'] == 'other4':
    show_other4_screen()
# 金型メニュー
elif st.session_state['current_screen'] == 'other5':
    # show_other5_screen()
    unknown_screen()
# 治工具メニュー
elif st.session_state['current_screen'] == 'other6':
    # show_other6_screen()
    unknown_screen()
# 検具メニュー
elif st.session_state['current_screen'] == 'other7':
    # show_other7_screen()
    unknown_screen()
# 設備メニュー
elif st.session_state['current_screen'] == 'other8':
    # show_other8_screen()
    unknown_screen()
# 備品メニュー
elif st.session_state['current_screen'] == 'other9':
    # show_other9_screen()
    unknown_screen()
# 在庫管理メニュー
elif st.session_state['current_screen'] == 'other25':
    show_other25_screen()
else:
    unknown_screen()
'''
