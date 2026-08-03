import json
import os
import uuid
import tempfile
import base64
import shutil
import yt_dlp
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            url = data.get('url', '').strip()

            if not url:
                self._send_json(400, {'error': 'URL is required'})
                return

            task_id = str(uuid.uuid4())[:8]
            tmp_dir = tempfile.mkdtemp()

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
                'ignoreerrors': True,
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            downloaded_files = []
            for f in os.listdir(tmp_dir):
                file_path = os.path.join(tmp_dir, f)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    with open(file_path, 'rb') as af:
                        audio_data = af.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    downloaded_files.append({
                        'name': f,
                        'size': size,
                        'data': audio_base64
                    })

            shutil.rmtree(tmp_dir, ignore_errors=True)

            if not downloaded_files:
                self._send_json(400, {'error': 'No downloadable content found'})
                return

            self._send_json(200, {
                'task_id': task_id,
                'status': 'completed',
                'files': downloaded_files
            })

        except Exception as e:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            self._send_json(400, {'error': str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())