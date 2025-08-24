_= '''
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
'''

# _= '''
import streamlit as st
import easyocr
import numpy as np
import cv2
from PIL import Image
import glob
import os
import re


def preprocess_image(image_np):
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

st.title("複数画像から指定文字を検出して赤い円（○）を描画")

# 🔤 検出したい文字を入力
target_text = st.text_input("検出したい文字を入力してください", value="")
if target_text == "":
    None
else:
    # 📂 同じフォルダ内の画像ファイル一覧を取得（PNG/JPG）
    image_files = sorted(glob.glob("TanaMap*.png") + glob.glob("TanaMap*.jpg") + glob.glob("TanaMap*.jpeg"))
    image_flag = False
    image_sub_flag = False
    image_search_flag = False
    if not image_files:
        st.warning("画像ファイルが見つかりませんでした。")
    else:
        reader = easyocr.Reader(['ja', 'en'], gpu=False)
        first_char = target_text[0]
        second_char = target_text[1]
        after_hyphen = target_text.split("-")[1]
        after_hyphen_int = int(after_hyphen)
        st.write(f"ハイフン以降の数値: {after_hyphen_int}（型: {type(after_hyphen_int)}）")
        # match = re.search(r"-(.+)", target_text)
        # after_hyphen = match.group(1) if match else ""
        # after_hyphen_int = int(after_hyphen)
        st.write(first_char)
        st.write(second_char)
        st.write(f"{after_hyphen_int}")
        
        if first_char == "完" and after_hyphen_int <= 9:
            sub_text = "P-1"
            image_path_sub = "TanaMap20250820-P1.png"
            image_path = "TanaMap20250820-1.png"
            image_search_flag = True
        elif (first_char == "完" and 10 <= after_hyphen_int <= 20): 
            sub_text = "P-2"
            image_path_sub = "TanaMap20250820-P2.png"
            image_path = "TanaMap20250820-2.png"
            image_search_flag = True
        elif ((first_char == "E" and 31 <= after_hyphen_int <= 37) 
            or (first_char == "G" and after_hyphen_int <= 18) 
            or (first_char == "H" and after_hyphen_int <= 18) 
            or (first_char == "R" and after_hyphen_int <= 19)):
            sub_text = "P-3"
            image_path_sub = "TanaMap20250820-P3.png"
            image_path = "TanaMap20250820-3.png"
            image_search_flag = True
        elif ((first_char == "A" and after_hyphen_int <= 16) 
            or (first_char == "D" and after_hyphen_int <= 16) 
            or (first_char == "E" and 51 <= after_hyphen_int <= 57) 
            or (first_char == "F" and after_hyphen_int <= 16)):
            sub_text = "P-4"
            image_path_sub = "TanaMap20250820-P4.png"
            image_path = "TanaMap20250820-4.png"
            image_search_flag = True
        elif ((first_char == "E" and 38 <= after_hyphen_int <= 50) 
            or (first_char == "G" and 20 <= after_hyphen_int <= 33) 
            or (first_char == "H" and 31 <= after_hyphen_int <= 37)):
            sub_text = "P-5"
            image_path_sub = "TanaMap20250820-P5.png"
            image_path = "TanaMap20250820-5.png"
            image_search_flag = True
        elif ((first_char == "A" and 19 <= after_hyphen_int <= 30) 
            or (first_char == "D" and 18 <= after_hyphen_int <= 28) 
            or (first_char == "F" and 20 <= after_hyphen_int <= 32) 
            or (first_char == "H" and 26 <= after_hyphen_int <= 30) 
            or (first_char == "S" and after_hyphen <= 12)):
            sub_text = "P-6"
            image_path_sub = "TanaMap20250820-P6.png"
            image_path = "TanaMap20250820-6.png"
            image_search_flag = True
        if image_search_flag:
            # OCR実行   r"完.?[ABC][-–—]?(1[0-5]|[1-9])"
            
            image_sub = Image.open(image_path_sub).convert("RGB")
            image_sub_np = np.array(image_sub)
            if os.path.exists(image_path):
                image = Image.open(image_path).convert("RGB")
                image_np = np.array(image)
            else:
                st.error(f"画像ファイルが見つかりません: {image_path}")
                st.stop()
            _= '''
            results_sub = reader.readtext(image_sub_np)
            target_center = None
            target_pattern = re.compile(fr"{sub_text}")
            target_pattern_b = re.compile(fr"{sub_text}_")
            # st.write(target_pattern)
            for bbox, text, prob in results_sub:
                cleaned = text.replace(" ", "")
                # st.write(cleaned)
                if target_pattern.search(cleaned):
                    (tl, tr, br, bl) = bbox
                    center_x = int((tl[0] + br[0]) / 2)
                    center_y = int((tl[1] + br[1]) / 2)
                    target_center = (center_x, center_y)
                    break
                else:
                    if target_pattern_b.search(cleaned):
                        (tl, tr, br, bl) = bbox
                        center_x = int((tl[0] + br[0]) / 2)
                        center_y = int((tl[1] + br[1]) / 2)
                        if second_char == "B" or second_char == "D":
                            center_x += 10
                        else:
                            center_x -= 10
                        target_center = (center_x, center_y)
                        break
            # 赤い円（○）を描画
            image_with_circle_a = image_sub_np.copy()
            if target_center:
                cv2.circle(image_with_circle_a, target_center, 60, (255, 0, 0), thickness=8)
                # 画像サイズに合わせて矩形を描画
                h, w = image_with_circle_a.shape[:2]
                cv2.rectangle(image_with_circle_a, (0, 0), (w - 1, h - 1), (0, 0, 0), 20)
                # st.image(image_with_circle_a, caption=f"{sub_text} を検出しました", use_container_width=True)
                st.success(f"座標: {target_center}")
                image_sub_flag = True
            else:
                None
                # st.image(image_with_circle_a, caption=f"{sub_text} は検出されませんでした", use_container_width=True)
                # st.warning(f"{sub_text} はこの画像には見つかりませんでした。")
            if image_sub_flag == False:
                st.warning(f"{sub_text} はこの画像には見つかりませんでした。")
            '''

            image_with_circle_a = image_sub_np.copy()
            results = reader.readtext(image_np)
            target_center = None
            if first_char == "完":
                target_pattern = re.compile(fr"完{second_char}-{after_hyphen_int}")
                target_pattern_b = re.compile(fr"{second_char}-{after_hyphen_int}")
                # st.write(target_pattern)
                for bbox, text, prob in results:
                    cleaned = text.replace(" ", "")
                    # st.write(cleaned)
                    if target_pattern.search(cleaned):
                        (tl, tr, br, bl) = bbox
                        center_x = int((tl[0] + br[0]) / 2)
                        center_y = int((tl[1] + br[1]) / 2)
                        target_center = (center_x, center_y)
                        break
                    else:
                        if target_pattern_b.search(cleaned):
                            (tl, tr, br, bl) = bbox
                            center_x = int((tl[0] + br[0]) / 2)
                            center_y = int((tl[1] + br[1]) / 2)
                            if second_char == "B" or second_char == "D":
                                center_x += 10
                            else:
                                center_x -= 10
                            target_center = (center_x, center_y)
                            break
            else:
                for bbox, text, prob in results:
                    if text.strip() == target_text.strip():
                        (tl, tr, br, bl) = bbox
                        center_x = int((tl[0] + br[0]) / 2)
                        center_y = int((tl[1] + br[1]) / 2)
                        target_center = (center_x, center_y)
                        break
    
            # 赤い円（○）を描画
            image_with_circle_b = image_np.copy()
            if target_center:
                # cv2.circle(image_with_circle_b, target_center, 50, (255, 0, 0), thickness=8)
                axes = (65, 35)  # 横長：横55、縦25
                angle = 0         # 回転なし
                cv2.ellipse(image_with_circle_b, target_center, axes, angle, 0, 360, (255, 0, 0), thickness=8)
                # st.image(image_with_circle_b, caption=f"{target_text} を検出しました", use_container_width=True)

                # 画像サイズに合わせて矩形を描画
                h, w = image_with_circle_b.shape[:2]
                cv2.rectangle(image_with_circle_b, (0, 0), (w - 1, h - 1), (255, 0, 255), 20)
                
                # サイズ取得
                h1, w1 = image_with_circle_a.shape[:2]
                h2, w2 = image_with_circle_b.shape[:2]
                # キャンバスサイズ（幅は最大、縦は合計）
                canvas_width = max(w1, w2)
                canvas_height = h1 + h2
                # 白背景キャンバス作成
                canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
                # img1 を上に貼り付け（中央揃え）
                x1_offset = (canvas_width - w1) // 2
                canvas[0:h1, x1_offset:x1_offset + w1] = image_with_circle_a
                # img2 を下に貼り付け（中央揃え）
                x2_offset = (canvas_width - w2) // 2
                canvas[h1:h1 + h2, x2_offset:x2_offset + w2] = image_with_circle_b
                
                st.image(canvas, caption=f"画像を結合しました", use_container_width=True)
                st.success(f"座標: {target_center}")
                image_flag = True
            else:
                None
                # st.image(image_with_circle, caption=f"{target_text} は検出されませんでした", use_container_width=True)
                # st.warning(f"{target_text} はこの画像には見つかりませんでした。")
        if image_flag == False:
            st.warning(f"{target_text} はこの画像には見つかりませんでした。")
    st.stop()
# '''
