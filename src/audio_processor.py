"""
Audio Processing Module - LLM-Powered Translation with Groq
"""
import os
import subprocess
import streamlit as st
from deep_translator import GoogleTranslator
import re
import tempfile
import json
import requests
import time

# ============================================
# GET API KEY FROM STREAMLIT SECRETS
# ============================================

def get_api_key():
    """Get Groq API key from Streamlit secrets"""
    try:
        api_key = st.secrets.get("GROQ_API_KEY", None)
        if api_key:
            return api_key
        else:
            st.warning("⚠️ Groq API key not found in secrets. Using Google Translate fallback.")
            return None
    except Exception as e:
        st.warning(f"⚠️ Error reading secrets: {str(e)}. Using Google Translate fallback.")
        return None

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
# LANGUAGE SUPPORT - COMPLETE DICTIONARIES
# ============================================

WHISPER_LANGUAGES = {
    'auto': '🔍 Auto-detect',
    # Indian Languages
    'hi': 'Hindi 🇮🇳', 'bn': 'Bengali 🇮🇳', 'ta': 'Tamil 🇮🇳', 
    'te': 'Telugu 🇮🇳', 'mr': 'Marathi 🇮🇳', 'gu': 'Gujarati 🇮🇳',
    'kn': 'Kannada 🇮🇳', 'ml': 'Malayalam 🇮🇳', 'pa': 'Punjabi 🇮🇳',
    'ur': 'Urdu 🇮🇳', 'or': 'Odia 🇮🇳', 'as': 'Assamese 🇮🇳',
    'ne': 'Nepali 🇳🇵', 'sd': 'Sindhi 🇮🇳', 'sa': 'Sanskrit 🇮🇳',
    'ks': 'Kashmiri 🇮🇳', 'kok': 'Konkani 🇮🇳', 'mai': 'Maithili 🇮🇳',
    'sat': 'Santali 🇮🇳', 'doi': 'Dogri 🇮🇳', 'mni': 'Manipuri 🇮🇳',
    'bodo': 'Bodo 🇮🇳', 'si': 'Sinhala 🇱🇰', 'dv': 'Divehi 🇲🇻',
    
    # European Languages
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
    'bs': 'Bosnian 🇧🇦', 'cy': 'Welsh 🏴', 'gd': 'Scots Gaelic 🏴',
    'la': 'Latin 🏛️', 'eo': 'Esperanto 🌐',
    # East Asian
    'zh-cn': 'Chinese (Simplified) 🇨🇳', 'zh-tw': 'Chinese (Traditional) 🇹🇼',
    'ja': 'Japanese 🇯🇵', 'ko': 'Korean 🇰🇷', 'mn': 'Mongolian 🇲🇳',
    'my': 'Burmese 🇲🇲', 'km': 'Khmer 🇰🇭', 'lo': 'Lao 🇱🇦',
    'th': 'Thai 🇹🇭', 'vi': 'Vietnamese 🇻🇳', 'bo': 'Tibetan 🇨🇳',
    'ug': 'Uyghur 🇨🇳', 'za': 'Zhuang 🇨🇳',
    # Southeast Asian
    'ms': 'Malay 🇲🇾', 'id': 'Indonesian 🇮🇩', 'tl': 'Filipino 🇵🇭',
    'jw': 'Javanese 🇮🇩', 'su': 'Sundanese 🇮🇩', 'ceb': 'Cebuano 🇵🇭',
    'ilo': 'Ilocano 🇵🇭', 'hil': 'Hiligaynon 🇵🇭', 'bcl': 'Bicolano 🇵🇭',
    'war': 'Waray 🇵🇭',
    # African
    'af': 'Afrikaans 🇿🇦', 'am': 'Amharic 🇪🇹', 'ha': 'Hausa 🇳🇬',
    'ig': 'Igbo 🇳🇬', 'rw': 'Kinyarwanda 🇷🇼', 'sn': 'Shona 🇿🇼',
    'so': 'Somali 🇸🇴', 'st': 'Sesotho 🇱🇸', 'sw': 'Swahili 🇹🇿',
    'xh': 'Xhosa 🇿🇦', 'yo': 'Yoruba 🇳🇬', 'zu': 'Zulu 🇿🇦',
    'ny': 'Chichewa 🇲🇼', 'mg': 'Malagasy 🇲🇬', 'ak': 'Akan 🇬🇭',
    'bm': 'Bambara 🇲🇱', 'ee': 'Ewe 🇬🇭', 'ff': 'Fulah 🇸🇳',
    'ln': 'Lingala 🇨🇩', 'om': 'Oromo 🇪🇹', 'rn': 'Rundi 🇧🇮',
    'sg': 'Sango 🇨🇫', 'ss': 'Swati 🇸🇿', 'tn': 'Setswana 🇧🇼',
    'ts': 'Tsonga 🇿🇦', 've': 'Venda 🇿🇦',
    # Middle Eastern
    'ar': 'Arabic 🇸🇦', 'fa': 'Persian 🇮🇷', 'he': 'Hebrew 🇮🇱',
    'ps': 'Pashto 🇦🇫', 'ku': 'Kurdish 🏴', 'hy': 'Armenian 🇦🇲',
    'az': 'Azerbaijani 🇦🇿', 'ka': 'Georgian 🇬🇪',
    'ckb': 'Kurdish (Sorani) 🏴', 'tuk': 'Turkmen 🇹🇲',
    'uz': 'Uzbek 🇺🇿', 'tg': 'Tajik 🇹🇯',
    # Central Asian
    'kk': 'Kazakh 🇰🇿', 'ky': 'Kyrgyz 🇰🇬', 'tt': 'Tatar 🇷🇺',
    'sah': 'Sakha 🇷🇺',
    # Americas
    'qu': 'Quechua 🇵🇪', 'ay': 'Aymara 🇧🇴', 'gn': 'Guarani 🇵🇾',
    'nah': 'Nahuatl 🇲🇽', 'maya': 'Yucatec Maya 🇲🇽',
    'moh': 'Mohawk 🇨🇦', 'chr': 'Cherokee 🇺🇸', 'nav': 'Navajo 🇺🇸',
    'oj': 'Ojibwe 🇨🇦', 'cr': 'Cree 🇨🇦', 'ik': 'Inupiaq 🇺🇸',
    'iu': 'Inuktitut 🇨🇦',
    # Pacific
    'sm': 'Samoan 🇼🇸', 'mi': 'Maori 🇳🇿', 'haw': 'Hawaiian 🌺',
    'fj': 'Fijian 🇫🇯', 'to': 'Tongan 🇹🇴', 'ty': 'Tahitian 🇵🇫',
    'gil': 'Gilbertese 🇰🇮', 'mh': 'Marshallese 🇲🇭', 'pau': 'Palauan 🇵🇼',
    'na': 'Nauruan 🇳🇷', 'tkl': 'Tokelauan 🇹🇰',
    # Other
    'eo': 'Esperanto 🌐', 'la': 'Latin 🏛️', 'yi': 'Yiddish ✡️',
    'ht': 'Haitian Creole 🇭🇹', 'co': 'Corsican 🇫🇷', 'fy': 'Frisian 🇳🇱',
    'wo': 'Wolof 🇸🇳', 'hmn': 'Hmong 🇨🇳'
}

