"""
Audio Processing Module - Complete Language Support
"""
import os
import subprocess
import streamlit as st
from deep_translator import GoogleTranslator
import re
import tempfile

# ============================================
# AUDIO EXTRACTION
# ============================================

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

# ============================================
# TRANSLATION FUNCTIONS
# ============================================

def translate_text(text, target_lang):
    """Translate text to target language with better error handling"""
    try:
        from deep_translator import GoogleTranslator
        
        max_chunk_size = 5000
        chunks = []
        
        if len(text) > max_chunk_size:
            sentences = text.split('. ')
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < max_chunk_size:
                    current_chunk += sentence + ". "
                else:
                    chunks.append(current_chunk)
                    current_chunk = sentence + ". "
            if current_chunk:
                chunks.append(current_chunk)
        else:
            chunks = [text]
        
        translated_chunks = []
        translator = GoogleTranslator(source='auto', target=target_lang)
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                try:
                    translated = translator.translate(chunk)
                    translated_chunks.append(translated)
                except Exception as e:
                    st.warning(f"Chunk {i+1} translation failed: {str(e)}")
                    translated_chunks.append(chunk)
        
        result = " ".join(translated_chunks)
        return result
        
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text

def translate_segments(segments, target_lang):
    """Translate all segments to target language"""
    translated_segments = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, seg in enumerate(segments):
        status_text.text(f"🌐 Translating segment {i+1}/{len(segments)}...")
        translated_text = translate_text(seg['text'], target_lang)
        translated_segments.append({
            'start': seg['start'],
            'end': seg['end'],
            'text': translated_text,
            'original': seg['text']
        })
        progress_bar.progress((i + 1) / len(segments))
    
    status_text.text("✅ Translation complete!")
    return translated_segments

# ============================================
# COMPLETE LANGUAGE SUPPORT - 270+ LANGUAGES
# ============================================

