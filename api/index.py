import json
import os
import uuid
import tempfile
import base64
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/download':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            url = data.get('url')

            if not url:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'URL is required'}).encode())
                return

            task_id = str(uuid.uuid4())[:8]

            try:
                import yt_dlp

                tmp_dir = tempfile.mkdtemp()
                output_path = os.path.join(tmp_dir, f'{task_id}_%(playlist_index)s_%(title)s.%(ext)s')

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'ignoreerrors': True,
                    'noplaylist': False,
                    'quiet': True,
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                downloaded_files = []
                for f in os.listdir(tmp_dir):
                    if f.endswith('.mp3'):
                        file_path = os.path.join(tmp_dir, f)
                        size = os.path.getsize(file_path)
                        
                        with open(file_path, 'rb') as audio_file:
                            audio_data = audio_file.read()
                            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                        
                        downloaded_files.append({
                            'name': f,
                            'size': size,
                            'data': audio_base64
                        })

                shutil.rmtree(tmp_dir, ignore_errors=True)

                result = {
                    'task_id': task_id,
                    'status': 'completed',
                    'files': downloaded_files
                }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

import shutil