TTS_LANGUAGES = {
    'hi': 'Hindi', 'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu',
    'mr': 'Marathi', 'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam',
    'pa': 'Punjabi', 'ur': 'Urdu', 'or': 'Odia', 'as': 'Assamese',
    'ne': 'Nepali', 'sd': 'Sindhi', 'si': 'Sinhala',
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'pl': 'Polish',
    'ru': 'Russian', 'uk': 'Ukrainian', 'ro': 'Romanian', 'bg': 'Bulgarian',
    'cs': 'Czech', 'da': 'Danish', 'el': 'Greek', 'fi': 'Finnish',
    'hr': 'Croatian', 'hu': 'Hungarian', 'is': 'Icelandic', 'lt': 'Lithuanian',
    'lv': 'Latvian', 'mk': 'Macedonian', 'mt': 'Maltese', 'no': 'Norwegian',
    'sk': 'Slovak', 'sl': 'Slovenian', 'sq': 'Albanian', 'sr': 'Serbian',
    'sv': 'Swedish', 'ca': 'Catalan', 'et': 'Estonian', 'ga': 'Irish',
    'gl': 'Galician', 'bs': 'Bosnian', 'cy': 'Welsh', 'gd': 'Scots Gaelic',
    'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
    'ja': 'Japanese', 'ko': 'Korean', 'mn': 'Mongolian',
    'th': 'Thai', 'vi': 'Vietnamese',
    'ms': 'Malay', 'id': 'Indonesian', 'tl': 'Filipino',
    'jw': 'Javanese', 'su': 'Sundanese',
    'af': 'Afrikaans', 'am': 'Amharic', 'ha': 'Hausa',
    'ig': 'Igbo', 'rw': 'Kinyarwanda', 'sn': 'Shona',
    'so': 'Somali', 'st': 'Sesotho', 'sw': 'Swahili',
    'xh': 'Xhosa', 'yo': 'Yoruba', 'zu': 'Zulu',
    'ny': 'Chichewa', 'mg': 'Malagasy',
    'ar': 'Arabic', 'fa': 'Persian', 'he': 'Hebrew',
    'ps': 'Pashto', 'ku': 'Kurdish', 'hy': 'Armenian',
    'az': 'Azerbaijani', 'ka': 'Georgian', 'kk': 'Kazakh',
    'ky': 'Kyrgyz', 'uz': 'Uzbek', 'tg': 'Tajik',
    'tk': 'Turkmen',
    'eo': 'Esperanto', 'la': 'Latin', 'ht': 'Haitian Creole',
    'co': 'Corsican', 'fy': 'Frisian', 'haw': 'Hawaiian',
    'hmn': 'Hmong', 'mi': 'Maori', 'sm': 'Samoan',
    'yi': 'Yiddish', 'wo': 'Wolof'
}

