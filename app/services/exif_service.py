"""
EXIF extraction and categorization service.
All image processing logic lives here.
"""

import io
import logging
from typing import Any, Dict, List

from PIL import Image
from PIL.ExifTags import TAGS

from app.core.exceptions import ExifProcessingError, NoExifDataError

logger = logging.getLogger(__name__)

# Category definitions: maps category names to known EXIF tags
CATEGORY_MAP: Dict[str, List[str]] = {
    "Camera & Device": [
        "Make", "Model", "Software", "Artist", "Copyright",
        "ImageDescription", "BodySerialNumber", "LensSerialNumber",
        "LensMake", "LensModel",
    ],
    "Date & Time": [
        "DateTime", "DateTimeOriginal", "DateTimeDigitized",
        "OffsetTime", "OffsetTimeOriginal", "OffsetTimeDigitized",
        "SubsecTime", "SubsecTimeOriginal", "SubsecTimeDigitized",
    ],
    "Image Dimensions": [
        "ImageWidth", "ImageLength", "ExifImageWidth", "ExifImageHeight",
        "XResolution", "YResolution", "ResolutionUnit",
        "PixelXDimension", "PixelYDimension",
    ],
    "Camera Settings": [
        "ExposureTime", "FNumber", "ISOSpeedRatings",
        "ShutterSpeedValue", "ApertureValue", "BrightnessValue",
        "ExposureBiasValue", "MaxApertureValue", "MeteringMode",
        "LightSource", "Flash", "FocalLength", "FocalLengthIn35mmFilm",
        "ExposureProgram", "SceneCaptureType", "WhiteBalance",
        "DigitalZoomRatio", "Contrast", "Saturation", "Sharpness",
        "GainControl", "SubjectDistanceRange",
    ],
    "GPS & Location": [
        "GPSLatitude", "GPSLongitude", "GPSAltitude",
        "GPSLatitudeRef", "GPSLongitudeRef", "GPSAltitudeRef",
        "GPSProcessingMethod", "GPSMapDatum", "GPSTimeStamp",
        "GPSDateStamp", "GPSImgDirection",
    ],
}


def extract_exif_data(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extract raw EXIF data from image bytes.

    Args:
        image_bytes: Raw bytes of the image file.

    Returns:
        Dictionary mapping EXIF tag names to their values.

    Raises:
        NoExifDataError: If the image has no EXIF data.
        ExifProcessingError: If the image cannot be processed.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        exif_data = image._getexif()

        if not exif_data:
            raise NoExifDataError()

        result: Dict[str, Any] = {}
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            result[tag_name] = value

        logger.info("Extracted %d EXIF tags", len(result))
        return result

    except NoExifDataError:
        raise
    except Exception as e:
        logger.error("Failed to extract EXIF data: %s", e)
        raise ExifProcessingError(str(e))


def format_exif_value(value: Any) -> str:
    """
    Format an EXIF value for display.
    Handles bytes, tuples, lists, rationals, and other types.
    """
    if isinstance(value, bytes):
        try:
            decoded = value.decode("utf-8", errors="replace")
            # Strip null bytes common in EXIF byte strings
            return decoded.strip("\x00").strip()
        except Exception:
            return str(value)
    elif isinstance(value, (tuple, list)):
        # Handle GPS coordinates which use IFDRational tuples
        parts = []
        for v in value:
            if hasattr(v, "numerator") and hasattr(v, "denominator"):
                if v.denominator != 0:
                    parts.append(f"{float(v):.6f}")
                else:
                    parts.append(str(v))
            else:
                parts.append(str(v))
        return ", ".join(parts)
    elif hasattr(value, "numerator") and hasattr(value, "denominator"):
        # IFDRational
        if value.denominator != 0:
            return f"{float(value):.4f}"
        return str(value)
    elif hasattr(value, "real") and hasattr(value, "imag"):
        # Complex number
        return f"{value.real:.4f}"
    else:
        return str(value)


def categorize_exif(exif_dict: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Group EXIF data into logical categories.

    Args:
        exif_dict: Raw EXIF tag-name -> value dictionary.

    Returns:
        Dictionary of category name -> list of {tag, value} dicts.
    """
    result: Dict[str, List[Dict[str, str]]] = {cat: [] for cat in CATEGORY_MAP}
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

    # Remove empty categories
    return {k: v for k, v in result.items() if v}
