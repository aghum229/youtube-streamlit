import streamlit as st

# 共通CSS
common_css = """
<style>
.big-font { font-size: 40px !important; font-weight: bold; text-align: center; }
.center-button-container { display: flex; justify-content: center; width: 100%; }
.center-button-container > button {
    font-size: 50px !important; font-weight: bold; color: #000;
    border-radius: 5px; background: #0FF; width: 200px; max-width: 200px; height: 50px;
}
.footer-text-center { font-size: 14px !important; text-align: center; }
.footer-text-left { font-size: 10px !important; text-align: left; }
.horizontal-buttons { display: flex; gap: 10px; } /* 横並びボタン用 */
</style>
"""
st.markdown(common_css, unsafe_allow_html=True)

# 画面の状態を管理
if 'current_screen' not in st.session_state:
    st.session_state['current_screen'] = 'main'

def set_screen(screen_name):
    st.session_state['current_screen'] = screen_name

def display_header(title):
    st.markdown(f'<p class="big-font">{title}</p>', unsafe_allow_html=True)
    st.write('---')

def display_footer():
    left_column, center_column, right_column = st.columns(3)
    center_column.markdown('<p class="footer-text-center">〇〇〇〇〇株式会社</p>', unsafe_allow_html=True)
    right_column.markdown('<p class="footer-text-left">ver.XX.XXX.XXX</p>', unsafe_allow_html=True)

def centered_button(label, target_screen):
    col = st.columns(3)[1] # 中央の列を使用
    if col.button(label):
        set_screen(target_screen)

def horizontal_buttons(labels_targets):
    cols = st.columns(len(labels_targets))
    for i, (label, target) in enumerate(labels_targets):
        if cols[i].button(label):
            set_screen(target)

# 画面定義
screens = {
    'main': lambda: (
        display_header("メイン画面"),
        centered_button("製造関連", 'other1'),
        centered_button("ＩＳＯ関連", 'other2'),
        centered_button("労務関連", 'other3'),
        display_footer()
    ),
    'other1': lambda: (
        display_header("製造関連メニュー"),
        centered_button("⏎メイン画面へ戻る", 'main'),
        horizontal_buttons([
            ('製品', 'other4'), ('金型', 'other5'), ('治工具', 'other6'),
            ('検具', 'other7'), ('設備', 'other8'), ('備品', 'other9')
        ]),
        display_footer()
    ),
    'other2': lambda: (
        display_header("ＩＳＯメニュー"),
        centered_button("⏎メイン画面へ戻る", 'main'),
        horizontal_buttons([
            ('品質・環境マニュアル', 'other10'), ('規定', 'other11'), ('要領', 'other12'),
            ('外部文書', 'other13'), ('マネジメントレビュー', 'other14'), ('内部監査', 'other15'),
            ('外部監査', 'other16')
        ]),
        display_footer()
    ),
    'other3': lambda: (
        display_header("労務メニュー"),
        centered_button("⏎メイン画面へ戻る", 'main'),
        horizontal_buttons([
            ('就業規則', 'other17'), ('規定', 'other18'), ('外部監査', 'other19')
        ]),
        display_footer()
    ),
    'other4': lambda: (
        display_header("製品メニュー"),
        centered_button("⏎メイン画面へ戻る", 'main'),
        centered_button("⏎製造関連メニューへ戻る", 'other1'),
        horizontal_buttons([
            ('図面', 'other20'), ('検査基準書', 'other21'), ('ＱＣ表', 'other22'),
            ('作業標準', 'other23'), ('検査表', 'other24'), ('在庫管理', 'other25')
        ]),
        display_footer()
    ),
    'other25': lambda: (
        display_header("在庫管理メニュー"),
        centered_button("⏎メイン画面へ戻る", 'main'),
        centered_button("⏎製造関連メニューへ戻る", 'other1'),
        centered_button("⏎製品メニューへ戻る", 'other4'),
        horizontal_buttons([
            ('在庫管理', 'other26'), ('棚卸', 'other27')
        ]),
        display_footer()
    ),
    # 他の画面定義も同様に追加
}

# 画面の切り替え
if st.session_state['current_screen'] in screens:
    screens[st.session_state['current_screen']]()
else:
    st.error("不明な画面です")


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
