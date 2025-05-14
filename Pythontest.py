import streamlit as st
import time

button_css = f"""
<style>
  div.stButton > button:first-child  {{
    font-weight  : bold                ;/* 文字：太字                   */
    color        : #000                ;
    border       :  1px solid #000     ;/* 枠線：ピンク色で5ピクセルの実線 */
    border-radius: 10px 10px 10px 10px ;/* 枠線：半径10ピクセルの角丸     */
    background   : #0FF               ;/* 背景色：aqua            */
  }}
</style>
"""
st.markdown(button_css, unsafe_allow_html=True)

# st.title('文書・記録管理システム  \n' + 'メインメニュー')
st.title('文書・記録')
st.title('管理システム')

# st.write('<span style="color:red;background:pink">該当するデータがありません・・・・</span>',
#               unsafe_allow_html=True)

button = st.button('製造関連')

button = st.button('ＩＳＯ関連')

button = st.button('労務関連')

left_column, right_column = st.columns(2)
left_column.write('〇〇〇〇〇株式会社')
right_column.write('ver.XX.XXX.XXX')
st.write('<span style="color:black;background:white">〇〇〇〇〇株式会社　　ver.XX.XXX.XXX</span>',
              unsafe_allow_html=True)

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
