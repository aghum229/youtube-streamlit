import streamlit as st
from streamlit_javascript import st_javascript
import streamlit.components.v1 as components

st.title("QRコード読み取り（確実に表示）")

# QRコード読み取りUI（JavaScript）
components.html(
    """
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <div id="reader" style="width:300px;"></div>
    <script>
      window.qrCodeResult = "";

      function onScanSuccess(decodedText, decodedResult) {
          window.qrCodeResult = decodedText;
      }

      if (!window.qrScannerInitialized) {
        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess);
        window.qrScannerInitialized = true;
      }
    </script>
    """,
    height=400,
)

# JavaScriptから値を取得
qr_result = st_javascript("window.qrCodeResult")

# 結果があれば表示
if qr_result and qr_result != "":
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)