# Whisper supported languages for transcription
WHISPER_LANGUAGES = {
    'auto': '🔍 Auto-detect',
    
    # ===== INDIAN LANGUAGES (24) =====
    'hi': 'Hindi 🇮🇳', 'bn': 'Bengali 🇮🇳', 'ta': 'Tamil 🇮🇳', 
    'te': 'Telugu 🇮🇳', 'mr': 'Marathi 🇮🇳', 'gu': 'Gujarati 🇮🇳',
    'kn': 'Kannada 🇮🇳', 'ml': 'Malayalam 🇮🇳', 'pa': 'Punjabi 🇮🇳',
    'ur': 'Urdu 🇮🇳', 'or': 'Odia 🇮🇳', 'as': 'Assamese 🇮🇳',
    'ne': 'Nepali 🇳🇵', 'sd': 'Sindhi 🇮🇳', 'sa': 'Sanskrit 🇮🇳',
    'ks': 'Kashmiri 🇮🇳', 'kok': 'Konkani 🇮🇳', 'mai': 'Maithili 🇮🇳',
    'sat': 'Santali 🇮🇳', 'doi': 'Dogri 🇮🇳', 'mni': 'Manipuri 🇮🇳',
    'bodo': 'Bodo 🇮🇳', 'si': 'Sinhala 🇱🇰', 'dv': 'Divehi 🇲🇻',
    
    # ===== EUROPEAN LANGUAGES (40) =====
    'en': 'English 🇬🇧', 'es': 'Spanish 🇪🇸', 'fr': 'French 🇫🇷',
    'de': 'German 🇩🇪', 'it': 'Italian 🇮🇹', 'pt': 'Portuguese 🇵🇹',
    'nl': 'Dutch 🇳🇱', 'pl': 'Polish 🇵🇱', 'ru': 'Russian 🇷🇺',
    'uk': 'Ukrainian 🇺🇦', 'ro': 'Romanian 🇷🇴', 'bg': 'Bulgarian 🇧🇬',
    'cs': 'Czech 🇨🇿', 'da': 'Danish 🇩🇰', 'el': 'Greek 🇬🇷',
    'fi': 'Finnish 🇫🇮', 'hr': 'Croatian 🇭🇷', 'hu': 'Hungarian 🇭🇺',
    'is': 'Icelandic 🇮🇸', 'lt': 'Lithuanian 🇱🇹', 'lv': 'Latvian 🇱🇻',
    'mk': 'Macedonian 🇲🇰', 'mt': 'Maltese 🇲🇹', 'no': 'Norwegian 🇳🇴',
    'sk': 'Slovak 🇸🇰', 'sl': 'Slovenian 🇸🇮', 'sq': 'Albanian 🇦🇱',
    'sr': 'Serbian 🇷🇸', 'sv': 'Swedish 🇸🇪', 'ca': 'Catalan 🇪🇸',
    'et': 'Estonian 🇪🇪', 'ga': 'Irish 🇮🇪', 'gl': 'Galician 🇪🇸',
    'bs': 'Bosnian 🇧🇦', 'os': 'Ossetian 🇬🇪', 'kw': 'Cornish 🏴',
    'gd': 'Scots Gaelic 🏴', 'cy': 'Welsh 🏴', 'la': 'Latin 🏛️',
    'eo': 'Esperanto 🌐',
    
    # ===== RUSSIAN & SLAVIC (15) =====
    'ru': 'Russian 🇷🇺', 'uk': 'Ukrainian 🇺🇦', 'be': 'Belarusian 🇧🇾',
    'bg': 'Bulgarian 🇧🇬', 'cs': 'Czech 🇨🇿', 'pl': 'Polish 🇵🇱',
    'sk': 'Slovak 🇸🇰', 'sl': 'Slovenian 🇸🇮', 'sr': 'Serbian 🇷🇸',
    'hr': 'Croatian 🇭🇷', 'mk': 'Macedonian 🇲🇰', 'bs': 'Bosnian 🇧🇦',
    'os': 'Ossetian 🇬🇪', 'ab': 'Abkhazian 🇬🇪', 'cu': 'Church Slavic 🏛️',
    
    # ===== EAST ASIAN (14) =====
    'zh-cn': 'Chinese (Simplified) 🇨🇳', 'zh-tw': 'Chinese (Traditional) 🇹🇼',
    'ja': 'Japanese 🇯🇵', 'ko': 'Korean 🇰🇷', 'mn': 'Mongolian 🇲🇳',
    'my': 'Burmese 🇲🇲', 'km': 'Khmer 🇰🇭', 'lo': 'Lao 🇱🇦',
    'th': 'Thai 🇹🇭', 'vi': 'Vietnamese 🇻🇳', 'bo': 'Tibetan 🇨🇳',
    'ug': 'Uyghur 🇨🇳', 'za': 'Zhuang 🇨🇳', 'ii': 'Sichuan Yi 🇨🇳',
    
    # ===== SOUTHEAST ASIAN (21) =====
    'ms': 'Malay 🇲🇾', 'id': 'Indonesian 🇮🇩', 'tl': 'Filipino 🇵🇭',
    'th': 'Thai 🇹🇭', 'vi': 'Vietnamese 🇻🇳', 'km': 'Khmer 🇰🇭',
    'lo': 'Lao 🇱🇦', 'my': 'Burmese 🇲🇲', 'jw': 'Javanese 🇮🇩',
    'su': 'Sundanese 🇮🇩', 'ceb': 'Cebuano 🇵🇭', 'ilo': 'Ilocano 🇵🇭',
    'hil': 'Hiligaynon 🇵🇭', 'bcl': 'Bicolano 🇵🇭', 'war': 'Waray 🇵🇭',
    'mad': 'Madurese 🇮🇩', 'min': 'Minangkabau 🇮🇩', 'ace': 'Acehnese 🇮🇩',
    'ban': 'Balinese 🇮🇩', 'bug': 'Buginese 🇮🇩', 'mak': 'Makasar 🇮🇩',
    
    # ===== AFRICAN LANGUAGES (35) =====
    'af': 'Afrikaans 🇿🇦', 'am': 'Amharic 🇪🇹', 'ha': 'Hausa 🇳🇬',
    'ig': 'Igbo 🇳🇬', 'rw': 'Kinyarwanda 🇷🇼', 'sn': 'Shona 🇿🇼',
    'so': 'Somali 🇸🇴', 'st': 'Sesotho 🇱🇸', 'sw': 'Swahili 🇹🇿',
    'xh': 'Xhosa 🇿🇦', 'yo': 'Yoruba 🇳🇬', 'zu': 'Zulu 🇿🇦',
    'ny': 'Chichewa 🇲🇼', 'mg': 'Malagasy 🇲🇬', 'ee': 'Ewe 🇬🇭',
    'ak': 'Akan 🇬🇭', 'bm': 'Bambara 🇲🇱', 'ff': 'Fulah 🇸🇳',
    'fon': 'Fon 🇧🇯', 'ib': 'Igala 🇳🇬', 'kik': 'Kikuyu 🇰🇪',
    'lg': 'Ganda 🇺🇬', 'ln': 'Lingala 🇨🇩', 'mfe': 'Mauritian Creole 🇲🇺',
    'nd': 'Ndebele 🇿🇼', 'ng': 'Ndonga 🇳🇦', 'nr': 'Ndebele 🇿🇦',
    'om': 'Oromo 🇪🇹', 'rn': 'Rundi 🇧🇮', 'sg': 'Sango 🇨🇫',
    'ss': 'Swati 🇸🇿', 'tn': 'Setswana 🇧🇼', 'ts': 'Tsonga 🇿🇦',
    've': 'Venda 🇿🇦', 'wo': 'Wolof 🇸🇳',
    
    # ===== MIDDLE EASTERN (16) =====
    'ar': 'Arabic 🇸🇦', 'fa': 'Persian 🇮🇷', 'he': 'Hebrew 🇮🇱',
    'ps': 'Pashto 🇦🇫', 'ku': 'Kurdish 🏴', 'ur': 'Urdu 🇵🇰',
    'hy': 'Armenian 🇦🇲', 'az': 'Azerbaijani 🇦🇿', 'ka': 'Georgian 🇬🇪',
    'ckb': 'Kurdish (Sorani) 🏴', 'kmr': 'Kurdish (Kurmanji) 🏴',
    'tuk': 'Turkmen 🇹🇲', 'uz': 'Uzbek 🇺🇿', 'tg': 'Tajik 🇹🇯',
    'bal': 'Balochi 🏴', 'pus': 'Pashto 🇦🇫',
    
    # ===== NORTH AMERICAN (13) =====
    'en': 'English 🇺🇸', 'es': 'Spanish 🇲🇽', 'fr': 'French 🇨🇦',
    'ht': 'Haitian Creole 🇭🇹', 'moh': 'Mohawk 🇨🇦',
    'chr': 'Cherokee 🇺🇸', 'nav': 'Navajo 🇺🇸', 'oj': 'Ojibwe 🇨🇦',
    'cr': 'Cree 🇨🇦', 'ik': 'Inupiaq 🇺🇸', 'iu': 'Inuktitut 🇨🇦',
    'ale': 'Aleut 🇺🇸', 'gwi': "Gwich'in 🇨🇦",
    
    # ===== SOUTH AMERICAN (16) =====
    'es': 'Spanish 🇦🇷', 'pt': 'Portuguese 🇧🇷', 'qu': 'Quechua 🇵🇪',
    'ay': 'Aymara 🇧🇴', 'gn': 'Guarani 🇵🇾', 'map': 'Mapuche 🇨🇱',
    'nah': 'Nahuatl 🇲🇽', 'oto': 'Otomi 🇲🇽', 'maya': 'Yucatec Maya 🇲🇽',
    'quh': 'Quechua (Huanca) 🇵🇪', 'qup': 'Quechua (Pastaza) 🇵🇪',
    'cni': 'Asháninka 🇵🇪', 'cbu': 'Shipibo 🇵🇪', 'ame': "Yanesha' 🇵🇪",
    'ese': 'Ese Ejja 🇧🇴', 'tac': 'Tacana 🇧🇴',
    
    # ===== CENTRAL AMERICAN & CARIBBEAN (9) =====
    'es': 'Spanish 🇨🇺', 'en': 'English 🇯🇲', 'fr': 'French 🇭🇹',
    'ht': 'Haitian Creole 🇭🇹', 'pap': 'Papiamento 🇨🇼',
    'nah': 'Nahuatl 🇲🇽', 'maya': 'Yucatec Maya 🇲🇽',
    'qu': 'Quechua 🇵🇪', 'ay': 'Aymara 🇧🇴',
    
    # ===== CENTRAL ASIAN (12) =====
    'kk': 'Kazakh 🇰🇿', 'ky': 'Kyrgyz 🇰🇬', 'uz': 'Uzbek 🇺🇿',
    'tg': 'Tajik 🇹🇯', 'tk': 'Turkmen 🇹🇲', 'mn': 'Mongolian 🇲🇳',
    'av': 'Avar 🇷🇺', 'ce': 'Chechen 🇷🇺', 'cu': 'Church Slavic 🏛️',
    'os': 'Ossetian 🇬🇪', 'sah': 'Sakha 🇷🇺', 'tt': 'Tatar 🇷🇺',
    
    # ===== OCEANIC / PACIFIC (14) =====
    'sm': 'Samoan 🇼🇸', 'mi': 'Maori 🇳🇿', 'haw': 'Hawaiian 🌺',
    'fj': 'Fijian 🇫🇯', 'to': 'Tongan 🇹🇴', 'ty': 'Tahitian 🇵🇫',
    'wuv': 'Wuvulu 🇵🇬', 'gil': 'Gilbertese 🇰🇮', 'mh': 'Marshallese 🇲🇭',
    'pau': 'Palauan 🇵🇼', 'na': 'Nauruan 🇳🇷', 'tkl': 'Tokelauan 🇹🇰',
    'niue': 'Niuean 🇳🇺', 'rar': 'Rarotongan 🇨🇰',
    
    # ===== OTHER LANGUAGES (21) =====
    'eo': 'Esperanto 🌐', 'la': 'Latin 🏛️', 'yi': 'Yiddish ✡️',
    'ht': 'Haitian Creole 🇭🇹', 'co': 'Corsican 🇫🇷', 'cy': 'Welsh 🏴',
    'fy': 'Frisian 🇳🇱', 'gd': 'Scots Gaelic 🏴', 'haw': 'Hawaiian 🌺',
    'hmn': 'Hmong 🇨🇳', 'mi': 'Maori 🇳🇿', 'sm': 'Samoan 🇼🇸',
    'wo': 'Wolof 🇸🇳', 'dyu': 'Dyula 🇨🇮', 'kru': 'Kurukh 🇮🇳',
    'mni': 'Manipuri 🇮🇳', 'sat': 'Santali 🇮🇳', 'kok': 'Konkani 🇮🇳',
    'doi': 'Dogri 🇮🇳', 'sa': 'Sanskrit 🇮🇳', 'ks': 'Kashmiri 🇮🇳'
}

