"""
🎯 Interview Practice Simulator - Reliable Cloud Version
=========================================================
This version is optimised for Streamlit Cloud deployment.
Video questions use a practice timer + optional file upload.

To run: streamlit run app_cloud.py
"""

import streamlit as st
import json
import random
import os
import csv
from datetime import datetime
from pathlib import Path
from io import StringIO, BytesIO
import time

# ============================================================
# CONFIGURATION
# ============================================================

QUESTIONS_FILE = "questions.json"
RESPONSES_DIR = "responses"

Path(RESPONSES_DIR).mkdir(exist_ok=True)

# ============================================================
# PAGE CONFIG & STYLING
# ============================================================

st.set_page_config(
    page_title="Interview Practice Simulator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
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
    
    .timer-big {
        font-size: 5rem;
        font-weight: bold;
        text-align: center;
        font-family: 'Courier New', monospace;
        padding: 2rem;
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        margin: 1.5rem 0;
    }
    
    .timer-green { color: #10b981; }
    .timer-yellow { color: #f59e0b; }
    .timer-red { color: #ef4444; }
    
    .feedback-card {
        background: linear-gradient(145deg, #fffbeb 0%, #fef3c7 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    
    .success-banner {
        background: linear-gradient(145deg, #ecfdf5 0%, #d1fae5 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stats-card {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        height: 100%;
    }
    
    .instruction-step {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #3b82f6;
    }
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
        return get_default_questions()


def get_default_questions():
    """Return default questions if file not found."""
    return [
        {"id": "A1", "category": "A", "category_name": "Personal & Motivation",
         "question": "Tell us about yourself and what interests you about working in retail.",
         "type": "both", "tips": "Keep it professional. Mention your interests and why retail appeals to you."},
        {"id": "B1", "category": "B", "category_name": "Customer Service",
         "question": "What does excellent customer service mean to you?",
         "type": "both", "tips": "Think about making customers feel valued and solving their problems."},
    ]


def select_session_questions(all_questions, typed_count=5, video_count=5):
    """Randomly select questions for a practice session."""
    typed_eligible = [q for q in all_questions if q['type'] in ['typed', 'both']]
    video_eligible = [q for q in all_questions if q['type'] in ['video', 'both']]
    
    # Shuffle and select
    random.shuffle(typed_eligible)
    random.shuffle(video_eligible)
    
    # Ensure no overlap
    selected_typed = typed_eligible[:typed_count]
    used_ids = {q['id'] for q in selected_typed}
    
    selected_video = [q for q in video_eligible if q['id'] not in used_ids][:video_count]
    
    return {'typed': selected_typed, 'video': selected_video}


def save_session(student_name, data):
    """Save session data to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in student_name if c.isalnum() or c == ' ').strip().replace(' ', '_')
    filename = f"{RESPONSES_DIR}/{timestamp}_{safe_name}.json"
    
    save_data = {
        'student_name': student_name,
        'session_timestamp': datetime.now().isoformat(),
        'typed_responses': data.get('typed_responses', []),
        'video_responses': data.get('video_responses', [])
    }
    
    with open(filename, 'w') as f:
        json.dump(save_data, f, indent=2)
    return filename


def load_all_sessions():
    """Load all saved sessions."""
    sessions = []
    if os.path.exists(RESPONSES_DIR):
        for filename in os.listdir(RESPONSES_DIR):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(RESPONSES_DIR, filename), 'r') as f:
                        data = json.load(f)
                        data['filename'] = filename
                        sessions.append(data)
                except:
                    pass
    sessions.sort(key=lambda x: x.get('session_timestamp', ''), reverse=True)
    return sessions


def get_ai_feedback(question, response, api_key):
    """Get AI feedback on a response."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"""You're a friendly interview coach helping a secondary school student practice for a retail job interview.

Question: "{question}"
Student's response: "{response}"

Give brief, encouraging feedback (3-4 sentences):
1. One thing they did well
2. One specific improvement suggestion
3. A practical tip for next time

Keep it warm and supportive!"""
            }]
        )
        return message.content[0].text
    except ImportError:
        return "💡 Install the 'anthropic' package for AI feedback: pip install anthropic"
    except Exception as e:
        return f"⚠️ Couldn't get feedback: {str(e)}"


def export_to_csv(sessions):
    """Export sessions to CSV."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student', 'Date', 'Type', 'Question', 'Response', 'Feedback'])
    
    for session in sessions:
        student = session.get('student_name', 'Unknown')
        date = session.get('session_timestamp', '')[:10]
        
        for resp in session.get('typed_responses', []):
            writer.writerow([
                student, date, 'Typed',
                resp.get('question', ''),
                resp.get('response', ''),
                resp.get('ai_feedback', '')
            ])
        
        for resp in session.get('video_responses', []):
            writer.writerow([
                student, date, 'Video',
                resp.get('question', ''),
                resp.get('notes', ''),
                ''
            ])
    
    return output.getvalue()


# ============================================================
# STUDENT PAGES
# ============================================================

def show_welcome():
    """Welcome page for students."""
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Interview Practice Simulator</h1>
        <p>Prepare for your Woolworths interview with confidence!</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### How It Works
        
        <div class="instruction-step">
        <strong>📝 Phase 1: Typed Questions</strong><br>
        Answer 5 questions by typing your responses. Take your time!
        </div>
        
        <div class="instruction-step">
        <strong>🎬 Phase 2: Video Practice</strong><br>
        Practice answering 5 questions out loud with a 60-second timer.
        Record yourself on your phone to review later!
        </div>
        
        <div class="instruction-step">
        <strong>🤖 Bonus: AI Feedback</strong><br>
        Get instant, personalised tips on your typed responses.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-card">
            <h3>📊 Session Info</h3>
            <p><strong>10</strong> Questions</p>
            <p><strong>60 sec</strong> Per Video Q</p>
            <p><strong>~20 min</strong> Total Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Student info
    name = st.text_input("👤 Your name:", key="name_input")
    
    # AI feedback option
    with st.expander("🤖 Enable AI Feedback (Optional)"):
        st.info("AI feedback gives you personalised tips on your typed responses.")
        api_key = st.text_input("Anthropic API key:", type="password", key="api_key_input",
                                help="Your teacher may provide this, or leave blank to skip AI feedback.")
    
    st.divider()
    
    if st.button("🚀 Start Practice", type="primary", disabled=not name):
        st.session_state.student_name = name
        st.session_state.api_key = api_key if api_key else None
        st.session_state.phase = 'typed'
        st.session_state.q_index = 0
        st.session_state.typed_responses = []
        st.session_state.video_responses = []
        st.session_state.questions = select_session_questions(load_questions())
        st.rerun()


def show_typed_questions():
    """Typed questions page."""
    questions = st.session_state.questions['typed']
    idx = st.session_state.q_index
    
    st.progress(idx / len(questions))
    st.markdown(f"### 📝 Typed Questions ({idx + 1}/{len(questions)})")
    
    q = questions[idx]
    
    st.markdown(f"""
    <div class="question-card">
        <span class="category-badge">{q['category_name']}</span>
        <h3>{q['question']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("💡 Tips"):
        st.write(q.get('tips', 'Be authentic and specific!'))
    
    response = st.text_area("Your answer:", height=200, key=f"typed_{idx}",
                           placeholder="Type your response here... (aim for 3-5 sentences)")
    
    word_count = len(response.split()) if response else 0
    st.caption(f"📊 Word count: {word_count}")
    
    # Finish button - prominently placed right after text box
    st.markdown("")  # Small spacer
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if idx < len(questions) - 1:
            btn_label = "✅ Finish & Next Question"
        else:
            btn_label = "✅ Finish & Continue to Video"
        
        finish_clicked = st.button(
            btn_label, 
            type="primary", 
            disabled=not response.strip(),
            use_container_width=True,
            key=f"finish_btn_{idx}"
        )
    
    # Help text
    if not response.strip():
        st.caption("💡 Type your answer above, then click the Finish button to continue.")
    
    # Handle button click
    if finish_clicked and response.strip():
        # Save response
        resp_data = {
            'question_id': q['id'],
            'question': q['question'],
            'response': response,
            'word_count': word_count
        }
        
        # Get AI feedback if enabled
        if st.session_state.api_key:
            with st.spinner("Getting AI feedback..."):
                resp_data['ai_feedback'] = get_ai_feedback(q['question'], response, st.session_state.api_key)
        
        st.session_state.typed_responses.append(resp_data)
        
        if idx < len(questions) - 1:
            st.session_state.q_index += 1
        else:
            st.session_state.phase = 'video_intro'
            st.session_state.q_index = 0
        st.rerun()


def show_video_intro():
    """Introduction to video questions."""
    st.markdown("""
    <div class="main-header">
        <h1>🎬 Phase 2: Video Practice</h1>
        <p>Practice answering questions out loud</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### How This Works
        
        1. A question will appear on screen
        2. A **60-second timer** will count down
        3. **Practice speaking your answer out loud**
        4. Add notes about how you went
        
        ### 📱 Pro Tip: Record Yourself!
        
        Use your phone to record yourself while practicing.
        This helps you:
        - See your body language
        - Hear your pacing
        - Review and improve
        """)
    
    with col2:
        st.markdown("""
        ### Video Interview Tips
        
        - 📷 **Eye contact**: Look at the camera
        - 🗣️ **Pace**: Speak clearly, not too fast
        - 😊 **Expression**: Smile naturally
        - 🎯 **Structure**: Beginning, middle, end
        - ⏱️ **Time**: Use the full 60 seconds
        - 💪 **Confidence**: You've got this!
        """)
    
    if st.button("🎬 Begin Video Practice", type="primary"):
        st.session_state.phase = 'video'
        st.rerun()


def show_video_questions():
    """Video questions with timer."""
    questions = st.session_state.questions['video']
    idx = st.session_state.q_index
    
    st.progress(idx / len(questions))
    st.markdown(f"### 🎬 Video Practice ({idx + 1}/{len(questions)})")
    
    q = questions[idx]
    
    # Question display (large, centered)
    st.markdown(f"""
    <div class="question-card question-card-video">
        <span class="category-badge" style="background:#ef4444;">{q['category_name']}</span>
        <h2 style="font-size: 1.6rem; margin-top: 15px;">{q['question']}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Timer section
    st.markdown("---")
    
    # Initialize timer state
    timer_key = f"timer_started_{idx}"
    if timer_key not in st.session_state:
        st.session_state[timer_key] = False
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state[timer_key]:
            st.markdown("""
            <div class="timer-big timer-green">
                60
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("▶️ Start 60-Second Timer", type="primary", use_container_width=True):
                st.session_state[timer_key] = True
                st.session_state[f"timer_end_{idx}"] = time.time() + 60
                st.rerun()
        else:
            # Calculate remaining time
            remaining = max(0, int(st.session_state[f"timer_end_{idx}"] - time.time()))
            
            # Color based on time
            if remaining > 30:
                color_class = "timer-green"
            elif remaining > 10:
                color_class = "timer-yellow"
            else:
                color_class = "timer-red"
            
            st.markdown(f"""
            <div class="timer-big {color_class}">
                {remaining}
            </div>
            """, unsafe_allow_html=True)
            
            if remaining > 0:
                # Auto-refresh to update timer
                time.sleep(1)
                st.rerun()
            else:
                st.success("⏱️ Time's up! How did you go?")
    
    # Tips
    with st.expander("💡 Tips for this question"):
        st.write(q.get('tips', 'Take a breath, then speak confidently!'))
    
    # Self-reflection
    st.markdown("### 📝 Self-Reflection")
    notes = st.text_area("How did that go? What would you improve?",
                        height=100, key=f"video_notes_{idx}",
                        placeholder="Jot down your thoughts...")
    
    st.divider()
    
    # Navigation
    col1, col2 = st.columns([3, 1])
    with col2:
        btn_label = "Next Question →" if idx < len(questions) - 1 else "Finish Practice →"
        if st.button(btn_label, type="primary"):
            st.session_state.video_responses.append({
                'question_id': q['id'],
                'question': q['question'],
                'notes': notes
            })
            
            if idx < len(questions) - 1:
                st.session_state.q_index += 1
            else:
                st.session_state.phase = 'complete'
            st.rerun()


def show_completion():
    """Completion page with summary."""
    st.balloons()
    
    st.markdown(f"""
    <div class="success-banner">
        <h1>🎉 Awesome Work, {st.session_state.student_name}!</h1>
        <p>You've completed your practice interview!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Save session
    try:
        save_session(st.session_state.student_name, {
            'typed_responses': st.session_state.typed_responses,
            'video_responses': st.session_state.video_responses
        })
        st.success("✅ Your responses have been saved!")
    except Exception as e:
        st.warning(f"Note: Couldn't save responses locally.")
    
    # Summary tabs
    tab1, tab2 = st.tabs(["📝 Typed Responses", "🎬 Video Practice"])
    
    with tab1:
        for i, resp in enumerate(st.session_state.typed_responses, 1):
            with st.expander(f"Q{i}: {resp['question'][:50]}...", expanded=(i == 1)):
                st.markdown(f"**{resp['question']}**")
                st.info(resp['response'])
                
                if resp.get('ai_feedback'):
                    st.markdown(f"""
                    <div class="feedback-card">
                        <strong>🤖 AI Feedback:</strong><br>
                        {resp['ai_feedback']}
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        for i, resp in enumerate(st.session_state.video_responses, 1):
            with st.expander(f"Q{i}: {resp['question'][:50]}..."):
                st.markdown(f"**{resp['question']}**")
                if resp.get('notes'):
                    st.caption(f"Your notes: {resp['notes']}")
    
    st.divider()
    
    # Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Practice Again", type="primary"):
            # Keep name but reset session
            name = st.session_state.student_name
            api_key = st.session_state.get('api_key')
            for key in list(st.session_state.keys()):
                if key != 'app_mode':
                    del st.session_state[key]
            st.session_state.name_input = name
            st.session_state.api_key_input = api_key or ""
            st.rerun()
    
    with col2:
        if st.button("🏠 Start Over"):
            for key in list(st.session_state.keys()):
                if key != 'app_mode':
                    del st.session_state[key]
            st.rerun()
    
    # Tips
    st.markdown("""
    ---
    ### 💪 Keep Improving!
    
    **STAR Method** for behavioural questions:
    - **S**ituation – Set the scene
    - **T**ask – Your responsibility  
    - **A**ction – What you did
    - **R**esult – The outcome
    """)


# ============================================================
# TEACHER DASHBOARD
# ============================================================

def show_teacher_dashboard():
    """Teacher review dashboard."""
    st.markdown("""
    <div class="main-header">
        <h1>👩‍🏫 Teacher Dashboard</h1>
        <p>Review and export student responses</p>
    </div>
    """, unsafe_allow_html=True)
    
    sessions = load_all_sessions()
    
    if not sessions:
        st.info("📭 No student sessions yet. They'll appear here after students complete practice.")
        return
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sessions", len(sessions))
    with col2:
        st.metric("Unique Students", len(set(s.get('student_name', '') for s in sessions)))
    with col3:
        st.metric("Total Responses", 
                 sum(len(s.get('typed_responses', [])) + len(s.get('video_responses', [])) for s in sessions))
    
    st.divider()
    
    # Filter
    students = ['All'] + list(set(s.get('student_name', 'Unknown') for s in sessions))
    selected = st.selectbox("Filter by student:", students)
    
    filtered = sessions if selected == 'All' else [s for s in sessions if s.get('student_name') == selected]
    
    # Export
    st.download_button(
        "⬇️ Export to CSV",
        export_to_csv(filtered),
        f"responses_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv"
    )
    
    st.divider()
    
    # Session list
    for session in filtered:
        student = session.get('student_name', 'Unknown')
        timestamp = session.get('session_timestamp', '')[:16].replace('T', ' ')
        typed_n = len(session.get('typed_responses', []))
        video_n = len(session.get('video_responses', []))
        
        with st.expander(f"📋 {student} – {timestamp} ({typed_n} typed, {video_n} video)"):
            if session.get('typed_responses'):
                st.markdown("**Typed Responses:**")
                for r in session['typed_responses']:
                    st.markdown(f"*Q: {r.get('question', '')}*")
                    st.info(r.get('response', ''))
                    if r.get('ai_feedback'):
                        st.caption(f"AI: {r['ai_feedback']}")
                    st.markdown("---")
            
            if session.get('video_responses'):
                st.markdown("**Video Practice Notes:**")
                for r in session['video_responses']:
                    st.markdown(f"*Q: {r.get('question', '')}*")
                    st.caption(r.get('notes', 'No notes'))


# ============================================================
# MAIN APP
# ============================================================

def main():
    """Main application."""
    
    # Sidebar
    with st.sidebar:
        st.title("🎯 Interview Practice")
        st.divider()
        
        mode = st.radio(
            "Mode:",
            ["🎯 Student Practice", "👩‍🏫 Teacher Dashboard"],
            key="app_mode"
        )
        
        st.divider()
        st.caption("Practice for Woolworths-style interviews")
        
        # Exit button
        if 'phase' in st.session_state and st.session_state.get('phase') not in ['welcome', None]:
            if st.button("⚠️ Exit Session"):
                for key in list(st.session_state.keys()):
                    if key != 'app_mode':
                        del st.session_state[key]
                st.rerun()
    
    # Route
    if mode == "👩‍🏫 Teacher Dashboard":
        show_teacher_dashboard()
    else:
        if 'phase' not in st.session_state:
            st.session_state.phase = 'welcome'
        
        phase = st.session_state.phase
        
        if phase == 'welcome':
            show_welcome()
        elif phase == 'typed':
            show_typed_questions()
        elif phase == 'video_intro':
            show_video_intro()
        elif phase == 'video':
            show_video_questions()
        elif phase == 'complete':
            show_completion()


if __name__ == "__main__":
    main()
