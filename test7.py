import streamlit as st
import urllib.parse
import streamlit.components.v1 as components

st.title("QRコード読み取り")

qr_result = urllib.parse.unquote_plus(st.query_params.get("qr", ""))

if qr_result:
    st.success("読み取ったQRコードの内容:")
    st.write(qr_result)

    if st.button("QRコードを再スキャンする"):
        st.query_params.clear()
        st.rerun()
else:
    html_code = """
    <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
    <div id="reader" style="width:300px;"></div>
    <script>
      function onScanSuccess(decodedText, decodedResult) {
        const baseUrl = window.location.origin + window.location.pathname;
        const newUrl = baseUrl + "?qr=" + encodeURIComponent(decodedText);
        window.location.href = newUrl;
      }
    
      if (!document.getElementById("reader").hasChildNodes()) {
        const html5QrCode = new Html5Qrcode("reader");
        html5QrCode.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: 250 },
          onScanSuccess,
          (errorMessage) => { console.log("読み取りエラー:", errorMessage); }
        );
      }
    </script>
    """
    components.html(html_code.strip(), height=400)


