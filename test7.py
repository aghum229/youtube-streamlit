import streamlit as st
import urllib.parse
import streamlit.components.v1 as components

st.title("QRコード読み取り")

# クエリパラメータ取得
qr_result = urllib.parse.unquote_plus(st.query_params.get("qr", ""))

# QRコード読み取りUIは、qrが空のときだけ表示
if not qr_result:
    components.html(
        """
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        <div id="reader" style="width:300px;"></div>
        <script>
          function onScanSuccess(decodedText, decodedResult) {
              const url = new URL(window.location.href);
              url.searchParams.set("qr", encodeURIComponent(decodedText));
              window.location.href = url.toString();
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

# 読み取り結果を表示
if qr_result:
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)
