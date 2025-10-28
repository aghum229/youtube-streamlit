import streamlit as st
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval

st.title("QRコード読み取り結果の表示")

# JavaScript埋め込み
components.html(
    """
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <div id="reader" style="width:300px;"></div>
    <script>
      window.qrCodeResult = "";

      function onScanSuccess(decodedText, decodedResult) {
          window.qrCodeResult = decodedText;
          setTimeout(() => {
              window.qrCodeResult = "";
          }, 1500);
      }

      let html5QrcodeScanner = new Html5QrcodeScanner(
          "reader", { fps: 10, qrbox: 250 });
      html5QrcodeScanner.render(onScanSuccess);
    </script>
    """,
    height=400,
)

# JavaScriptから結果を取得
qr_result = streamlit_js_eval(
    js_expressions="window.qrCodeResult",
    key="qr-reader",
    debounce=0.1,
    trigger_on_change=True
)

# 結果があれば表示
if qr_result and qr_result != "":
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)