# ============================================
# LANGUAGE HELPER FUNCTIONS
# ============================================

def get_source_languages():
    return WHISPER_LANGUAGES

def get_target_languages():
    target_langs = {k: v for k, v in WHISPER_LANGUAGES.items() if k != 'auto'}
    return target_langs

def get_language_name(code):
    lang_names = {
        'hi': 'Hindi', 'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu',
        'mr': 'Marathi', 'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam',
        'pa': 'Punjabi', 'ur': 'Urdu', 'or': 'Odia', 'as': 'Assamese',
        'ne': 'Nepali', 'sd': 'Sindhi', 'si': 'Sinhala', 'dv': 'Divehi',
        'sa': 'Sanskrit', 'ks': 'Kashmiri', 'kok': 'Konkani', 'mai': 'Maithili',
        'sat': 'Santali', 'doi': 'Dogri', 'mni': 'Manipuri', 'bodo': 'Bodo', 
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
        'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'pl': 'Polish',
        'ru': 'Russian', 'uk': 'Ukrainian', 'ro': 'Romanian', 'bg': 'Bulgarian',
        'cs': 'Czech', 'da': 'Danish', 'el': 'Greek', 'fi': 'Finnish',
        'hr': 'Croatian', 'hu': 'Hungarian', 'is': 'Icelandic', 'lt': 'Lithuanian',
        'lv': 'Latvian', 'mk': 'Macedonian', 'mt': 'Maltese', 'no': 'Norwegian',
        'sk': 'Slovak', 'sl': 'Slovenian', 'sq': 'Albanian', 'sr': 'Serbian',
        'sv': 'Swedish', 'ca': 'Catalan', 'et': 'Estonian', 'ga': 'Irish',
        'gl': 'Galician', 'bs': 'Bosnian', 'cy': 'Welsh', 'gd': 'Scots Gaelic',
        'la': 'Latin', 'eo': 'Esperanto',
        'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)',
        'ja': 'Japanese', 'ko': 'Korean', 'mn': 'Mongolian',
        'my': 'Burmese', 'km': 'Khmer', 'lo': 'Lao',
        'th': 'Thai', 'vi': 'Vietnamese', 'bo': 'Tibetan',
        'ug': 'Uyghur', 'za': 'Zhuang',
        'ms': 'Malay', 'id': 'Indonesian', 'tl': 'Filipino',
        'jw': 'Javanese', 'su': 'Sundanese', 'ceb': 'Cebuano',
        'af': 'Afrikaans', 'am': 'Amharic', 'ha': 'Hausa',
        'ig': 'Igbo', 'rw': 'Kinyarwanda', 'sn': 'Shona',
        'so': 'Somali', 'st': 'Sesotho', 'sw': 'Swahili',
        'xh': 'Xhosa', 'yo': 'Yoruba', 'zu': 'Zulu',
        'ny': 'Chichewa', 'mg': 'Malagasy', 'ak': 'Akan',
        'bm': 'Bambara', 'ee': 'Ewe', 'ff': 'Fulah',
        'ln': 'Lingala', 'om': 'Oromo', 'rn': 'Rundi',
        'sg': 'Sango', 'ss': 'Swati', 'tn': 'Setswana',
        'ts': 'Tsonga', 've': 'Venda',
        'ar': 'Arabic', 'fa': 'Persian', 'he': 'Hebrew',
        'ps': 'Pashto', 'ku': 'Kurdish', 'hy': 'Armenian',
        'az': 'Azerbaijani', 'ka': 'Georgian',
        'ckb': 'Kurdish (Sorani)', 'tuk': 'Turkmen',
        'uz': 'Uzbek', 'tg': 'Tajik',
        'kk': 'Kazakh', 'ky': 'Kyrgyz', 'tt': 'Tatar',
        'sah': 'Sakha',
        'qu': 'Quechua', 'ay': 'Aymara', 'gn': 'Guarani',
        'nah': 'Nahuatl', 'maya': 'Yucatec Maya',
        'moh': 'Mohawk', 'chr': 'Cherokee', 'nav': 'Navajo',
        'oj': 'Ojibwe', 'cr': 'Cree', 'ik': 'Inupiaq',
        'iu': 'Inuktitut',
        'sm': 'Samoan', 'mi': 'Maori', 'haw': 'Hawaiian',
        'fj': 'Fijian', 'to': 'Tongan', 'ty': 'Tahitian',
        'eo': 'Esperanto', 'la': 'Latin', 'yi': 'Yiddish',
        'ht': 'Haitian Creole', 'co': 'Corsican', 'fy': 'Frisian',
        'wo': 'Wolof', 'hmn': 'Hmong'
    }
    return lang_names.get(code, code)

