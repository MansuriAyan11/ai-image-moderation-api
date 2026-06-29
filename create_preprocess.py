with open('preprocess.py', 'w', encoding='utf-8') as f:
    f.write("""from PIL import Image
from pathlib import Path
import tempfile
import os


def is_closeup(image_path: str) -> bool:
    try:
        img = Image.open(image_path)
        w, h = img.size
        aspect_ratio = w / h
        is_square_crop = 0.75 <= aspect_ratio <= 1.35
        is_small = (w * h) < (800 * 800)
        return is_square_crop or is_small
    except Exception:
        return False


def create_padded_version(image_path: str, pad_percent: float = 0.4) -> str:
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    pad_x = int(w * pad_percent)
    pad_y = int(h * pad_percent)
    new_w = w + 2 * pad_x
    new_h = h + 2 * pad_y
    padded = Image.new("RGB", (new_w, new_h), (255, 255, 255))
    padded.paste(img, (pad_x, pad_y))
    suffix = Path(image_path).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="padded_")
    padded.save(tmp.name)
    tmp.close()
    return tmp.name


def merge_detections(result_original: dict, result_padded: dict) -> dict:
    if result_original["status"] == "safe" and result_padded["status"] == "safe":
        return result_original
    combined_labels = list(set(
        result_original.get("detected_labels", []) +
        result_padded.get("detected_labels", [])
    ))
    highest_confidence = max(
        result_original.get("confidence", 0),
        result_padded.get("confidence", 0)
    )
    combined_time = (
        result_original.get("processing_time", 0) +
        result_padded.get("processing_time", 0)
    )
    return {
        "status": "unsafe",
        "confidence": round(highest_confidence, 4),
        "detected_labels": combined_labels,
        "processing_time": round(combined_time, 4)
    }


def apply_fallback_rules(detections: list, is_closeup_image: bool):
    if not is_closeup_image:
        return None
    labels_found = {item.get("class") for item in detections}
    scores = {item.get("class"): item.get("score", 0) for item in detections}
    has_belly = "BELLY_EXPOSED" in labels_found
    has_face = any(l in labels_found for l in ["FACE_FEMALE", "FACE_MALE"])
    belly_score = scores.get("BELLY_EXPOSED", 0)
    if has_belly and not has_face and belly_score >= 0.65:
        print("[FALLBACK] Rule triggered: close-up belly with no face")
        print("[FALLBACK] BELLY_EXPOSED score: " + str(belly_score))
        return {
            "status": "unsafe",
            "confidence": round(belly_score, 4),
            "detected_labels": ["MALE_GENITALIA_COVERED_INFERRED"],
            "processing_time": 0.0
        }
    return None


def detect_with_preprocessing(image_path: str, detect_fn) -> dict:
    result_original = detect_fn(image_path)

    if result_original["status"] == "unsafe":
        return result_original

    closeup = is_closeup(image_path)

    if closeup:
        print("[PREPROCESS] Close-up detected - running padded version too")
        padded_path = None
        try:
            padded_path = create_padded_version(image_path)
            print("[PREPROCESS] Padded image created: " + padded_path)
            result_padded = detect_fn(padded_path)
            print("[PREPROCESS] Original result : " + result_original["status"])
            print("[PREPROCESS] Padded result   : " + result_padded["status"])
            final = merge_detections(result_original, result_padded)
            print("[PREPROCESS] Final decision  : " + final["status"])
            if final["status"] == "unsafe":
                return final
        except Exception as e:
            print("[PREPROCESS] Padded detection failed: " + str(e))
        finally:
            if padded_path and os.path.exists(padded_path):
                try:
                    os.remove(padded_path)
                    print("[PREPROCESS] Cleaned up padded temp file")
                except Exception:
                    pass

    try:
        from nudenet import NudeDetector
        detector = NudeDetector()
        raw_detections = detector.detect(image_path)
    except Exception:
        raw_detections = []

    fallback = apply_fallback_rules(raw_detections, closeup)
    if fallback:
        fallback["processing_time"] = round(
            result_original.get("processing_time", 0) + fallback["processing_time"], 4
        )
        return fallback

    return result_original
""")
print("preprocess.py created successfully")