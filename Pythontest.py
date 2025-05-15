import streamlit as st
import time

# st.title('文書・記録管理システム  \n' + 'メインメニュー')
# st.title('文書・記録')
# st.title('管理システム')

button_css = f"""
<style>
  div.stButton > button:first-child  {{
    # position: absolute;
    # left: 50%;
    # transform: translateX(-50%);
    transform: translateX(100%);
    # display: flex;
    # display: block;
    # text-decoration: none;
    # display: inline-block;
    # margin:auto
    # text-align:center
    # position: relative;
    max-width: 100%;
    width: 200px;
    height: 40px;
    font-size: 20px;
    # font-size: 10px;
    font-weight  : bold                ;/* 文字：太字                   */
    # font-weight  : 1000                ;/* 文字：太字                   */
    color        : #000                ;
    # border       :  1px solid #000     ;/* 枠線：ピンク色で5ピクセルの実線 */
    border-radius: 5px 5px 5px 5px     ;/* 枠線：半径10ピクセルの角丸     */
    background   : #0FF                ;/* 背景色：aqua            */
    # align-items: center;
    # justify-content: center;
  }}
</style>
"""
st.markdown(button_css, unsafe_allow_html=True)

# st.set_page_config(layout="wide")
# st.markdown("""
write_css1 = """
<style>
.big-font {
    font-size    :40px !important;
    font-weight    :bold;
    text-align     :center;
}
</style>
"""

# _= '''
write_css2 = """
<style>
.right-font {
    font-size    :16px !important;
    text-align     :right;
}
</style>
"""
# '''

# _= '''
write_css3 = """
<style>
.small-font {
    font-size    :10px !important;
    text-align     :left;
}
</style>
"""
# '''

st.markdown(write_css1, unsafe_allow_html=True)
# """, unsafe_allow_html=True)
st.markdown('<p class="big-font">管理システム</p>', unsafe_allow_html=True)
# st.write('管理システム')

# st.title('文書・記録管理システム  \n' + 'メインメニュー')
# st.title('文書・記録')
# st.write('<span style="color:red;background:pink">管理システム</span>',
#              unsafe_allow_html=True)
# st.title('# 管理システム')
st.write('## 管理システム')

# st.write('<span style="color:red;background:pink">該当するデータがありません・・・・</span>',
#               unsafe_allow_html=True)

button1 = st.button('製造関連')

button2 = st.button('ＩＳＯ関連')

button3 = st.button('労務関連')

left_column, right_column = st.columns(2)
st.markdown(write_css2, unsafe_allow_html=True)
left_column.markdown('<p class="right-font">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
st.markdown(write_css3, unsafe_allow_html=True)
right_column.markdown('<p class="small-font">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)
# left_column.write('##### 〇〇〇〇〇株式会社')
# right_column.write('ver.XX.XXX.XXX')
# left_column.write('<span style="color:black;background:white,font-size=10px,text-align:right,float:right">〇〇〇〇〇株式会社</span>',
#               unsafe_allow_html=True)
# right_column.write('<span style="color:black;background:white,font-size=6px">ver.XX.XXX.XXX</span>',
#               unsafe_allow_html=True)

# st.write('〇〇〇〇〇株式会社  ver.XX.XXX.XXX')
# left_column, right_column = st.columns(2)
# left_column.write('〇〇〇〇〇株式会社')
# right_column.write('ver.XX.XXX.XXX')
# st.write('<span style="color:black;background:white">〇〇〇〇〇株式会社　　ver.XX.XXX.XXX</span>',
#               unsafe_allow_html=True)

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
