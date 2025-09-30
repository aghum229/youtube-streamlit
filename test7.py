_= '''
import cv2
import streamlit as st

st.title('Webcam Barcode Reader')

# カメラ映像を配置するプレースホルダーを作成
placeholder = st.empty()

cap = cv2.VideoCapture(0)  # カメラ番号は環境に合わせて調整してください

# バーコードリーダーを作成
barcode_reader = cv2.barcode.BarcodeDetector()

# 検出されたバーコード情報を格納する集合
detected_codes = set()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # OpenCVはBGRフォーマットなので、RGBに変換
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # バーコード情報を取得
    try:
        # バーコードを検出
        ok, decoded_info, decoded_type, corners = barcode_reader.detectAndDecode(frame)
    except ValueError:
        decoded_info, decoded_type, corners = barcode_reader.detectAndDecode(frame)
        ok = bool(decoded_info)

    # st.write(f"decoded_info: {decoded_info}")  # デバッグ出力
    if len(decoded_info) > 2:
        detected_codes.add(f'{decoded_info}')

    # `st.image()`でプレースホルダーに画像を表示
    placeholder.image(frame, channels="RGB")

    # バーコードが検出されたらループを終了
    if len(detected_codes) >= 2:
        l = list(detected_codes)
        st.header(f'Barcodes: {l[0]}, {l[1]}')
        break

cap.release()
'''


_= '''
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
'''


_= '''
import cv2
from pyzbar.pyzbar import decode 
import tkinter as tk1 
from PIL import Image, ImageTk

def stop1(): 
    global stp1 
    if stp1 == 0: 
        stp1 = 1 
        button1["text"] = "start" 
    else: 
        stp1 = 0 
        button1["text"] = "stop" 

def decoder1(): 
    global cap1 
    global frame1 
    global canvas1 
    global img1 
    global cnt1 
    global stp1 
    if stp1 == 0: 
        result0, img0 = cap1.read()
        if result0:
            decode0 = decode( cv2.cvtColor( img0, cv2.COLOR_RGBA2GRAY )  ) 
            img1 = cv2.cvtColor( img0, cv2.COLOR_BGR2RGB ) 
            if len( decode0 ) > 0: 
                str1 = decode0[0].data.decode("utf-8") 
                rect1 = decode0[0].rect
                textbox1.delete( 0, tk1.END ) 
                textbox1.insert( 0, str1 ) 
                cv2.rectangle( img1, ( rect1.left, rect1.top ), ( rect1.left + rect1.width, rect1.top + rect1.height ), ( 0, 0, 255 ), thickness = 1 ) 
                cnt1 = 0 
            else: 
                cnt1 = cnt1 + 1 
                if cnt1 > 5: 
                    textbox1.delete( 0, tk1.END ) 
            img1 = ImageTk.PhotoImage( image= Image.fromarray( img1 ) ) 
            canvas1.create_image( 0, 0, anchor=tk1.NW, image=img1 ) 
    frame1.after( 3000, decoder1 ) 

frame1 = tk1.Tk()
frame1.title(u"barcode_reader v0.1")
frame1.geometry("680x550")

label1 = tk1.Label(text='barcode data')
label1.place(x=10, y=10, width = 100) 

textbox1 = tk1.Entry( master=frame1 ) 
textbox1.place(x=110, y=10, width=400) 

button1 = tk1.Button( frame1, text='stop', command=stop1 )
button1.place(x=560, y=10, width=100)

cap1 = cv2.VideoCapture( 0, cv2.CAP_DSHOW )   # camera number 

canvas1 = tk1.Canvas( frame1, width=cap1.get( cv2.CAP_PROP_FRAME_WIDTH ), height=cap1.get( cv2.CAP_PROP_FRAME_HEIGHT ), bg='white' )
canvas1.place(x=20, y=50) 

img1 = 0 
cnt1 = 0 
stp1 = 0 
decoder1() 

frame1.mainloop()
cap1.release()
'''

# _= '''
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
# '''
