import streamlit as st
import cv2
from pyzbar.pyzbar import decode
from PIL import Image

st.title("📷 バーコード・QRコード読み取り")

# カメラ起動
camera = st.camera_input("Webカメラで撮影")

if camera:
    # 画像をOpenCV形式に変換
    img = Image.open(camera)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # バーコード・QRコードの読み取り
    decoded_objects = decode(img_cv)

    if decoded_objects:
        for obj in decoded_objects:
            st.success(f"🔍 読み取り結果: {obj.data.decode('utf-8')}")
            st.write(f"種類: {obj.type}")
    else:
        st.warning("コードが検出されませんでした。もう一度試してください。")

