# AI Image Moderation API

This is a FastAPI-based Image Moderation API that detects nudity or inappropriate content in uploaded images before storing them in a database.

The API is designed for a dating application use case where user-uploaded images must be scanned first. Safe images can be allowed, while unsafe images are rejected.

## Live API

Base URL:

```text
https://ai-image-moderation-api.onrender.com/
```

Swagger Documentation:

```text
https://ai-image-moderation-api.onrender.com/docs
```

## API Endpoint

### POST `/detect`

This endpoint accepts an image file and returns whether the image is safe or unsafe.

## Request Type

Use `multipart/form-data`.

| Key    | Type | Description              |
| ------ | ---- | ------------------------ |
| `file` | File | Image file to be scanned |

## Example Success Response: Safe Image

```json
{
  "success": true,
  "message": "Image is safe",
  "data": {
    "status": "safe",
    "confidence": 1.0,
    "detected_labels": [],
    "processing_time": 0.08
  }
}
```

## Example Success Response: Unsafe Image

```json
{
  "success": true,
  "message": "Inappropriate content detected",
  "data": {
    "status": "unsafe",
    "confidence": 0.95,
    "detected_labels": [
      "FEMALE_BREAST_EXPOSED"
    ],
    "processing_time": 0.09
  }
}
```

## Error Handling

Invalid file type:

```json
{
  "detail": "Invalid file extension. Only jpg, jpeg, png, and webp are allowed."
}
```

Missing file:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "file"
      ],
      "msg": "Field required"
    }
  ]
}
```

## Features

* FastAPI REST API
* Image upload support
* NudeNet-based image moderation
* Safe / unsafe classification
* Confidence score
* Detected unsafe labels
* Processing time measurement
* File type validation
* Temporary file cleanup after scanning
* Swagger UI testing support
* Render deployment

## Supported Image Formats

```text
.jpg
.jpeg
.png
.webp
```

## Local Setup

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run server:

```bash
uvicorn app:app --reload
```

Open local API:

```text
http://127.0.0.1:8000/
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## API Testing Summary

| Endpoint  | Method | Input        | Result                          | Status Code              |
| --------- | ------ | ------------ | ------------------------------- | ------------------------ |
| `/`       | GET    | None         | API health check working        | 200 OK                   |
| `/detect` | POST   | Safe image   | Image marked safe               | 200 OK                   |
| `/detect` | POST   | Unsafe image | Inappropriate content detected  | 200 OK                   |
| `/detect` | POST   | `.txt` file  | Invalid file extension rejected | 400 Bad Request          |
| `/detect` | POST   | No file      | Required file validation error  | 422 Unprocessable Entity |

## Deployment

The API is deployed on Render.

Render start command:

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

## Project Structure

```text
nudenet_project/
│
├── app.py
├── detector.py
├── requirements.txt
├── README.md
├── uploads/
│   └── .gitkeep
├── image_check.py
├── video_check.py
├── dataset_test.py
└── speed_test.py
```

## Notes

This API does not permanently store uploaded images.
Images are temporarily saved for scanning and deleted after detection.

Final decision flow:

```text
User Upload
    ↓
Backend API
    ↓
AI Image Scan
    ↓
Safe Image → Allow Upload
Unsafe Image → Reject Upload
```
