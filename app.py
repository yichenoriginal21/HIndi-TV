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

    # Extract domain and surl code from the input URL
    match = re.search(r'https?://([a-zA-Z0-9.\-]+)/s/([a-zA-Z0-9\-_]+)', terabox_url)
    if not match:
        # Fallback regex if domain isn't fully captured
        match_code = re.search(r'/s/([a-zA-Z0-9\-_]+)', terabox_url)
        if not match_code:
            return jsonify({"status": "error", "message": "Invalid TeraBox URL format"}), 400
        domain = "www.terabox.com"
        surl_code = match_code.group(1)
    else:
        domain = match.group(1)
        surl_code = match.group(2)

    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": f"ndus={NDUS_COOKIE}; lang=en",
            "Referer": f"https://{domain}/"
        }

        # Step 1: Visit the share page using the correct domain
        share_page_url = f"https://{domain}/s/{surl_code}"
        page_res = session.get(share_page_url, headers=headers, timeout=20)
        
        if page_res.status_code != 200:
            # Try fallback to standard www.terabox.com if custom domain fails
            domain = "www.terabox.com"
            share_page_url = f"https://{domain}/s/{surl_code}"
            page_res = session.get(share_page_url, headers=headers, timeout=20)
            
            if page_res.status_code != 200:
                return jsonify({
                    "status": "error", 
                    "message": "Failed to load TeraBox share page (404/Blocked)", 
                    "attempted_url": share_page_url,
                    "status_code": page_res.status_code
                }, 500)

        html_content = page_res.text

        # Step 2: Extract jsToken and sign using regex
        js_token_match = re.search(r'jsToken["\s*:]+["\']([a-zA-Z0-9]+)["\']', html_content)
        sign_match = re.search(r'sign["\s*:]+["\']([a-zA-Z0-9]+)["\']', html_content)
        
        if not js_token_match:
            js_token_match = re.search(r'bdstoken["\s*:]+["\']([a-zA-Z0-9]+)["\']', html_content)

        # Step 3: Query the file info endpoint
        api_url = f"https://{domain}/share/info?surl={surl_code}"
        if js_token_match:
            api_url += f"&jsToken={js_token_match.group(1)}"
        if sign_match:
            api_url += f"&sign={sign_match.group(1)}"

        api_res = session.get(api_url, headers=headers, timeout=20)
        
        try:
            data = api_res.json()
        except Exception:
            return jsonify({
                "status": "error",
                "message": "Failed to parse API response as JSON",
                "raw_text": api_res.text[:300]
            }), 500

        if data.get("errno") == 0 and "list" in data and len(data["list"]) > 0:
            file_info = data["list"][0]
            download_link = file_info.get("dlink") or file_info.get("download_url")
            
            if download_link:
                return redirect(download_link)

        return jsonify({
            "status": "error",
            "message": "Failed to extract download link from API response.",
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