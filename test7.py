import streamlit as st
import easyocr
import numpy as np
from PIL import Image

st.title("🔍 easyocrでバーコード文字認識")

uploaded_file = st.file_uploader("バーコード画像をアップロード", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    reader = easyocr.Reader(['en'])  # 日本語が必要なら ['ja', 'en']
    result = reader.readtext(np.array(image))

    if result:
        st.subheader("📋 認識されたテキスト:")
        for (bbox, text, prob) in result:
            st.write(f"- {text}（信頼度: {prob:.2f}）")
    else:
        st.warning("文字が認識できませんでした。画像の解像度や明るさを確認してください。")


