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

    # 画像を2倍に拡大
    enlarged = cv2.resize(img_cv, None, fx=5.0, fy=5.0, interpolation=cv2.INTER_LINEAR)

    # 表示用にRGBへ戻す
    enlarged_rgb = cv2.cvtColor(enlarged, cv2.COLOR_BGR2RGB)
    # st.image(enlarged_rgb, caption="2倍に拡大された画像", use_column_width=True)


    # easyocrで文字認識
    reader = easyocr.Reader(['en'])  # Code39は英数字なので英語でOK
    # results = reader.readtext(img_cv)
    results = reader.readtext(enlarged_rgb)

    search_flag = 0
    # 結果表示
    if results:
        st.subheader("🔍 認識された文字:")
        for (bbox, text, prob) in results:
            # st.write(f"- {text}（信頼度: {prob:.2f}）")
            if text[0 : 2] == "PO":
                st.write(f"- {text}（信頼度: {prob:.2f}）")
                break
    else:
        st.warning("文字が認識できませんでした。画像の明るさや角度を調整して再撮影してください。")
    if search_flag == 0:
        results = None
        camera_image = None
        st.rerun()

