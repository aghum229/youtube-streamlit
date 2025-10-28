import streamlit as st
import urllib.parse
import streamlit.components.v1 as components

st.title("QRコード読み取り")

# クエリパラメータ取得
qr_result = urllib.parse.unquote_plus(st.query_params.get("qr", ""))

# 読み取り結果がある場合は表示し、読み取りUIは非表示
if qr_result:
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)
else:
    # QRコード読み取りUI
    components.html(
        """
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        <div id="reader" style="width:300px;"></div>
        <script>
          function onScanSuccess(decodedText, decodedResult) {
              const baseUrl = window.location.origin + window.location.pathname;
              const newUrl = baseUrl + "?qr=" + encodeURIComponent(decodedText);
              window.location.href = newUrl;
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

