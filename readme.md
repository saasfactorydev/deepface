# 🎯 Auto-Registration Face Recognition API

A powerful FastAPI-based face recognition system that automatically identifies and registers people. Simply upload an image and the system will tell you if the person has been seen before or automatically register them as new.

## ✨ Features

- **🆔 Automatic Person Registration**: New faces are automatically registered with unique IDs
- **🔍 Instant Recognition**: Identifies previously seen people with confidence scores
- **📊 Complete Analysis**: Age, gender, emotion, and ethnicity detection using DeepFace
- **🚫 Duplicate Prevention**: Detects exact same images and repeated faces
- **📈 Analytics**: Track detection history and statistics
- **🎯 Single Endpoint**: One simple endpoint handles everything

## 🚀 Quick Start

### 1. Setup Virtual Environment

#### Step-by-Step Process:

**Step 1: Create Virtual Environment**
```bash
python -m venv face_recognition_env
```

**Step 2: Activate Virtual Environment**

**On Windows (Command Prompt):**
```cmd
face_recognition_env\Scripts\activate
```

**On Windows (PowerShell):**
```powershell
face_recognition_env\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
source face_recognition_env/bin/activate
```

**Step 3: Verify Activation**
You should see `(face_recognition_env)` at the beginning of your command prompt.

**Step 4: Upgrade pip (recommended)**
```bash
python -m pip install --upgrade pip
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Start the API server
python simplified_face_recognition.py
```

The API will be available at:
- **Main API**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📡 API Endpoints

### 🎯 Main Endpoint: `/check_person` (POST)

**The only endpoint you need!** Upload any image and get instant results.

```bash
curl -X POST "http://localhost:8000/check_person" \
  -F "file=@your_image.jpg" \
  -F "threshold=0.65"
```

**Parameters:**
- `file`: Image file (jpg, png, etc.)
- `threshold`: Similarity threshold (0.0-1.0, default: 0.65)

### 📊 Analytics Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/stats` | GET | Database statistics |
| `/recent_activity` | GET | Recent detection history |
| `/all_persons` | GET | List all registered persons |

## 🔄 Response Examples

### ✅ Person Recognized (Seen Before)

```json
{
  "status": "person_recognized",
  "seen_before": true,
  "person_code": "PERSON_20250814_1423_5678",
  "confidence": 87.5,
  "total_detections": 5,
  "deepface_analysis": {
    "age": 28,
    "gender": {
      "dominant": "Woman",
      "scores": {
        "Woman": 95.2,
        "Man": 4.8
      }
    },
    "emotion": {
      "dominant": "happy",
      "scores": {
        "happy": 85.3,
        "neutral": 8.7,
        "surprise": 3.2,
        "sad": 1.8,
        "angry": 0.7,
        "fear": 0.2,
        "disgust": 0.1
      }
    },
    "race": {
      "dominant": "white",
      "scores": {
        "white": 67.8,
        "latino hispanic": 15.2,
        "asian": 10.1,
        "black": 4.9,
        "middle eastern": 1.7,
        "indian": 0.3
      }
    }
  },
  "message": "✅ Person recognized! Seen 5 times before."
}
```

### 🆕 New Person Registered

```json
{
  "status": "new_person_registered",
  "seen_before": false,
  "person_code": "PERSON_20250814_1423_5678",
  "deepface_analysis": {
    "age": 25,
    "gender": {
      "dominant": "Man",
      "scores": {
        "Man": 92.1,
        "Woman": 7.9
      }
    },
    "emotion": {
      "dominant": "neutral",
      "scores": {
        "neutral": 78.4,
        "happy": 12.3,
        "surprise": 4.1,
        "sad": 3.2,
        "angry": 1.5,
        "fear": 0.3,
        "disgust": 0.2
      }
    }
  },
  "message": "🆕 New person automatically registered as 'PERSON_20250814_1423_5678'"
}
```

### 🚫 No Face Detected

```json
{
  "status": "no_face",
  "seen_before": false,
  "message": "No face detected in the image"
}
```

## 🛠️ Usage Examples

### Python Requests

```python
import requests

# Check if person was seen before
url = "http://localhost:8000/check_person"
files = {"file": open("person_photo.jpg", "rb")}
data = {"threshold": 0.7}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Seen before: {result['seen_before']}")
if result['seen_before']:
    print(f"Person: {result['person_code']}")
    print(f"Confidence: {result['confidence']}%")
```

### JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('threshold', '0.65');

fetch('http://localhost:8000/check_person', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Seen before:', data.seen_before);
    console.log('Analysis:', data.deepface_analysis);
});
```

### cURL Examples

```bash
# Basic check
curl -X POST "http://localhost:8000/check_person" \
  -F "file=@image.jpg"

# With custom threshold
curl -X POST "http://localhost:8000/check_person" \
  -F "file=@image.jpg" \
  -F "threshold=0.8"

# Get statistics
curl "http://localhost:8000/stats"

# Get recent activity
curl "http://localhost:8000/recent_activity?limit=10"
```

## 📁 Project Structure

```
face-recognition-api/
├── simplified_face_recognition.py    # Main application
├── requirements.txt                  # Dependencies
├── README.md                        # This file
├── auto_face_database.db            # SQLite database (created automatically)
└── auto_face_database/              # Stored face images (created automatically)
    ├── PERSON_20250814_1423_5678/
    ├── PERSON_20250814_1456_9012/
    └── ...
