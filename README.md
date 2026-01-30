# Box Storage

A simple QR code-based inventory system for tracking what's in your storage boxes.

**Created by Moss Music Software**

## Features

- **QR Codes** - Generate and print QR codes for each box
- **Photo Support** - Add photos of box contents
- **Search** - Find items across all boxes
- **Mobile Friendly** - Works great on phones for scanning and adding photos
- **Markdown Storage** - Box contents stored as simple .md files

## How It Works

1. Create a new box in the app
2. Add contents (text description) and photos
3. Print the QR code and stick it on your physical box
4. Scan the QR code anytime to see what's inside

## Tech Stack

- **Backend**: Python / Flask
- **Storage**: Markdown files + image files
- **Hosting**: Fly.io
- **QR Generation**: qrcode library

## Local Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/box-storage.git
cd box-storage

# Run the start script (creates venv, installs deps, starts server)
./start.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deployment (Fly.io)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy
flyctl deploy
```

The app uses a Fly.io volume for persistent storage of boxes and photos.

## Project Structure

```
box-storage/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container config
├── fly.toml           # Fly.io config
├── start.sh           # Local dev startup script
├── templates/         # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── box.html
│   ├── edit.html
│   └── search.html
├── boxes/             # Markdown files (one per box)
└── photos/            # Photo storage (subdirs per box)
```

## License

MIT
