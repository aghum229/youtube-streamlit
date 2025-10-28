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
    # QRコード読み取りUI（背面カメラで即開始）
    components.html(
        """
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        <div id="reader" style="width:300px;"></div>
        <script>
          async function startScanner() {
            const devices = await Html5Qrcode.getCameras();
            if (devices && devices.length) {
              // 背面カメラを優先（labelに "back" を含むものを探す）
              let backCamera = devices.find(d => d.label.toLowerCase().includes("back"));
              let cameraId = backCamera ? backCamera.id : devices[0].id;

              const html5QrCode = new Html5Qrcode("reader");
              html5QrCode.start(
                cameraId,
                {
                  fps: 10,
                  qrbox: 250
                },
                (decodedText, decodedResult) => {
                  const baseUrl = window.location.origin + window.location.pathname;
                  const newUrl = baseUrl + "?qr=" + encodeURIComponent(decodedText);
                  window.location.href = newUrl;
                },
                (errorMessage) => {
                  // 読み取り失敗時のログ（必要なら表示）
                  console.log("読み取りエラー:", errorMessage);
                }
              );
            } else {
              document.getElementById("reader").innerText = "カメラが見つかりませんでした。";
            }
          }

          if (!window.qrScannerInitialized) {
            startScanner();
            window.qrScannerInitialized = true;
          }
        </script>
        """,
        height=400,
    )
