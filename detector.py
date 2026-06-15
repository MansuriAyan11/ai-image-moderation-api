import time
from pathlib import Path
from nudenet import NudeDetector


# Model ko ek hi baar load karna hai
detector = NudeDetector()


# Dating app ke liye unsafe labels
UNSAFE_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED"
}


# Threshold means minimum confidence required to mark image unsafe
THRESHOLD = 0.50


def detect_image(image_path: str) -> dict:
    """
    This function takes image path,
    scans image using NudeNet,
    and returns moderation result as dictionary.
    """

    start_time = time.time()

    path = Path(image_path)

    if not path.exists():
        return {
            "status": "error",
            "message": "Image file not found",
            "processing_time": round(time.time() - start_time, 4)
        }

    try:
        detections = detector.detect(str(path))

        detected_labels = []
        highest_confidence = 0.0

        for item in detections:
            label = item.get("class")
            confidence = item.get("score", 0)

            if label in UNSAFE_LABELS and confidence >= THRESHOLD:
                detected_labels.append(label)
                highest_confidence = max(highest_confidence, confidence)

        processing_time = round(time.time() - start_time, 4)

        if detected_labels:
            return {
                "status": "unsafe",
                "confidence": round(highest_confidence, 4),
                "detected_labels": detected_labels,
                "processing_time": processing_time
            }

        return {
            "status": "safe",
            "confidence": round(1 - highest_confidence, 4),
            "detected_labels": [],
            "processing_time": processing_time
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "processing_time": round(time.time() - start_time, 4)
        }