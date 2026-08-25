"""
Sidebar UI Components - Clean Language Selection
"""
import streamlit as st
from src.audio_processor import (
    get_source_languages,
    get_target_languages,
    get_language_name,
    get_language_flag,
    is_tts_supported
)

# ============================================
# COMPLETE LANGUAGE CATEGORIES
# ============================================

LANGUAGE_CATEGORIES = {
    "🇮🇳 Indian": {
        "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
        "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam",
        "pa": "Punjabi", "ur": "Urdu", "or": "Odia", "as": "Assamese",
        "ne": "Nepali", "sd": "Sindhi", "sa": "Sanskrit", "ks": "Kashmiri",
        "kok": "Konkani", "mai": "Maithili", "sat": "Santali", "doi": "Dogri",
        "mni": "Manipuri", "bodo": "Bodo", "si": "Sinhala", "dv": "Divehi", 
    },
    "🇪🇺 European": {
        "en": "English", "es": "Spanish", "fr": "French", "de": "German",
        "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
        "ru": "Russian", "uk": "Ukrainian", "ro": "Romanian", "bg": "Bulgarian",
        "cs": "Czech", "da": "Danish", "el": "Greek", "fi": "Finnish",
        "hr": "Croatian", "hu": "Hungarian", "is": "Icelandic", "lt": "Lithuanian",
        "lv": "Latvian", "mk": "Macedonian", "mt": "Maltese", "no": "Norwegian",
        "sk": "Slovak", "sl": "Slovenian", "sq": "Albanian", "sr": "Serbian",
        "sv": "Swedish", "ca": "Catalan", "et": "Estonian", "ga": "Irish",
        "gl": "Galician", "bs": "Bosnian", "cy": "Welsh", "gd": "Scots Gaelic",
        "la": "Latin", "eo": "Esperanto"
    },
    "🇷🇺 Russian & Slavic": {
        "ru": "Russian", "uk": "Ukrainian", "be": "Belarusian",
        "bg": "Bulgarian", "cs": "Czech", "pl": "Polish",
        "sk": "Slovak", "sl": "Slovenian", "sr": "Serbian",
        "hr": "Croatian", "mk": "Macedonian", "bs": "Bosnian"
    },
    "🇯🇵 East Asian": {
        "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
        "ja": "Japanese", "ko": "Korean", "mn": "Mongolian",
        "my": "Burmese", "km": "Khmer", "lo": "Lao",
        "th": "Thai", "vi": "Vietnamese", "bo": "Tibetan"
    },
    "🇲🇾 Southeast Asian": {
        "ms": "Malay", "id": "Indonesian", "tl": "Filipino",
        "th": "Thai", "vi": "Vietnamese", "km": "Khmer",
        "lo": "Lao", "my": "Burmese", "jw": "Javanese",
        "su": "Sundanese", "ceb": "Cebuano"
    },
    "🌍 African": {
        "af": "Afrikaans", "am": "Amharic", "ha": "Hausa",
        "ig": "Igbo", "rw": "Kinyarwanda", "sn": "Shona",
        "so": "Somali", "st": "Sesotho", "sw": "Swahili",
        "xh": "Xhosa", "yo": "Yoruba", "zu": "Zulu",
        "ny": "Chichewa", "mg": "Malagasy", "ak": "Akan",
        "bm": "Bambara", "ee": "Ewe", "ff": "Fulah",
        "ln": "Lingala", "om": "Oromo", "rn": "Rundi"
    },
    "🌏 Middle Eastern": {
        "ar": "Arabic", "fa": "Persian", "he": "Hebrew",
        "ps": "Pashto", "ku": "Kurdish", "ur": "Urdu",
        "hy": "Armenian", "az": "Azerbaijani", "ka": "Georgian",
        "tuk": "Turkmen", "uz": "Uzbek", "tg": "Tajik"
    },
    "🌎 Americas": {
        "es": "Spanish", "pt": "Portuguese", "en": "English",
        "fr": "French", "ht": "Haitian Creole", "qu": "Quechua",
        "ay": "Aymara", "gn": "Guarani", "nah": "Nahuatl",
        "maya": "Yucatec Maya", "moh": "Mohawk", "chr": "Cherokee",
        "nav": "Navajo", "oj": "Ojibwe", "cr": "Cree"
    },
    "🇰🇿 Central Asian": {
        "kk": "Kazakh", "ky": "Kyrgyz", "uz": "Uzbek",
        "tg": "Tajik", "tk": "Turkmen", "mn": "Mongolian",
        "tt": "Tatar", "sah": "Sakha", "ce": "Chechen"
    },
    "🌺 Pacific": {
        "sm": "Samoan", "mi": "Maori", "haw": "Hawaiian",
        "fj": "Fijian", "to": "Tongan", "ty": "Tahitian",
        "gil": "Gilbertese", "mh": "Marshallese", "pau": "Palauan"
    },
    "🌐 Other": {
        "eo": "Esperanto", "la": "Latin", "yi": "Yiddish",
        "co": "Corsican", "fy": "Frisian", "wo": "Wolof",
        "hmn": "Hmong", "sa": "Sanskrit", "kok": "Konkani"
    }
}

def get_all_languages():
    """Get all languages from categories"""
    all_langs = {}
    for category, langs in LANGUAGE_CATEGORIES.items():
        all_langs.update(langs)
    return all_langs

