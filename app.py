from flask import Flask, request, jsonify, redirect
import requests
import os

app = Flask(__name__)

# The external proxy/worker URL that handles the resolution
PROXY_WORKER_URL = "https://tbx-proxy.shakir-ansarii075.workers.dev"

@app.route('/api', methods=['GET'])
def handle_api():
    terabox_url = request.args.get('url')
    # Pass 'resolve' as the mode or include a mode parameter as required by your worker
    mode = request.args.get('mode', 'resolve')

    if not terabox_url:
        return jsonify({"status": "error", "message": "Missing 'url' parameter"}), 400

    try:
        # Construct the endpoint call matching what the Cloudflare worker expects
        proxy_endpoint = f"{PROXY_WORKER_URL}/api?mode={mode}&url={requests.utils.quote(terabox_url)}"
        response = requests.get(proxy_endpoint, timeout=30)
        
        # Try to return JSON if the worker responds with JSON
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
            "url": terabox_url
        }), 500

@app.route('/')
def home():
    return "TeraBox Render Backend is Live and Running!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)