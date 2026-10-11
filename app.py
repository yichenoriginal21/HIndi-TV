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

    # Extract share code (surl) from the URL
    match = re.search(r'/s/([a-zA-Z0-9\-_]+)', terabox_url)
    if not match:
        return jsonify({"status": "error", "message": "Invalid TeraBox URL format"}), 400
    
    surl_code = match.group(1)

    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": f"ndus={NDUS_COOKIE}; lang=en",
            "Referer": "https://www.terabox.com/"
        }

        # Query TeraBox's mobile share info API directly using the surl
        api_url = f"https://www.terabox.com/wap/share/info?surl={surl_code}"
        response = session.get(api_url, headers=headers, timeout=20)
        
        try:
            data = response.json()
        except Exception:
            return jsonify({
                "status": "error",
                "message": "TeraBox returned non-JSON response (authentication or block issue)",
                "raw_text": response.text[:300]
            }), 500

        # Check if file info list exists
        if data.get("errno") == 0 and "list" in data and len(data["list"]) > 0:
            file_info = data["list"][0]
            download_link = file_info.get("dlink") or file_info.get("download_url")
            
            if download_link:
                return redirect(download_link)

        return jsonify({
            "status": "error",
            "message": "Failed to extract download link. Cookie might be invalid/expired or file is restricted.",
            "terabox_response": data
        }), 400

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