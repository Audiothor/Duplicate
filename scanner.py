import os
import hashlib
from collections import defaultdict

PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}

def get_file_hash(filepath, chunk_size=8192):
    """Calculate the MD5 hash of a file."""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
    return hasher.hexdigest()

def scan_directory(directory, scan_photos=True, scan_videos=True, status_callback=None):
    """
    Scans a directory recursively and returns a list of duplicate groups.
    Each group is a list of file paths that are identical.
    """
    allowed_exts = set()
    if scan_photos:
        allowed_exts.update(PHOTO_EXTENSIONS)
    if scan_videos:
        allowed_exts.update(VIDEO_EXTENSIONS)

    # 1. Group files by size to avoid hashing everything
    size_dict = defaultdict(list)
    total_files_in_dir = 0
    scanned_images = 0
    scanned_videos = 0
    
    for root, _, files in os.walk(directory):
        # Skip Trash directory if it exists
        if "Trash" in root:
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            is_photo = ext in PHOTO_EXTENSIONS
            is_video = ext in VIDEO_EXTENSIONS
            
            total_files_in_dir += 1
            
            if (is_photo and scan_photos) or (is_video and scan_videos):
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    size_dict[size].append(filepath)
                    
                    if is_photo:
                        scanned_images += 1
                    elif is_video:
                        scanned_videos += 1
                        
                    # Update status dynamically during discovery
                    scanned_total = scanned_images + scanned_videos
                    others_remaining = total_files_in_dir - scanned_total
                    
                    if status_callback and scanned_total % 50 == 0:
                        status_callback({
                            'phase': 'discovering',
                            'total_files': scanned_total,
                            'images': scanned_images,
                            'videos': scanned_videos,
                            'others_remaining': others_remaining,
                            'duplicate_groups': 0,
                            'duplicate_files': 0,
                            'progress': 0
                        })
                except OSError:
                    pass

    # Send final discovery update
    scanned_total = scanned_images + scanned_videos
    others_remaining = total_files_in_dir - scanned_total
    
    if status_callback:
        status_callback({
            'phase': 'hashing',
            'total_files': scanned_total,
            'images': scanned_images,
            'videos': scanned_videos,
            'others_remaining': others_remaining,
            'duplicate_groups': 0,
            'duplicate_files': 0,
            'progress': 0
        })

    # Filter out sizes with only 1 file
    potential_duplicates = {size: paths for size, paths in size_dict.items() if len(paths) > 1}
    
    # 2. Hash files that have the same size
    duplicates = []
    files_to_hash = sum(len(paths) for paths in potential_duplicates.values())
    hashed_count = 0
    duplicate_groups_count = 0
    duplicate_files_count = 0
    
    for size, paths in potential_duplicates.items():
        hash_dict = defaultdict(list)
        for filepath in paths:
            file_hash = get_file_hash(filepath)
            if file_hash:
                hash_dict[file_hash].append(filepath)
                
            hashed_count += 1
            if status_callback and hashed_count % 10 == 0:
                progress = int((hashed_count / files_to_hash) * 100) if files_to_hash > 0 else 0
                status_callback({
                    'phase': 'hashing',
                    'total_files': scanned_total,
                    'images': scanned_images,
                    'videos': scanned_videos,
                    'others_remaining': others_remaining,
                    'duplicate_groups': duplicate_groups_count,
                    'duplicate_files': duplicate_files_count,
                    'progress': progress
                })
                
        # Any hash with > 1 path is a duplicate group
        for file_hash, identical_paths in hash_dict.items():
            if len(identical_paths) > 1:
                duplicates.append({
                    'hash': file_hash,
                    'size': size,
                    'files': identical_paths
                })
                duplicate_groups_count += 1
                duplicate_files_count += len(identical_paths)

    if status_callback:
        status_callback({
            'phase': 'finished',
            'total_files': scanned_total,
            'images': scanned_images,
            'videos': scanned_videos,
            'others_remaining': others_remaining,
            'duplicate_groups': duplicate_groups_count,
            'duplicate_files': duplicate_files_count,
            'progress': 100
        })
        
    return duplicates
