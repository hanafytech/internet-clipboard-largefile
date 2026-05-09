import os
import uuid
from flask import Flask, request, render_template_string, Response

app = Flask(__name__)

# 10GB Limit
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024
UPLOAD_FOLDER = '/data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = {}
pending_downloads = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>internet-clipboard-largefile</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background-color: #121212; color: #e0e0e0; }
        .container { background: #1e1e1e; padding: 30px; border-radius: 10px; box-shadow: 0 8px 16px rgba(0,0,0,0.6); }
        textarea { width: 100%; height: 300px; font-family: 'Courier New', Courier, monospace; padding: 15px; background-color: #2d2d2d; color: #f8f8f2; border: 1px solid #444; border-radius: 6px; resize: vertical; box-sizing: border-box; font-size: 15px; line-height: 1.5; }
        textarea:focus { outline: none; border-color: #0d6efd; box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.25); }
        button { background-color: #0d6efd; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: 600; border-radius: 6px; margin-top: 15px; cursor: pointer; transition: background-color 0.2s; width: 100%; }
        button:hover { background-color: #0b5ed7; }
        button:disabled { background-color: #444; cursor: not-allowed; color: #888; }
        .download-btn { display: inline-block; background-color: #198754; color: white; text-decoration: none; padding: 12px 20px; border-radius: 6px; font-weight: 600; margin-top: 10px; transition: 0.2s; }
        .download-btn:hover { background-color: #157347; }
        .file-input { display: block; width: 100%; margin-bottom: 5px; padding: 10px; background: #2d2d2d; border: 1px dashed #666; border-radius: 6px; color: #ccc; box-sizing: border-box; cursor: pointer; }
        .alert { background-color: #332701; color: #ffda6a; padding: 15px; border-radius: 6px; border-left: 5px solid #ffda6a; margin-bottom: 20px; font-weight: 500; }
        .success { background-color: #0f291a; color: #75b798; padding: 15px; border-radius: 6px; border-left: 5px solid #75b798; margin-bottom: 20px; font-weight: 500; }
        .info-box { background-color: #0c2b4d; color: #9ec5fe; padding: 15px; border-radius: 6px; border-left: 5px solid #9ec5fe; margin-bottom: 20px; font-family: monospace; font-size: 15px; }
        .warning-text { color: #ff6b6b; font-size: 13px; margin-top: 0; margin-bottom: 15px; font-weight: 600; }
        h2 { margin-top: 0; color: #ffffff; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px; font-weight: 500; }
        p { line-height: 1.6; margin-bottom: 10px; }

        /* Progress Bar Styles */
        #progressWrapper { display: none; margin-top: 20px; background-color: #2d2d2d; border-radius: 6px; overflow: hidden; border: 1px solid #444; position: relative; height: 30px; }
        #progressBar { height: 100%; width: 0%; background-color: #0d6efd; transition: width 0.2s ease; }
        #progressText { position: absolute; width: 100%; text-align: center; top: 5px; font-weight: bold; color: white; font-size: 14px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }
    </style>
</head>
<body>
    <div class="container">
        {% if status == 'home' %}
            <h2>Welcome to internet-clipboard-largefile</h2>
            <p>To create a secure, burn-after-reading paste, simply type a custom name at the end of your URL.</p>
            <div class="info-box">Example: <strong>yourdomain.com/secret123</strong></div>
        {% else %}
            <h2>/{{ path }}</h2>

            {% if status == 'saved' %}
                <div class="success">✅ Saved! Share this exact URL. The text will be destroyed when opened. The file will be destroyed upon download.</div>
                {% if paste_data.file_name %}
                    <div class="info-box">📎 Attached: {{ paste_data.file_name }}</div>
                {% endif %}
                {% if paste_data.content %}
                    <textarea readonly>{{ paste_data.content }}</textarea>
                {% endif %}

            {% elif status == 'read' %}
                <div class="alert">⚠️ The text message has been destroyed from the server.</div>

                {% if paste_data.file_token %}
                    <div class="info-box" style="margin-bottom: 15px;">
                        <p style="margin-top: 0;">📎 Attached File: <strong>{{ paste_data.file_name }}</strong></p>
                        <a href="/download/{{ paste_data.file_token }}" class="download-btn">Download File (Burns on click)</a>
                    </div>
                {% endif %}
                {% if paste_data.content %}
                    <textarea readonly>{{ paste_data.content }}</textarea>
                {% endif %}

            {% else %}
                <form id="uploadForm" method="POST" enctype="multipart/form-data">
                    <input type="file" name="file_upload" class="file-input" />
                    <p class="warning-text">Max file size: 10GB. Do not close this tab until the upload completes.</p>
                    <textarea name="content" placeholder="Type or paste your text here (optional)..."></textarea>

                    <div id="progressWrapper">
                        <div id="progressBar"></div>
                        <div id="progressText">0%</div>
                    </div>

                    <button type="submit" id="submitBtn">Save (Burn on Next Read)</button>
                </form>

                <script>
                    const form = document.getElementById('uploadForm');
                    if (form) {
                        form.addEventListener('submit', function(e) {
                            e.preventDefault(); // Stop standard HTML submission

                            const submitBtn = document.getElementById('submitBtn');
                            const progressWrapper = document.getElementById('progressWrapper');
                            const progressBar = document.getElementById('progressBar');
                            const progressText = document.getElementById('progressText');

                            // UI Updates
                            submitBtn.disabled = true;
                            submitBtn.innerText = 'Uploading... Please wait';
                            progressWrapper.style.display = 'block';

                            const formData = new FormData(form);
                            const xhr = new XMLHttpRequest();

                            xhr.open('POST', window.location.pathname, true);

                            // Track upload progress
                            xhr.upload.addEventListener('progress', function(e) {
                                if (e.lengthComputable) {
                                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                                    progressBar.style.width = percentComplete + '%';
                                    progressText.innerText = percentComplete + '%';
                                }
                            });

                            // Handle completion
                            xhr.onload = function() {
                                if (xhr.status === 200) {
                                    // Overwrite the current page with the server's success page
                                    document.open();
                                    document.write(xhr.responseText);
                                    document.close();
                                } else {
                                    alert('Error: File may be too large or the server timed out.');
                                    submitBtn.disabled = false;
                                    submitBtn.innerText = 'Save (Burn on Next Read)';
                                    progressWrapper.style.display = 'none';
                                }
                            };

                            xhr.onerror = function() {
                                alert('Network error. Connection was lost.');
                                submitBtn.disabled = false;
                                submitBtn.innerText = 'Save (Burn on Next Read)';
                                progressWrapper.style.display = 'none';
                            };

                            xhr.send(formData);
                        });
                    }
                </script>
            {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    if path.startswith('download/'):
        return "Invalid path", 400

    if not path:
        return render_template_string(HTML_TEMPLATE, path='', paste_data=None, status='home')

    if request.method == 'POST':
        content = request.form.get('content', '')
        file = request.files.get('file_upload')

        file_name = None
        file_token = None

        if file and file.filename:
            file_name = file.filename
            file_token = str(uuid.uuid4())
            filepath = os.path.join(UPLOAD_FOLDER, file_token)
            file.save(filepath)

        if content.strip() or file_name:
            db[path] = {
                'content': content,
                'file_name': file_name,
                'file_token': file_token
            }
            return render_template_string(HTML_TEMPLATE, path=path, paste_data=db[path], status='saved')

    if path in db:
        paste_data = db.pop(path)

        if paste_data.get('file_token'):
            pending_downloads[paste_data['file_token']] = {
                'file_name': paste_data['file_name'],
                'filepath': os.path.join(UPLOAD_FOLDER, paste_data['file_token'])
            }

        return render_template_string(HTML_TEMPLATE, path=path, paste_data=paste_data, status='read')
    else:
        return render_template_string(HTML_TEMPLATE, path=path, paste_data=None, status='new')

@app.route('/download/<token>')
def download_file(token):
    if token not in pending_downloads:
        return "File has already been burned, does not exist, or link is invalid.", 404

    file_info = pending_downloads.pop(token)
    filepath = file_info['filepath']

    def generate_and_delete():
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    yield chunk
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    return Response(
        generate_and_delete(),
        headers={'Content-Disposition': f'attachment; filename="{file_info["file_name"]}"'}
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
