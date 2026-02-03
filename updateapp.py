"""
🎯 Interview Practice Simulator - Enhanced Edition
===================================================
Features:
- Typed and video response practice
- Actual video recording via browser
- AI-powered feedback on responses
- Teacher review dashboard
- Response export to CSV

To run: streamlit run app.py
"""

import streamlit as st
import json
import random
import os
import base64
import csv
from datetime import datetime
from pathlib import Path
from io import StringIO

# ============================================================
# CONFIGURATION
# ============================================================

QUESTIONS_FILE = "questions.json"
RESPONSES_DIR = "responses"
VIDEOS_DIR = "responses/videos"

# Create directories
Path(RESPONSES_DIR).mkdir(exist_ok=True)
Path(VIDEOS_DIR).mkdir(exist_ok=True)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Interview Practice Simulator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    /* Main styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .question-card {
        background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #3b82f6;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .question-card-video {
        background: linear-gradient(145deg, #fef3f2 0%, #fee2e2 100%);
        border-left: 5px solid #ef4444;
    }
    
    .category-badge {
        background: #3b82f6;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    
    .timer-display {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
        color: #ef4444;
        font-family: 'Courier New', monospace;
        padding: 1rem;
        background: #1a1a2e;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .success-card {
        background: linear-gradient(145deg, #ecfdf5 0%, #d1fae5 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #10b981;
        margin: 1rem 0;
    }
    
    .feedback-card {
        background: linear-gradient(145deg, #fffbeb 0%, #fef3c7 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .recording-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #ef4444;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_questions():
    """Load questions from JSON file."""
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            data = json.load(f)
            return data['questions']
    except FileNotFoundError:
        st.error(f"❌ Questions file not found: {QUESTIONS_FILE}")
        return []


def select_session_questions(all_questions, typed_count=5, video_count=5):
    """Randomly select questions for a practice session."""
    typed_eligible = [q for q in all_questions if q['type'] in ['typed', 'both']]
    video_eligible = [q for q in all_questions if q['type'] in ['video', 'both']]
    
    def group_by_category(questions):
        groups = {}
        for q in questions:
            cat = q['category']
            if cat not in groups:
                groups[cat] = []
            groups[cat].append(q)
        return groups
    
    typed_by_cat = group_by_category(typed_eligible)
    video_by_cat = group_by_category(video_eligible)
    
    typed_quotas = {'A': 2, 'B': 1, 'C': 1, 'D': 1}
    video_quotas = {'A': 1, 'B': 2, 'C': 1, 'D': 1}
    
    selected_typed = []
    selected_video = []
    used_ids = set()
    
    for category, quota in typed_quotas.items():
        if category in typed_by_cat:
            available = [q for q in typed_by_cat[category] if q['id'] not in used_ids]
            chosen = random.sample(available, min(quota, len(available)))
            selected_typed.extend(chosen)
            used_ids.update(q['id'] for q in chosen)
    
    for category, quota in video_quotas.items():
        if category in video_by_cat:
            available = [q for q in video_by_cat[category] if q['id'] not in used_ids]
            chosen = random.sample(available, min(quota, len(available)))
            selected_video.extend(chosen)
            used_ids.update(q['id'] for q in chosen)
    
    random.shuffle(selected_typed)
    random.shuffle(selected_video)
    
    return {
        'typed': selected_typed[:typed_count],
        'video': selected_video[:video_count]
    }


def save_session_response(student_name, session_data):
    """Save the student's responses to a JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    filename = f"{RESPONSES_DIR}/{timestamp}_{safe_name}.json"
    
    save_data = {
        'student_name': student_name,
        'session_id': f"{timestamp}_{safe_name}",
        'session_timestamp': datetime.now().isoformat(),
        'typed_responses': session_data.get('typed_responses', []),
        'video_responses': session_data.get('video_responses', []),
        'ai_feedback': session_data.get('ai_feedback', [])
    }
    
    with open(filename, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    return filename


def load_all_sessions():
    """Load all saved session files for teacher review."""
    sessions = []
    if os.path.exists(RESPONSES_DIR):
        for filename in os.listdir(RESPONSES_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(RESPONSES_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        data['filename'] = filename
                        sessions.append(data)
                except:
                    pass
    # Sort by timestamp, newest first
    sessions.sort(key=lambda x: x.get('session_timestamp', ''), reverse=True)
    return sessions


def save_video_file(video_data_b64, session_id, question_id):
    """Save base64 encoded video to file."""
    try:
        video_data = base64.b64decode(video_data_b64.split(',')[1] if ',' in video_data_b64 else video_data_b64)
        filename = f"{VIDEOS_DIR}/{session_id}_{question_id}.webm"
        with open(filename, 'wb') as f:
            f.write(video_data)
        return filename
    except Exception as e:
        return None


def get_ai_feedback(question, response, api_key):
    """Get AI feedback on a response using Claude API."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""You are a helpful interview coach providing feedback to a secondary school student 
practicing for a retail job interview at Woolworths Australia.

The student was asked: "{question}"

Their response was: "{response}"

Please provide brief, encouraging feedback (3-4 sentences) that:
1. Highlights one thing they did well
2. Suggests one specific improvement
3. Gives a concrete tip for their next attempt

Keep your tone friendly and supportive - remember they're a student, likely nervous about their first job interview.
"""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text
    
    except ImportError:
        return "⚠️ AI feedback requires the 'anthropic' package. Install with: pip install anthropic"
    except Exception as e:
        return f"⚠️ Could not generate AI feedback: {str(e)}"


def export_sessions_to_csv(sessions):
    """Export sessions to CSV format."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Student Name', 'Session Date', 'Question Type', 'Question ID',
        'Question', 'Response', 'AI Feedback'
    ])
    
    for session in sessions:
        student = session.get('student_name', 'Unknown')
        timestamp = session.get('session_timestamp', '')[:10]
        
        # Typed responses
        for resp in session.get('typed_responses', []):
            writer.writerow([
                student, timestamp, 'Typed', resp.get('question_id', ''),
                resp.get('question', ''), resp.get('response', ''),
                resp.get('ai_feedback', '')
            ])
        
        # Video responses
        for resp in session.get('video_responses', []):
            writer.writerow([
                student, timestamp, 'Video', resp.get('question_id', ''),
                resp.get('question', ''), '[Video Recording]',
                resp.get('notes', '')
            ])
    
    return output.getvalue()


# ============================================================
# VIDEO RECORDING COMPONENT
# ============================================================

def video_recorder_component(question_text, time_limit=60):
    """
    Custom HTML/JS component for video recording.
    Returns the recorded video as base64 when complete.
    """
    
    component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: transparent;
            }}
            #video-container {{
                text-align: center;
                max-width: 700px;
                margin: 0 auto;
            }}
            .video-wrapper {{
                background: #1a1a2e;
                padding: 15px;
                border-radius: 15px;
                margin-bottom: 15px;
            }}
            #preview, #playback {{
                width: 100%;
                max-width: 640px;
                height: auto;
                aspect-ratio: 16/9;
                border-radius: 10px;
                background: #000;
                display: block;
                margin: 0 auto;
            }}
            #timer {{
                font-size: 3.5rem;
                font-weight: bold;
                color: #ef4444;
                font-family: 'Courier New', monospace;
                margin: 15px 0;
            }}
            #status {{
                margin: 12px 0;
                padding: 12px;
                border-radius: 8px;
                background: #f0f0f0;
                font-size: 1rem;
            }}
            .btn {{
                border: none;
                padding: 14px 28px;
                font-size: 1rem;
                border-radius: 8px;
                cursor: pointer;
                margin: 5px;
                transition: transform 0.1s, opacity 0.2s;
            }}
            .btn:hover:not(:disabled) {{
                transform: scale(1.02);
            }}
            .btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            .btn-start {{
                background: #10b981;
                color: white;
            }}
            .btn-stop {{
                background: #ef4444;
                color: white;
            }}
            .btn-retry {{
                background: #f59e0b;
                color: white;
            }}
            .btn-submit {{
                background: #3b82f6;
                color: white;
            }}
            #playback-container {{
                display: none;
                margin-top: 20px;
                padding: 20px;
                background: #f8fafc;
                border-radius: 15px;
                border: 2px solid #e2e8f0;
            }}
            #playback-container h4 {{
                margin: 0 0 15px 0;
                color: #1e3a5f;
            }}
            .button-row {{
                margin: 15px 0;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
            .recording-dot {{
                display: inline-block;
                width: 12px;
                height: 12px;
                background: #ef4444;
                border-radius: 50%;
                margin-right: 8px;
                animation: pulse 1s infinite;
            }}
        </style>
    </head>
    <body>
        <div id="video-container">
            <div class="video-wrapper">
                <video id="preview" autoplay muted playsinline></video>
            </div>
            
            <div id="timer">{time_limit}</div>
            
            <div id="status">Click "Start Recording" when ready</div>
            
            <div class="button-row">
                <button id="startBtn" class="btn btn-start" onclick="startRecording()">
                    🎬 Start Recording
                </button>
                <button id="stopBtn" class="btn btn-stop" onclick="stopRecording()" disabled>
                    ⏹️ Stop Recording
                </button>
            </div>
            
            <div id="playback-container">
                <h4>📹 Review Your Recording:</h4>
                <video id="playback" controls playsinline></video>
                <div class="button-row">
                    <button class="btn btn-retry" onclick="retryRecording()">
                        🔄 Record Again
                    </button>
                    <button class="btn btn-submit" onclick="submitRecording()">
                        ✅ Submit This Recording
                    </button>
                </div>
            </div>
            
            <input type="hidden" id="videoData" name="videoData">
        </div>
        
        <script>
            let mediaRecorder;
            let recordedChunks = [];
            let stream;
            let timerInterval;
            let timeLeft = {time_limit};
            
            async function initCamera() {{
                try {{
                    stream = await navigator.mediaDevices.getUserMedia({{ 
                        video: {{ facingMode: "user", width: {{ ideal: 1280 }}, height: {{ ideal: 720 }} }}, 
                        audio: true 
                    }});
                    document.getElementById('preview').srcObject = stream;
                    document.getElementById('status').innerHTML = '✅ Camera ready! Click "Start Recording" when ready.';
                    document.getElementById('status').style.background = '#d1fae5';
                }} catch (err) {{
                    document.getElementById('status').innerHTML = '❌ Camera access denied. Please allow camera access and refresh the page.';
                    document.getElementById('status').style.background = '#fee2e2';
                    console.error('Camera error:', err);
                }}
            }}
            
            function startRecording() {{
                recordedChunks = [];
                timeLeft = {time_limit};
                
                // Try different codecs for compatibility
                let options = {{ mimeType: 'video/webm;codecs=vp9,opus' }};
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                    options = {{ mimeType: 'video/webm;codecs=vp8,opus' }};
                }}
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {{
                    options = {{ mimeType: 'video/webm' }};
                }}
                
                mediaRecorder = new MediaRecorder(stream, options);
                
                mediaRecorder.ondataavailable = (event) => {{
                    if (event.data.size > 0) {{
                        recordedChunks.push(event.data);
                    }}
                }};
                
                mediaRecorder.onstop = () => {{
                    const blob = new Blob(recordedChunks, {{ type: 'video/webm' }});
                    const url = URL.createObjectURL(blob);
                    
                    const playbackVideo = document.getElementById('playback');
                    playbackVideo.src = url;
                    playbackVideo.load();
                    
                    document.getElementById('playback-container').style.display = 'block';
                    
                    // Scroll to playback
                    document.getElementById('playback-container').scrollIntoView({{ behavior: 'smooth' }});
                    
                    // Convert to base64 for storage
                    const reader = new FileReader();
                    reader.onloadend = () => {{
                        document.getElementById('videoData').value = reader.result;
                    }};
                    reader.readAsDataURL(blob);
                }};
                
                mediaRecorder.start(100);
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('status').innerHTML = '<span class="recording-dot"></span> Recording in progress...';
                document.getElementById('status').style.background = '#fee2e2';
                document.getElementById('playback-container').style.display = 'none';
                
                timerInterval = setInterval(() => {{
                    timeLeft--;
                    document.getElementById('timer').textContent = timeLeft;
                    
                    if (timeLeft <= 10) {{
                        document.getElementById('timer').style.color = '#ef4444';
                    }} else if (timeLeft <= 30) {{
                        document.getElementById('timer').style.color = '#f59e0b';
                    }}
                    
                    if (timeLeft <= 0) {{
                        stopRecording();
                    }}
                }}, 1000);
            }}
            
            function stopRecording() {{
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                    mediaRecorder.stop();
                }}
                clearInterval(timerInterval);
                
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('status').innerHTML = '✅ Recording complete! Review your video below.';
                document.getElementById('status').style.background = '#d1fae5';
                document.getElementById('timer').style.color = '#10b981';
            }}
            
            function retryRecording() {{
                document.getElementById('playback-container').style.display = 'none';
                document.getElementById('playback').src = '';
                document.getElementById('timer').textContent = '{time_limit}';
                document.getElementById('timer').style.color = '#ef4444';
                document.getElementById('status').innerHTML = 'Ready to record again. Click "Start Recording".';
                document.getElementById('status').style.background = '#f0f0f0';
                document.getElementById('videoData').value = '';
            }}
            
            function submitRecording() {{
                const videoData = document.getElementById('videoData').value;
                if (videoData) {{
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: videoData
                    }}, '*');
                    
                    document.getElementById('status').innerHTML = '✅ Recording submitted! Click "Next Question" below to continue.';
                    document.getElementById('status').style.background = '#d1fae5';
                }} else {{
                    document.getElementById('status').innerHTML = '⚠️ No recording found. Please record first.';
                    document.getElementById('status').style.background = '#fef3c7';
                }}
            }}
            
            // Initialize camera when page loads
            initCamera();
        </script>
    </body>
    </html>
    """
    
    return component_html


# ============================================================
# PAGE: STUDENT PRACTICE
# ============================================================

def show_student_welcome():
    """Display the welcome/start screen for students."""
    
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Interview Practice Simulator</h1>
        <p>Master your Woolworths interview with realistic practice</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### What to Expect
        
        **Phase 1: Typed Questions** (5 questions)
        - Type your responses in the text boxes
        - Take your time to think before answering
        - Aim for 3-5 sentences per answer
        
        **Phase 2: Video Questions** (5 questions)  
        - Record yourself answering using your webcam
        - You have 60 seconds per question
        - You can re-record if you're not happy
        
        **Phase 3: AI Feedback** (Optional)
        - Get instant feedback on your typed responses
        - Learn what you did well and how to improve
        """)
    
    with col2:
        st.markdown("""
        <div class="stats-card">
            <h3>📊 Quick Stats</h3>
            <p><strong>10</strong> Questions Total</p>
            <p><strong>60 sec</strong> Per Video</p>
            <p><strong>~20 min</strong> Session Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Student info input
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Enter your name:", key="student_name_input")
    with col2:
        student_id = st.text_input("🔢 Student ID (optional):", key="student_id_input")
    
    # AI Feedback option
    st.markdown("### 🤖 AI Feedback (Optional)")
    enable_ai = st.checkbox("Enable AI-powered feedback on my responses", value=False)
    
    api_key = None
    if enable_ai:
        api_key = st.text_input(
            "Enter your Anthropic API key:",
            type="password",
            help="Your teacher may provide this, or get one at console.anthropic.com"
        )
        st.caption("💡 Your API key is used only for this session and is not stored.")
    
    st.divider()
    
    if st.button("🚀 Start Practice Session", type="primary", disabled=not name):
        # Initialize session
        st.session_state.student_name = name
        st.session_state.student_id = student_id
        st.session_state.api_key = api_key if enable_ai else None
        st.session_state.phase = 'typed'
        st.session_state.current_question = 0
        st.session_state.typed_responses = []
        st.session_state.video_responses = []
        st.session_state.ai_feedback = []
        
        # Generate session ID
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Select random questions
        all_questions = load_questions()
        st.session_state.session_questions = select_session_questions(all_questions)
        
        st.rerun()


def show_typed_questions():
    """Display typed question interface."""
    
    questions = st.session_state.session_questions['typed']
    current_idx = st.session_state.current_question
    
    # Progress
    progress = (current_idx) / len(questions)
    st.progress(progress)
    st.markdown(f"### 📝 Phase 1: Typed Questions ({current_idx + 1} of {len(questions)})")
    
    if current_idx < len(questions):
        question = questions[current_idx]
        
        # Question card
        st.markdown(f"""
        <div class="question-card">
            <span class="category-badge">{question['category_name']}</span>
            <h3 style="margin-top: 10px;">{question['question']}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Tips
        with st.expander("💡 Tips for this question"):
            st.write(question.get('tips', 'Take your time and be authentic!'))
        
        # Response area
        response = st.text_area(
            "Your response:",
            height=200,
            key=f"typed_response_{current_idx}",
            placeholder="Type your answer here... Aim for 3-5 sentences."
        )
        
        # Word count
        word_count = len(response.split()) if response else 0
        st.caption(f"Word count: {word_count}")
        
        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col3:
            if current_idx < len(questions) - 1:
                if st.button("Next Question →", type="primary", disabled=not response.strip()):
                    # Save response
                    response_data = {
                        'question_id': question['id'],
                        'question': question['question'],
                        'response': response,
                        'word_count': word_count,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Get AI feedback if enabled
                    if st.session_state.api_key:
                        with st.spinner("Getting AI feedback..."):
                            feedback = get_ai_feedback(
                                question['question'],
                                response,
                                st.session_state.api_key
                            )
                            response_data['ai_feedback'] = feedback
                    
                    st.session_state.typed_responses.append(response_data)
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("Continue to Video Questions →", type="primary", disabled=not response.strip()):
                    # Save final typed response
                    response_data = {
                        'question_id': question['id'],
                        'question': question['question'],
                        'response': response,
                        'word_count': word_count,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    if st.session_state.api_key:
                        with st.spinner("Getting AI feedback..."):
                            feedback = get_ai_feedback(
                                question['question'],
                                response,
                                st.session_state.api_key
                            )
                            response_data['ai_feedback'] = feedback
                    
                    st.session_state.typed_responses.append(response_data)
                    st.session_state.phase = 'video_intro'
                    st.session_state.current_question = 0
                    st.rerun()


def show_video_intro():
    """Show introduction before video questions."""
    
    st.markdown("""
    <div class="main-header">
        <h1>🎬 Phase 2: Video Questions</h1>
        <p>Record yourself answering interview questions</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### How It Works
        
        1. **Allow camera access** when prompted
        2. **Read the question** displayed on screen
        3. **Click "Start Recording"** when ready
        4. **Speak your answer** within 60 seconds
        5. **Review and submit** or re-record
        """)
    
    with col2:
        st.markdown("""
        ### Tips for Video Interviews
        
        - 📷 Look at the camera, not the screen
        - 🗣️ Speak clearly and at a moderate pace
        - 😊 Smile naturally
        - 💡 Good lighting helps!
        - 🎯 Use the full 60 seconds if needed
        """)
    
    st.divider()
    
    # Camera test
    st.markdown("### 📹 Camera Check")
    st.info("Make sure your camera and microphone are working before proceeding.")
    
    if st.button("🎥 Begin Video Questions", type="primary"):
        st.session_state.phase = 'video'
        st.rerun()


def show_video_questions():
    """Display video question interface with recording."""
    
    questions = st.session_state.session_questions['video']
    current_idx = st.session_state.current_question
    
    # Progress
    progress = (current_idx) / len(questions)
    st.progress(progress)
    st.markdown(f"### 🎬 Phase 2: Video Questions ({current_idx + 1} of {len(questions)})")
    
    if current_idx < len(questions):
        question = questions[current_idx]
        
        # Question card (larger for video)
        st.markdown(f"""
        <div class="question-card question-card-video">
            <span class="category-badge" style="background: #ef4444;">{question['category_name']}</span>
            <h2 style="margin-top: 15px; font-size: 1.5rem;">{question['question']}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Tips
        with st.expander("💡 Tips for this question"):
            st.write(question.get('tips', 'Take a breath, then start speaking confidently!'))
        
        # Video recorder
        st.markdown("### Your Recording")
        
        # Use iframe for video component (simpler approach)
        video_html = video_recorder_component(question['question'], time_limit=60)
        st.components.v1.html(video_html, height=900, scrolling=True)
        
        # Self-assessment notes
        st.markdown("### 📝 Self-Reflection (Optional)")
        notes = st.text_area(
            "How did that go? What would you improve?",
            height=100,
            key=f"video_notes_{current_idx}",
            placeholder="Jot down any thoughts about your response..."
        )
        
        st.divider()
        
        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col3:
            if current_idx < len(questions) - 1:
                if st.button("Next Question →", type="primary"):
                    st.session_state.video_responses.append({
                        'question_id': question['id'],
                        'question': question['question'],
                        'notes': notes,
                        'timestamp': datetime.now().isoformat()
                    })
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("Complete Practice Session →", type="primary"):
                    st.session_state.video_responses.append({
                        'question_id': question['id'],
                        'question': question['question'],
                        'notes': notes,
                        'timestamp': datetime.now().isoformat()
                    })
                    st.session_state.phase = 'complete'
                    st.rerun()


def show_completion():
    """Display completion screen with summary and feedback."""
    
    st.balloons()
    
    st.markdown(f"""
    <div class="main-header">
        <h1>🎉 Excellent Work, {st.session_state.student_name}!</h1>
        <p>You've completed your practice interview session</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Save session
    try:
        filename = save_session_response(
            st.session_state.student_name,
            {
                'typed_responses': st.session_state.typed_responses,
                'video_responses': st.session_state.video_responses
            }
        )
        st.success("✅ Your responses have been saved!")
    except Exception as e:
        st.warning(f"Could not save responses: {e}")
    
    # Summary tabs
    tab1, tab2, tab3 = st.tabs(["📝 Typed Responses", "🎬 Video Responses", "🤖 AI Feedback"])
    
    with tab1:
        for i, resp in enumerate(st.session_state.typed_responses, 1):
            with st.expander(f"Question {i}: {resp['question'][:50]}...", expanded=(i==1)):
                st.markdown(f"**Question:** {resp['question']}")
                st.markdown("**Your Response:**")
                st.info(resp['response'])
                st.caption(f"Word count: {resp.get('word_count', 'N/A')}")
    
    with tab2:
        for i, resp in enumerate(st.session_state.video_responses, 1):
            with st.expander(f"Question {i}: {resp['question'][:50]}..."):
                st.markdown(f"**Question:** {resp['question']}")
                if resp.get('notes'):
                    st.markdown("**Your Notes:**")
                    st.info(resp['notes'])
    
    with tab3:
        if st.session_state.api_key:
            st.markdown("### AI Feedback on Your Responses")
            for i, resp in enumerate(st.session_state.typed_responses, 1):
                if resp.get('ai_feedback'):
                    st.markdown(f"""
                    <div class="feedback-card">
                        <strong>Question {i}:</strong> {resp['question'][:50]}...<br><br>
                        {resp['ai_feedback']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("AI feedback was not enabled for this session. Enable it next time for personalized tips!")
    
    st.divider()
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Practice Again", type="primary"):
            name = st.session_state.student_name
            api_key = st.session_state.api_key
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.student_name_input = name
            st.rerun()
    
    with col2:
        if st.button("🏠 Return to Start"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # STAR method reminder
    st.markdown("""
    ---
    ### 💪 Keep Improving!
    
    **The STAR Method** for behavioural questions:
    - **S**ituation: Set the scene
    - **T**ask: What was your responsibility?
    - **A**ction: What did you do?
    - **R**esult: What was the outcome?
    """)


# ============================================================
# PAGE: TEACHER DASHBOARD
# ============================================================

def show_teacher_dashboard():
    """Display the teacher review dashboard."""
    
    st.markdown("""
    <div class="main-header">
        <h1>👩‍🏫 Teacher Dashboard</h1>
        <p>Review and export student practice sessions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load all sessions
    sessions = load_all_sessions()
    
    if not sessions:
        st.info("📭 No student sessions found yet. Sessions will appear here once students complete practice interviews.")
        return
    
    # Stats overview
    col1, col2, col3, col4 = st.columns(4)
    
    unique_students = len(set(s.get('student_name', '') for s in sessions))
    total_typed = sum(len(s.get('typed_responses', [])) for s in sessions)
    total_video = sum(len(s.get('video_responses', [])) for s in sessions)
    
    with col1:
        st.metric("Total Sessions", len(sessions))
    with col2:
        st.metric("Unique Students", unique_students)
    with col3:
        st.metric("Typed Responses", total_typed)
    with col4:
        st.metric("Video Responses", total_video)
    
    st.divider()
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        student_names = ['All Students'] + list(set(s.get('student_name', 'Unknown') for s in sessions))
        selected_student = st.selectbox("Filter by Student:", student_names)
    
    with col2:
        sort_option = st.selectbox("Sort by:", ['Newest First', 'Oldest First', 'Student Name'])
    
    # Filter and sort
    filtered_sessions = sessions
    if selected_student != 'All Students':
        filtered_sessions = [s for s in sessions if s.get('student_name') == selected_student]
    
    if sort_option == 'Oldest First':
        filtered_sessions = list(reversed(filtered_sessions))
    elif sort_option == 'Student Name':
        filtered_sessions.sort(key=lambda x: x.get('student_name', ''))
    
    # Export button
    st.markdown("### 📥 Export Data")
    csv_data = export_sessions_to_csv(filtered_sessions)
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv_data,
        file_name=f"interview_responses_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
    
    st.divider()
    
    # Session list
    st.markdown("### 📋 Session Details")
    
    for session in filtered_sessions:
        student = session.get('student_name', 'Unknown')
        timestamp = session.get('session_timestamp', '')[:16].replace('T', ' ')
        typed_count = len(session.get('typed_responses', []))
        video_count = len(session.get('video_responses', []))
        
        with st.expander(f"📌 {student} - {timestamp} ({typed_count} typed, {video_count} video)"):
            # Typed responses
            if session.get('typed_responses'):
                st.markdown("#### 📝 Typed Responses")
                for resp in session['typed_responses']:
                    st.markdown(f"**Q: {resp.get('question', 'N/A')}**")
                    st.info(resp.get('response', 'No response'))
                    if resp.get('ai_feedback'):
                        st.markdown(f"**AI Feedback:** {resp['ai_feedback']}")
                    st.markdown("---")
            
            # Video responses
            if session.get('video_responses'):
                st.markdown("#### 🎬 Video Responses")
                for resp in session['video_responses']:
                    st.markdown(f"**Q: {resp.get('question', 'N/A')}**")
                    if resp.get('notes'):
                        st.caption(f"Student notes: {resp['notes']}")
                    st.markdown("---")


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    """Main application entry point."""
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f5/Woolworths_logo.svg/200px-Woolworths_logo.svg.png", width=150)
        st.markdown("---")
        
        mode = st.radio(
            "Select Mode:",
            ["🎯 Student Practice", "👩‍🏫 Teacher Dashboard"],
            key="app_mode"
        )
        
        st.markdown("---")
        st.markdown("""
        ### About
        Practice simulator for Woolworths-style interviews.
        
        **Features:**
        - ✅ Random questions
        - ✅ Video recording
        - ✅ AI feedback
        - ✅ Response tracking
        """)
        
        # Exit button for students in session
        if 'phase' in st.session_state and st.session_state.phase not in ['welcome', None]:
            st.markdown("---")
            if st.button("⚠️ Exit Session"):
                for key in list(st.session_state.keys()):
                    if key != 'app_mode':
                        del st.session_state[key]
                st.rerun()
    
    # Route based on mode
    if mode == "👩‍🏫 Teacher Dashboard":
        show_teacher_dashboard()
    else:
        # Student practice flow
        if 'phase' not in st.session_state:
            st.session_state.phase = 'welcome'
        
        if st.session_state.phase == 'welcome':
            show_student_welcome()
        elif st.session_state.phase == 'typed':
            show_typed_questions()
        elif st.session_state.phase == 'video_intro':
            show_video_intro()
        elif st.session_state.phase == 'video':
            show_video_questions()
        elif st.session_state.phase == 'complete':
            show_completion()


if __name__ == "__main__":
    main()
