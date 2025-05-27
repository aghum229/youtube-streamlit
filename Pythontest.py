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
    width: 250px; /* ボタンの横幅を固定値に設定 */
    max-width: 250px; /* 必要に応じて最大幅も設定 */
    height: 50px;
    margin-bottom: 0px;
    line-height: 1.0;
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
        <span style='margin-bottom: 0px;line-height: 1.0'>------------------------------------------------------------</span> \
        </p>"
        , unsafe_allow_html=True
    )

def display_mainheader():
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='font-size: 40px;font-weight:bold;color:yellow;margin-bottom: 0px;line-height: 1.0'>☆メイン画面☆</span> \
        </p>"
        , unsafe_allow_html=True
    )
    display_line()

def display_footer():
    display_line()
    # st.write('---')
    # left_column, center_column, right_column = st.columns(3)
    _= '''
    st.markdown(
        "<p style='text-align:center;'> \
        これは<span style='color:red;'>赤い</span>文字と、 \
        <span style='font-weight:bold;'>太字の</span>文字を含む一行です。 \
        </p>"
        , unsafe_allow_html=True
    )
    st.markdown(
    "これは文章です <img src='画像へのURL' width='50' height='50'> そしてこれは続きの文章です。"
    , unsafe_allow_html=True
    )
    '''
    st.markdown(
        "<p style='text-align:center;'> \
        <span style='font-size: 14px;'>〇〇〇〇〇株式会社&nbsp;&nbsp;&nbsp;</span> \
        <span style='font-size: 10px;'>ver.XX.XXX.XXX</span> \
        </p>"
        , unsafe_allow_html=True
    )
    # st.markdown(write_css2, unsafe_allow_html=True)
    # st.markdown('<p class="right-font">'<span style="font-size: 14px;">〇〇〇〇〇株式会社 </span>''<span style="font-size: 10px;">ver.XX.XXX.XXX</span>'</p>', unsafe_allow_html=True)
    # st.markdown('<p class="right-font">'<span class="right-font">〇〇〇〇〇株式会社 </span>''<span class="small-font">ver.XX.XXX.XXX</span>'</p>', unsafe_allow_html=True)
    # center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    # st.markdown(write_css3, unsafe_allow_html=True)
    # right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_main_screen():
    # st.markdown(write_css1, unsafe_allow_html=True)
    # st.markdown('<p class="main-font">☆メイン画面☆</p>', unsafe_allow_html=True)
    display_mainheader()
    # st.write('---')
    # st.markdown(button_style, unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<p class="main-font"> \
        button1 = st.button("1.製造関連", on_click=set_screen, args=('other1',))
        button2 = st.button("2.ＩＳＯ関連", on_click=set_screen, args=('other2',))
        button3 = st.button("3.労務関連", on_click=set_screen, args=('other3',)) \
        </p>', unsafe_allow_html=True)
    display_footer()

def show_other1_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">1.製造関連メニュー</p>', unsafe_allow_html=True)
    display_line()
    # st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    display_line()
    # st.write('---')
    button4 = st.button('11.製品', on_click=set_screen, args=('other11',))
    button5 = st.button('12.金型', on_click=set_screen, args=('other12',))
    button6 = st.button('13.治工具', on_click=set_screen, args=('other13',))
    button7 = st.button('14.検具', on_click=set_screen, args=('other14',))
    button8 = st.button('15.設備', on_click=set_screen, args=('other15',))
    button9 = st.button('16.備品', on_click=set_screen, args=('other16',))
    display_footer()

def show_other2_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">2.ＩＳＯメニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    st.write('---')
    button10 = st.button('21.品質・環境マニュアル', on_click=set_screen, args=('other21',))
    button11 = st.button('22.規定', on_click=set_screen, args=('other22',))
    button12 = st.button('23.要領', on_click=set_screen, args=('other23',))
    button13 = st.button('24.外部文書', on_click=set_screen, args=('other24',))
    button14 = st.button('25.マネジメントレビュー', on_click=set_screen, args=('other25',))
    button15 = st.button('26.内部監査', on_click=set_screen, args=('other26',))
    button16 = st.button('27.外部監査', on_click=set_screen, args=('other27',))
    display_footer()

def show_other3_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">3.労務メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    st.write('---')
    button17 = st.button('31.就業規則', on_click=set_screen, args=('other31',))
    button18 = st.button('32.規定', on_click=set_screen, args=('other32',))
    button19 = st.button('33.外部監査', on_click=set_screen, args=('other33',))
    display_footer()

def show_other11_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">11.製品メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    btn2 = st.button("⏎1.製造関連メニュー　へ戻る", on_click=set_screen, args=('other1',))
    st.write('---')
    button20 = st.button('111.図面', on_click=set_screen, args=('other111',))
    button21 = st.button('112.検査基準書', on_click=set_screen, args=('other112',))
    button22 = st.button('113.ＱＣ表', on_click=set_screen, args=('other113',))
    button23 = st.button('114.作業標準', on_click=set_screen, args=('other114',))
    button24 = st.button('115.検査表', on_click=set_screen, args=('other115',))
    button25 = st.button('116.在庫管理', on_click=set_screen, args=('other116',))
    display_footer()

def show_other116_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">116.在庫管理メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("⏎☆メイン画面☆　へ戻る", on_click=set_screen, args=('main',))
    btn2 = st.button("⏎1.製造関連メニュー　へ戻る", on_click=set_screen, args=('other1',))
    btn3 = st.button("⏎11.製品メニュー　へ戻る", on_click=set_screen, args=('other11',))
    st.write('---')
    button26 = st.button('1161.在庫置き場', on_click=set_screen, args=('other1161',))
    button27 = st.button('1162.棚卸', on_click=set_screen, args=('other1162',))
    display_footer()

_= '''
# 画面定義
screens = {
    'main',
    'other1',
    'other2',
    'other3',
    'other4',
    'other25'
    # 他の画面定義も同様に追加
}
'''

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

_= '''
# 画面の切り替え
if st.session_state['current_screen'] in screens:
    screens[st.session_state['current_screen']]()
else:
    unknown_screen()
'''

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
