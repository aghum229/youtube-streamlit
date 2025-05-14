import streamlit as st
import time

# サイドバーにテーマの選択オプションを追加
theme = st.sidebar.radio(
    "テーマを選択してください",
    options=["ライトモード", "ダークモード"]
)
 
# 選択されたテーマに基づいてスタイルを適用
if theme == "ライトモード":
    st.markdown(
        """
        <style>
        body {
            background-color: #FFFFFF;
            color: #000000;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        body {
            background-color: #2c3e50;
            color: #ecf0f1;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

st.title('文書・記録管理　メニュー')

st.write('<span style="color:red;background:pink">該当するデータがありません・・・・</span>',
              unsafe_allow_html=True)

button = st.button('製造関連')

button = st.button('ＩＳＯ関連')

button = st.button('労務関連')

left_column, right_column = st.columns(2)
left_column.write('〇〇〇〇〇株式会社')
right_column.write('ver.XX.XXX.XXX<')
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
