"""
EXIF Analyzer Web App
Upload an image and view all its EXIF metadata in a beautiful GUI.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
from PIL.ExifTags import TAGS
import io
import os
from typing import Dict, Any, List

app = FastAPI(title="EXIF Analyzer", description="Analyze EXIF data from images")

templates = Jinja2Templates(directory="templates")


def get_exif_data(image_path_or_bytes) -> Dict[str, Any]:
    """Extract EXIF data from an image file or bytes."""
    try:
        image = Image.open(image_path_or_bytes)
        exif_data = image._getexif()

        if not exif_data:
            return {"error": "No EXIF data found in this image."}

        exif_dict = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_dict[tag] = value

        return exif_dict
    except Exception as e:
        return {"error": f"Error reading EXIF data: {str(e)}"}


def format_exif_value(value) -> str:
    """Format EXIF values for display."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return str(value)
    elif isinstance(value, (tuple, list)):
        return ", ".join(str(v) for v in value)
    else:
        return str(value)


def categorize_exif(exif_dict: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """Categorize EXIF data into logical groups."""
    categories = {
        "Camera & Device": ["Make", "Model", "Software", "Artist", "Copyright", "ImageDescription"],
        "Date & Time": ["DateTime", "DateTimeOriginal", "DateTimeDigitized", "OffsetTime", "OffsetTimeOriginal", "OffsetTimeDigitized"],
        "Image Dimensions": ["ImageWidth", "ImageLength", "ExifImageWidth", "ExifImageHeight", "XResolution", "YResolution", "ResolutionUnit"],
        "Camera Settings": ["ExposureTime", "FNumber", "ISOSpeedRatings", "ShutterSpeedValue", "ApertureValue",
                            "BrightnessValue", "ExposureBiasValue", "MaxApertureValue", "MeteringMode",
                            "LightSource", "Flash", "FocalLength", "FocalLengthIn35mmFilm"],
        "GPS & Location": ["GPSLatitude", "GPSLongitude", "GPSAltitude", "GPSLatitudeRef", "GPSLongitudeRef",
                           "GPSAltitudeRef", "GPSProcessingMethod", "GPSMapDatum"],
        "Other": []
    }

    result = {cat: [] for cat in categories}

    for tag, value in exif_dict.items():
        formatted = format_exif_value(value)
        placed = False
        for cat, tags_list in categories.items():
            if tag in tags_list:
                result[cat].append({"tag": tag, "value": formatted})
                placed = True
                break
        if not placed:
            result["Other"].append({"tag": tag, "value": formatted})

    # Remove empty categories
    return {k: v for k, v in result.items() if v}


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main GUI page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EXIF Analyzer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .upload-section {
            padding: 40px;
            text-align: center;
            border-bottom: 1px solid #e0e0e0;
        }
        .drop-zone {
            border: 3px dashed #667eea;
            border-radius: 12px;
            padding: 60px 20px;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.3s ease;
            max-width: 600px;
            margin: 0 auto;
        }
        .drop-zone:hover, .drop-zone.dragover {
            background: #eef0ff;
            border-color: #764ba2;
            transform: translateY(-2px);
        }
        .drop-zone-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        .drop-zone h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        .drop-zone p {
            color: #666;
            margin-bottom: 20px;
        }
        #fileInput {
            display: none;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .preview-section {
            padding: 30px 40px;
            display: none;
        }
        .preview-section.active {
            display: block;
        }
        .preview-container {
            display: flex;
            gap: 30px;
            align-items: flex-start;
            flex-wrap: wrap;
        }
        .image-preview {
            flex: 0 0 300px;
        }
        .image-preview img {
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .image-info {
            flex: 1;
            min-width: 300px;
        }
        .info-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }
        .info-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .info-row:last-child {
            border-bottom: none;
        }
        .info-label {
            font-weight: 600;
            color: #555;
        }
        .info-value {
            color: #333;
            text-align: right;
            max-width: 60%;
            word-break: break-word;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #667eea;
            font-size: 1.2em;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 40px;
            display: none;
        }
        .error.active {
            display: block;
        }
        .category-toggle {
            cursor: pointer;
            user-select: none;
        }
        .category-content {
            display: none;
        }
        .category-content.open {
            display: block;
        }
        .no-data {
            text-align: center;
            padding: 40px;
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📸 EXIF Analyzer</h1>
            <p>Upload an image to view its EXIF metadata</p>
        </div>

        <div class="upload-section">
            <div class="drop-zone" id="dropZone">
                <div class="drop-zone-icon">📷</div>
                <h3>Drag & Drop your image here</h3>
                <p>or click to browse</p>
                <input type="file" id="fileInput" accept="image/*">
                <button class="btn" onclick="document.getElementById('fileInput').click()">
                    Choose Image
                </button>
            </div>
        </div>

        <div class="error" id="errorBox"></div>

        <div class="preview-section" id="previewSection">
            <div class="preview-container">
                <div class="image-preview">
                    <img id="imagePreview" src="" alt="Preview">
                </div>
                <div class="image-info" id="exifData">
                    <div class="loading">Analyzing EXIF data...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const previewSection = document.getElementById('previewSection');
        const imagePreview = document.getElementById('imagePreview');
        const exifData = document.getElementById('exifData');
        const errorBox = document.getElementById('errorBox');

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        async function handleFile(file) {
            if (!file.type.startsWith('image/')) {
                showError('Please upload an image file.');
                return;
            }

            hideError();
            previewSection.classList.add('active');
            imagePreview.src = URL.createObjectURL(file);
            exifData.innerHTML = '<div class="loading">Analyzing EXIF data...</div>';

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    displayExifData(result);
                } else {
                    showError(result.detail || 'Error analyzing image');
                }
            } catch (err) {
                showError('Error uploading file: ' + err.message);
            }
        }

        function displayExifData(data) {
            if (data.error) {
                exifData.innerHTML = `<div class="no-data">${data.error}</div>`;
                return;
            }

            let html = '';
            for (const [category, items] of Object.entries(data.categorized)) {
                html += `
                    <div class="info-card">
                        <h3 class="category-toggle" onclick="toggleCategory(this)">
                            ${category} (${items.length}) ▾
                        </h3>
                        <div class="category-content open">
                            ${items.map(item => `
                                <div class="info-row">
                                    <span class="info-label">${item.tag}</span>
                                    <span class="info-value">${item.value}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            exifData.innerHTML = html;
        }

        function toggleCategory(header) {
            const content = header.nextElementSibling;
            content.classList.toggle('open');
            header.innerHTML = header.innerHTML.includes('▾')
                ? header.innerHTML.replace('▾', '▸')
                : header.innerHTML.replace('▸', '▾');
        }

        function showError(message) {
            errorBox.textContent = message;
            errorBox.classList.add('active');
        }

        function hideError() {
            errorBox.classList.remove('active');
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze EXIF data from uploaded image."""
    try:
        contents = await file.read()
        image_stream = io.BytesIO(contents)

        # Reset stream position
        image_stream.seek(0)

        exif_dict = get_exif_data(image_stream)

        if "error" in exif_dict:
            return JSONResponse(status_code=400, content={"detail": exif_dict["error"]})

        categorized = categorize_exif(exif_dict)

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "total_tags": len(exif_dict),
            "categorized": categorized
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "EXIF Analyzer"}


if __name__ == "__main__":
    import uvicorn
    print("Starting EXIF Analyzer...")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
