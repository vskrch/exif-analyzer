"""
EXIF extraction and categorization service.
All image processing logic lives here.
"""

import io
import logging
from typing import Any

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS

from app.config import get_settings
from app.core.exceptions import ExifProcessingError, NoExifDataError

logger = logging.getLogger(__name__)

# Category definitions: maps category names to known EXIF tags
CATEGORY_MAP: dict[str, list[str]] = {
    "Camera & Device": [
        "Make",
        "Model",
        "Software",
        "Artist",
        "Copyright",
        "ImageDescription",
        "BodySerialNumber",
        "LensSerialNumber",
        "LensMake",
        "LensModel",
    ],
    "Date & Time": [
        "DateTime",
        "DateTimeOriginal",
        "DateTimeDigitized",
        "OffsetTime",
        "OffsetTimeOriginal",
        "OffsetTimeDigitized",
        "SubsecTime",
        "SubsecTimeOriginal",
        "SubsecTimeDigitized",
    ],
    "Image Dimensions": [
        "ImageWidth",
        "ImageLength",
        "ExifImageWidth",
        "ExifImageHeight",
        "XResolution",
        "YResolution",
        "ResolutionUnit",
        "PixelXDimension",
        "PixelYDimension",
    ],
    "Camera Settings": [
        "ExposureTime",
        "FNumber",
        "ISOSpeedRatings",
        "ShutterSpeedValue",
        "ApertureValue",
        "BrightnessValue",
        "ExposureBiasValue",
        "MaxApertureValue",
        "MeteringMode",
        "LightSource",
        "Flash",
        "FocalLength",
        "FocalLengthIn35mmFilm",
        "ExposureProgram",
        "SceneCaptureType",
        "WhiteBalance",
        "DigitalZoomRatio",
        "Contrast",
        "Saturation",
        "Sharpness",
        "GainControl",
        "SubjectDistanceRange",
    ],
    "GPS & Location": [
        "GPSLatitude",
        "GPSLongitude",
        "GPSAltitude",
        "GPSLatitudeRef",
        "GPSLongitudeRef",
        "GPSAltitudeRef",
        "GPSProcessingMethod",
        "GPSMapDatum",
        "GPSTimeStamp",
        "GPSDateStamp",
        "GPSImgDirection",
    ],
}


def _configure_pillow_limits() -> None:
    """Apply decompression-bomb protection from settings."""
    settings = get_settings()
    Image.MAX_IMAGE_PIXELS = settings.max_image_pixels


def extract_exif_data(image_bytes: bytes) -> dict[str, Any]:
    """
    Extract raw EXIF data from image bytes.

    Raises:
        NoExifDataError: If the image has no EXIF data.
        ExifProcessingError: If the image cannot be processed.
    """
    _configure_pillow_limits()

    try:
        # Verify integrity before full decode
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.verify()

        with Image.open(io.BytesIO(image_bytes)) as image:
            exif = image.getexif()

        if not exif:
            raise NoExifDataError()

        result: dict[str, Any] = {}
        for tag_id, value in exif.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            result[tag_name] = value

        logger.info("Extracted %d EXIF tags", len(result))
        return result

    except NoExifDataError:
        raise
    except UnidentifiedImageError as e:
        logger.error("Unidentified image format: %s", e)
        raise ExifProcessingError("The image could not be processed.") from e
    except Image.DecompressionBombError as e:
        logger.error("Image exceeds pixel limit: %s", e)
        raise ExifProcessingError("Image dimensions exceed the allowed limit.") from e
    except Exception as e:
        logger.error("Failed to extract EXIF data: %s", e)
        raise ExifProcessingError("The image could not be processed.") from e


def format_exif_value(value: Any) -> str:
    """Format an EXIF value for display."""
    if isinstance(value, bytes):
        try:
            decoded = value.decode("utf-8", errors="replace")
            return decoded.strip("\x00").strip()
        except Exception:
            return str(value)
    elif isinstance(value, tuple | list):
        parts = []
        for v in value:
            if hasattr(v, "numerator") and hasattr(v, "denominator"):
                if v.denominator != 0:
                    f = float(v)
                    parts.append(str(int(f)) if f == int(f) else f"{f:.6f}")
                else:
                    parts.append(str(v))
            else:
                parts.append(str(v))
        return ", ".join(parts)
    elif type(value).__name__ == "IFDRational":
        if value.denominator != 0:
            f = float(value)
            return str(int(f)) if f == int(f) else f"{f:.4f}"
        return str(value)
    elif isinstance(value, complex):
        return f"{value.real:.4f}"
    else:
        return str(value)


def categorize_exif(exif_dict: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    """Group EXIF data into logical categories."""
    result: dict[str, list[dict[str, str]]] = {cat: [] for cat in CATEGORY_MAP}
    result["Other"] = []

    for tag, value in exif_dict.items():
        formatted = format_exif_value(value)
        placed = False
        for cat, tags_list in CATEGORY_MAP.items():
            if tag in tags_list:
                result[cat].append({"tag": tag, "value": formatted})
                placed = True
                break
        if not placed:
            result["Other"].append({"tag": tag, "value": formatted})

    return {k: v for k, v in result.items() if v}
