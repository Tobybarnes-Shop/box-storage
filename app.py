"""
Box Storage - QR Code Inventory System
A simple web app to manage box contents via QR codes.
"""

import os
import io
import base64
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import qrcode

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Configuration - use /data in production (Fly.io volume), local in dev
DATA_DIR = Path(os.environ.get('DATA_PATH', Path(__file__).parent))
BOXES_DIR = DATA_DIR / "boxes"
PHOTOS_DIR = DATA_DIR / "photos"
BOXES_DIR.mkdir(exist_ok=True)
PHOTOS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_box_photos(box_id):
    """Get all photos for a box."""
    box_photos_dir = PHOTOS_DIR / box_id
    if not box_photos_dir.exists():
        return []
    photos = []
    for f in sorted(box_photos_dir.glob('*')):
        if f.suffix.lower().lstrip('.') in ALLOWED_EXTENSIONS:
            photos.append(f.name)
    return photos

def get_all_boxes():
    """Get all box files sorted by modification time."""
    boxes = []
    for f in BOXES_DIR.glob("*.md"):
        box_id = f.stem
        content = f.read_text()
        # Extract title from first line if it's a heading
        lines = content.strip().split('\n')
        title = lines[0].lstrip('# ').strip() if lines else box_id
        boxes.append({
            'id': box_id,
            'title': title,
            'modified': datetime.fromtimestamp(f.stat().st_mtime)
        })
    return sorted(boxes, key=lambda x: x['modified'], reverse=True)

def get_box_content(box_id):
    """Read box markdown file."""
    box_file = BOXES_DIR / f"{box_id}.md"
    if box_file.exists():
        return box_file.read_text()
    return None

def save_box_content(box_id, content):
    """Save box markdown file."""
    box_file = BOXES_DIR / f"{box_id}.md"
    box_file.write_text(content)

def generate_box_id():
    """Generate a new unique box ID."""
    existing = {f.stem for f in BOXES_DIR.glob("*.md")}
    counter = 1
    while f"box-{counter:03d}" in existing:
        counter += 1
    return f"box-{counter:03d}"

def generate_qr_code(url):
    """Generate QR code as base64 image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()

@app.route('/')
def index():
    """Home page - list all boxes."""
    boxes = get_all_boxes()
    return render_template('index.html', boxes=boxes)

@app.route('/box/<box_id>')
def view_box(box_id):
    """View a single box's contents."""
    content = get_box_content(box_id)
    if content is None:
        # New box - create with template
        content = f"# {box_id}\n\n## Contents\n\n- \n\n## Location\n\n\n## Notes\n\n"
        save_box_content(box_id, content)

    # Generate QR code URL
    host = request.host_url.rstrip('/')
    qr_url = f"{host}/box/{box_id}"
    qr_base64 = generate_qr_code(qr_url)

    # Get photos for this box
    photos = get_box_photos(box_id)

    return render_template('box.html', box_id=box_id, content=content, qr_base64=qr_base64, qr_url=qr_url, photos=photos)

@app.route('/box/<box_id>/edit', methods=['GET', 'POST'])
def edit_box(box_id):
    """Edit a box's contents."""
    if request.method == 'POST':
        content = request.form.get('content', '')
        save_box_content(box_id, content)
        return redirect(url_for('view_box', box_id=box_id))

    content = get_box_content(box_id)
    if content is None:
        content = f"# {box_id}\n\n## Contents\n\n- \n\n## Location\n\n\n## Notes\n\n"

    return render_template('edit.html', box_id=box_id, content=content)

@app.route('/box/<box_id>/qr')
def download_qr(box_id):
    """Download QR code as PNG."""
    host = request.host_url.rstrip('/')
    qr_url = f"{host}/box/{box_id}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png', download_name=f'{box_id}-qr.png')

@app.route('/new')
def new_box():
    """Create a new box and redirect to edit."""
    box_id = generate_box_id()
    return redirect(url_for('edit_box', box_id=box_id))

@app.route('/search')
def search():
    """Search across all boxes."""
    query = request.args.get('q', '').lower()
    results = []

    if query:
        for f in BOXES_DIR.glob("*.md"):
            content = f.read_text()
            if query in content.lower():
                box_id = f.stem
                lines = content.strip().split('\n')
                title = lines[0].lstrip('# ').strip() if lines else box_id
                # Find matching lines for preview
                matching_lines = [l.strip() for l in lines if query in l.lower()][:3]
                results.append({
                    'id': box_id,
                    'title': title,
                    'preview': matching_lines
                })

    return render_template('search.html', query=query, results=results)

@app.route('/box/<box_id>/photos', methods=['POST'])
def upload_photo(box_id):
    """Upload a photo for a box."""
    if 'photo' not in request.files:
        return redirect(url_for('view_box', box_id=box_id))

    file = request.files['photo']
    if file.filename == '':
        return redirect(url_for('view_box', box_id=box_id))

    if file and allowed_file(file.filename):
        # Create box photos directory
        box_photos_dir = PHOTOS_DIR / box_id
        box_photos_dir.mkdir(exist_ok=True)

        # Generate unique filename with timestamp
        ext = file.filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}.{ext}"

        file.save(box_photos_dir / filename)

    return redirect(url_for('view_box', box_id=box_id))

@app.route('/box/<box_id>/photos/<filename>')
def get_photo(box_id, filename):
    """Serve a photo."""
    photo_path = PHOTOS_DIR / box_id / secure_filename(filename)
    if photo_path.exists():
        return send_file(photo_path)
    return "Not found", 404

@app.route('/box/<box_id>/photos/<filename>/delete', methods=['POST'])
def delete_photo(box_id, filename):
    """Delete a photo."""
    photo_path = PHOTOS_DIR / box_id / secure_filename(filename)
    if photo_path.exists():
        photo_path.unlink()
    return redirect(url_for('view_box', box_id=box_id))

@app.route('/box/<box_id>/delete', methods=['POST'])
def delete_box(box_id):
    """Delete a box and its photos."""
    box_file = BOXES_DIR / f"{box_id}.md"
    if box_file.exists():
        box_file.unlink()
    # Also delete photos
    box_photos_dir = PHOTOS_DIR / box_id
    if box_photos_dir.exists():
        for photo in box_photos_dir.glob('*'):
            photo.unlink()
        box_photos_dir.rmdir()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run on all interfaces so it's accessible on local network
    app.run(host='0.0.0.0', port=5000, debug=True)
