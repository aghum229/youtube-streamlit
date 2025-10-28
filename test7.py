import streamlit as st
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
          const newUrl = window.location.pathname + "?qr=" + encodeURIComponent(decodedText);
          window.history.replaceState(null, "", newUrl);  // 履歴を増やさずURL更新
          location.reload();  // 明示的に再読み込み
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

# クエリパラメータ取得（リストではなく文字列で）
qr_result = urllib.parse.unquote_plus(st.query_params.get("qr", ""))

if qr_result:
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)