def render_language_selector(label, key_prefix, include_auto=True):
    """
    Clean language selector with dropdown categories
    """
    all_langs = get_all_languages()
    category_names = list(LANGUAGE_CATEGORIES.keys())
    
    # Session state keys
    category_key = f"{key_prefix}_category"
    lang_key = f"{key_prefix}_lang"
    
    # Initialize session state
    if category_key not in st.session_state:
        st.session_state[category_key] = category_names[0]
    
    if lang_key not in st.session_state:
        st.session_state[lang_key] = "en" if include_auto else list(all_langs.keys())[0]
    
    # ============================================
    # REGION SELECTOR - SCROLLABLE DROPDOWN
    # ============================================
    st.markdown(f"**{label}**")
    
    # Create a clean dropdown for categories (scrollable)
    selected_category = st.selectbox(
        "Select Region",
        options=category_names,
        index=category_names.index(st.session_state[category_key]),
        key=f"{key_prefix}_category_select",
        label_visibility="collapsed"
    )
    
    # Update session state
    if selected_category != st.session_state[category_key]:
        st.session_state[category_key] = selected_category
        # Auto-select first language in new category
        first_lang = list(LANGUAGE_CATEGORIES[selected_category].keys())[0]
        st.session_state[lang_key] = first_lang
        st.rerun()
    
    # Show region info
    st.caption(f"📂 {st.session_state[category_key]}")
    
    # ============================================
    # LANGUAGE SELECTOR - VERTICAL LIST
    # ============================================
    # Get languages for selected category
    selected_category = st.session_state[category_key]
    category_langs = LANGUAGE_CATEGORIES.get(selected_category, {})
    
    # Build options
    lang_options = {}
    if include_auto:
        lang_options["auto"] = "🔍 Auto-detect"
    lang_options.update(category_langs)
    
    # Create scrollable language list
    lang_codes = list(lang_options.keys())
    lang_display = [f"{get_language_flag(code)} {name}" for code, name in lang_options.items()]
    
    # Find current index
    current_lang = st.session_state[lang_key]
    if current_lang not in lang_codes:
        current_lang = lang_codes[0]
        st.session_state[lang_key] = current_lang
    
    try:
        current_index = lang_codes.index(current_lang)
    except ValueError:
        current_index = 0
    
    # Show language dropdown
    selected_lang = st.selectbox(
        label="Select Language",
        options=lang_codes,
        format_func=lambda x: f"{get_language_flag(x)} {lang_options.get(x, x)}",
        index=current_index,
        key=f"{key_prefix}_lang_select",
        label_visibility="collapsed"
    )
    
    # Update session state
    if selected_lang != st.session_state[lang_key]:
        st.session_state[lang_key] = selected_lang
    
    # Show language count
    st.caption(f"🗣️ {len(category_langs)} languages available")
    
    # Show selected language prominently
    if selected_lang != "auto":
        st.markdown(f"""
        <div style="
            background: #e3f2fd; 
            padding: 8px 12px; 
            border-radius: 5px; 
            border-left: 4px solid #2196f3;
            margin-top: 5px;
        ">
            <b>Selected:</b> {get_language_flag(selected_lang)} {lang_options.get(selected_lang, selected_lang)}
        </div>
        """, unsafe_allow_html=True)
    
    return st.session_state[lang_key]

def render_sidebar():
    """Render the sidebar with all settings"""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Extraction Settings
        st.markdown("### 📷 Extraction")
        frame_interval = st.slider(
            "Extract every N frame",
            min_value=1,
            max_value=120,
            value=30
        )
        
        quality = st.slider(
            "JPEG Quality",
            min_value=30,
            max_value=100,
            value=85
        )
        
        with st.expander("🔄 Resize Options"):
            resize_frames = st.checkbox("Resize frames", value=False)
            if resize_frames:
                col1, col2 = st.columns(2)
                with col1:
                    resize_width = st.number_input("Width", min_value=100, max_value=3840, value=1280)
                with col2:
                    resize_height = st.number_input("Height", min_value=100, max_value=2160, value=720)
        
        with st.expander("⚙️ Advanced"):
            max_frames = st.number_input(
                "Max frames (0=unlimited)",
                min_value=0,
                max_value=10000,
                value=0
            )
        
        st.markdown("---")
        st.markdown("### 🌐 Language Settings")
        
        # ============================================
        # SOURCE LANGUAGE
        # ============================================
        st.markdown("#### 🎯 Source Language")
        st.caption("Language spoken in the video")
        
        source_lang_code = render_language_selector(
            "Source Language",
            "source",
            include_auto=True
        )
        
        st.markdown("---")
        
        # ============================================
        # TARGET LANGUAGE
        # ============================================
        st.markdown("#### 🎯 Target Language")
        st.caption("Language to translate into")
        
        target_lang_code = render_language_selector(
            "Target Language",
            "target",
            include_auto=False
        )
        
        # Show TTS support
        if is_tts_supported(target_lang_code):
            st.success("✅ Audio generation supported")
        else:
            st.warning("⚠️ Audio will use English fallback")
        
        target_lang_name = get_language_name(target_lang_code)
        
        st.markdown("---")
        
        # ============================================
        # AUDIO SETTINGS
        # ============================================
        st.markdown("### 🎵 Audio Settings")
        
        audio_speed = st.slider(
            "Audio Speed",
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
        'resize_width': resize_width if 'resize_width' in locals() else 1280,
        'resize_height': resize_height if 'resize_height' in locals() else 720,
        'max_frames': max_frames,
        'source_lang': source_lang_code,
        'target_lang_code': target_lang_code,
        'target_lang_name': target_lang_name,
        'audio_speed': audio_speed
    }