def get_language_flag(code):
    flags = {
        'hi': '🇮🇳', 'bn': '🇧🇩', 'ta': '🇮🇳', 'te': '🇮🇳',
        'mr': '🇮🇳', 'gu': '🇮🇳', 'kn': '🇮🇳', 'ml': '🇮🇳',
        'pa': '🇮🇳', 'ur': '🇮🇳', 'or': '🇮🇳', 'as': '🇮🇳',
        'ne': '🇳🇵', 'sd': '🇮🇳', 'si': '🇱🇰', 'dv': '🇲🇻',
        'sa': '🇮🇳', 'ks': '🇮🇳', 'kok': '🇮🇳', 'mai': '🇮🇳',
        'sat': '🇮🇳', 'doi': '🇮🇳', 'mni': '🇮🇳', 'bodo': '🇮🇳',
        'en': '🇬🇧', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪',
        'it': '🇮🇹', 'pt': '🇵🇹', 'nl': '🇳🇱', 'pl': '🇵🇱',
        'ru': '🇷🇺', 'uk': '🇺🇦', 'ro': '🇷🇴', 'bg': '🇧🇬',
        'cs': '🇨🇿', 'da': '🇩🇰', 'el': '🇬🇷', 'fi': '🇫🇮',
        'hr': '🇭🇷', 'hu': '🇭🇺', 'is': '🇮🇸', 'lt': '🇱🇹',
        'lv': '🇱🇻', 'mk': '🇲🇰', 'mt': '🇲🇹', 'no': '🇳🇴',
        'sk': '🇸🇰', 'sl': '🇸🇮', 'sq': '🇦🇱', 'sr': '🇷🇸',
        'sv': '🇸🇪', 'ca': '🇪🇸', 'et': '🇪🇪', 'ga': '🇮🇪',
        'gl': '🇪🇸', 'bs': '🇧🇦', 'cy': '🏴', 'gd': '🏴',
        'la': '🏛️', 'eo': '🌐',
        'zh-cn': '🇨🇳', 'zh-tw': '🇹🇼', 'ja': '🇯🇵', 'ko': '🇰🇷',
        'mn': '🇲🇳', 'my': '🇲🇲', 'km': '🇰🇭', 'lo': '🇱🇦',
        'th': '🇹🇭', 'vi': '🇻🇳', 'bo': '🇨🇳', 'ug': '🇨🇳',
        'ms': '🇲🇾', 'id': '🇮🇩', 'tl': '🇵🇭', 'jw': '🇮🇩',
        'su': '🇮🇩', 'ceb': '🇵🇭',
        'af': '🇿🇦', 'am': '🇪🇹', 'ha': '🇳🇬', 'ig': '🇳🇬',
        'rw': '🇷🇼', 'sn': '🇿🇼', 'so': '🇸🇴', 'st': '🇱🇸',
        'sw': '🇹🇿', 'xh': '🇿🇦', 'yo': '🇳🇬', 'zu': '🇿🇦',
        'ar': '🇸🇦', 'fa': '🇮🇷', 'he': '🇮🇱', 'ps': '🇦🇫',
        'ku': '🏴', 'hy': '🇦🇲', 'az': '🇦🇿', 'ka': '🇬🇪',
        'kk': '🇰🇿', 'ky': '🇰🇬', 'uz': '🇺🇿', 'tg': '🇹🇯',
        'tk': '🇹🇲', 'tt': '🇷🇺',
        'qu': '🇵🇪', 'ay': '🇧🇴', 'gn': '🇵🇾', 'nah': '🇲🇽',
        'moh': '🇨🇦', 'chr': '🇺🇸', 'nav': '🇺🇸',
        'sm': '🇼🇸', 'mi': '🇳🇿', 'haw': '🌺', 'fj': '🇫🇯',
        'to': '🇹🇴', 'ty': '🇵🇫',
        'ht': '🇭🇹', 'co': '🇫🇷', 'fy': '🇳🇱', 'wo': '🇸🇳',
        'hmn': '🇨🇳', 'yi': '✡️'
    }
    return flags.get(code, '🌐')

