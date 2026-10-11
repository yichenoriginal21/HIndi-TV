from flask import Flask, request, jsonify, redirect
import requests
import re
import os

app = Flask(__name__)

# Paste your TeraBox 'ndus' cookie value here to bypass verification challenges
TERABOX_NDUS_COOKIE = os.environ.get('TERABOX_NDUS', 'YOUR_NDUS_COOKIE_HERE')

def extract_surl(terabox_url):
    # Extracts the share code identifier following /s/ in the URL
    match = re.search(r'/s/([a-zA-Z0-9\-_]+)', terabox_url)
    if match:
        return match.group(1)
    return terabox_url

@app.route('/api', methods=['GET'])
def handle_api():
    terabox_url = request.args.get('url')
    
    if not terabox_url:
        return jsonify({"status": "error", "message": "Missing 'url' parameter"}), 400

    surl_code = extract_surl(terabox_url)

    try:
        # Headers to mimic a real browser session with your authentication cookie
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": f"ndus={TERABOX_NDUS_COOKIE}"
        }

        # Query TeraBox's share info endpoint directly
        api_url = f"https://www.terabox.com/wap/share/info?surl={surl_code}"
        response = requests.get(api_url, headers=headers, timeout=30)
        data = response.json()

        # Check if TeraBox successfully returned file details
        if data.get("errno") == 0 and "list" in data and len(data["list"]) > 0:
            file_info = data["list"][0]
            download_link = file_info.get("dlink") or file_info.get("download_url")
            file_name = file_info.get("server_filename", "video.mp4")
            
            if download_link:
                # Redirect user's browser straight to the actual direct file download link
                return redirect(download_link)
            else:
                return jsonify({"status": "error", "message": "Download link not found in response", "data": data}), 500
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to resolve file info. Cookie might be invalid or expired.",
                "terabox_response": data
            }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Internal server error during resolution",
            "url": terabox_url,
            "surl": surl_code
        }), 500

@app.route('/')
def home():
    return "TeraBox Direct Python Backend is Live and Running!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)