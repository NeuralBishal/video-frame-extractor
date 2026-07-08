"""
Video Frame Extractor Pro - Main Application
"""
import streamlit as st
import os
import tempfile
import json
import whisper
import subprocess
import time
import cv2
from src.utils import *
from src.audio_processor import *
from src.video_processor import *
from src.text_processor import *
from src.document_generator import *
from ui.main_ui import *
from ui.sidebar import render_sidebar
from ui.components import *

# Page configuration
st.set_page_config(
    page_title="Video Frame Extractor Pro",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        .main-header {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        
        .main-header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .main-header p { font-size: 1.1rem; opacity: 0.9; }
        
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
        
        .feature-icon { font-size: 2rem; margin-bottom: 1rem; }
        .feature-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; color: #333; }
        .feature-desc { color: #666; line-height: 1.5; }
        
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
        
        .subtitle-box {
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.2rem;
            margin: 10px 0;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        @media (max-width: 768px) {
            .main-header h1 { font-size: 1.8rem; }
        }
    </style>
    """, unsafe_allow_html=True)

def process_video_to_text(video_path, video_filename, settings):
    """Main processing function for video to text & audio"""
    # Extract settings
    target_lang_code = settings['target_lang_code']
    target_lang_name = settings['target_lang_name']
    source_lang = settings['source_lang']
    audio_speed = settings['audio_speed']
    simplify_text_flag = settings.get('simplify_text', True)
    translate_to_target = settings.get('translate_to_target', True)
    generate_translated_audio = settings.get('generate_translated_audio', True)
    generate_pdf_flag = settings.get('generate_pdf', True)
    generate_pptx_flag = settings.get('generate_pptx', False)
    
    # Check ffmpeg
    if not check_ffmpeg():
        st.error("FFmpeg is not installed. Please install ffmpeg to extract audio.")
        return None
    
    try:
        # Extract audio
        audio_path = extract_audio_from_video(video_path)
        
        if not audio_path or not os.path.exists(audio_path):
            st.error("Failed to extract audio from video")
            return None
        
        # Load Whisper model
        progress_text = st.empty()
        progress_text.text("🔄 Loading Whisper model...")
        
        # Check for GPU (silent - no user messages)
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load model on GPU if available
        model = whisper.load_model("medium", device=device)
        
        # Transcribe
        progress_text.text("🔄 Transcribing audio...")
        
        result = model.transcribe(audio_path)
        segments = result["segments"]
        full_text = result["text"]
        
        progress_text.text("📊 Processing content...")
        
        # Simplify if needed
        if simplify_text_flag:
            full_text = simplify_english(full_text)
            segments = simplify_segments(segments)
        
        # Store original
        original_text = full_text
        original_segments = segments.copy()
        
        # Translate if requested
        translated_text = None
        translated_segments = None
        
        if translate_to_target and target_lang_code != 'en':
            progress_text.text(f"🌐 Translating to {target_lang_name}...")
            translated_text = translate_text(full_text, target_lang_code)
            translated_segments = translate_segments(segments, target_lang_code)
            final_text = translated_text
            final_segments = translated_segments
        else:
            final_text = full_text
            final_segments = segments
        
        # Structure content
        progress_text.text("📝 Structuring content for documents...")
        structured = structure_transcript(final_text, final_segments)
        structured['title'] = f"Transcript: {os.path.splitext(video_filename)[0]}"
        
        # Generate SRT files
        srt_original_path = "subtitles_original.srt"
        with open(srt_original_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(original_segments, 1):
                start = format_time(seg['start'])
                end = format_time(seg['end'])
                text = seg['text']
                f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        
        srt_translated_path = None
        if translate_to_target and target_lang_code != 'en' and translated_segments:
            srt_translated_path = f"subtitles_{target_lang_code}.srt"
            with open(srt_translated_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(translated_segments, 1):
                    start = format_time(seg['start'])
                    end = format_time(seg['end'])
                    text = seg['text']
                    f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
        
        # Generate TXT file
        txt_path = "transcript.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        
        # Generate PDF
        pdf_path = None
        if generate_pdf_flag:
            progress_text.text("📄 Generating PDF...")
            pdf_path = generate_pdf(structured, "transcript.pdf")
        
        # Generate PPTX
        pptx_path = None
        if generate_pptx_flag:
            progress_text.text("📊 Generating PPTX...")
            pptx_path = generate_pptx(structured, "transcript.pptx")
        
        # Generate Audio
        audio_paths = {}
        
        if generate_translated_audio:
            # Generate translated audio
            if translate_to_target and target_lang_code != 'en':
                progress_text.text(f"🎵 Generating audio in {target_lang_name}...")
                
                audio_paths['translated'] = generate_audio_by_language(
                    translated_text,
                    f"transcript_audio_{target_lang_code}.mp3",
                    target_lang_code
                )
                
                if not audio_paths['translated']:
                    st.warning(f"Audio in {target_lang_name} failed. Trying English...")
                    audio_paths['translated'] = generate_audio_by_language(
                        translated_text,
                        f"transcript_audio_{target_lang_code}_en.mp3",
                        'en'
                    )
            
            # Generate original audio (English)
            progress_text.text("🎵 Generating audio in English...")
            audio_paths['original'] = generate_audio_by_language(
                original_text,
                "transcript_audio_en.mp3",
                'en'
            )
            
            if not audio_paths['original']:
                short_text = original_text[:1000]
                audio_paths['original'] = generate_audio_by_language(
                    short_text,
                    "transcript_audio_en_short.mp3",
                    'en'
                )
        
        # Cleanup
        clean_temp_files(audio_path)
        
        # Clear GPU memory silently (no user message)
        if device == "cuda":
            torch.cuda.empty_cache()
        
        return {
            'srt_original_path': srt_original_path,
            'srt_translated_path': srt_translated_path,
            'txt_path': txt_path,
            'pdf_path': pdf_path,
            'pptx_path': pptx_path,
            'audio_paths': audio_paths,
            'final_text': final_text,
            'original_text': original_text,
            'translated_text': translated_text,
            'structured': structured,
            'target_lang_name': target_lang_name,
            'target_lang_code': target_lang_code
        }
        
    except Exception as e:
        st.error(f"Error processing video: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def display_results(result, video_filename, settings):
    """Display results with audio player and download buttons"""
    
    st.markdown("---")
    st.markdown("## 📥 Download Results")
    
    # Success Message
    lang_info = f"Translated to {result['target_lang_name']}" if (settings['translate_to_target'] and settings['target_lang_code'] != 'en') else "Original language"
    st.markdown(f"""
    <div class="success-badge" style="background: #d4edda; padding: 1rem; text-align: center;">
        <h3>✅ Processing Complete!</h3>
        <p>📝 Generated content in: {lang_info}</p>
        <p>🎵 Audio available in: {'Translated language' if settings['generate_translated_audio'] else 'English'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # DOCUMENTS SECTION
    # ============================================
    st.markdown("### 📄 Documents")
    
    doc_cols = st.columns(3)
    
    # Original SRT
    with doc_cols[0]:
        if result['srt_original_path'] and os.path.exists(result['srt_original_path']):
            with open(result['srt_original_path'], 'rb') as f:
                st.download_button(
                    label="📥 Original SRT (English)",
                    data=f,
                    file_name=f"{os.path.splitext(video_filename)[0]}_original.srt",
                    mime="text/plain",
                    width="stretch"
                )
    
    # Translated SRT
    with doc_cols[1]:
        if result['srt_translated_path'] and os.path.exists(result['srt_translated_path']):
            with open(result['srt_translated_path'], 'rb') as f:
                st.download_button(
                    label=f"📥 {result['target_lang_name']} SRT",
                    data=f,
                    file_name=f"{os.path.splitext(video_filename)[0]}_{result['target_lang_code']}.srt",
                    mime="text/plain",
                    width="stretch"
                )
        else:
            st.info("No translation available")
    
    # TXT Transcript
    with doc_cols[2]:
        if result['txt_path'] and os.path.exists(result['txt_path']):
            with open(result['txt_path'], 'rb') as f:
                st.download_button(
                    label="📥 TXT Transcript",
                    data=f,
                    file_name=f"{os.path.splitext(video_filename)[0]}_transcript.txt",
                    mime="text/plain",
                    width="stretch"
                )
    
    # PDF and PPTX
    if result['pdf_path'] and os.path.exists(result['pdf_path']):
        with open(result['pdf_path'], 'rb') as f:
            st.download_button(
                label="📄 Download PDF",
                data=f,
                file_name=f"{os.path.splitext(video_filename)[0]}_transcript.pdf",
                mime="application/pdf",
                width="stretch"
            )
    
    if result['pptx_path'] and os.path.exists(result['pptx_path']):
        with open(result['pptx_path'], 'rb') as f:
            st.download_button(
                label="📊 Download PPTX",
                data=f,
                file_name=f"{os.path.splitext(video_filename)[0]}_presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                width="stretch"
            )
    
    # ============================================
    # AUDIO SECTION - WITH PLAY AND DOWNLOAD
    # ============================================
    if result['audio_paths']:
        st.markdown("### 🎵 Audio Files")
        st.markdown("*Click play to listen, or download to save*")
        
        audio_cols = st.columns(2)
        
        # Original English Audio
        if 'original' in result['audio_paths'] and result['audio_paths']['original']:
            original_path = result['audio_paths']['original']
            if os.path.exists(original_path):
                with audio_cols[0]:
                    st.markdown("**🇬🇧 English Audio**")
                    try:
                        with open(original_path, 'rb') as f:
                            audio_bytes = f.read()
                            
                            # PLAY BUTTON (Hearing)
                            st.audio(audio_bytes, format="audio/mp3")
                            
                            # DOWNLOAD BUTTON
                            st.download_button(
                                label="💾 Download English Audio",
                                data=audio_bytes,
                                file_name=f"{os.path.splitext(video_filename)[0]}_en.mp3",
                                mime="audio/mpeg",
                                width="stretch"
                            )
                    except Exception as e:
                        st.error(f"Error loading English audio: {str(e)}")
            else:
                with audio_cols[0]:
                    st.warning("English audio file not found")
        
        # Translated Audio
        if 'translated' in result['audio_paths'] and result['audio_paths']['translated']:
            translated_path = result['audio_paths']['translated']
            if os.path.exists(translated_path):
                with audio_cols[1]:
                    st.markdown(f"**{result['target_lang_name']} Audio**")
                    try:
                        with open(translated_path, 'rb') as f:
                            audio_bytes = f.read()
                            
                            # PLAY BUTTON (Hearing)
                            st.audio(audio_bytes, format="audio/mp3")
                            
                            # DOWNLOAD BUTTON
                            st.download_button(
                                label=f"💾 Download {result['target_lang_name']} Audio",
                                data=audio_bytes,
                                file_name=f"{os.path.splitext(video_filename)[0]}_{result['target_lang_code']}.mp3",
                                mime="audio/mpeg",
                                width="stretch"
                            )
                    except Exception as e:
                        st.error(f"Error loading translated audio: {str(e)}")
            else:
                with audio_cols[1]:
                    st.warning(f"{result['target_lang_name']} audio file not found")
    else:
        st.warning("⚠️ No audio files were generated")
    
    # ============================================
    # TRANSCRIPT PREVIEW
    # ============================================
    with st.expander("📝 Preview Transcript"):
        st.text(result['final_text'][:2000] + ("..." if len(result['final_text']) > 2000 else ""))
    
    # ============================================
    # TRANSLATION PREVIEW
    # ============================================
    if settings['translate_to_target'] and settings['target_lang_code'] != 'en':
        with st.expander(f"🌐 Translation Preview ({result['target_lang_name']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original (English):**")
                st.text(result['original_text'][:500] + ("..." if len(result['original_text']) > 500 else ""))
            with col2:
                st.markdown(f"**Translated ({result['target_lang_name']}):**")
                st.text(result['translated_text'][:500] + ("..." if len(result['translated_text']) > 500 else ""))
    
    # Cleanup temp files
    clean_temp_files(
        result['srt_original_path'],
        result['txt_path'],
        result['srt_translated_path'],
        result['pdf_path'],
        result['pptx_path']
    )
    for audio_file in result['audio_paths'].values():
        clean_temp_files(audio_file)

def main():
    """Main application entry point"""
    load_css()
    render_header()
    render_features()
    st.markdown("---")
    
    settings = render_sidebar()
    
    # Only video upload - no YouTube
    video_path, video_filename = render_video_input()
    
    if video_path and os.path.exists(video_path):
        try:
            # Get video info
            video_info = get_video_info(video_path)
            
            if video_info['duration'] <= 0:
                st.error("❌ Invalid video file. Duration is 0. Please try another video.")
                if video_path and os.path.exists(video_path):
                    os.unlink(video_path)
                st.rerun()
                return
            
            render_video_info(video_info)
            
            st.markdown("---")
            st.markdown("## 🎬 Video Preview")
            try:
                with open(video_path, 'rb') as f:
                    video_bytes = f.read()
                st.video(video_bytes)
            except Exception as e:
                st.warning(f"Video preview not available: {str(e)}")
            
            st.markdown("---")
            st.markdown("## 📝 Video to Text & Audio")
            st.markdown("*Generate structured documents and audio from your video content*")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                generate_pdf_flag = st.checkbox("📄 Generate PDF", value=True)
            with col2:
                generate_pptx_flag = st.checkbox("📊 Generate PPTX", value=False)
            with col3:
                generate_audio_flag = st.checkbox("🎵 Generate Audio", value=True)
            
            st.markdown("### 🌐 Translation Options")
            
            target_lang_name = settings.get('target_lang_name', 'English')
            target_lang_code = settings.get('target_lang_code', 'en')
            
            trans_col1, trans_col2, trans_col3 = st.columns(3)
            
            with trans_col1:
                simplify_text = st.checkbox("✨ Simplify English", value=True)
            with trans_col2:
                translate_to_target = st.checkbox(f"🌐 Translate to {target_lang_name}", value=True)
            with trans_col3:
                generate_translated_audio = st.checkbox("🎵 Generate Translated Audio", value=True)
            
            settings.update({
                'generate_pdf': generate_pdf_flag,
                'generate_pptx': generate_pptx_flag,
                'generate_audio': generate_audio_flag,
                'simplify_text': simplify_text,
                'translate_to_target': translate_to_target,
                'generate_translated_audio': generate_translated_audio
            })
            
            source_flag = get_language_flag(settings['source_lang'])
            target_flag = get_language_flag(settings['target_lang_code'])

            st.markdown(f"""
            <div class="info-box">
                <strong>🌐 Language Settings Summary:</strong><br>
                • 🎯 Source: {source_flag} {get_language_name(settings['source_lang'])} {'(Auto-detect)' if settings['source_lang'] == 'auto' else ''}<br>
                • 🌍 Target: {target_flag} {settings['target_lang_name']}<br>
                • 🎵 Audio Output: {'Translated audio' if generate_translated_audio else 'Original audio'}<br>
                • ✨ Simplification: {'Enabled' if simplify_text else 'Disabled'}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🎬 Generate Documents & Audio", type="primary", width="stretch"):
                result = process_video_to_text(video_path, video_filename, settings)
                
                if result:
                    display_results(result, video_filename, settings)
            
            render_real_time_subtitles(video_path)
            
            st.markdown("---")
            st.markdown("## 🎬 Video Preview & Timeline Selection")
            st.markdown("*Watch the video and select the exact time range for frame extraction*")
            
            if video_info['duration'] > 0:
                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.slider(
                        "Start Time (seconds)",
                        min_value=0.0,
                        max_value=float(video_info['duration']),
                        value=0.0,
                        step=0.5
                    )
                
                with col2:
                    end_time = st.slider(
                        "End Time (seconds)",
                        min_value=0.0,
                        max_value=float(video_info['duration']),
                        value=float(video_info['duration']),
                        step=0.5
                    )
                
                if start_time >= end_time:
                    st.error("❌ End time must be greater than start time!")
                    st.stop()
                
                start_frame = int(start_time * video_info['fps'])
                end_frame = int(end_time * video_info['fps'])
                frames_in_range = end_frame - start_frame
                estimated_frames = int(frames_in_range / settings['frame_interval']) if frames_in_range > 0 else 0
                
                if settings['max_frames'] > 0 and estimated_frames > settings['max_frames']:
                    estimated_frames = settings['max_frames']
                
                timeline_length = 50
                if video_info['duration'] > 0:
                    start_pos = int((start_time / video_info['duration']) * timeline_length)
                    end_pos = int((end_time / video_info['duration']) * timeline_length)
                    
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
                        • 💾 Frames to extract: {estimated_frames:,} (interval: every {settings['frame_interval']} frame)
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.text(f"Timeline: {timeline_visual}")
                    st.text(f"{start_time:.1f}s" + " " * (timeline_length - 10) + f"{end_time:.1f}s")
            else:
                st.warning("⚠️ Video duration is 0. Cannot display timeline.")
            
            st.markdown("---")
            
            if video_info['duration'] > 0:
                if st.button("🚀 START EXTRACTION", type="primary", width="stretch"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    preview_image = st.empty()
                    
                    result = extract_frames(
                        video_path,
                        start_time,
                        end_time,
                        video_info['fps'],
                        settings['frame_interval'],
                        settings['resize_frames'],
                        settings['resize_width'],
                        settings['resize_height'],
                        settings['quality'],
                        settings['max_frames']
                    )
                    
                    if result['saved_count'] > 0:
                        zip_path, zip_size = create_zip_from_frames(result['output_dir'])
                        
                        st.balloons()
                        st.markdown(f"""
                        <div class="success-badge" style="background: #d4edda; padding: 1rem; text-align: center;">
                            <h3>✅ Extraction Complete!</h3>
                            <p>📊 Saved {result['saved_count']:,} frames from {result['frame_count']:,} frames</p>
                            <p>⏱️ Processing time: {result['extraction_time']:.1f} seconds</p>
                            <p>💾 ZIP size: {zip_size:.2f} MB</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with open(zip_path, 'rb') as f:
                            st.download_button(
                                label=f"📥 Download Frames ({result['saved_count']} images, {zip_size:.1f} MB)",
                                data=f,
                                file_name=f"frames_{os.path.splitext(video_filename)[0]}.zip",
                                mime="application/zip",
                                width="stretch"
                            )
                        
                        st.markdown("## 🖼️ Frame Gallery")
                        previews = get_frame_previews(result['output_dir'])
                        if previews:
                            preview_cols = st.columns(min(6, len(previews)))
                            for i, col in enumerate(preview_cols):
                                if i < len(previews):
                                    col.image(previews[i], caption=f"Frame {i+1}", use_container_width=True)
                            
                            if len(previews) < result['saved_count']:
                                st.caption(f"Showing first {len(previews)} frames out of {result['saved_count']} total frames")
                        
                        for filename in os.listdir(result['output_dir']):
                            os.unlink(os.path.join(result['output_dir'], filename))
                        os.rmdir(result['output_dir'])
                        clean_temp_files(zip_path)
                    else:
                        st.warning("No frames were extracted. Try adjusting the settings.")
            else:
                st.warning("⚠️ Cannot extract frames from invalid video.")
            
            if st.button("🗑️ Clear Video", width="stretch"):
                if video_path and os.path.exists(video_path):
                    os.unlink(video_path)
                st.rerun()
        
        except Exception as e:
            st.error(f"Error loading video: {str(e)}")
            if video_path and os.path.exists(video_path):
                os.unlink(video_path)
    
    else:
        if video_path is None:
            st.info("👈 Upload a video to get started!")
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>Made with ❤️ using OpenCV, Whisper & Streamlit</p>
        <p>🌐 Supports: 30+ languages for translation</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()