def is_tts_supported(lang_code):
    return lang_code in TTS_LANGUAGES

# ============================================
# TRANSLATION FUNCTIONS - GROQ INTEGRATION
# ============================================

def translate_text_google(text, target_lang):
    """Fallback: Google Translate"""
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
        
        return " ".join(translated_chunks)
        
    except Exception as e:
        st.error(f"Google Translate error: {str(e)}")
        return text

def translate_with_groq(text, target_lang, source_lang="auto", context="educational video content"):
    """Translate using Groq API - Fast and Free"""
    try:
        api_key = get_api_key()
        
        if not api_key:
            return translate_text_google(text, target_lang)
        
        target_lang_name = get_language_name(target_lang)
        source_lang_name = get_language_name(source_lang) if source_lang != "auto" else "the original language"
        
        prompt = f"""You are a professional translator specializing in educational and business content.

Source Language: {source_lang_name}
Target Language: {target_lang_name}
Context: {context}

Please translate the following text accurately while:
1. Maintaining the original meaning and intent
2. Using natural, fluent language in the target language
3. Preserving technical terms when appropriate
4. Adapting cultural references if needed
5. Keeping the tone professional and clear

Text to translate:
"""
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Groq has high rate limits, but we'll chunk for safety
        max_chunk = 4000
        if len(text) > max_chunk:
            chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                if len(chunks) > 1:
                    st.info(f"🔄 Translating part {i+1}/{len(chunks)} with Groq...")
                
                if i > 0:
                    time.sleep(0.3)  # Small delay between chunks
                
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": chunk}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    translated = data['choices'][0]['message']['content'].strip()
                    translated_chunks.append(translated)
                elif response.status_code == 429:
                    st.warning(f"⏳ Rate limit. Waiting 2 seconds...")
                    time.sleep(2)
                    response = requests.post(url, headers=headers, json=payload, timeout=60)
                    if response.status_code == 200:
                        data = response.json()
                        translated = data['choices'][0]['message']['content'].strip()
                        translated_chunks.append(translated)
                    else:
                        translated_chunks.append(chunk)
                else:
                    st.warning(f"Groq API error: {response.status_code}")
                    translated_chunks.append(chunk)
            
            return " ".join(translated_chunks)
        else:
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            elif response.status_code == 429:
                st.warning(f"⏳ Rate limit. Waiting 2 seconds...")
                time.sleep(2)
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content'].strip()
                else:
                    return translate_text_google(text, target_lang)
            else:
                st.warning(f"Groq API error: {response.status_code}")
                return translate_text_google(text, target_lang)
        
    except requests.exceptions.Timeout:
        st.warning("Groq API timeout. Using Google Translate fallback.")
        return translate_text_google(text, target_lang)
    except Exception as e:
        st.warning(f"Groq translation failed: {str(e)}. Using Google Translate fallback.")
        return translate_text_google(text, target_lang)

