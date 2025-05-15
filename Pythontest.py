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

st.markdown(write_css1, unsafe_allow_html=True)
st.markdown('<p class="big-font">管理システム</p>', unsafe_allow_html=True)

st.write('---')

st.markdown(button_style, unsafe_allow_html=True)
button1 = st.button('製造関連')
button2 = st.button('ISO関連')
button3 = st.button('労務関連')

st.write('---')

left_column, center_column, right_column = st.columns(3)
st.markdown(write_css2, unsafe_allow_html=True)
center_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
st.markdown(write_css3, unsafe_allow_html=True)
right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

# 画面の状態を管理する変数（初期状態はメイン画面）
if 'current_screen' not in st.session_state:
    st.session_state['current_screen'] = 'main'

def show_main_screen():
    # st.title("メイン画面")
    if button1:
        st.session_state['current_screen'] = 'other1'

def show_other1_screen():
    st.title("別画面")
    st.write("こちらは別の画面の内容です。")
    if st.button("メイン画面へ戻る"):
        st.session_state['current_screen'] = 'main'

# 画面の切り替え
if st.session_state['current_screen'] == 'main':
    show_main_screen()
elif st.session_state['current_screen'] == 'other1':
    show_other1_screen()

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
