from flask import Flask, request, jsonify, redirect
import requests
import re
import os

app = Flask(__name__)

PROXY_WORKER_URL = "https://tbx-proxy.shakir-ansarii075.workers.dev"

def extract_surl(terabox_url):
    # Extracts the share code identifier following /s/ in the URL
    match = re.search(r'/s/([a-zA-Z0-9\-_]+)', terabox_url)
    if match:
        return match.group(1)
    # Fallback to the raw URL string if no /s/ pattern is found
    return terabox_url

@app.route('/api', methods=['GET'])
def handle_api():
    terabox_url = request.args.get('url')
    mode = request.args.get('mode', 'resolve')

    if not terabox_url:
        return jsonify({"status": "error", "message": "Missing 'url' parameter"}), 400

    # Extract the clean surl code required by the worker
    surl_code = extract_surl(terabox_url)

    try:
        proxy_endpoint = f"{PROXY_WORKER_URL}/api?mode={mode}&surl={requests.utils.quote(surl_code)}"
        response = requests.get(proxy_endpoint, timeout=30)
        
        try:
            data = response.json()
            return jsonify(data), response.status_code
        except ValueError:
            return response.text, response.status_code

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Failed to connect to external proxy worker",
            "url": terabox_url,
            "surl": surl_code
        }), 500

@app.route('/')
def home():
    return "TeraBox Render Backend is Live and Running!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)