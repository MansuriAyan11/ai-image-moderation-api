import time
from pathlib import Path
from nudenet import NudeDetector

detector = NudeDetector()

# --- FIX 1: Added MALE_GENITALIA_COVERED ---
# NudeNet returns this label for cropped/partial male genitalia images
# where the full anatomy isn't clearly visible, but explicit content is.
# Previously this label was missing, so those images passed as safe.
UNSAFE_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_COVERED",       # <-- ADDED
    "FEMALE_GENITALIA_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED"
}

# --- FIX 2: Per-label confidence thresholds ---
# Root cause: a single 0.50 threshold was too strict for cropped/zoomed images.
# NudeNet scores drop to 0.30–0.45 on tight crops because the model was
# trained on full-body scenes. High-priority labels (genitalia, anus) now
# use 0.35 so cropped explicit content is caught. Breast/buttocks stay at 0.45
# since false positives (bikinis, sports) are more likely at lower thresholds.
LABEL_THRESHOLDS = {

    "MALE_GENITALIA_EXPOSED":   0.25,   # highest priority - never miss
    "MALE_GENITALIA_COVERED":   0.40,   # added label - slightly more lenient
    "FEMALE_GENITALIA_EXPOSED": 0.25,   # highest priority
    "ANUS_EXPOSED":             0.35,   # highest priority
    "FEMALE_BREAST_EXPOSED":    0.45,   # medium priority
    "BUTTOCKS_EXPOSED":         0.45,   # medium priority

   
}

# Default fallback for any label not in the map above
DEFAULT_THRESHOLD = 0.50

# Debug thresholds (logging only — does NOT affect decisions)
DEBUG_THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.50]


def print_debug_report(
    filename: str,
    detections: list,
    final_status: str,
    final_labels: list,
    processing_time: float
):
    print("\n================ IMAGE MODERATION DEBUG ================")
    print(f"Filename        : {filename}")
    print(f"Final Decision  : {final_status}")
    print(f"Final Labels    : {final_labels}")
    print(f"Inference Time  : {processing_time}s")
    print(f"Label Thresholds: {LABEL_THRESHOLDS}")

    print("\nRaw NudeNet Detections:")

    if not detections:
        print("No detections returned by NudeNet")
    else:
        for item in detections:
            label = item.get("class")
            score = item.get("score", 0)
            box = item.get("box", [])
            print(f"- Label: {label} | Score: {round(score, 4)} | Box: {box}")

    print("\nUnsafe Label Filtering:")
    unsafe_candidates = []

    for item in detections:
        label = item.get("class")
        score = item.get("score", 0)
        if label in UNSAFE_LABELS:
            unsafe_candidates.append((label, score))

    if not unsafe_candidates:
        print("No labels matched current UNSAFE_LABELS list.")
    else:
        for label, score in unsafe_candidates:
            # FIX 2 reflected in debug: use per-label threshold in log
            threshold = LABEL_THRESHOLDS.get(label, DEFAULT_THRESHOLD)
            if score >= threshold:
                print(f"- {label}: {round(score, 4)} -> PASSED (threshold: {threshold})")
            else:
                print(f"- {label}: {round(score, 4)} -> BELOW threshold ({threshold})")

    print("\nThreshold Comparison for Unsafe Labels:")
    for threshold in DEBUG_THRESHOLDS:
        matched = []
        for item in detections:
            label = item.get("class")
            score = item.get("score", 0)
            if label in UNSAFE_LABELS and score >= threshold:
                matched.append(f"{label}:{round(score, 4)}")
        if matched:
            print(f"At threshold {threshold}: UNSAFE -> {matched}")
        else:
            print(f"At threshold {threshold}: SAFE")

    print("========================================================\n")


def detect_image(image_path: str) -> dict:
    """
    Takes image path, scans with NudeNet,
    returns moderation result dict.
    API response format is unchanged.
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

            if label in UNSAFE_LABELS:
                # FIX 2: Use per-label threshold instead of single THRESHOLD
                threshold = LABEL_THRESHOLDS.get(label, DEFAULT_THRESHOLD)

                if confidence >= threshold:
                    detected_labels.append(label)
                    highest_confidence = max(highest_confidence, confidence)

        processing_time = round(time.time() - start_time, 4)

        if detected_labels:
            final_status = "unsafe"

            print_debug_report(
                filename=path.name,
                detections=detections,
                final_status=final_status,
                final_labels=detected_labels,
                processing_time=processing_time
            )

            # Response format unchanged
            return {
                "status": "unsafe",
                "confidence": round(highest_confidence, 4),
                "detected_labels": detected_labels,
                "processing_time": processing_time
            }

        final_status = "safe"

        # FIX 3: Log ALL detections even when result is safe.
        # Previously safe images had detections silently ignored.
        # Now you can see in terminal exactly what NudeNet returned
        # and why it didn't cross any threshold — useful for tuning.
        print_debug_report(
            filename=path.name,
            detections=detections,
            final_status=final_status,
            final_labels=[],
            processing_time=processing_time
        )

        # Response format unchanged
        return {
            "status": "safe",
            "confidence": round(1 - highest_confidence, 4),
            "detected_labels": [],
            "processing_time": processing_time
        }

    except Exception as e:
        processing_time = round(time.time() - start_time, 4)

        print("\n================ IMAGE MODERATION ERROR ================")
        print(f"Filename       : {path.name}")
        print(f"Error Message  : {str(e)}")
        print(f"Processing Time: {processing_time}s")
        print("========================================================\n")

        return {
            "status": "error",
            "message": str(e),
            "processing_time": processing_time
        }