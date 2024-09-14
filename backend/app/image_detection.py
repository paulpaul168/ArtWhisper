from pathlib import Path
import random
import pickle
from fastapi import (
    HTTPException,
    File,
    UploadFile
)
import cv2
import os
import shutil

async def test_find_similar_artwork():
    # Path to the test images folder
    test_images_folder = Path("test_images")
    
    # Get a list of all image files in the test folder
    test_images = list(test_images_folder.glob("*.jpg"))
    
    if not test_images:
        raise HTTPException(status_code=404, detail="No test images found")
    
    # Randomly select a test image
    test_image_path = random.choice(test_images)
    
    # Create a temporary UploadFile object
    with open(test_image_path, "rb") as image_file:
        temp_upload_file = UploadFile(filename=test_image_path.name, file=image_file)
        
        # Call the find_similar_artwork_endpoint function
        result = await find_similar_artwork_endpoint(temp_upload_file)
    
    return result

# Global variable to store the cached keypoints and descriptors
cached_paintings = {}

CACHE_FILE = 'paintings_cache.pkl'
PAINTINGS_FOLDER = Path("../crawler/belvedere_images")

def keypoints_to_list(keypoints):
    return [(kp.pt, kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in keypoints]

def list_to_keypoints(keypoints_list):
    return [cv2.KeyPoint(x=kp[0][0], y=kp[0][1], size=kp[1], angle=kp[2], response=kp[3], octave=kp[4], class_id=kp[5]) for kp in keypoints_list]

def load_or_compute_features():
    global cached_paintings
    
    if os.path.exists(CACHE_FILE):
        print("Loading cached features")
        try:
            with open(CACHE_FILE, 'rb') as f:
                cached_data = pickle.load(f)
            for painting_file, data in cached_data.items():
                cached_paintings[painting_file] = (list_to_keypoints(data['keypoints']), data['descriptors'])
            return
        except (EOFError, pickle.UnpicklingError, KeyError):
            print("Cache file is corrupted. Recomputing features.")
            os.remove(CACHE_FILE)
    
    print("Computing features for all paintings")
    sift = cv2.SIFT_create()
    
    for painting_file in PAINTINGS_FOLDER.glob("*.jpeg"):
        print(f"Processing {painting_file.name}")
        painting_image = cv2.imread(str(painting_file), cv2.IMREAD_GRAYSCALE)
        if painting_image is None:
            print(f"Failed to load image: {painting_file.name}")
            continue
        
        kp, des = sift.detectAndCompute(painting_image, None)
        cached_paintings[painting_file] = (kp, des)
    
    # Cache all computed features
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle_data = {k: {'keypoints': keypoints_to_list(v[0]), 'descriptors': v[1]} for k, v in cached_paintings.items()}
            pickle.dump(pickle_data, f)
        print("Features cached successfully")
    except Exception as e:
        print(f"Failed to cache features: {str(e)}")

async def find_similar_artwork_endpoint(image: UploadFile = File(...)):
    print(f"Received image: {image.filename}")
    
    # Save the uploaded image temporarily
    temp_image_path = "temp_uploaded_image.jpg"
    with open(temp_image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Load and preprocess the uploaded image
    query_image = cv2.imread(temp_image_path, cv2.IMREAD_GRAYSCALE)
    if query_image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Initialize SIFT detector
    sift = cv2.SIFT_create()
    
    # Detect keypoints and compute descriptors for the query image
    query_kp, query_des = sift.detectAndCompute(query_image, None)
    print(f"Query image keypoints: {len(query_kp)}")
    
    best_match = None
    best_score = 0
    
    # Match against all cached paintings
    for painting_file, (painting_kp, painting_des) in cached_paintings.items():
        # Match descriptors
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(query_des, painting_des, k=2)
        
        # Apply ratio test
        good_matches = [m for m, n in matches if m.distance < 0.4 * n.distance]
        
        # Calculate similarity score
        similarity_score = len(good_matches) / max(len(query_kp), len(painting_kp))
        
        if similarity_score > best_score:
            best_score = similarity_score
            best_match = painting_file.stem
            print(f"New best match: {best_match} with score: {best_score}")
    
    # Clean up temporary file
    os.remove(temp_image_path)
    
    if best_match:
        print(f"Final result: Best match {best_match} with similarity {best_score}")
        return {"similar_artwork_id": best_match, "similarity": best_score}
    else:
        print("No match found")
        return {"similar_artwork_id": None, "similarity": 0.0}