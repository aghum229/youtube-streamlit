import streamlit as st
# import numpy as np
# import pandas as pd
# from PIL import Image
import time

st.title('Streamlit 超入門')

# st.write('DataFrame')

'''
df = pd.DataFrame({
	'1列目': [1, 2, 3, 4],
	'2列目': [10, 20, 30, 40]
})

#st.write(df) #引数が無い

#動的な表
st.dataframe(df.style.highlight_max(axis=0), width=300, height=300)

#静的な表
st.table(df.style.highlight_max(axis=0))
'''

"""
# 章
## 節
### 項
~~~python
import streamlit as st
import numpy as np
import pandas as pd
~~~
"""

# df2 = pd.DataFrame(
# 	np.random.rand(20, 3),
# 	columns=['a', 'b', 'c']
# )
# df2

#st.line_chart(df2)
#st.area_chart(df2)
#st.bar_chart(df2)

# df3 = pd.DataFrame(
# 	np.random.rand(100, 2)/[50, 50] + [35.69, 139.70],
# 	columns=['lat', 'lon']
# )
# df3

#st.map(df3)

#st.write('Display Image')

# if st.checkbox('Show Image'):
# 	img = Image.open(r'D:\Python Folder\test.jpg')
# 	st.image(img, caption='test', use_column_width=True)

st.write('Interactive Widgets')

# text = st.text_input('あなたの趣味を教えて下さい。')

# 'あなたの趣味は、　', text, '　です。'

# condition = st.slider('あなたの今の調子は？', 0, 100, 50)

# 'あなたのコンディションは、　', condition, '　です。'

# text = st.sidebar.text_input('あなたの趣味を教えて下さい。')
# condition = st.sidebar.slider('あなたの今の調子は？', 0, 100, 50)

# 'あなたの趣味は、　', text, '　です。'
# 'あなたのコンディションは、　', condition, '　です。'

left_column, right_column = st.columns(2)
button = left_column.button('右カラムに文字を表示')
if button:
	right_column.write('右カラムです。')

expander = st.expander('問い合わせ')
expander.write('問い合わせ内容を書く')

st.write('Progress Bar')
'Start!!'

latest_iteration = st.empty()
bar = st.progress(0)
for i in range(100):
	latest_iteration.text(f'Iteration{i+1}')
	bar.progress(i+1)
	time.sleep(0.1)

'Done!!!'