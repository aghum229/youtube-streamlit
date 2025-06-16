from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

# GitHub Webhook の Secret (GitHubのWebhook設定で登録した値)
GITHUB_SECRET = "your_webhook_secret"

# Webhook のエンドポイント
@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    # GitHub から送られたデータを取得
    payload = request.data
    signature = request.headers.get("X-Hub-Signature-256")

    # 署名が正しいか検証
    expected_signature = "sha256=" + hmac.new(
        GITHUB_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({"error": "Invalid signature"}), 403

    # Webhook のイベントをログに記録
    data = request.json
    print("Received Webhook:", data)

    return jsonify({"message": "Webhook received successfully"}), 200

if __name__ == "__main__":
    app.run(port=5000)
