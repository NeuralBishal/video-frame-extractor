"""
Reusable UI Components
"""
import streamlit as st

def feature_card(icon, title, desc):
    """Display a feature card"""
    st.markdown(f"""
    <div class="feature-card">
        <div class="feature-icon">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

def success_badge(message):
    """Display a success badge"""
    st.markdown(f"""
    <div class="success-badge" style="background: #d4edda; padding: 1rem; text-align: center;">
        {message}
    </div>
    """, unsafe_allow_html=True)

def info_box(message):
    """Display an info box"""
    st.markdown(f"""
    <div class="info-box">
        {message}
    </div>
    """, unsafe_allow_html=True)

def subtitle_display(text):
    """Display subtitles in a styled box"""
    st.markdown(f"""
    <div class="subtitle-box">
        🎯 {text}
    </div>
    """, unsafe_allow_html=True)

def stats_container(stats):
    """Display stats in a grid"""
    cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.metric(label, value)