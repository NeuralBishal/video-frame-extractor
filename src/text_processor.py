"""
Text Processing Module - Structuring & Simplification
"""
import re

def structure_transcript(transcript_text, segments=None):
    """Structure the transcript into sections with topics"""
    sentences = re.split(r'(?<=[.!?])\s+', transcript_text)
    
    topics = {
        'Introduction': ['hello', 'welcome', 'introduction', 'today', 'going to'],
        'Main Content': ['now', 'first', 'second', 'next', 'then', 'finally'],
        'Summary': ['summary', 'conclusion', 'finally', 'in conclusion', 'to summarize'],
        'Examples': ['example', 'for instance', 'such as', 'like'],
        'Key Points': ['important', 'key point', 'remember', 'note that']
    }
    
    structured = {
        'title': 'Video Transcript',
        'sections': [],
        'key_points': [],
        'summary': ''
    }
    
    current_section = {'title': 'Content', 'points': []}
    key_points = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        is_key_point = any(kw in sentence.lower() for kw in ['important', 'key', 'remember', 'note', 'crucial'])
        if is_key_point:
            key_points.append(sentence)
        
        assigned = False
        for topic, keywords in topics.items():
            if any(kw in sentence.lower() for kw in keywords):
                if current_section['points']:
                    structured['sections'].append(current_section)
                current_section = {'title': topic, 'points': [sentence]}
                assigned = True
                break
        
        if not assigned:
            current_section['points'].append(sentence)
    
    if current_section['points']:
        structured['sections'].append(current_section)
    
    if len(sentences) > 5:
        structured['summary'] = ' '.join(sentences[:2] + sentences[-2:])
    else:
        structured['summary'] = transcript_text[:200] + ('...' if len(transcript_text) > 200 else '')
    
    structured['key_points'] = key_points[:10]
    return structured

def simplify_english(text):
    """Simplify complex English to plain language"""
    replacements = {
        'utilize': 'use', 'demonstrate': 'show', 'implement': 'do',
        'consequently': 'so', 'nevertheless': 'but', 'furthermore': 'also',
        'significant': 'big', 'approximately': 'about', 'establish': 'set up',
        'obtain': 'get', 'determine': 'find', 'evaluate': 'check',
        'analyze': 'study', 'therefore': 'so', 'thus': 'so', 'hence': 'so'
    }
    
    for complex_word, simple_word in replacements.items():
        text = text.replace(complex_word, simple_word)
        text = text.replace(complex_word.capitalize(), simple_word.capitalize())
    
    return text

def simplify_segments(segments):
    """Simplify text in all segments"""
    simplified = []
    for seg in segments:
        simplified.append({
            'start': seg['start'],
            'end': seg['end'],
            'text': simplify_english(seg['text'])
        })
    return simplified