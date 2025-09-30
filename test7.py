import streamlit as st
import cv2
import numpy as np

img_file_buffer = st.camera_input("カメラのボタンを押してバーコードをスキャン")

if img_file_buffer is not None:
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    # 以降の処理をここに追加

    # qrcode_detector = cv2.QRCodeDetector()
    # detected, decoded_info, points, _ = qrcode_detector.detectAndDecodeMulti(cv2_img)
    # if detected:
    #     st.write("検出されたQRコード情報:", decoded_info)

    barcode_detector = cv2.barcode.BarcodeDetector()
    decoded_objects, decoded_types, _ = barcode_detector.detectAndDecodeMulti(cv2_img)
    if decoded_objects is not None:
        st.write("検出されたバーコード情報:", decoded_objects)
        st.write("バーコードの種類:", decoded_types)



_= '''
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
    enlarged = cv2.resize(img_cv, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_LINEAR)

    # 表示用にRGBへ戻す
    enlarged_rgb = cv2.cvtColor(enlarged, cv2.COLOR_BGR2RGB)
    # st.image(enlarged_rgb, caption="2倍に拡大された画像", use_column_width=True)


    # easyocrで文字認識
    reader = easyocr.Reader(['en'])  # Code39は英数字なので英語でOK
    # results = reader.readtext(img_cv)
    results = reader.readtext(enlarged_rgb)

    # search_flag = 0
    # 結果表示
    if results:
        st.subheader("🔍 認識された文字:")
        for (bbox, text, prob) in results:
            # st.write(f"- {text}（信頼度: {prob:.2f}）")
            if text[0 : 2] == "PO":
                st.write(f"- {text.strip()}（信頼度: {prob:.2f}）")
                break
    else:
        st.warning("文字が認識できませんでした。画像の明るさや角度を調整して再撮影してください。")
    # if search_flag == 0:
    #     results = None
    #     camera_image = None
    #     st.rerun()
'''
