from flask import Flask, request, jsonify, redirect
import os
from terabox_downloader import TeraboxDL

app = Flask(__name__)

# Retrieve the ndus cookie from environment variables
NDUS_COOKIE = os.environ.get('TERABOX_NDUS', 'YfT-ICyteHuihyVEh7BTwRnFOP2jLdMN6LfttPBV')

@app.route('/api', methods=['GET'])
def handle_api():
    terabox_url = request.args.get('url')
    
    if not terabox_url:
        return jsonify({"status": "error", "message": "Missing 'url' parameter"}), 400

    try:
        # Properly format cookie string with lang and ndus
        cookie_str = f"lang=en; ndus={NDUS_COOKIE}"
        downloader = TeraboxDL(cookie=cookie_str)
        
        # Fetch file info directly using the library wrapper
        file_info = downloader.get_file_info(terabox_url)
        
        if file_info and isinstance(file_info, dict):
            if "error" in file_info:
                return jsonify({
                    "status": "error",
                    "message": "TeraBox error returned by downloader",
                    "details": file_info["error"]
                }), 400
                
            download_link = file_info.get("download_link") or file_info.get("dlink")
            if download_link:
                return redirect(download_link)

        return jsonify({
            "status": "error",
            "message": "Could not extract download link from response.",
            "raw_response": str(file_info)
        }), 400

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Internal server error during link resolution",
            "url": terabox_url
        }), 500

@app.route('/')
def home():
    return "DramaHub TeraBox Gateway is Live!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)