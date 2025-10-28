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
        const url = new URL(window.location.href);
        url.searchParams.set("qr", encodeURIComponent(decodedText));
        setTimeout(() => {
          window.location.href = url.toString();
        }, 500); // 少し待ってからリロード
      }
    
      if (!window.qrScannerInitialized && document.getElementById("reader")) {
        const scanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 });
        scanner.render(onScanSuccess);
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
