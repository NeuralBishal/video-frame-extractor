"""
Audio Processing Module - Optimized for English, Hindi, Bengali
"""
import os
import subprocess
import tempfile
import streamlit as st
from deep_translator import GoogleTranslator
import re

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

def translate_text(text, target_lang):
    """Translate text to target language"""
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        st.warning(f"Translation error: {str(e)}")
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
# LANGUAGE-SPECIFIC AUDIO GENERATION
# ============================================

def generate_english_audio(text, output_path="output_en.mp3"):
    """Generate English audio"""
    try:
        from gtts import gTTS
        
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if not clean_text:
            return None
        
        # English audio
        tts = gTTS(text=clean_text, lang='en', slow=False)
        tts.save(output_path)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        return None
        
    except Exception as e:
        st.error(f"English audio generation failed: {str(e)}")
        return None

def generate_hindi_audio(text, output_path="output_hi.mp3"):
    """Generate Hindi audio with explicit Hindi language setting"""
    try:
        from gtts import gTTS
        
        # Clean the text - remove extra spaces
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if not clean_text:
            return None
        
        # FORCE Hindi language with explicit 'hi' code
        # gTTS supports Hindi with 'hi' language code
        tts = gTTS(text=clean_text, lang='hi', slow=False)
        tts.save(output_path)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        return None
        
    except Exception as e:
        st.error(f"Hindi audio generation failed: {str(e)}")
        
        # Fallback: Try with pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Try to find Hindi voice
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'hindi' in voice.name.lower() or 'hi' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 150)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
        except:
            pass
        
        return None

def generate_bengali_audio(text, output_path="output_bn.mp3"):
    """Generate Bengali audio with explicit Bengali language setting"""
    try:
        from gtts import gTTS
        
        # Clean the text
        clean_text = re.sub(r'\s+', ' ', text).strip()
        if not clean_text:
            return None
        
        # FORCE Bengali language with 'bn' code
        # gTTS supports Bengali with 'bn' language code
        tts = gTTS(text=clean_text, lang='bn', slow=False)
        tts.save(output_path)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        return None
        
    except Exception as e:
        st.error(f"Bengali audio generation failed: {str(e)}")
        
        # Fallback: Try with pyttsx3
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Try to find Bengali voice
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'bengali' in voice.name.lower() or 'bn' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 150)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
        except:
            pass
        
        return None

# ============================================
# MAIN AUDIO GENERATION FUNCTION
# ============================================

def generate_audio_by_language(text, output_path, language_code):
    """
    Generate audio in specified language
    Supported: 'en' (English), 'hi' (Hindi), 'bn' (Bengali)
    """
    language_code = language_code.lower()
    
    if language_code == 'en':
        return generate_english_audio(text, output_path)
    elif language_code == 'hi':
        return generate_hindi_audio(text, output_path)
    elif language_code == 'bn':
        return generate_bengali_audio(text, output_path)
    else:
        # Fallback to English if language not supported
        st.warning(f"Language '{language_code}' not fully supported. Using English.")
        return generate_english_audio(text, output_path)

def generate_audio_with_timestamps(segments, output_path="output_audio.mp3", lang='en'):
    """
    Generate audio with timestamps for each segment
    Optimized for English, Hindi, Bengali
    """
    try:
        from pydub import AudioSegment
        
        combined = AudioSegment.silent(duration=0)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, seg in enumerate(segments):
            text = seg.get('text', '').strip()
            
            if text:
                status_text.text(f"🎵 Generating audio for segment {i+1}/{len(segments)}...")
                
                # Generate audio for this segment
                temp_path = f"temp_segment_{i}.mp3"
                
                # Use language-specific generation
                result = generate_audio_by_language(text, temp_path, lang)
                
                if result and os.path.exists(temp_path):
                    # Load audio segment
                    audio_seg = AudioSegment.from_mp3(temp_path)
                    
                    # Add small gap between segments
                    combined += audio_seg + AudioSegment.silent(duration=150)
                    
                    # Cleanup
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                else:
                    # Add silence for failed segment
                    combined += AudioSegment.silent(duration=500)
            
            progress_bar.progress((i + 1) / len(segments))
        
        status_text.text("✅ Audio generation complete!")
        
        # Export with proper settings
        if len(combined) > 0:
            combined.export(output_path, format="mp3", bitrate="192k")
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
        
        return None
        
    except Exception as e:
        st.error(f"Audio generation failed: {str(e)}")
        return None

# ============================================
# LANGUAGE SUPPORT FUNCTIONS
# ============================================

def get_supported_languages():
    """Get list of supported languages with their codes"""
    languages = {
        'en': 'English (🇬🇧)',
        'hi': 'Hindi (🇮🇳)',
        'bn': 'Bengali (🇧🇩)'
    }
    return languages

def get_language_name(code):
    """Get language name from code"""
    names = {
        'en': 'English',
        'hi': 'Hindi',
        'bn': 'Bengali'
    }
    return names.get(code, code)

def validate_language_code(code):
    """Validate if language is supported"""
    supported = ['en', 'hi', 'bn']
    return code in supported

# ============================================
# TEST FUNCTIONS (for debugging)
# ============================================

def test_audio_generation():
    """Test audio generation for all three languages"""
    
    test_texts = {
        'en': "This is a test of English audio generation.",
        'hi': "यह हिंदी ऑडियो जनरेशन का परीक्षण है।",
        'bn': "এটি বাংলা অডিও জেনারেশন এর পরীক্ষণ।"
    }
    
    results = {}
    
    for lang, text in test_texts.items():
        output_path = f"test_{lang}.mp3"
        result = generate_audio_by_language(text, output_path, lang)
        results[lang] = result is not None
        
        if result:
            print(f"✅ {lang.upper()} audio generated: {output_path}")
        else:
            print(f"❌ {lang.upper()} audio generation failed")
    
    return results