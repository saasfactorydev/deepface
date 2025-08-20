from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from typing import Dict, Any
import uvicorn
import sqlite3
from datetime import datetime
import hashlib
import shutil
from deepface import DeepFace

app = FastAPI(title="Auto-Registration Face Recognition API", version="1.0.0")

# Database and storage setup
DATABASE_PATH = "auto_face_database.db"
FACE_DATABASE_DIR = "auto_face_database"

def init_database():
    """Initialize SQLite database for automatic face registration"""
    os.makedirs(FACE_DATABASE_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create table for auto-registered persons
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auto_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_code TEXT UNIQUE NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_detections INTEGER DEFAULT 1,
            confidence_avg REAL DEFAULT 0.0,
            age_estimate INTEGER,
            gender_estimate TEXT,
            main_image_path TEXT
        )
    ''')
    
    # Create table for all detections
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence REAL,
            image_hash TEXT,
            age_detected INTEGER,
            gender_detected TEXT,
            emotion_detected TEXT,
            FOREIGN KEY (person_id) REFERENCES auto_persons (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

def clean_analysis_data(analysis_data):
    """Clean and convert analysis data for JSON serialization"""
    cleaned = {}
    
    # Convert age - handle numpy types
    if 'age' in analysis_data:
        age_val = analysis_data['age']
        if hasattr(age_val, 'item'):  # numpy type
            cleaned['age'] = int(age_val.item())
        else:
            cleaned['age'] = int(age_val) if age_val is not None else None
    
    # Convert gender data
    if 'gender' in analysis_data and 'dominant_gender' in analysis_data:
        gender_scores = analysis_data['gender']
        cleaned_scores = {}
        for k, v in gender_scores.items():
            if hasattr(v, 'item'):  # numpy type
                cleaned_scores[k] = float(v.item())
            else:
                cleaned_scores[k] = float(v)
        
        cleaned['gender'] = {
            'dominant': str(analysis_data['dominant_gender']),
            'scores': cleaned_scores
        }
    
    # Convert emotion data
    if 'emotion' in analysis_data and 'dominant_emotion' in analysis_data:
        emotion_scores = analysis_data['emotion']
        cleaned_scores = {}
        for k, v in emotion_scores.items():
            if hasattr(v, 'item'):  # numpy type
                cleaned_scores[k] = float(v.item())
            else:
                cleaned_scores[k] = float(v)
        
        cleaned['emotion'] = {
            'dominant': str(analysis_data['dominant_emotion']),
            'scores': cleaned_scores
        }
    
    # Convert race data
    if 'race' in analysis_data and 'dominant_race' in analysis_data:
        race_scores = analysis_data['race']
        cleaned_scores = {}
        for k, v in race_scores.items():
            if hasattr(v, 'item'):  # numpy type
                cleaned_scores[k] = float(v.item())
            else:
                cleaned_scores[k] = float(v)
        
        cleaned['race'] = {
            'dominant': str(analysis_data['dominant_race']),
            'scores': cleaned_scores
        }
    
    return cleaned

def save_uploaded_file(uploaded_file: UploadFile) -> str:
    """Save uploaded file to temporary location"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            content = uploaded_file.file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        return temp_file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

def cleanup_temp_file(file_path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Warning: Could not delete temporary file {file_path}: {str(e)}")

def get_image_hash(image_content: bytes) -> str:
    """Generate hash for image content"""
    return hashlib.md5(image_content).hexdigest()

def generate_person_code() -> str:
    """Generate unique person code"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"PERSON_{timestamp}_{hash(timestamp) % 10000:04d}"

def find_existing_person(temp_file_path: str, threshold: float = 0.6) -> Dict[str, Any]:
    """Check if person already exists in database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all stored persons
        cursor.execute('SELECT id, person_code, main_image_path FROM auto_persons')
        stored_persons = cursor.fetchall()
        
        if not stored_persons:
            return {"found": False}
        
        best_match = None
        highest_confidence = 0.0
        
        # Compare with each stored person
        for person_id, person_code, stored_image_path in stored_persons:
            if os.path.exists(stored_image_path):
                try:
                    result = DeepFace.verify(
                        img1_path=temp_file_path,
                        img2_path=stored_image_path,
                        enforce_detection=False
                    )
                    
                    confidence = (1 - result["distance"]) * 100
                    
                    if result["verified"] and confidence > highest_confidence:
                        highest_confidence = confidence
                        if confidence >= (threshold * 100):
                            best_match = {
                                "person_id": person_id,
                                "person_code": person_code,
                                "confidence": confidence
                            }
                        
                except Exception as e:
                    print(f"Error comparing with {stored_image_path}: {str(e)}")
                    continue
        
        if best_match:
            return {"found": True, **best_match}
        else:
            return {"found": False, "highest_similarity": highest_confidence}
            
    except Exception as e:
        print(f"Error in find_existing_person: {str(e)}")
        return {"found": False, "error": str(e)}
    finally:
        conn.close()

def register_new_person(temp_file_path: str, analysis_data: dict, image_hash: str) -> Dict[str, Any]:
    """Automatically register a new person"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Generate unique person code
        person_code = generate_person_code()
        
        # Create directory for this person
        person_dir = os.path.join(FACE_DATABASE_DIR, person_code)
        os.makedirs(person_dir, exist_ok=True)
        
        # Save main image
        main_image_path = os.path.join(person_dir, f"main_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        shutil.copy2(temp_file_path, main_image_path)
        
        # Extract analysis data - handle numpy types
        age = analysis_data.get("age")
        if hasattr(age, 'item'):
            age = int(age.item())
        else:
            age = int(age) if age is not None else None
            
        gender = str(analysis_data.get("dominant_gender", "unknown"))
        
        # Insert new person
        cursor.execute('''
            INSERT INTO auto_persons 
            (person_code, age_estimate, gender_estimate, main_image_path)
            VALUES (?, ?, ?, ?)
        ''', (person_code, age, gender, main_image_path))
        
        person_id = cursor.lastrowid
        
        # Log first detection
        emotion = str(analysis_data.get("dominant_emotion", "unknown"))
        cursor.execute('''
            INSERT INTO detections 
            (person_id, confidence, image_hash, age_detected, gender_detected, emotion_detected)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (person_id, 100.0, image_hash, age, gender, emotion))
        
        conn.commit()
        
        return {
            "person_id": person_id,
            "person_code": person_code,
            "age": age,
            "gender": gender,
            "emotion": emotion
        }
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_existing_person(person_id: int, confidence: float, analysis_data: dict, image_hash: str):
    """Update existing person's data"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Update person stats
        cursor.execute('''
            UPDATE auto_persons 
            SET last_seen = CURRENT_TIMESTAMP,
                total_detections = total_detections + 1,
                confidence_avg = (confidence_avg * (total_detections - 1) + ?) / total_detections
            WHERE id = ?
        ''', (confidence, person_id))
        
        # Log detection - handle numpy types
        age = analysis_data.get("age")
        if hasattr(age, 'item'):
            age = int(age.item())
        else:
            age = int(age) if age is not None else None
            
        gender = str(analysis_data.get("dominant_gender", "unknown"))
        emotion = str(analysis_data.get("dominant_emotion", "unknown"))
        
        cursor.execute('''
            INSERT INTO detections 
            (person_id, confidence, image_hash, age_detected, gender_detected, emotion_detected)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (person_id, confidence, image_hash, age, gender, emotion))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating person: {str(e)}")
    finally:
        conn.close()

def log_detection(person_id: int, confidence: float, is_duplicate: bool, image_hash: str):
    """Log detection event"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO detection_logs (person_id, confidence, is_duplicate, image_hash)
            VALUES (?, ?, ?, ?)
        ''', (person_id, confidence, is_duplicate, image_hash))
        conn.commit()
    except Exception as e:
        print(f"Error logging detection: {str(e)}")
    finally:
        conn.close()

@app.get("/")
async def root():
    return {
        "message": "Auto-Registration Face Recognition API is running!",
        "description": "Simply upload any image - the system will automatically tell you if the person was seen before or register them as new"
    }

@app.post("/check_person")
async def check_person(
    file: UploadFile = File(...),
    threshold: float = 0.65
):
    """
    MAIN ENDPOINT: Check if person was seen before, automatically register if new
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    temp_file_path = None
    try:
        # Read file content for hash
        file_content = await file.read()
        image_hash = get_image_hash(file_content)
        
        # Reset file pointer and save temporarily
        file.file.seek(0)
        temp_file_path = save_uploaded_file(file)
        
        # Check for exact duplicate image first
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT person_id FROM detections WHERE image_hash = ?', (image_hash,))
        duplicate_check = cursor.fetchone()
        conn.close()
        
        if duplicate_check:
            return JSONResponse(content={
                "status": "exact_duplicate",
                "seen_before": True,
                "message": "This exact same image was processed before",
                "person_id": duplicate_check[0]
            })
        
        # Detect and analyze face
        try:
            analysis = DeepFace.analyze(
                img_path=temp_file_path,
                actions=['age', 'gender', 'emotion', 'race'],
                enforce_detection=False
            )
            
            # Handle multiple faces or no faces
            if isinstance(analysis, list):
                if len(analysis) == 0:
                    return JSONResponse(content={
                        "status": "no_face",
                        "seen_before": False,
                        "message": "No face detected in the image"
                    })
                elif len(analysis) > 1:
                    return JSONResponse(content={
                        "status": "multiple_faces",
                        "seen_before": False,
                        "message": f"Multiple faces detected ({len(analysis)}). Please use an image with a single person."
                    })
                else:
                    analysis_data = analysis[0]
            else:
                analysis_data = analysis
                
        except Exception as e:
            return JSONResponse(content={
                "status": "no_face",
                "seen_before": False,
                "message": "No face could be detected in the image"
            })
        
        # Check if person exists in database
        match_result = find_existing_person(temp_file_path, threshold)
        
        if match_result["found"]:
            # PERSON SEEN BEFORE - Update their record
            confidence_val = match_result["confidence"]
            if hasattr(confidence_val, 'item'):
                confidence_val = float(confidence_val.item())
            else:
                confidence_val = float(confidence_val)
                
            update_existing_person(
                match_result["person_id"], 
                confidence_val, 
                analysis_data, 
                image_hash
            )
            
            # Get updated person info
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT person_code, first_seen, total_detections, confidence_avg 
                FROM auto_persons WHERE id = ?
            ''', (match_result["person_id"],))
            person_info = cursor.fetchone()
            conn.close()
            
            return JSONResponse(content={
                "status": "person_recognized",
                "seen_before": True,
                "person_id": match_result["person_id"],
                "person_code": person_info[0],
                "confidence": round(confidence_val, 2),
                "first_seen": person_info[1],
                "total_detections": person_info[2],
                "avg_confidence": round(float(person_info[3]), 2),
                "deepface_analysis": clean_analysis_data(analysis_data),
                "message": f"✅ Person recognized! Seen {person_info[2]} times before."
            })
        
        else:
            # NEW PERSON - Automatically register them
            new_person = register_new_person(temp_file_path, analysis_data, image_hash)
            
            return JSONResponse(content={
                "status": "new_person_registered",
                "seen_before": False,
                "person_id": new_person["person_id"],
                "person_code": new_person["person_code"],
                "deepface_analysis": clean_analysis_data(analysis_data),
                "message": f"🆕 New person automatically registered as '{new_person['person_code']}'"
            })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        if temp_file_path:
            cleanup_temp_file(temp_file_path)

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get total persons
        cursor.execute('SELECT COUNT(*) FROM auto_persons')
        total_persons = cursor.fetchone()[0]
        
        # Get total detections
        cursor.execute('SELECT COUNT(*) FROM detections')
        total_detections = cursor.fetchone()[0]
        
        # Get recent activity (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) FROM detections 
            WHERE detection_time > datetime('now', '-1 day')
        ''')
        recent_activity = cursor.fetchone()[0]
        
        # Get most seen person
        cursor.execute('''
            SELECT person_code, total_detections 
            FROM auto_persons 
            ORDER BY total_detections DESC 
            LIMIT 1
        ''')
        most_seen = cursor.fetchone()
        
        return JSONResponse(content={
            "total_registered_persons": total_persons,
            "total_detections": total_detections,
            "detections_last_24h": recent_activity,
            "most_seen_person": {
                "person_code": most_seen[0] if most_seen else None,
                "detection_count": most_seen[1] if most_seen else 0
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")
    finally:
        conn.close()

@app.get("/all_persons")
async def all_persons():
    """List all automatically registered persons"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                person_code, 
                first_seen, 
                last_seen, 
                total_detections, 
                confidence_avg,
                age_estimate,
                gender_estimate
            FROM auto_persons 
            ORDER BY last_seen DESC
        ''')
        
        persons = cursor.fetchall()
        
        persons_list = []
        for person_code, first_seen, last_seen, total_detections, confidence_avg, age, gender in persons:
            persons_list.append({
                "person_code": person_code,
                "first_seen": first_seen,
                "last_seen": last_seen,
                "total_detections": total_detections,
                "avg_confidence": round(float(confidence_avg), 2) if confidence_avg else 0,
                "estimated_age": age,
                "estimated_gender": gender
            })
        
        return JSONResponse(content={
            "total_persons": len(persons_list),
            "persons": persons_list
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)