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
    
    # Video Player & Timeline Selection
    st.markdown("---")
    st.markdown("## 🎬 Video Preview & Timeline Selection")
    st.markdown("*Watch the video and select the exact time range for frame extraction*")
    
    # Display video player
    try:
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        st.video(video_bytes)
    except Exception as e:
        st.warning(f"Video preview not available: {str(e)}")
    
    # Timeline selection sliders
    st.markdown("### 📍 Select Time Range")
    
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.slider(
            "Start Time (seconds)",
            min_value=0.0,
            max_value=float(duration_seconds),
            value=0.0,
            step=0.5,
            help="Select where to start extracting frames"
        )
    
    with col2:
        end_time = st.slider(
            "End Time (seconds)",
            min_value=0.0,
            max_value=float(duration_seconds),
            value=float(duration_seconds),
            step=0.5,
            help="Select where to stop extracting frames"
        )
    
    # Validate time range
    if start_time >= end_time:
        st.error("❌ End time must be greater than start time!")
        st.stop()
    
    # Calculate frames in selected range
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    frames_in_range = end_frame - start_frame
    estimated_frames = int(frames_in_range / frame_interval) if frames_in_range > 0 else 0
    
    if max_frames > 0 and estimated_frames > max_frames:
        estimated_frames = max_frames
    
# Visual timeline representation
timeline_length = 50
start_pos = int((start_time / duration_seconds) * timeline_length) if duration_seconds > 0 else 0
end_pos = int((end_time / duration_seconds) * timeline_length) if duration_seconds > 0 else timeline_length

timeline_bar = "░" * timeline_length
timeline_list = list(timeline_bar)
for i in range(start_pos, min(end_pos, len(timeline_list))):
    timeline_list[i] = "█"
timeline_visual = "".join(timeline_list)

st.markdown(f"""
<div class="info-box">
    <strong>📊 Selected Range Details:</strong><br>
    • ⏱️ Time: {start_time:.1f}s - {end_time:.1f}s<br>
    • 📏 Duration: {end_time - start_time:.1f} seconds<br>
    • 🎞️ Frames in range: {frames_in_range:,}<br>
    • 💾 Frames to extract: {estimated_frames:,} (interval: every {frame_interval} frame)
</div>
""", unsafe_allow_html=True)

# Display timeline
st.text(f"Timeline: {timeline_visual}")
st.text(f"{start_time:.1f}s" + " " * (timeline_length - 10) + f"{end_time:.1f}s")