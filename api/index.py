import json
import os
import uuid
import tempfile
import base64
import re
import shutil
from http.server import BaseHTTPRequestHandler

def extract_video_id(url):
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_playlist(url):
    return 'playlist' in url or 'list=' in url

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/download':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)
            url = data.get('url', '').strip()

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

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(tmp_dir, f'{task_id}_%(title)s.%(ext)s'),
                    'ignoreerrors': True,
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': not is_playlist(url),
                    'extract_flat': False,
                    'writethumbnail': False,
                    'encoding': 'utf-8',
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                downloaded_files = []
                for f in os.listdir(tmp_dir):
                    file_path = os.path.join(tmp_dir, f)
                    if os.path.isfile(file_path):
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

                if not downloaded_files:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'No downloadable content found. Check the URL.'}).encode())
                    return

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

            except yt_dlp.utils.DownloadError as e:
                error_msg = str(e)
                if 'Invalid URL' in error_msg or 'id' in error_msg.lower():
                    error_msg = 'Could not process this URL. Make sure it is a valid YouTube video/playlist link.'
                
                shutil.rmtree(tmp_dir, ignore_errors=True)
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': error_msg}).encode())

            except Exception as e:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'Server error: {str(e)}'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()