import streamlit as st
import urllib.parse
import streamlit.components.v1 as components
import textwrap

st.title("QRコード読み取り")

qr_result = urllib.parse.unquote_plus(st.query_params.get("qr", ""))

if qr_result:
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)

    if st.button("QRコードを再スキャンする"):
        st.query_params.clear()
        st.rerun()
else:
    html_code = textwrap.dedent("""
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        <div id="reader" style="width:300px;"></div>
        <script>
        function startScanner() {
            const html5QrCode = new Html5Qrcode("reader");
            html5QrCode.start(
                { facingMode: "environment" },
                { fps: 10, qrbox: 250 },
                function(decodedText, decodedResult) {
                    const baseUrl = window.location.origin + window.location.pathname;
                    const newUrl = baseUrl + "?qr=" + encodeURIComponent(decodedText);
                    window.location.href = newUrl;
                },
                function(errorMessage) {
                    console.log("読み取りエラー:", errorMessage);
                }
            );
        }

        if (!window.qrScannerInitialized) {
            startScanner();
            window.qrScannerInitialized = true;
        }
        </script>
    """)

    components.html(html_code, height=400, key="qr-reader")
