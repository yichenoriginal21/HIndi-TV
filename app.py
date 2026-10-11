from flask import Flask, request, jsonify, redirect
import requests
import re
import os

app = Flask(__name__)

# Retrieve the ndus cookie from environment variables
NDUS_COOKIE = os.environ.get('TERABOX_NDUS', 'YfT-ICyteHuihyVEh7BTwRnFOP2jLdMN6LfttPBV')

@app.route('/api', methods=['GET'])
def handle_api():
    terabox_url = request.args.get('url')
    
    if not terabox_url:
        return jsonify({"status": "error", "message": "Missing 'url' parameter"}), 400

    # Extract the share code from the URL
    match = re.search(r'/s/([a-zA-Z0-9\-_]+)', terabox_url)
    if not match:
        return jsonify({"status": "error", "message": "Invalid TeraBox URL format"}), 400
    
    surl_code = match.group(1)

    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": f"ndus={NDUS_COOKIE}; lang=en"
        }

        # Query TeraBox's mobile share endpoint
        api_url = f"https://www.terabox.com/wap/share/info?surl={surl_code}"
        response = session.get(api_url, headers=headers, timeout=20)
        data = response.json()

        if data.get("errno") == 0 and "list" in data and len(data["list"]) > 0:
            file_info = data["list"][0]
            download_link = file_info.get("dlink") or file_info.get("download_url")
            
            if download_link:
                return redirect(download_link)

        return jsonify({
            "status": "error",
            "message": "Failed to extract download link from TeraBox response.",
            "terabox_response": data
        }, 400)

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Internal server error during resolution"
        }), 500

@app.route('/')
def home():
    return "DramaHub TeraBox Gateway is Live!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)