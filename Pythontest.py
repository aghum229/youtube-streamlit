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

def show_main_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">メイン画面</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    button1 = st.button('製造関連')
    button2 = st.button('ＩＳＯ関連')
    button3 = st.button('労務関連')
    if button1:
        st.session_state['current_screen'] = 'other1'
    elif button2:
        st.session_state['current_screen'] = 'other2'
    elif button3:
        st.session_state['current_screen'] = 'other3'
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
    btn1 = st.button("メイン画面へ戻る")
    button4 = st.button('製品')
    button5 = st.button('金型')
    button6 = st.button('治工具')
    button7 = st.button('検具')
    button8 = st.button('設備')
    button9 = st.button('備品')
    if button4:
        st.session_state['current_screen'] = 'other4'
    elif button5:
        st.session_state['current_screen'] = 'other5'
    elif button6:
        st.session_state['current_screen'] = 'other6'
    elif button7:
        st.session_state['current_screen'] = 'other7'
    elif button8:
        st.session_state['current_screen'] = 'other8'
    elif button9:
        st.session_state['current_screen'] = 'other9'
    elif btn1:
        st.session_state['current_screen'] = 'main'
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other2_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">ISO関連メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("メイン画面へ戻る")
    button10 = st.button('品質・環境マニュアル')
    button11 = st.button('規定')
    button12 = st.button('要領')
    button13 = st.button('外部文書')
    button14 = st.button('マネジメントレビュー')
    button15 = st.button('内部監査')
    button16 = st.button('外部監査')
    if button10:
        st.session_state['current_screen'] = 'other10'
    elif button11:
        st.session_state['current_screen'] = 'other11'
    elif button12:
        st.session_state['current_screen'] = 'other12'
    elif button13:
        st.session_state['current_screen'] = 'other13'
    elif button14:
        st.session_state['current_screen'] = 'other14'
    elif button15:
        st.session_state['current_screen'] = 'other15'
    elif button16:
        st.session_state['current_screen'] = 'other16'
    elif btn1:
        st.session_state['current_screen'] = 'main'
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other3_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">労務関連メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("メイン画面へ戻る")
    button17 = st.button('就業規則')
    button18 = st.button('規定')
    button19 = st.button('外部監査')
    if button17:
        st.session_state['current_screen'] = 'other17'
    elif button18:
        st.session_state['current_screen'] = 'other18'
    elif button19:
        st.session_state['current_screen'] = 'other19'
    elif btn1:
        st.session_state['current_screen'] = 'main'
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
    btn1 = st.button("メイン画面へ戻る")
    btn2 = st.button("製造関連メニュー")
    button17 = st.button('図面')
    button18 = st.button('検査基準書')
    button19 = st.button('ＱＣ表')
    button20 = st.button('作業標準')
    button21 = st.button('検査表')
    button22 = st.button('在庫管理')
    if button17:
        st.session_state['current_screen'] = 'other17'
    elif button18:
        st.session_state['current_screen'] = 'other18'
    elif button19:
        st.session_state['current_screen'] = 'other19'
    elif button20:
        st.session_state['current_screen'] = 'other20'
    elif button21:
        st.session_state['current_screen'] = 'other21'
    elif button22:
        st.session_state['current_screen'] = 'other22'
    elif btn2:
        st.session_state['current_screen'] = 'other1'
    elif btn1:
        st.session_state['current_screen'] = 'main'
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def show_other22_screen():
    st.markdown(write_css1, unsafe_allow_html=True)
    st.markdown('<p class="big-font">在庫管理メニュー</p>', unsafe_allow_html=True)
    st.write('---')
    st.markdown(button_style, unsafe_allow_html=True)
    btn1 = st.button("メイン画面へ戻る")
    btn2 = st.button("製造関連メニュー")
    btn3 = st.button("製品メニュー")
    button23 = st.button('在庫管理')
    button24 = st.button('棚卸')
    if button23:
        st.session_state['current_screen'] = 'other23'
    elif button24:
        st.session_state['current_screen'] = 'other24'
    elif btn3:
        st.session_state['current_screen'] = 'other4'
    elif btn2:
        st.session_state['current_screen'] = 'other1'
    elif btn1:
        st.session_state['current_screen'] = 'main'
    st.write('---')
    left_column, center_column, right_column = st.columns(3)
    st.markdown(write_css2, unsafe_allow_html=True)
    center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    st.markdown(write_css3, unsafe_allow_html=True)
    right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

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
    show_other5_screen()
# 治工具メニュー
elif st.session_state['current_screen'] == 'other6':
    show_other6_screen()
# 検具メニュー
elif st.session_state['current_screen'] == 'other7':
    show_other7_screen()
# 設備メニュー
elif st.session_state['current_screen'] == 'other8':
    show_other8_screen()
# 備品メニュー
elif st.session_state['current_screen'] == 'other9':
    show_other9_screen()
# 在庫管理メニュー
elif st.session_state['current_screen'] == 'other22':
    show_other22_screen()


# st.write('Progress Bar')
# 'Start!!'

# latest_iteration = st.empty()
# bar = st.progress(0)
# for i in range(100):
# 	latest_iteration.text(f'Iteration{i+1}')
# 	bar.progress(i+1)
# 	time.sleep(0.05)

# 'Done!!!'

# left_column, right_column = st.columns(2)
# button = left_column.button('右カラムに文字を表示')
# if button:
# 	right_column.write('右カラムです。')

# expander = st.expander('問い合わせ')
# expander.write('問い合わせ内容を書く')