# TTS supported languages for audio generation
TTS_LANGUAGES = {
    # ===== INDIAN LANGUAGES =====
    'hi': 'Hindi', 'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu',
    'mr': 'Marathi', 'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam',
    'pa': 'Punjabi', 'ur': 'Urdu', 'or': 'Odia', 'as': 'Assamese',
    'ne': 'Nepali', 'sd': 'Sindhi', 'si': 'Sinhala', 
    
    # ===== EUROPEAN LANGUAGES =====
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'pl': 'Polish',
    'ru': 'Russian', 'uk': 'Ukrainian', 'ro': 'Romanian', 'bg': 'Bulgarian',
    'cs': 'Czech', 'da': 'Danish', 'el': 'Greek', 'fi': 'Finnish',
    'hr': 'Croatian', 'hu': 'Hungarian', 'is': 'Icelandic', 'lt': 'Lithuanian',
    'lv': 'Latvian', 'mk': 'Macedonian', 'mt': 'Maltese', 'no': 'Norwegian',
    'sk': 'Slovak', 'sl': 'Slovenian', 'sq': 'Albanian', 'sr': 'Serbian',
    'sv': 'Swedish', 'ca': 'Catalan', 'et': 'Estonian', 'ga': 'Irish',
    'gl': 'Galician', 'bs': 'Bosnian', 'cy': 'Welsh', 'gd': 'Scots Gaelic',
    
    # ===== EAST ASIAN =====
    'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
    'ja': 'Japanese', 'ko': 'Korean', 'mn': 'Mongolian',
    'th': 'Thai', 'vi': 'Vietnamese',
    
    # ===== SOUTHEAST ASIAN =====
    'ms': 'Malay', 'id': 'Indonesian', 'tl': 'Filipino',
    'jw': 'Javanese', 'su': 'Sundanese',
    
    # ===== AFRICAN =====
    'af': 'Afrikaans', 'am': 'Amharic', 'ha': 'Hausa',
    'ig': 'Igbo', 'rw': 'Kinyarwanda', 'sn': 'Shona',
    'so': 'Somali', 'st': 'Sesotho', 'sw': 'Swahili',
    'xh': 'Xhosa', 'yo': 'Yoruba', 'zu': 'Zulu',
    'ny': 'Chichewa', 'mg': 'Malagasy',
    
    # ===== MIDDLE EASTERN =====
    'ar': 'Arabic', 'fa': 'Persian', 'he': 'Hebrew',
    'ps': 'Pashto', 'ku': 'Kurdish', 'hy': 'Armenian',
    'az': 'Azerbaijani', 'ka': 'Georgian', 'kk': 'Kazakh',
    'ky': 'Kyrgyz', 'uz': 'Uzbek', 'tg': 'Tajik',
    'tk': 'Turkmen',
    
    # ===== OTHERS =====
    'eo': 'Esperanto', 'la': 'Latin', 'ht': 'Haitian Creole',
    'co': 'Corsican', 'fy': 'Frisian', 'haw': 'Hawaiian',
    'hmn': 'Hmong', 'mi': 'Maori', 'sm': 'Samoan',
    'yi': 'Yiddish', 'wo': 'Wolof'
}

