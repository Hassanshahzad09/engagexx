"""
Lightweight screenshot / proof image analysis for EngageX.

This module is intentionally dependency-light. It uses Pillow, which is already
needed by Django ImageField. It does not use OCR because OCR can be slow and
fragile in local development.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List


def _safe_seek(file_obj, position: int = 0) -> None:
    try:
        file_obj.seek(position)
    except Exception:
        pass


def _variance(values) -> float:
    values = list(values)
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def analyze_proof_image_quality(uploaded_file=None, image_path: str | None = None) -> Dict[str, Any]:
    """
    Returns a simple quality/fake-risk analysis for a proof screenshot.

    It checks:
    - Can Pillow open the file as an image?
    - Image dimensions are not too small.
    - File size is not suspiciously tiny.
    - Image is not mostly blank / one-color.
    - Image is not extremely dark or over-bright.
    - Image is not extremely blurry.

    The output is safe to store inside suspicious_signals / API responses.
    """
    result: Dict[str, Any] = {
        "image_quality_score": 0,
        "image_quality_label": "No image provided",
        "image_signals": [],
        "image_width": 0,
        "image_height": 0,
        "image_format": "",
        "image_file_size_kb": 0,
    }

    if not uploaded_file and not image_path:
        return result

    try:
        from PIL import Image, ImageFilter, ImageStat
    except Exception as exc:
        result["image_quality_label"] = "Image analysis unavailable"
        result["image_signals"].append({
            "feature": "image_library",
            "layer": "Layer 1 — Screenshot Image Check",
            "reason": f"Image library could not run: {exc}",
            "value": "Pillow unavailable",
            "impact": 0,
        })
        return result

    try:
        if uploaded_file:
            _safe_seek(uploaded_file, 0)
            img = Image.open(uploaded_file)
            file_size = getattr(uploaded_file, "size", 0) or 0
        else:
            img = Image.open(image_path)
            try:
                import os
                file_size = os.path.getsize(image_path)
            except Exception:
                file_size = 0

        img.verify()

        if uploaded_file:
            _safe_seek(uploaded_file, 0)
            img = Image.open(uploaded_file)
        else:
            img = Image.open(image_path)

        width, height = img.size
        result["image_width"] = int(width)
        result["image_height"] = int(height)
        result["image_format"] = (img.format or "").upper()
        result["image_file_size_kb"] = round(file_size / 1024, 2) if file_size else 0

        risk_score = 0
        signals: List[Dict[str, Any]] = []

        def add_signal(feature: str, reason: str, value: Any, impact: int) -> None:
            nonlocal risk_score
            risk_score += impact
            signals.append({
                "feature": feature,
                "layer": "Layer 1 — Screenshot Image Check",
                "reason": reason,
                "value": value,
                "impact": impact,
            })

        if width < 500 or height < 400:
            add_signal(
                "image_dimensions",
                "Screenshot resolution is too small to verify clearly",
                f"{width}x{height}",
                20,
            )

        if file_size and file_size < 20 * 1024:
            add_signal(
                "image_file_size",
                "Screenshot file size is unusually small",
                f"{round(file_size / 1024, 2)} KB",
                15,
            )

        # Downscale for cheap analysis.
        analysis_img = img.convert("RGB")
        analysis_img.thumbnail((320, 320))
        gray = analysis_img.convert("L")

        stat = ImageStat.Stat(gray)
        brightness = float(stat.mean[0]) if stat.mean else 0.0
        contrast = float(stat.stddev[0]) if stat.stddev else 0.0

        if brightness < 25:
            add_signal("image_brightness", "Screenshot is too dark", round(brightness, 2), 15)
        elif brightness > 245:
            add_signal("image_brightness", "Screenshot is too bright / washed out", round(brightness, 2), 15)

        if contrast < 8:
            add_signal("image_contrast", "Screenshot looks almost blank or one-color", round(contrast, 2), 20)

        # Edge variance approximation for blur. Higher = sharper.
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_values = list(edges.getdata())
        edge_variance = _variance(edge_values)
        if edge_variance < 35:
            add_signal("image_blur_score", "Screenshot appears very blurry", round(edge_variance, 2), 15)

        # Very low color diversity often means blank screen / fake placeholder.
        small = analysis_img.resize((64, 64))
        unique_colors = len(set(small.getdata()))
        if unique_colors < 25:
            add_signal("image_color_diversity", "Screenshot has very low visual detail", unique_colors, 15)

        risk_score = min(int(risk_score), 100)
        result["image_quality_score"] = risk_score
        result["image_signals"] = signals

        if risk_score >= 60:
            result["image_quality_label"] = "High image risk"
        elif risk_score >= 30:
            result["image_quality_label"] = "Needs manual review"
        else:
            result["image_quality_label"] = "Image looks readable"

        return result

    except Exception as exc:
        result["image_quality_score"] = 80
        result["image_quality_label"] = "Invalid image file"
        result["image_signals"] = [{
            "feature": "image_file_validity",
            "layer": "Layer 1 — Screenshot Image Check",
            "reason": "Uploaded proof could not be opened as a valid image",
            "value": str(exc),
            "impact": 80,
        }]
        return result
    finally:
        if uploaded_file:
            _safe_seek(uploaded_file, 0)
