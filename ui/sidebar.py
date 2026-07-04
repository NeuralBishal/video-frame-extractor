"""
Sidebar UI Components
"""
import streamlit as st
from src.utils import get_supported_languages

def render_sidebar():
    """Render the sidebar with all settings"""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Extraction Settings
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
        resize_width = 1280
        resize_height = 720
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
        
        st.markdown("---")
        st.markdown("### 🌐 Language Settings")
        
        # Get supported languages (EN, HI, BN only)
        supported_langs = {
            'en': 'English 🇬🇧',
            'hi': 'Hindi 🇮🇳',
            'bn': 'Bengali 🇧🇩'
        }
        
        # Source language for transcription
        source_lang = st.selectbox(
            "📝 Source Language",
            ["auto", "en"],
            index=1,
            help="Language of the video content"
        )
        
        # Target language for translation (3 languages only)
        target_lang_code = st.selectbox(
            "🌐 Translate To",
            list(supported_langs.keys()),
            format_func=lambda x: supported_langs[x],
            index=1,  # Default to Hindi
            help="Choose language for translation and audio"
        )
        target_lang_name = supported_langs.get(target_lang_code, 'Hindi 🇮🇳')
        
        audio_speed = st.slider(
            "🎵 Audio Speed",
            min_value=50,
            max_value=200,
            value=100,
            step=10,
            help="50% = slow, 100% = normal, 200% = fast"
        )
    
    return {
        'frame_interval': frame_interval,
        'quality': quality,
        'resize_frames': resize_frames,
        'resize_width': resize_width,
        'resize_height': resize_height,
        'max_frames': max_frames,
        'source_lang': source_lang,
        'target_lang_code': target_lang_code,
        'target_lang_name': target_lang_name.replace(' 🇬🇧', '').replace(' 🇮🇳', '').replace(' 🇧🇩', ''),
        'audio_speed': audio_speed
    }