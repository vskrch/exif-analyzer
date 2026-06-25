# EXIF Analyzer

A beautiful web application for analyzing EXIF metadata from images. Built with FastAPI and a modern responsive GUI.

## Features

- 📤 Drag & drop or click to upload images
- 📊 Categorized EXIF data display (Camera, Date, GPS, Settings, etc.)
- 🎨 Beautiful gradient UI with collapsible categories
- 📱 Responsive design for mobile and desktop
- ⚡ Fast API backend with async processing

## Installation

```bash
# Clone or navigate to the project
cd exif-analyzer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python main.py
```

Then open your browser to: **http://localhost:8000**

## API Endpoints

- `GET /` - Web GUI
- `POST /analyze` - Upload and analyze image EXIF data
- `GET /health` - Health check

## Project Structure

```
exif-analyzer/
├── main.py           # FastAPI application
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## How It Works

1. Upload an image (JPG, PNG, TIFF, etc.) via drag & drop or file picker
2. The app extracts EXIF metadata using PIL/Pillow
3. Data is categorized into logical groups:
   - Camera & Device info
   - Date & Time stamps
   - Image dimensions
   - Camera settings (aperture, ISO, etc.)
   - GPS coordinates (if available)
   - Other metadata
4. View results in an organized, collapsible interface

## Supported Image Formats

- JPEG/JPG
- PNG (limited EXIF support)
- TIFF
- WebP
- HEIC/HEIF (with Pillow 10.1+)

## License

MIT
