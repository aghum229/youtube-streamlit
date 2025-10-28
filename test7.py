import streamlit as st
from streamlit_javascript import st_javascript
import streamlit.components.v1 as components
import urllib.parse


st.title("QRコード読み取り")

# JavaScript埋め込み
components.html(
    """
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <div id="reader" style="width:300px;"></div>
    <script>
      function onScanSuccess(decodedText, decodedResult) {
          window.location.href = window.location.pathname + "?qr=" + encodeURIComponent(decodedText);
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

query_params = st.query_params
qr_result = query_params.get("qr", [""])[0]

if qr_result:
    st.success("読み取ったQRコードの内容:")
    st.write(urllib.parse.unquote(qr_result))

