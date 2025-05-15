import streamlit as st
import time


# スタイル定義（ボタンの文字サイズと中央配置）
button_style = """
<style>
div.stButton {
    display: flex;
    justify-content: center;
}
div.stButton > button {
    font-size: 24px !important; /* 文字サイズを指定 */
    padding: 10px 20px; /* 余白を設定 */
}
</style>
"""
st.markdown(button_style, unsafe_allow_html=True)

# 画面の状態を管理する変数（初期状態はメイン画面）
if 'current_screen' not in st.session_state:
    st.session_state['current_screen'] = 'main'

def show_main_screen():
    st.title("メイン画面")
    if st.button("別画面へ"):
        st.session_state['current_screen'] = 'other'

def show_other_screen():
    st.title("別画面")
    st.write("こちらは別の画面の内容です。")
    if st.button("メイン画面へ戻る"):
        st.session_state['current_screen'] = 'main'

# 画面の切り替え
if st.session_state['current_screen'] == 'main':
    show_main_screen()
elif st.session_state['current_screen'] == 'other':
    show_other_screen()

