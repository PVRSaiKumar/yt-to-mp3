const API_URL = window.location.origin + '/api';
let currentFiles = [];

function startDownload() {
    const urlInput = document.getElementById('playlistUrl');
    const url = urlInput.value.trim();

    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }

    if (!isValidYouTubeUrl(url)) {
        showError('Please enter a valid YouTube video or playlist URL');
        return;
    }

    hideError();
    hideFiles();
    showStatus('Downloading... This may take a while.', 50);
    setButtonLoading(true);

    fetch(`${API_URL}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(data => { throw new Error(data.error || 'Server error'); });
        }
        return res.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        if (data.status === 'completed' && data.files) {
            currentFiles = data.files;
            showStatus('Download complete!', 100);
            showFiles(data.files);
        }
        setButtonLoading(false);
    })
    .catch(err => {
        showError(err.message || 'Failed to download');
        setButtonLoading(false);
        hideStatus();
    });
}

function showFiles(files) {
    const section = document.getElementById('filesSection');
    const list = document.getElementById('filesList');
    list.innerHTML = '';

    files.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <span class="file-name">${formatFileName(file.name)}</span>
            <span class="file-size">${formatSize(file.size)}</span>
            <button class="file-download" onclick="downloadFile(${index})">Download</button>
        `;
        list.appendChild(item);
    });

    section.classList.remove('hidden');
}

function downloadAll() {
    currentFiles.forEach((file, i) => {
        setTimeout(() => downloadFile(i), i * 500);
    });
}

function downloadFile(index) {
    const file = currentFiles[index];
    if (!file || !file.data) return;

    try {
        const byteCharacters = atob(file.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'audio/mpeg' });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        showError('Failed to download file');
    }
}

function isValidYouTubeUrl(url) {
    const patterns = [
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=[a-zA-Z0-9_-]{11}/,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/playlist\?list=[a-zA-Z0-9_-]+/,
        /(?:https?:\/\/)?youtu\.be\/[a-zA-Z0-9_-]{11}/,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/[a-zA-Z0-9_-]{11}/,
    ];
    return patterns.some(p => p.test(url));
}

function showStatus(text, progress) {
    const status = document.getElementById('status');
    const statusText = document.getElementById('statusText');
    const progressFill = document.getElementById('progressFill');

    status.classList.remove('hidden');
    statusText.textContent = text;
    progressFill.style.width = `${progress}%`;
}

function hideStatus() {
    document.getElementById('status').classList.add('hidden');
}

function showError(message) {
    const error = document.getElementById('error');
    error.textContent = message;
    error.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

function hideFiles() {
    document.getElementById('filesSection').classList.add('hidden');
}

function setButtonLoading(loading) {
    const btn = document.getElementById('downloadBtn');
    const text = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');

    btn.disabled = loading;
    text.textContent = loading ? 'Processing...' : 'Download';
    loader.classList.toggle('hidden', !loading);
}

function formatFileName(name) {
    return name.replace(/^[\w]+_/, '').replace(/\.[^.]+$/, '');
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

document.getElementById('playlistUrl').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') startDownload();
});