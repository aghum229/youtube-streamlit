import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import cv2

st.title("📷 バーコード文字部分のOCR抽出")

# Webカメラから画像取得
camera_image = st.camera_input("バーコードを撮影してください")

if camera_image:
    # PIL → NumPy → OpenCV形式に変換
    img = Image.open(camera_image)
    img_np = np.array(img)
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # easyocrで文字認識
    reader = easyocr.Reader(['en'])  # Code39は英数字なので英語でOK
    results = reader.readtext(img_cv)

    # 結果表示
    if results:
        st.subheader("🔍 認識された文字:")
        for (bbox, text, prob) in results:
            st.write(f"- {text}（信頼度: {prob:.2f}）")
    else:
        st.warning("文字が認識できませんでした。画像の明るさや角度を調整して再撮影してください。")