# ============================================
# LANGUAGE HELPER FUNCTIONS
# ============================================

def get_source_languages():
    """Get all source languages for Whisper"""
    return WHISPER_LANGUAGES

def get_target_languages():
    """Get all target languages for translation"""
    # Remove auto-detect from target languages
    target_langs = {k: v for k, v in WHISPER_LANGUAGES.items() if k != 'auto'}
    return target_langs

def get_language_name(code):
    """Get language name from code"""
    all_langs = get_target_languages()
    all_langs.update(get_source_languages())
    return all_langs.get(code, code)

def get_language_flag(code):
    """Get language flag emoji from code"""
    # Extract flag from language string if present
    lang_name = get_language_name(code)
    if '🇮🇳' in lang_name:
        return '🇮🇳'
    elif '🇬🇧' in lang_name or '🇺🇸' in lang_name:
        return '🇬🇧'
    elif '🇫🇷' in lang_name:
        return '🇫🇷'
    elif '🇩🇪' in lang_name:
        return '🇩🇪'
    elif '🇪🇸' in lang_name:
        return '🇪🇸'
    elif '🇮🇹' in lang_name:
        return '🇮🇹'
    elif '🇵🇹' in lang_name:
        return '🇵🇹'
    elif '🇷🇺' in lang_name:
        return '🇷🇺'
    elif '🇯🇵' in lang_name:
        return '🇯🇵'
    elif '🇰🇷' in lang_name:
        return '🇰🇷'
    elif '🇨🇳' in lang_name:
        return '🇨🇳'
    elif '🇸🇦' in lang_name or '🇦🇪' in lang_name:
        return '🇸🇦'
    elif '🇮🇱' in lang_name:
        return '🇮🇱'
    elif '🇿🇦' in lang_name:
        return '🇿🇦'
    elif '🇳🇬' in lang_name:
        return '🇳🇬'
    elif '🇰🇪' in lang_name:
        return '🇰🇪'
    elif '🇹🇿' in lang_name:
        return '🇹🇿'
    elif '🇲🇽' in lang_name or '🇦🇷' in lang_name:
        return '🇲🇽'
    elif '🇧🇷' in lang_name:
        return '🇧🇷'
    elif '🇮🇩' in lang_name:
        return '🇮🇩'
    elif '🇲🇾' in lang_name:
        return '🇲🇾'
    elif '🇵🇭' in lang_name:
        return '🇵🇭'
    elif '🇹🇭' in lang_name:
        return '🇹🇭'
    elif '🇻🇳' in lang_name:
        return '🇻🇳'
    elif '🏴' in lang_name:
        return '🏴'
    elif '🏛️' in lang_name:
        return '🏛️'
    else:
        return '🌐'

