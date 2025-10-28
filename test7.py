import streamlit as st
from streamlit_javascript import st_javascript
import streamlit.components.v1 as components

st.title("QRコード読み取り")

# JavaScript埋め込み
components.html(
    """
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <div id="reader" style="width:300px;"></div>
    <script>
      function onScanSuccess(decodedText, decodedResult) {
          localStorage.setItem("qrCodeResult", decodedText);
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

# JavaScriptから値取得
qr_result = st_javascript("localStorage.getItem('qrCodeResult')")

if qr_result and qr_result != "":
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)
