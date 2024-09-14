import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.neighbors import NearestNeighbors
import os
import glob
import time
from tqdm import tqdm
import pickle
import hashlib

def print_debug(message):
    print(f"[DEBUG] {message}")

class ProgressMiniBatchKMeans(MiniBatchKMeans):
    def fit(self, X, y=None, sample_weight=None):
        self.n_iter = 100  # Adjust this based on your needs
        batch_size = min(1000, len(X) // 10)  # Adjust batch size as needed
        for i in tqdm(range(self.n_iter), desc="MiniBatchKMeans clustering"):
            if i == 0:
                super().partial_fit(X, y, sample_weight)
            else:
                super().partial_fit(X, y, sample_weight)
        return self

def load_images_from_folder(folder_path):
    print_debug(f"Loading images from folder: {folder_path}")
    images = []
    image_paths = glob.glob(os.path.join(folder_path, '*.jpeg')) + glob.glob(os.path.join(folder_path, '*.png'))
    for img_path in tqdm(image_paths, desc="Loading images"):
        img = cv2.imread(img_path)
        if img is not None:
            images.append((img, os.path.basename(img_path)))
        else:
            print_debug(f"Failed to load image: {os.path.basename(img_path)}")
    print_debug(f"Total images loaded: {len(images)}")
    return images

def load_single_image(folder_path):
    print_debug(f"Attempting to load a single image from folder: {folder_path}")
    image_paths = glob.glob(os.path.join(folder_path, '*.jpeg')) + glob.glob(os.path.join(folder_path, '*.png'))
    if image_paths:
        img_path = image_paths[0]
        img = cv2.imread(img_path)
        if img is not None:
            print_debug(f"Loaded test image: {os.path.basename(img_path)}")
            return img, os.path.basename(img_path)
        else:
            print_debug(f"Failed to load test image: {os.path.basename(img_path)}")
    else:
        print_debug("No image files found in the test folder")
    return None, None

def preprocess_image(image):
    print_debug("Preprocessing image")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    src_points = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    dst_points = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    corrected = cv2.warpPerspective(gray, matrix, (width, height))
    normalized = cv2.equalizeHist(corrected)
    return normalized

def extract_features(image):
    print_debug("Extracting SIFT features")
    sift = cv2.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(image, None)
    print_debug(f"Extracted {len(keypoints) if keypoints else 0} keypoints")
    if descriptors is not None:
        descriptors = descriptors.astype(np.float32)
    return keypoints, descriptors

def get_image_hash(image):
    return hashlib.md5(image.tobytes()).hexdigest()

def keypoints_to_list(keypoints):
    return [(kp.pt, kp.size, kp.angle, kp.response, kp.octave, kp.class_id) for kp in keypoints]

def list_to_keypoints(keypoints_list):
    return [cv2.KeyPoint(x=kp[0][0], y=kp[0][1], size=kp[1], angle=kp[2], response=kp[3], octave=kp[4], class_id=kp[5]) for kp in keypoints_list]

def load_or_compute_features(image, cache_dir='feature_cache'):
    os.makedirs(cache_dir, exist_ok=True)
    image_hash = get_image_hash(image)
    cache_file = os.path.join(cache_dir, f"{image_hash}.pkl")
    
    if os.path.exists(cache_file):
        print_debug("Loading cached features")
        with open(cache_file, 'rb') as f:
            cached_data = pickle.load(f)
        keypoints = list_to_keypoints(cached_data['keypoints'])
        descriptors = cached_data['descriptors']
        return keypoints, descriptors
    else:
        print_debug("Computing and caching features")
        preprocessed = preprocess_image(image)
        keypoints, descriptors = extract_features(preprocessed)
        
        # Store only necessary information from keypoints
        keypoints_list = keypoints_to_list(keypoints)
        
        with open(cache_file, 'wb') as f:
            pickle.dump({'keypoints': keypoints_list, 'descriptors': descriptors}, f)
        return keypoints, descriptors

def index_database(database_images, force_recompute=False):
    index_file = 'database_index.pkl'
    
    if not force_recompute and os.path.exists(index_file):
        print_debug("Loading pre-computed index")
        with open(index_file, 'rb') as f:
            kmeans, index, image_filenames = pickle.load(f)
        
        current_filenames = [img[1] for img in database_images]
        if set(current_filenames) == set(image_filenames):
            print_debug("Loaded pre-computed index successfully")
            return kmeans, index
        else:
            print_debug("Database has changed, recomputing index")
    
    print_debug("Indexing database")
    start_time = time.time()
    all_descriptors = []
    for i, (img, img_name) in enumerate(tqdm(database_images, desc="Processing images")):
        _, desc = load_or_compute_features(img)
        if desc is not None:
            all_descriptors.extend(desc)
    
    all_descriptors = np.array(all_descriptors, dtype=np.float32)
    
    print_debug(f"Creating MiniBatchKMeans with {len(all_descriptors)} descriptors")
    kmeans = ProgressMiniBatchKMeans(n_clusters=1000, random_state=42, batch_size=1000)
    kmeans.fit(all_descriptors)
    print_debug("MiniBatchKMeans clustering completed")
    
    print_debug("Creating histograms for database images")
    database_histograms = []
    for i, (img, img_name) in enumerate(tqdm(database_images, desc="Creating histograms")):
        _, desc = load_or_compute_features(img)
        if desc is not None:
            visual_words = kmeans.predict(desc)
            histogram = np.zeros(kmeans.n_clusters, dtype=np.float32)
            for word in visual_words:
                histogram[word] += 1
            histogram /= histogram.sum()  # Normalize the histogram
            database_histograms.append(histogram)

    database_histograms = np.array(database_histograms)

    print_debug("Creating NearestNeighbors index")
    index = NearestNeighbors(n_neighbors=1, algorithm='auto')
    index.fit(database_histograms)
    print_debug("NearestNeighbors index created")
    
    end_time = time.time()
    print_debug(f"Database indexing completed in {end_time - start_time:.2f} seconds")
    
    image_filenames = [img[1] for img in database_images]
    with open(index_file, 'wb') as f:
        pickle.dump((kmeans, index, image_filenames), f)
    print_debug("Saved computed index to file")
    
    return kmeans, index

def match_artwork(query_image, database_images, kmeans, index):
    print_debug("Matching artwork")
    start_time = time.time()
    
    _, query_descriptors = load_or_compute_features(query_image)
    
    if query_descriptors is None:
        print_debug("No features found in the query image")
        return None
    
    print_debug(f"Quantizing {len(query_descriptors)} query descriptors")
    query_descriptors = query_descriptors.astype(np.float32)
    query_visual_words = kmeans.predict(query_descriptors)
    
    print_debug("Computing histogram of visual words")
    histogram = np.zeros(kmeans.n_clusters, dtype=np.float32)
    for word in query_visual_words:
        histogram[word] += 1
    histogram /= histogram.sum()  # Normalize the histogram
    
    print_debug("Finding nearest neighbors")
    distances, indices = index.kneighbors(histogram.reshape(1, -1))
    
    best_match = indices[0][0]
    end_time = time.time()
    print_debug(f"Matching completed in {end_time - start_time:.2f} seconds")
    print_debug(f"Best match index: {best_match}, Distance: {distances[0][0]}")
    return best_match

# Main execution
print_debug("Starting artwork matching pipeline")

# Load database images
database_folder = '../crawler/belvedere_images'
database_images = load_images_from_folder(database_folder)

if not database_images:
    print_debug(f"No images found in the database folder: {database_folder}")
else:
    print_debug(f"Successfully loaded {len(database_images)} images from {database_folder}")

    # Index the database
    kmeans, index = index_database(database_images)

    # Load test image
    test_folder = 'test_images'
    test_image, test_image_name = load_single_image(test_folder)

    if test_image is None:
        print_debug(f"No test image found in the folder: {test_folder}")
    else:
        print_debug(f"Successfully loaded test image: {test_image_name}")

        # Match the test image against the database
        best_match_index = match_artwork(test_image, database_images, kmeans, index)
        
        if best_match_index is not None:
            matched_image_name = database_images[best_match_index][1]
            print_debug(f"Best match for {test_image_name} is database image: {matched_image_name}")
        else:
            print_debug("No match found")

print_debug("Artwork matching pipeline completed")