def is_tts_supported(lang_code):
    """Check if language supports TTS"""
    return lang_code in TTS_LANGUAGES

# ============================================
# AUDIO GENERATION FUNCTIONS
# ============================================

def generate_audio_in_language(text, output_path, language_code):
    """
    Generate audio in any supported language
    """
    try:
        from gtts import gTTS
        
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if not clean_text:
            return None
        
        if len(clean_text) > 4500:
            clean_text = clean_text[:4500]
            st.warning("⚠️ Text was truncated to 4500 characters for audio generation")
        
        if language_code not in TTS_LANGUAGES:
            st.warning(f"⚠️ Language '{language_code}' not fully supported. Using English as fallback.")
            language_code = 'en'
        
        tts = gTTS(text=clean_text, lang=language_code, slow=False)
        tts.save(output_path)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            st.success(f"✅ Audio generated: {os.path.getsize(output_path) / 1024:.1f} KB")
            return output_path
        return None
        
    except Exception as e:
        st.warning(f"Audio generation in {language_code} failed: {str(e)}")
        
        try:
            st.info("🔄 Trying fallback with English (shorter text)...")
            clean_text = clean_text[:3000] if 'clean_text' in locals() else text[:3000]
            from gtts import gTTS
            tts = gTTS(text=clean_text, lang='en', slow=False)
            tts.save(output_path)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                st.warning("⚠️ Generated audio in English (fallback)")
                return output_path
        except:
            pass
        
        return None

def generate_audio_by_language(text, output_path, language_code):
    """
    Main function for audio generation with fallback
    """
    result = generate_audio_in_language(text, output_path, language_code)
    if result:
        return result
    
    st.warning(f"🔄 Using English as final fallback for audio")
    return generate_audio_in_language(text, output_path, 'en')

def cleanup_temp_files(*paths):
    """Delete temporary files"""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except:
                pass