```

## ⚙️ Configuration

### Adjustable Parameters

- **Similarity Threshold**: Default 0.65 (65% similarity required)
- **Server Host**: Default localhost (0.0.0.0)
- **Server Port**: Default 8000

### Environment Variables (Optional)

```bash
# Set custom database path
export FACE_DB_PATH="/path/to/custom/database.db"

# Set custom storage directory
export FACE_STORAGE_DIR="/path/to/custom/storage"

# Run on different port
export PORT=8080
```

## 🔍 DeepFace Analysis Details

The system provides detailed analysis for each face:

### Age
- Estimated age in years (e.g., 28)

### Gender
- **Options**: Woman, Man
- **Confidence scores** for each option

### Emotion
- **Options**: happy, sad, angry, surprise, fear, disgust, neutral
- **Confidence scores** for each emotion

### Race/Ethnicity
- **Options**: white, black, asian, indian, latino hispanic, middle eastern
- **Confidence scores** for each ethnicity

## 🚨 Error Handling

| Status | Description | Action |
|--------|-------------|---------|
| `no_face` | No face detected | Use clearer image with visible face |
| `multiple_faces` | Multiple faces found | Use image with single person |
| `exact_duplicate` | Same image processed before | Image already in system |
| `error` | Processing error | Check image format and size |

## 📊 Database Schema

### auto_persons Table
- `id`: Unique person ID
- `person_code`: Human-readable person code
- `first_seen`: First detection timestamp
- `last_seen`: Most recent detection
- `total_detections`: Number of times seen
- `confidence_avg`: Average recognition confidence

### detections Table
- `id`: Detection ID
- `person_id`: Foreign key to person
- `detection_time`: When detected
- `confidence`: Recognition confidence
- `image_hash`: Image fingerprint
- `age_detected`: Detected age
- `gender_detected`: Detected gender
- `emotion_detected`: Detected emotion

## 🛡️ Security Considerations

- Images are stored locally in `auto_face_database/` directory
- Database is SQLite file - secure your server appropriately
- No external API calls (except initial model downloads)
- Consider implementing authentication for production use

## 🐛 Troubleshooting

### Common Issues

**1. Virtual Environment Activation Issues**

**Problem**: `source: no such file or directory: face_recognition_env/bin/activate`

**Solutions**:
```bash
# Make sure you created the venv first:
python -m venv face_recognition_env

# Then activate based on your system:
# Windows Command Prompt:
face_recognition_env\Scripts\activate

# Windows PowerShell:
face_recognition_env\Scripts\Activate.ps1

# macOS/Linux:
source face_recognition_env/bin/activate

# If still having issues, try:
python -m venv face_recognition_env --clear
```

**2. TensorFlow Version Issues**

**Problem**: `ERROR: Could not find a version that satisfies the requirement tensorflow==2.15.0`

**Solutions**:
```bash
# Install latest compatible TensorFlow
pip install tensorflow>=2.13.0

# Or install specific latest version
pip install tensorflow==2.17.0

# For GPU support (if you have NVIDIA GPU)
pip install tensorflow[and-cuda]>=2.13.0

# If still having issues, try installing without version constraints
pip install tensorflow tf-keras
```

**3. Python Command Not Found**
```bash
# Try these alternatives:
python3 -m venv face_recognition_env
py -m venv face_recognition_env
```

**3. Permission Denied (Windows PowerShell)**
```powershell
# Enable script execution:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**4. TensorFlow Warnings**
```
Solution: These are usually safe to ignore. Add to suppress:
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
```

**2. Models Not Downloading**
```
Solution: Ensure internet connection on first run.
Models are downloaded to ~/.deepface/weights/
```

**3. Poor Recognition Accuracy**
```
Solution: 
- Use clear, well-lit images
- Ensure face is clearly visible
- Adjust threshold parameter
- Use consistent lighting conditions
```

**4. Virtual Environment Issues**
```bash
# Recreate virtual environment
# First deactivate if active:
deactivate

# Remove old environment:
# Windows:
rmdir /s face_recognition_env
# macOS/Linux:
rm -rf face_recognition_env

# Create new environment:
python -m venv face_recognition_env

# Activate:
# Windows:
face_recognition_env\Scripts\activate
# macOS/Linux:
source face_recognition_env/bin/activate

# Install requirements:
pip install -r requirements.txt
```

**5. TensorFlow Warnings**

## 🔧 Development

### Running in Development Mode

```bash
# Install development dependencies
pip install pytest httpx

# Run with auto-reload
uvicorn simplified_face_recognition:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
```

### Docker Support (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "simplified_face_recognition.py"]
```

## 📈 Performance Tips

- **GPU Support**: Install `tensorflow-gpu` for faster processing
- **Batch Processing**: Process multiple images by calling endpoint multiple times
- **Threshold Tuning**: Lower threshold = more matches, higher = stricter matching
- **Image Quality**: Use images 224x224 or larger for best results

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **DeepFace**: For the powerful face recognition capabilities
- **FastAPI**: For the excellent web framework
- **TensorFlow**: For the deep learning backend

---

**Made with ❤️ for automatic face recognition**