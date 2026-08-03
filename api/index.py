import json
import os
import uuid
import tempfile
import base64
import shutil
import yt_dlp

def handler(request, response):
    if request.method == 'OPTIONS':
        response.status_code = 200
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if request.method != 'POST':
        response.status_code = 405
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.body = json.dumps({'error': 'Method not allowed'})
        return response

    try:
        body = json.loads(request.body)
        url = body.get('url', '').strip()

        if not url:
            response.status_code = 400
            response.headers['Content-Type'] = 'application/json'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.body = json.dumps({'error': 'URL is required'})
            return response

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
            response.status_code = 400
            response.headers['Content-Type'] = 'application/json'
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.body = json.dumps({'error': 'No downloadable content found'})
            return response

        response.status_code = 200
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.body = json.dumps({
            'task_id': task_id,
            'status': 'completed',
            'files': downloaded_files
        })
        return response

    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        response.status_code = 400
        response.headers['Content-Type'] = 'application/json'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.body = json.dumps({'error': str(e)})
        return response