def translate_text(text, target_lang, source_lang="auto", use_llm=True):
    """
    Main translation function with LLM support
    """
    if target_lang == 'en' and source_lang == 'en':
        return text
    
    if use_llm:
        api_key = get_api_key()
        if api_key:
            result = translate_with_groq(text, target_lang, source_lang)
            if result and result != text:
                return result
    
    return translate_text_google(text, target_lang)

def translate_segments(segments, target_lang, source_lang="auto", use_llm=True):
    """Translate all segments to target language"""
    translated_segments = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_segments = len(segments)
    
    if use_llm and total_segments > 5:
        status_text.text(f"🌐 Translating {total_segments} segments with Groq...")
        
        for i, seg in enumerate(segments):
            if i > 0:
                time.sleep(0.2)
            
            translated_text = translate_text(seg['text'], target_lang, source_lang, use_llm)
            translated_segments.append({
                'start': seg['start'],
                'end': seg['end'],
                'text': translated_text,
                'original': seg['text']
            })
            progress_bar.progress((i + 1) / total_segments)
    else:
        for i, seg in enumerate(segments):
            status_text.text(f"🌐 Translating segment {i+1}/{total_segments}...")
            translated_text = translate_text(seg['text'], target_lang, source_lang, use_llm)
            translated_segments.append({
                'start': seg['start'],
                'end': seg['end'],
                'text': translated_text,
                'original': seg['text']
            })
            progress_bar.progress((i + 1) / total_segments)
    
    status_text.text("✅ Translation complete!")
    return translated_segments

# ============================================
# AUDIO GENERATION FUNCTIONS
# ============================================

def generate_audio_in_language(text, output_path, language_code):
    """Generate audio in any supported language"""
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
    """Main function for audio generation with fallback"""
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