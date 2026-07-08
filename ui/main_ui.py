"""
Main UI Components - No YouTube
"""
import streamlit as st
import os
import tempfile
import urllib.request
from urllib.parse import urlparse
import json
import whisper
import subprocess
import time
import queue
import wave
from src.utils import format_time, clean_temp_files, check_ffmpeg
from src.audio_processor import *
from src.video_processor import *
from src.text_processor import *
from src.document_generator import *
from .components import *

def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🎬 Video Frame Extractor Pro</h1>
        <p>Extract frames, generate documents, and create audio from your videos</p>
    </div>
    """, unsafe_allow_html=True)

def render_features():
    """Render feature cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    features = [
        ("📤", "Easy Upload", "Upload any video file to get started"),
        ("⚙️", "Customizable", "Adjust interval, quality & resize options"),
        ("📥", "Bulk Download", "Download all frames as ZIP archive"),
        ("📄", "Smart Documents", "PDF, PPTX & Audio from video content")
    ]
    
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
        with col:
            feature_card(icon, title, desc)

def render_video_input():
    """Render video input section - File Upload Only"""
    st.markdown("## 📁 Upload Video")
    
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v'],
        help="Supported formats: MP4, AVI, MOV, MKV, WEBM, FLV"
    )
    
    video_path = None
    video_filename = None
    
    if uploaded_file:
        with st.spinner("Loading video..."):
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_path = tfile.name
            video_filename = uploaded_file.name
        success_badge(f"✅ Loaded: {uploaded_file.name}")
    
    return video_path, video_filename

def render_video_info(video_info):
    """Render video information"""
    st.markdown("## 📊 Video Information")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎞️ Total Frames", f"{video_info['total_frames']:,}")
    with col2:
        st.metric("⚡ FPS", f"{video_info['fps']:.2f}")
    with col3:
        st.metric("⏱️ Duration", f"{video_info['duration']:.1f}s")
    with col4:
        st.metric("📐 Resolution", f"{video_info['width']}×{video_info['height']}")

def render_real_time_subtitles(video_path):
    """Render real-time subtitle generator"""
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
    
    if enable_real_time:
        render_subtitle_player(video_path)

def render_subtitle_player(video_path):
    """Render subtitle player"""
    subtitle_container = st.container()
    
    class RealTimeSubtitleGenerator:
        def __init__(self, model_size="tiny"):
            self.model = whisper.load_model(model_size)
            self.is_running = False
            self.audio_queue = queue.Queue()
        
        def extract_audio_stream(self, video_path):
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
            try:
                temp_audio = "temp_chunk.wav"
                with wave.open(temp_audio, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(audio_chunk)
                
                result = self.model.transcribe(temp_audio)
                text = result["text"].strip()
                
                os.unlink(temp_audio)
                return text
            except Exception as e:
                return ""
    
    with subtitle_container:
        st.markdown("### 📝 Live Subtitles")
        current_subtitle_placeholder = st.empty()
    
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
            <div class="subtitle-box">
                🎯 {text}
            </div>
            """, unsafe_allow_html=True)
    
    if st.button("🎬 Start Real-Time Subtitles", width="stretch"):
        if not check_ffmpeg():
            st.error("FFmpeg is not installed.")
            st.stop()
        
        with st.spinner("Starting real-time subtitle generation..."):
            try:
                audio_path = extract_audio_from_video(video_path)
                if audio_path and os.path.exists(audio_path):
                    model = whisper.load_model("tiny")
                    result = model.transcribe(audio_path)
                    
                    for segment in result["segments"]:
                        text = segment["text"]
                        update_subtitle(text)
                        time.sleep(0.1)
                    
                    os.unlink(audio_path)
                    success_badge("✅ Subtitle generation complete!")
            except Exception as e:
                st.error(f"Error: {str(e)}")