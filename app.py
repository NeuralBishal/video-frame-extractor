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
import speech_recognition as sr
import whisper
import subprocess
import threading
import queue
from deep_translator import GoogleTranslator
import numpy as np
import wave


def extract_audio_from_video(video_path, audio_path="temp_audio.wav"):
    """Extract audio from video file"""
    try:
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ac', '1', '-ar', '16000',
            '-vn', '-y',
            audio_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return audio_path
    except Exception as e:
        st.error(f"Audio extraction failed: {str(e)}")
        return None

def format_time(seconds):
    """Convert seconds to SRT time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"



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
            download_btn = st.button("📥 Fetch Video", width="stretch")
        
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

# Initialize global variables for real-time processing
transcription_queue = queue.Queue()
subtitles_history = []
translator = GoogleTranslator(source='auto', target='en')

class RealTimeSubtitleGenerator:
    def __init__(self, model_size="base", target_lang='en'):
        self.model = whisper.load_model(model_size)
        self.target_lang = target_lang
        self.is_running = False
        self.audio_queue = queue.Queue()
        
    def extract_audio_stream(self, video_path):
        """Extract audio stream from video for real-time processing"""
        try:
            cmd = [
                'ffmpeg', '-i', video_path,
                '-f', 'wav', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                'pipe:1'
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return process
        except Exception as e:
            st.error(f"Audio stream extraction failed: {str(e)}")
            return None
    
    def process_audio_chunk(self, audio_chunk):
        """Process a chunk of audio and return transcribed text"""
        try:
            temp_audio = "temp_chunk.wav"
            with wave.open(temp_audio, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_chunk)
            
            result = self.model.transcribe(temp_audio)
            text = result["text"].strip()
            
            if self.target_lang != 'en' or self.target_lang == 'en':
                text = self.simplify_english(text)
            
            os.unlink(temp_audio)
            return text
        except Exception as e:
            return ""
    
    def simplify_english(self, text):
        """Simplify complex English to plain language"""
        replacements = {
            'utilize': 'use',
            'demonstrate': 'show',
            'implement': 'do',
            'consequently': 'so',
            'nevertheless': 'but',
            'furthermore': 'also',
            'in addition': 'plus',
            'significant': 'big',
            'approximately': 'about',
            'establish': 'set up',
            'obtain': 'get',
            'determine': 'find',
            'evaluate': 'check',
            'analyze': 'study',
            'therefore': 'so',
            'thus': 'so',
            'hence': 'so'
        }
        
        for complex_word, simple_word in replacements.items():
            text = text.replace(complex_word, simple_word)
            text = text.replace(complex_word.capitalize(), simple_word.capitalize())
        
        return text
    
    def generate_real_time_subtitles(self, video_path, callback):
        """Main function to generate subtitles in real-time"""
        process = self.extract_audio_stream(video_path)
        if not process:
            return
        
        self.is_running = True
        chunk_duration = 3
        chunk_size = int(16000 * chunk_duration)
        
        while self.is_running:
            audio_chunk = process.stdout.read(chunk_size * 2)
            
            if not audio_chunk:
                break
            
            text = self.process_audio_chunk(audio_chunk)
            
            if text:
                callback(text)
        
        process.wait()
        self.is_running = False

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

    # Real-Time Subtitle Generation
    st.markdown("---")
    st.markdown("## 🎙️ Real-Time Subtitle Generator")
    st.markdown("*Watch and learn with live subtitles - perfect for understanding different accents*")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        enable_real_time = st.checkbox("🔴 Enable Real-Time Subtitles", value=False)
    
    with col2:
        if enable_real_time:
            subtitle_language = st.selectbox(
                "Subtitle Language",
                ["Plain English (Simplified)", "Original + Simplified", "Only Key Terms"]
            )
    
    with col3:
        if enable_real_time:
            accent_adjustment = st.checkbox("🎯 Accent Optimization", value=True)
    
    # Real-time subtitle display area
    if enable_real_time:
        subtitle_container = st.container()
        subtitle_generator = RealTimeSubtitleGenerator(model_size="base")
        
        with subtitle_container:
            st.markdown("### 📝 Live Subtitles")
            current_subtitle_placeholder = st.empty()
            subtitle_history_placeholder = st.empty()
        
        if 'subtitle_history' not in st.session_state:
            st.session_state.subtitle_history = []
        
        def update_subtitle(text):
            if text:
                st.session_state.subtitle_history.append({
                    'time': time.strftime("%H:%M:%S"),
                    'text': text
                })
                
                if len(st.session_state.subtitle_history) > 10:
                    st.session_state.subtitle_history = st.session_state.subtitle_history[-10:]
                
                current_subtitle_placeholder.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    font-size: 1.2rem;
                    margin: 10px 0;
                ">
                    🎯 {text}
                </div>
                """, unsafe_allow_html=True)
                
                history_text = ""
                for sub in st.session_state.subtitle_history[-5:]:
                    history_text += f"⏱️ {sub['time']} | {sub['text']}\n\n"
                
                subtitle_history_placeholder.text(history_text)
        
        # This button should be HERE - inside if enable_real_time block
        if st.button("🎬 Generate Subtitles", width="stretch"):
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except:
                st.error("FFmpeg is not installed. Please install ffmpeg to extract audio.")
                st.stop()
            
            with st.spinner("Processing audio and generating subtitles..."):
                try:
                    # Extract audio from video
                    audio_path = extract_audio_from_video(video_path)
                    
                    if audio_path and os.path.exists(audio_path):
                        # Load Whisper model
                        model = whisper.load_model("base")
                        
                        # Transcribe
                        result = model.transcribe(audio_path)
                        
                        # Collect segments and display subtitles
                        segments = []
                        for segment in result["segments"]:
                            text = segment["text"]
                            
                            # Simplify if needed
                            if subtitle_language == "Plain English (Simplified)":
                                text = subtitle_generator.simplify_english(text)
                            
                            segments.append({
                                'start': segment['start'],
                                'end': segment['end'],
                                'text': text
                            })
                            
                            update_subtitle(text)
                            time.sleep(0.1)  # Small delay for visual effect
                        
                        # Create SRT file for download
                        srt_path = "subtitles.srt"
                        with open(srt_path, 'w', encoding='utf-8') as f:
                            for i, seg in enumerate(segments, 1):
                                start = format_time(seg['start'])
                                end = format_time(seg['end'])
                                text = seg['text']
                                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
                        
                        # Create plain text file
                        txt_path = "transcript.txt"
                        with open(txt_path, 'w', encoding='utf-8') as f:
                            for seg in segments:
                                f.write(f"{seg['text']}\n")
                        
                        # Offer downloads
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            with open(srt_path, 'rb') as f:
                                st.download_button(
                                    label="📥 Download Subtitles (.srt)",
                                    data=f,
                                    file_name="subtitles.srt",
                                    mime="text/plain",
                                    width="stretch"
                                )
                        
                        with col2:
                            with open(txt_path, 'rb') as f:
                                st.download_button(
                                    label="📥 Download Transcript (.txt)",
                                    data=f,
                                    file_name="transcript.txt",
                                    mime="text/plain",
                                    width="stretch"
                                )
                        
                        st.info("💡 Tip: Use VLC or any video player to add the .srt subtitle file while watching the video.")
                        
                        # Cleanup
                        os.unlink(audio_path)
                        os.unlink(srt_path)
                        os.unlink(txt_path)
                        st.success(f"✅ Generated {len(segments)} subtitle segments!")
                    else:
                        st.error("Failed to extract audio from video")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Timeline selection sliders
    st.markdown("### 📍 Select Time Range")
    
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.slider(
            "Start Time (seconds)",
            min_value=0.0,
            max_value=float(duration_seconds),
            value=0.0,
            step=0.5
        )
    
    with col2:
        end_time = st.slider(
            "End Time (seconds)",
            min_value=0.0,
            max_value=float(duration_seconds),
            value=float(duration_seconds),
            step=0.5
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
    if duration_seconds > 0:
        start_pos = int((start_time / duration_seconds) * timeline_length)
        end_pos = int((end_time / duration_seconds) * timeline_length)
        
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
    
    st.markdown("---")
    
    # START EXTRACTION BUTTON
    if st.button("🚀 START EXTRACTION", type="primary", width="stretch"):
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        preview_image = st.empty()
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        frame_count = 0
        saved_count = 0
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        start_time_extract = time.time()
        current_frame = start_frame
        
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
                
                # Show preview every 10 frames
                if saved_count % 10 == 0:
                    preview_image.image(frame, caption=f"Preview: Frame {saved_count}", use_container_width=True)
            
            current_frame += 1
            frame_count += 1
            
            # Update progress
            progress = (current_frame - start_frame) / frames_in_range if frames_in_range > 0 else 1
            progress_bar.progress(min(progress, 1.0))
            
            elapsed_time = time.time() - start_time_extract
            fps_processing = frame_count / elapsed_time if elapsed_time > 0 else 0
            status_text.info(f"📊 Processing: {frame_count:,}/{frames_in_range:,} frames | 💾 Saved: {saved_count:,} frames | ⚡ Speed: {fps_processing:.1f} fps")
        
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
                <p>📊 Saved {saved_count:,} frames from {frame_count:,} frames</p>
                <p>⏱️ Processing time: {extraction_time:.1f} seconds</p>
                <p>💾 ZIP size: {zip_size:.2f} MB</p>
                <p>🎯 Time range: {start_time:.1f}s - {end_time:.1f}s</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Download button
            with open(zip_path, 'rb') as f:
                st.download_button(
                    label=f"📥 Download Frames ({saved_count} images, {zip_size:.1f} MB)",
                    data=f,
                    file_name=f"frames_{os.path.splitext(video_filename)[0]}.zip",
                    mime="application/zip",
                    width="stretch"
                )
            
            # Preview gallery
            st.markdown("## 🖼️ Frame Gallery")
            frame_files = sorted([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
            if frame_files:
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
    if st.button("🗑️ Clear Video", width="stretch"):
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
    <p>✨ NEW: Real-time subtitles for better lecture comprehension! ✨</p>
</div>
""", unsafe_allow_html=True)