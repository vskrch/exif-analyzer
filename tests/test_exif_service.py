"""
Unit tests for EXIF extraction and categorization service.
"""

import io

import pytest
from PIL import Image

from app.core.exceptions import ExifProcessingError, NoExifDataError
from app.services.exif_service import (
    categorize_exif,
    extract_exif_data,
    format_exif_value,
)


class TestExtractExifData:
    """Tests for extract_exif_data function."""

    def test_extract_from_jpeg_with_exif(self) -> None:
        import struct

        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()

        # Build minimal EXIF with Make tag
        exif_header = b"Exif\x00\x00"
        tiff_header = b"II" + struct.pack("<HI", 42, 8)
        num_entries = struct.pack("<H", 1)
        make_val = b"TestCamera\x00"
        make_offset = 8 + 2 + 1 * 12 + 4
        entry_make = struct.pack("<HHII", 0x010F, 2, 11, make_offset)
        next_ifd = struct.pack("<I", 0)
        tiff_data = tiff_header + num_entries + entry_make + next_ifd + make_val
        full_exif = exif_header + tiff_data

        img.save(buf, format="JPEG", exif=full_exif)
        buf.seek(0)
        data = buf.read()

        result = extract_exif_data(data)
        assert isinstance(result, dict)
        assert "Make" in result

    def test_extract_from_jpeg_without_exif_raises(self) -> None:
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        data = buf.read()

        with pytest.raises(NoExifDataError):
            extract_exif_data(data)

    def test_extract_from_image_without_exif_raises(self) -> None:
        img = Image.new("RGB", (100, 100), color="green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        data = buf.read()

        with pytest.raises(NoExifDataError):
            extract_exif_data(data)

    def test_extract_invalid_bytes_raises(self) -> None:
        with pytest.raises((NoExifDataError, ExifProcessingError)):
            extract_exif_data(b"not an image at all")


class TestFormatExifValue:
    """Tests for format_exif_value function."""

    def test_format_string(self) -> None:
        assert format_exif_value("hello") == "hello"

    def test_format_integer(self) -> None:
        assert format_exif_value(42) == "42"

    def test_format_float(self) -> None:
        assert format_exif_value(3.14) == "3.14"

    def test_format_bytes(self) -> None:
        result = format_exif_value(b"test\x00")
        assert result == "test"

    def test_format_tuple(self) -> None:
        result = format_exif_value((1, 2, 3))
        assert result == "1, 2, 3"

    def test_format_list(self) -> None:
        result = format_exif_value(["a", "b", "c"])
        assert result == "a, b, c"

    def test_format_none(self) -> None:
        result = format_exif_value(None)
        assert result == "None"


class TestCategorizeExif:
    """Tests for categorize_exif function."""

    def test_categorize_known_tags(self) -> None:
        exif_dict = {
            "Make": "Canon",
            "Model": "EOS R5",
            "DateTime": "2024:01:15 10:30:00",
            "ExposureTime": (1, 250),
            "FNumber": (28, 10),
        }
        result = categorize_exif(exif_dict)
        assert "Camera & Device" in result
        assert "Date & Time" in result
        assert "Camera Settings" in result

    def test_categorize_unknown_tag_goes_to_other(self) -> None:
        exif_dict = {"CustomUnknownTag": "value"}
        result = categorize_exif(exif_dict)
        assert "Other" in result
        assert result["Other"][0]["tag"] == "CustomUnknownTag"

    def test_categorize_empty_dict(self) -> None:
        result = categorize_exif({})
        assert result == {}

    def test_categorize_removes_empty_categories(self) -> None:
        exif_dict = {"Make": "Nikon"}
        result = categorize_exif(exif_dict)
        # Should have "Camera & Device" but not empty categories
        assert "Camera & Device" in result
        assert len(result) == 1

    def test_categorize_gps_tags(self) -> None:
        exif_dict = {
            "GPSLatitude": ((37, 1), (46, 1), (36, 1)),
            "GPSLongitude": ((122, 1), (25, 1), (30, 1)),
        }
        result = categorize_exif(exif_dict)
        assert "GPS & Location" in result
        assert len(result["GPS & Location"]) == 2
