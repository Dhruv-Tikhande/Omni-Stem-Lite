import streamlit as st
from PIL import Image
from gtts import gTTS
import tempfile
import os
import time
from streamlit_mic_recorder import speech_to_text  # NEW IMPORT

# --- Page Config ---
st.set_page_config(page_title="Omni-STEM Assistant", page_icon="🎙️", layout="wide")

# --- Initialize Memory ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_image" not in st.session_state:
    st.session_state.current_image = None

# --- Text-to-Speech Function ---
def generate_audio(text):
    tts = gTTS(text=text, lang='en', tld='co.in')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

# --- MAIN UI STRUCTURE ---
st.title("🎙️ Omni-STEM Accessibility Assistant")
st.markdown("Upload a STEM diagram, and ask questions using your mic or keyboard.")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.header("1. Document Ingestion")
    uploaded_file = st.file_uploader("Upload PDF / Image", type=["png", "jpg", "jpeg", "pdf"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.session_state.current_image = image
        st.image(image, caption="Uploaded Diagram", use_container_width=True)
        st.success("Image successfully processed and ready for AI.")

with col2:
    st.header("2. AI Tutor Chat")
    
    # Display Chat History
    chat_container = st.container(height=300)
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f"**👤 You:** {chat['content']}")
            else:
                st.markdown(f"**🤖 Jarvis:** {chat['content']}")

    # --- THE ACCESSIBILITY FIX: Mic & Text Input ---
    st.markdown("### Ask a Question")
    
    # 1. The Physical Mic Button (Accessible via Tab & Spacebar)
    spoken_text = speech_to_text(
        language='en',
        start_prompt="🎤 Click to Speak",
        stop_prompt="🛑 Stop Recording",
        just_once=True,
        key='STT'
    )
    
    # 2. Backup Text Input
    typed_text = st.chat_input("Or type your question here...")
    
    # Capture whichever input the user used
    user_query = spoken_text if spoken_text else typed_text
    
    # Process the query
    if user_query and st.session_state.current_image:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        
        with st.spinner("Analyzing diagram..."):
            time.sleep(1.5) # Simulating AI processing
            ai_response = f"I heard you ask: '{user_query}'. Based on the diagram, the components are in series."
            
        st.session_state.chat_history.append({"role": "ai", "content": ai_response})
        
        # Generate Voice Playback
        audio_path = generate_audio(ai_response)
        st.audio(audio_path, format="audio/mp3", autoplay=True)
        
        st.rerun()
        
    elif user_query and not st.session_state.current_image:
        st.warning("Please upload an image first!")