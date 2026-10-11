from flask import Flask, request, jsonify, redirect
import os
from terabox_downloader import TeraboxDL

app = Flask(__name__)

# Retrieve the ndus cookie from environment variables
NDUS_COOKIE = os.environ.get('TERABOX_NDUS', '')

@app.route('/api', methods=['GET'])
def handle_api():
    terabox_url = request.args.get('url')
    
    if not terabox_url:
        return jsonify({"status": "error", "message": "Missing 'url' parameter"}), 400

    try:
        # Initialize downloader with cookie string
        cookie_str = f"ndus={NDUS_COOKIE}"
        downloader = TeraboxDL(cookie=cookie_str)
        
        # Fetch file info directly
        file_info = downloader.get_file_info(terabox_url)
        
        if file_info and 'download_link' in file_info:
            download_link = file_info['download_link']
            return redirect(download_link)
        else:
            return jsonify({
                "status": "error",
                "message": "Could not extract download link. Check if cookie is active.",
                "details": str(file_info)
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
    return "TeraBox Downloader API is Live!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)