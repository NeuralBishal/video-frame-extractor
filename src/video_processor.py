"""
Video Processing Module - Frame Extraction
"""
import cv2
import os
import tempfile
import time
import zipfile
import streamlit as st

def get_video_info(video_path):
    """Get video information"""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_seconds = total_frames / fps if fps > 0 else 0
    cap.release()
    
    return {
        'total_frames': total_frames,
        'fps': fps,
        'width': width,
        'height': height,
        'duration': duration_seconds
    }

def extract_frames(video_path, start_time, end_time, fps, frame_interval, 
                   resize_frames=False, resize_width=1280, resize_height=720,
                   quality=85, max_frames=0):
    """Extract frames from video"""
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    frames_in_range = end_frame - start_frame
    
    output_dir = tempfile.mkdtemp()
    frame_count = 0
    saved_count = 0
    
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    start_time_extract = time.time()
    current_frame = start_frame
    progress = 0
    
    while current_frame < end_frame:
        success, frame = cap.read()
        
        if not success:
            break
        
        if max_frames > 0 and saved_count >= max_frames:
            break
        
        if (current_frame - start_frame) % frame_interval == 0:
            if resize_frames:
                frame = cv2.resize(frame, (resize_width, resize_height))
            
            frame_path = os.path.join(output_dir, f'frame_{saved_count:06d}.jpg')
            cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            saved_count += 1
        
        current_frame += 1
        frame_count += 1
        
        progress = (current_frame - start_frame) / frames_in_range if frames_in_range > 0 else 1
    
    cap.release()
    extraction_time = time.time() - start_time_extract
    
    return {
        'output_dir': output_dir,
        'saved_count': saved_count,
        'frame_count': frame_count,
        'extraction_time': extraction_time
    }

def create_zip_from_frames(output_dir):
    """Create ZIP archive from extracted frames"""
    zip_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip').name
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            zipf.write(filepath, filename)
    
    zip_size = os.path.getsize(zip_path) / (1024 * 1024)
    return zip_path, zip_size

def get_frame_previews(output_dir, count=6):
    """Get preview images from extracted frames"""
    frame_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
    previews = []
    for i in range(min(count, len(frame_files))):
        preview_path = os.path.join(output_dir, frame_files[i])
        previews.append(preview_path)
    return previews