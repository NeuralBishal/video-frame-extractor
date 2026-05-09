import streamlit as st
import cv2
import tempfile
import os
import zipfile
import urllib.request
from urllib.parse import urlparse
import time
import base64
from pathlib import Path

st.set_page_config(
    page_title="Video Frame Extractor",
    page_icon="🎬",
    layout="wide"
)

# Custom HTML/CSS for better UI
st.markdown("""
<!DOCTYPE html>
<html>
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        .main-header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .main-header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .feature-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        
        .feature-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #333;
        }
        
        .feature-desc {
            color: #666;
            line-height: 1.5;
        }
        
        .success-badge {
            background: #d4edda;
            color: #155724;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 5px;
        }
        
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 1.8rem;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }
        
        @media (max-width: 768px) {
            .main-header h1 {
                font-size: 1.8rem;
            }
            .stats-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
</html>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎬 Video Frame Extractor Pro</h1>
    <p>Extract high-quality frames from any video in seconds</p>
</div>
""", unsafe_allow_html=True)

# Features section
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📤</div>
        <div class="feature-title">Easy Upload</div>
        <div class="feature-desc">Upload any video file or provide URL</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">⚙️</div>
        <div class="feature-title">Customizable</div>
        <div class="feature-desc">Adjust interval, quality & resize options</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📥</div>
        <div class="feature-title">Bulk Download</div>
        <div class="feature-desc">Download all frames as ZIP archive</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Fast Processing</div>
        <div class="feature-desc">Optimized extraction with progress tracking</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sidebar for settings
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    st.markdown("### Extraction Settings")
    frame_interval = st.slider(
        "Extract every N frame",
        min_value=1,
        max_value=120,
        value=30,
        help="1 = all frames, 30 = 1 frame/second (30fps)"
    )
    
    quality = st.slider(
        "JPEG Quality",
        min_value=30,
        max_value=100,
        value=85,
        help="Higher quality = larger file size"
    )
    
    st.markdown("### Resize Options")
    resize_frames = st.checkbox("Resize frames", value=False)
    if resize_frames:
        col1, col2 = st.columns(2)
        with col1:
            resize_width = st.number_input("Width", min_value=100, max_value=3840, value=1280)
        with col2:
            resize_height = st.number_input("Height", min_value=100, max_value=2160, value=720)
    
    st.markdown("### Advanced Options")
    with st.expander("Show advanced options"):
        max_frames = st.number_input(
            "Max frames (0=unlimited)",
            min_value=0,
            max_value=10000,
            value=0,
            help="Limit total frames extracted"
        )
        
        start_time = st.number_input(
            "Start time (seconds)",
            min_value=0.0,
            value=0.0,
            step=1.0
        )
        
        duration = st.number_input(
            "Duration (seconds, 0=all)",
            min_value=0.0,
            value=0.0,
            step=1.0
        )

# Main content
st.markdown("## 📁 Input Video")

# Two input methods
input_method = st.radio(
    "Select input method:",
    ["📤 Upload Video File", "🔗 Video URL"],
    horizontal=True
)

video_path = None
video_filename = None

if input_method == "📤 Upload Video File":
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v'],
        help="Supported formats: MP4, AVI, MOV, MKV, WEBM, FLV"
    )
    
    if uploaded_file:
        with st.spinner("Loading video..."):
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_path = tfile.name
            video_filename = uploaded_file.name
        st.markdown(f'<div class="success-badge">✅ Loaded: {uploaded_file.name}</div>', unsafe_allow_html=True)

