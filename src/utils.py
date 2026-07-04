"""
Utility Functions
"""
import os
import time
import tempfile
import subprocess
from pathlib import Path

def format_time(seconds):
    """Convert seconds to SRT time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def get_supported_languages():
    """Get list of supported languages with their codes"""
    languages = {
        'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic',
        'ar': 'Arabic', 'hy': 'Armenian', 'az': 'Azerbaijani',
        'eu': 'Basque', 'be': 'Belarusian', 'bn': 'Bengali',
        'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
        'ceb': 'Cebuano', 'ny': 'Chichewa', 'zh-cn': 'Chinese (Simplified)',
        'zh-tw': 'Chinese (Traditional)', 'co': 'Corsican', 'hr': 'Croatian',
        'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch', 'en': 'English',
        'eo': 'Esperanto', 'et': 'Estonian', 'tl': 'Filipino',
        'fi': 'Finnish', 'fr': 'French', 'fy': 'Frisian',
        'gl': 'Galician', 'ka': 'Georgian', 'de': 'German',
        'el': 'Greek', 'gu': 'Gujarati', 'ht': 'Haitian Creole',
        'ha': 'Hausa', 'haw': 'Hawaiian', 'he': 'Hebrew',
        'hi': 'Hindi', 'hmn': 'Hmong', 'hu': 'Hungarian',
        'is': 'Icelandic', 'ig': 'Igbo', 'id': 'Indonesian',
        'ga': 'Irish', 'it': 'Italian', 'ja': 'Japanese',
        'jw': 'Javanese', 'kn': 'Kannada', 'kk': 'Kazakh',
        'km': 'Khmer', 'rw': 'Kinyarwanda', 'ko': 'Korean',
        'ku': 'Kurdish', 'ky': 'Kyrgyz', 'lo': 'Lao',
        'la': 'Latin', 'lv': 'Latvian', 'lt': 'Lithuanian',
        'lb': 'Luxembourgish', 'mk': 'Macedonian', 'mg': 'Malagasy',
        'ms': 'Malay', 'ml': 'Malayalam', 'mt': 'Maltese',
        'mi': 'Maori', 'mr': 'Marathi', 'mn': 'Mongolian',
        'my': 'Myanmar (Burmese)', 'ne': 'Nepali', 'no': 'Norwegian',
        'or': 'Odia (Oriya)', 'ps': 'Pashto', 'fa': 'Persian',
        'pl': 'Polish', 'pt': 'Portuguese', 'pa': 'Punjabi',
        'ro': 'Romanian', 'ru': 'Russian', 'sm': 'Samoan',
        'gd': 'Scots Gaelic', 'sr': 'Serbian', 'st': 'Sesotho',
        'sn': 'Shona', 'sd': 'Sindhi', 'si': 'Sinhala',
        'sk': 'Slovak', 'sl': 'Slovenian', 'so': 'Somali',
        'es': 'Spanish', 'su': 'Sundanese', 'sw': 'Swahili',
        'sv': 'Swedish', 'tg': 'Tajik', 'ta': 'Tamil',
        'tt': 'Tatar', 'te': 'Telugu', 'th': 'Thai',
        'tr': 'Turkish', 'tk': 'Turkmen', 'uk': 'Ukrainian',
        'ur': 'Urdu', 'ug': 'Uyghur', 'uz': 'Uzbek',
        'vi': 'Vietnamese', 'cy': 'Welsh', 'xh': 'Xhosa',
        'yi': 'Yiddish', 'yo': 'Yoruba', 'zu': 'Zulu'
    }
    return languages

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

def clean_temp_files(*paths):
    """Clean up temporary files"""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except:
                pass