else:  # Video URL
    video_url = st.text_input(
        "Enter video URL",
        placeholder="https://example.com/video.mp4",
        help="Direct link to video file"
    )
    
    if video_url:
        col1, col2 = st.columns([3, 1])
        with col2:
            download_btn = st.button("📥 Fetch Video", use_container_width=True)
        
        if download_btn:
            with st.spinner("Downloading video from URL..."):
                try:
                    parsed_url = urlparse(video_url)
                    if not parsed_url.scheme in ['http', 'https']:
                        st.error("Please enter a valid HTTP/HTTPS URL")
                    else:
                        video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        urllib.request.urlretrieve(video_url, video_path)
                        video_filename = os.path.basename(parsed_url.path) or "downloaded_video.mp4"
                        st.markdown('<div class="success-badge">✅ Video downloaded successfully!</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Failed to download: {str(e)}")
                    video_path = None

# Process video if loaded
if video_path and os.path.exists(video_path):
    # Get video information
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_seconds = total_frames / fps if fps > 0 else 0
    cap.release()
    
    # Display video stats
    st.markdown("## 📊 Video Information")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎞️ Total Frames", f"{total_frames:,}")
    with col2:
        st.metric("⚡ FPS", f"{fps:.2f}")
    with col3:
        st.metric("⏱️ Duration", f"{duration_seconds:.1f}s")
    with col4:
        st.metric("📐 Resolution", f"{width}×{height}")
    
    # Estimated output
    estimated_frames = int((total_frames - int(start_time * fps)) / frame_interval) if duration == 0 else int((duration * fps) / frame_interval)
    if max_frames > 0 and estimated_frames > max_frames:
        estimated_frames = max_frames
    
    st.markdown(f"""
    <div class="info-box">
        💡 <strong>Estimated frames to extract:</strong> {estimated_frames:,} frames
    </div>
    """, unsafe_allow_html=True)
    
    # Extract button
    st.markdown("---")
    if st.button("🚀 START EXTRACTION", type="primary", use_container_width=True):
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        preview_image = st.empty()
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        frame_count = 0
        saved_count = 0
        start_frame = int(start_time * fps)
        
        # Calculate end frame
        if duration > 0:
            end_frame = start_frame + int(duration * fps)
        else:
            end_frame = total_frames
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        start_time_extract = time.time()
        
        while True:
            success, frame = cap.read()
            
            if not success or frame_count >= end_frame:
                break
            
            if frame_count < start_frame:
                frame_count += 1
                continue
            
            if max_frames > 0 and saved_count >= max_frames:
                break
            
            if (frame_count - start_frame) % frame_interval == 0:
                if resize_frames:
                    frame = cv2.resize(frame, (resize_width, resize_height))
                
                frame_path = os.path.join(output_dir, f'frame_{saved_count:06d}.jpg')
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                saved_count += 1
                
                # Show preview every 10 frames
                if saved_count % 10 == 0:
                    preview_image.image(frame, caption=f"Preview: Frame {saved_count}", use_container_width=True)
            
            frame_count += 1
            
            # Update progress
            progress = (frame_count - start_frame) / (end_frame - start_frame) if end_frame > start_frame else 1
            progress_bar.progress(min(progress, 1.0))
            
            elapsed_time = time.time() - start_time_extract
            fps_processing = (frame_count - start_frame) / elapsed_time if elapsed_time > 0 else 0
            status_text.info(f"📊 Processing: {frame_count:,}/{end_frame:,} frames | 💾 Saved: {saved_count:,} frames | ⚡ Speed: {fps_processing:.1f} fps")
        
        cap.release()
        extraction_time = time.time() - start_time_extract
        
        # Completion
        progress_bar.progress(1.0)
        
        if saved_count > 0:
            # Create ZIP
            with st.spinner("Creating ZIP archive..."):
                zip_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip').name
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for filename in os.listdir(output_dir):
                        filepath = os.path.join(output_dir, filename)
                        zipf.write(filepath, filename)
                
                zip_size = os.path.getsize(zip_path) / (1024 * 1024)
            
            # Success message
            st.balloons()
            st.markdown(f"""
            <div class="success-badge" style="background: #d4edda; padding: 1rem; text-align: center;">
                <h3>✅ Extraction Complete!</h3>
                <p>📊 Saved {saved_count:,} frames from {frame_count:,} total frames</p>
                <p>⏱️ Processing time: {extraction_time:.1f} seconds</p>
                <p>💾 ZIP size: {zip_size:.2f} MB</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Download button
            with open(zip_path, 'rb') as f:
                st.download_button(
                    label=f"📥 Download Frames ({saved_count} images, {zip_size:.1f} MB)",
                    data=f,
                    file_name=f"frames_{os.path.splitext(video_filename)[0]}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            
            # Preview gallery
            st.markdown("## 🖼️ Frame Gallery")
            frame_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
            preview_cols = st.columns(min(6, len(frame_files)))
            for i, col in enumerate(preview_cols):
                if i < len(frame_files):
                    preview_path = os.path.join(output_dir, frame_files[i])
                    col.image(preview_path, caption=f"Frame {i+1}", use_container_width=True)
            
            if len(frame_files) > 6:
                st.caption(f"Showing first 6 frames out of {len(frame_files)} total frames")
            
            # Cleanup
            for filename in os.listdir(output_dir):
                os.unlink(os.path.join(output_dir, filename))
            os.rmdir(output_dir)
        else:
            st.warning("No frames were extracted. Try adjusting the settings.")
    
    # Clear button
    if st.button("🗑️ Clear Video", use_container_width=True):
        if video_path and os.path.exists(video_path):
            os.unlink(video_path)
        st.rerun()

else:
    if video_path is None:
        st.info("👈 Upload a video or provide a URL to get started!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>Made with ❤️ using OpenCV & Streamlit</p>
    <p style="font-size: 0.9rem;">© 2024 Video Frame Extractor Pro</p>
</div>
""", unsafe_allow_html=True)
