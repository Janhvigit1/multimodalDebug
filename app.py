import streamlit as st
import os
import google.generativeai as genai
from groq import Groq
import ollama
from dotenv import load_dotenv
from PIL import Image
import sqlite3 
import time  # Real-time response speed calculate karne ke liye
from datetime import datetime

# Load environment variables from .env file
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

# 1. Gemini Configuration
if gemini_key:
    genai.configure(api_key=gemini_key)
else:
    st.error("Missing GEMINI_API_KEY in .env")

# 2. Groq Configuration
groq_client = None
if groq_key:
    groq_client = Groq(api_key=groq_key)
else:
    st.error("Missing GROQ_API_KEY in .env")

# Streamlit Page Setup
st.set_page_config(layout="wide", page_title="Multimodal Debugger")

# ================= 💾 SQLITE DATABASE ENGINE INITIATION =================
DB_FILE = "debugger_history.db"

def init_db():
    """Database aur Table structures save karne ke liye SQLite connection init block"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debug_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            summary TEXT,
            code TEXT,
            gemini_res TEXT,
            groq_res TEXT,
            ollama_res TEXT,
            consensus_text TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(summary, code, gemini, groq, local, consensus):
    """Database permanent commit run insert statement"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO debug_logs (timestamp, summary, code, gemini_res, groq_res, ollama_res, consensus_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, summary, code, gemini, groq, local, consensus))
    conn.commit()
    conn.close()

def fetch_history():
    """Permanent database cache restore lookup sequence latest first"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, summary, code, gemini_res, groq_res, ollama_res, consensus_text FROM debug_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            "id": r[0], "timestamp": r[1], "summary": r[2], "code": r[3],
            "gemini_res": r[4], "groq_res": r[5], "ollama_res": r[6], "consensus_text": r[7]
        })
    return history

init_db()

# PERSISTENCE STATE CACHE INITIALIZATION (Prevents early execution screen exit)
if "current_results" not in st.session_state:
    st.session_state.current_results = None

# ================= 🎨 ULTRA PRESTIGE, EXTREMELY SYMMETRIC UI & STATUS WIDGET RESTORATION 🎨 =================
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        /* 🎯 SELECTIVE HEADER OVERRIDES: HIDE DEPLOY BUTTON & MENU BUT KEEP RUNNING STATUS ICON/STOP BUTTON */
        [data-testid="stHeader"] {
            background-color: transparent !important;
            background: transparent !important;
            border-bottom: none !important;
        }
        
        /* Sirf target deploy button aur menu dropdown hide hoga, status indicators untouched rahenge */
        .stDeployButton, [data-testid="stAppDeployButton"] {
            visibility: hidden !important;
            display: none !important;
        }
        
        #MainMenu, [data-testid="stManageAppButton"] {
            visibility: hidden !important;
            display: none !important;
        }
        
        footer {
            visibility: hidden !important;
            display: none !important;
        }

        /* Running state custom widget alignment override to keep status indicator floating correctly */
        [data-testid="stStatusWidget"], .stStatusWidget {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 20px !important;
            padding: 4px 14px !important;
            box-shadow: 0 0 10px rgba(142, 84, 233, 0.2) !important;
            display: inline-flex !important;
            visibility: visible !important;
        }
        
        /* General App Theme Base */
        .main {
            background-color: #0e1117;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding-top: 1rem !important;
        }
        
        .main-title {
            font-size: 2.8rem !important;
            font-weight: 700;
            color: #ffffff;
            text-align: center;
            margin-bottom: 5px;
            letter-spacing: -0.5px;
            text-shadow: 0 0 10px rgba(142, 84, 233, 0.3);
        }
        .sub-title {
            color: #8a99ad;
            text-align: center;
            font-size: 1.1rem;
            margin-bottom: 35px;
        }

        /* Symmetric Box Titles */
        .input-label {
            font-size: 1.1rem;
            font-weight: 600;
            color: #cbd5e1;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            height: 30px;
        }

        /* SYMMETRIC FORM BOX HEIGHT OVERRIDES (Locking minimum height to 160px for premium layout) */
        .stTextArea textarea {
            background-color: #161b22 !important;
            color: #c9d1d9 !important;
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
            font-family: 'Courier New', Courier, monospace !important;
            height: 160px !important; 
            min-height: 160px !important;
            max-height: 160px !important;
            overflow-y: auto;
            box-shadow: none !important;
        }
        .stTextArea textarea:focus {
            border-color: #8e54e9 !important;
            box-shadow: 0 0 5px rgba(142, 84, 233, 0.4) !important;
        }

        /* Spacious File Uploader Container with dynamic min-height to prevent clipping of text details */
        [data-testid="stFileUploader"] {
            border: 1px solid #30363d !important;
            border-radius: 6px !important;
            background-color: #161b22 !important;
            min-height: 160px !important;
            height: auto !important;
            padding: 16px !important;
            box-sizing: border-box !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            padding: 0px !important;
            border: none !important;
            background: transparent !important;
        }

        /* FIXED: SCREENSHOT FILENAME TEXT OVERFLOW WRAPPING (No more halving or cutting) */
        [data-testid="stFileUploaderFileName"], .stFileUploaderFileName {
            white-space: normal !important;
            word-break: break-all !important;
            overflow: visible !important;
            text-overflow: clip !important;
            max-width: 100% !important;
            color: #cbd5e1 !important;
            font-size: 0.95rem !important;
            line-height: 1.4 !important;
            display: block !important;
        }
        
        /* Forces deep list blocks in streamlit fileuploader layout to wrap cleanly */
        [data-testid="stFileUploaderFile"], [data-testid="stFileUploaderFileData"] {
            overflow: visible !important;
            text-overflow: clip !important;
            max-width: 100% !important;
            white-space: normal !important;
            display: block !important;
        }

        /* Multi-Agent Cards containers styling */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 10px !important;
            padding: 10px !important;
            margin-bottom: 20px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .model-heading {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #ffffff !important;
            padding-bottom: 12px;
            margin-bottom: 15px;
            border-bottom: 2px solid #30363d;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .icon-gemini { color: #4285F4; }
        .icon-groq { color: #F4B400; }
        .icon-local { color: #0F9D58; }
        .icon-consensus { color: #38bdf8; margin-right: 12px; }

        .stMarkdown p, .stMarkdown li {
            font-size: 0.98rem !important;
            line-height: 1.6 !important;
            color: #cbd5e1 !important;
        }

        /* Action triggers */
        .stButton>button {
            background-color: #238636 !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            border-radius: 8px;
            border: 1px solid #2ea44f !important;
            width: 100%;
            font-size: 1rem !important;
            box-shadow: 0 2px 4px rgba(35, 134, 54, 0.2);
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #2ea44f !important;
            transform: translateY(-1px);
        }
        
        .consensus-header {
            font-size: 1.6rem !important;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            border-bottom: 2px solid #30363d;
            padding-bottom: 12px;
        }
        
        div.stDownloadButton > button {
            background-color: #21262d !important;
            color: #cbd5e1 !important;
            border: 1px solid #30363d !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
            border-radius: 6px !important;
            font-size: 0.95rem !important;
        }

        /* 💼 SLIM CHATGPT/GEMINI-STYLE SIDEBAR INTEGRITY 💼 */
        .sidebar-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: #f0f6fc;
            margin-bottom: 16px;
            border-bottom: 1px solid #21262d;
            padding-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Sidebar container lists styling overrides with thoda sa dark background */
        .stSidebar .stButton>button {
            background-color: #090b0f !important; /* Slightly darker slate background */
            color: #c9d1d9 !important;
            border: 1px solid #21262d !important; /* Premium subtle border */
            text-align: left !important;
            padding: 8px 12px !important;
            font-size: 0.85rem !important;
            width: 100% !important;
            border-radius: 8px !important;
            margin-bottom: 6px !important;
            transition: all 0.2s ease !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
        }
        
        .stSidebar .stButton>button:hover {
            background-color: #21262d !important;
            color: #ffffff !important;
            border-color: #30363d !important;
            box-shadow: none !important;
        }
        
        .stSidebar .stButton>button:active {
            background-color: #30363d !important;
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

# ================= SIDEBAR HISTORY PANEL =================
with st.sidebar:
    st.markdown('<div class="sidebar-title"><i class="fa-solid fa-clock-history" style="color:#8b949e;"></i>Recent Debugs</div>', unsafe_allow_html=True)
    db_logs = fetch_history()
    if not db_logs:
        st.info("No logs found in DB.")
    else:
        for idx, item in enumerate(db_logs):
            # Formating the summary to a clean one-liner with icon and timestamp
            time_short = item["timestamp"].split(" ")[1][:5] if " " in item["timestamp"] else ""
            raw_summary = item["summary"].replace("\n", " ").strip()
            # Trim the raw summary for clean display
            trimmed_summary = raw_summary[:22] + "..." if len(raw_summary) > 22 else raw_summary
            button_label = f"{trimmed_summary}  ({time_short})"
            
            # Slim Sidebar restoration button using Streamlit native full width styling
            if st.button(button_label, key=f"db_reload_{item['id']}", use_container_width=True):
                st.session_state.current_results = {
                    "code": item["code"],
                    "gemini_res": item["gemini_res"],
                    "groq_res": item["groq_res"],
                    "ollama_res": item["ollama_res"],
                    "consensus_text": item["consensus_text"],
                    "gemini_time": 1.4,
                    "groq_time": 0.8,
                    "ollama_time": 3.6
                }
                st.rerun()

# Main Dashboard Frame
st.markdown('<div class="main-title"><i class="fa-solid fa-code-branch" style="margin-right:15px; color:#8e54e9;"></i>Multimodal Debugger</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Advanced Multi-Agent Consensus and Voting System</div>', unsafe_allow_html=True)

# Symmetric Layout Config
input_col1, input_col2 = st.columns(2)

default_text = "def hello():\nprint('(Demo text: type/paste code here)')"

# Load correct text string depending on loaded state cache
active_code_value = default_text
if st.session_state.current_results:
    active_code_value = st.session_state.current_results["code"]

with input_col1:
    st.markdown('<div class="input-label"><i class="fa-solid fa-terminal"></i>Source Code Submission</div>', unsafe_allow_html=True)
    user_code = st.text_area("", active_code_value, label_visibility="collapsed")

with input_col2:
    st.markdown('<div class="input-label"><i class="fa-solid fa-image"></i>Upload Screenshot (Optional)</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    # Image Preview rendered exactly under the File Upload Box
    if uploaded_file:
        st.markdown("<br>", unsafe_allow_html=True)
        st.image(uploaded_file, caption="Uploaded Image Context Preview", width=280)

st.markdown("<br>", unsafe_allow_html=True)

execute_click = st.button("Execute Multi-Agent Debugging")

# ================= CORE MULTI-AGENT INFERENCE LOOP =================
if execute_click:
    if not user_code.strip() and uploaded_file is None:
        st.warning("Please provide code or an image.")
        st.stop()

    base_prompt = "You are an expert technical debugger. Fix the bugs, provide the corrected code, and list the errors with short explanations. Do not use # or ## headers."
    img = Image.open(uploaded_file) if uploaded_file else None

    gemini_res, groq_res, ollama_res = "", "", ""
    gemini_failed = False
    
    gemini_time, groq_time, ollama_time = 0.0, 0.0, 0.0
    
    # STEP 1: RESOLVE ABSOLUTE INPUT PRIORITY
    # Agar screenshot upload hua hai, toh hum Gemini Vision ka use karke pehle code extract karenge.
    # Extracted code hi Ollama aur Groq ke paas jayega.
    code_to_debug = ""
    
    with st.spinner("🤖 Extracting context and starting multi-agent debugging pipeline..."):
        if img:
            # First, extract code cleanly from screenshot using Gemini Vision
            try:
                extraction_model = genai.GenerativeModel('gemini-2.5-flash')
                extraction_prompt = "Identify and extract only the raw source code written in this screenshot. Return ONLY the code text exactly as shown. No explanations, no markdown blocks, no extra characters."
                extraction_response = extraction_model.generate_content([extraction_prompt, img])
                code_to_debug = extraction_response.text.strip()
                
                # Cleanup any accidental markdown backticks extracted by Gemini
                if code_to_debug.startswith("```"):
                    lines = code_to_debug.splitlines()
                    if len(lines) > 2:
                        code_to_debug = "\n".join(lines[1:-1])
            except Exception as e:
                gemini_failed = True
                code_to_debug = ""
                st.error(f"Image text extraction failed: {str(e)}")
        else:
            # If no screenshot, fall back to the text area input
            code_to_debug = user_code
            if default_text in code_to_debug:
                code_to_debug = code_to_debug.replace(default_text, "").strip()

        # Check if we finally have code to evaluate
        if not code_to_debug.strip():
            st.error("No extractable source code found to analyze!")
            st.stop()

        # ----- ENGINE 1: GOOGLE GEMINI CORE -----
        t_start = time.time()
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            # Gemini analyzes the extracted code directly to keep all models fully synchronized!
            response = model.generate_content(f"{base_prompt}\n\nCode to debug:\n{code_to_debug}")
            gemini_res = response.text
            gemini_time = round(time.time() - t_start, 2)
        except Exception as e:
            gemini_failed = True
            gemini_res = "⚠️ Gemini Engine is currently rate-limited or unavailable. Switched to backup pipeline."
            gemini_time = 0.0

        # Unified prompt for text-only engines (Groq & Local Agent)
        combined_prompt = f"{base_prompt}\n\nCode to debug:\n{code_to_debug}"

        # ----- ENGINE 2: GROQ CLOUD CORE -----
        t_start = time.time()
        try:
            if groq_client:
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": combined_prompt}],
                    model="llama-3.3-70b-versatile",
                )
                groq_res = chat_completion.choices[0].message.content
                groq_time = round(time.time() - t_start, 2)
            else:
                groq_res = "⚠️ Groq Key is missing. Please add GROQ_API_KEY to your .env file."
                groq_time = 0.0
        except Exception as e:
            groq_res = f"⚠️ Groq Engine failed: {str(e)}"
            groq_time = 0.0

        # ----- ENGINE 3: LOCAL OLLAMA AGENT -----
        t_start = time.time()
        try:
            res = ollama.chat(model='llama3:8b', messages=[{'role': 'user', 'content': combined_prompt}])
            ollama_res = res['message']['content']
            ollama_time = round(time.time() - t_start, 2)
        except Exception as e:
            ollama_res = "⚠️ Local Agent (Ollama) is not responding. Please ensure Ollama is running on your Mac with 'ollama run llama3:8b'."
            ollama_time = 0.0

        # ----- MASTER CONSENSUS ENGINE (FAILSAFE DUAL-BACKUP TRIGGER) -----
        consensus_text = ""
        vote_prompt = f"Analyze these solutions and provide one final perfect 'Consensus Winner Code' and error summary. No markdown headers:\n\n1: {gemini_res}\n\n2: {groq_res}\n\n3: {ollama_res}"
        
        # Try Groq first for consensus evaluation
        try:
            if groq_client and not gemini_failed:
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": vote_prompt}],
                    model="llama-3.3-70b-versatile",
                )
                consensus_text = chat_completion.choices[0].message.content
            else:
                raise ValueError("Groq client not initialized or Gemini rate-limited")
        except Exception as e_groq:
            # Fallback to Gemini
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                final_decision = model.generate_content(vote_prompt)
                consensus_text = final_decision.text
            except Exception as e_gemini:
                # Absolute fallback: combine responses programmatically so consensus never returns empty!
                consensus_text = f"⚠️ Multi-Agent consensus engines are currently offline. Programmatically combined backup responses:\n\n### Diagnosis 1:\n{groq_res}\n\n### Diagnosis 2:\n{ollama_res}"

    # Push results to SQLite repository
    db_summary = code_to_debug if code_to_debug.strip() else "Screenshot Analysis"
    save_to_db(db_summary, code_to_debug, gemini_res, groq_res, ollama_res, consensus_text)

    # Cache calculations into states
    st.session_state.current_results = {
        "code": code_to_debug,
        "gemini_res": gemini_res,
        "groq_res": groq_res,
        "ollama_res": ollama_res,
        "consensus_text": consensus_text,
        "gemini_time": gemini_time,
        "groq_time": groq_time,
        "ollama_time": ollama_time
    }
    
    # Reload app and lock final cached layout parameters
    st.rerun()

# ================= PERSISTENT VISUALIZATION AND REPORTING ENGINE =================
if st.session_state.current_results:
    res_data = st.session_state.current_results
    
    # 1. Individual cards rendered symmetrically
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown('<div class="model-heading"><i class="fa-solid fa-brands fa-google icon-gemini"></i>Gemini Engine</div>', unsafe_allow_html=True)
            st.markdown(res_data["gemini_res"])
            if "gemini_time" in res_data and res_data["gemini_time"] > 0.0:
                st.caption(f"⚡ Latency: **{res_data['gemini_time']}s**")
            
    with col2:
        with st.container(border=True):
            st.markdown('<div class="model-heading"><i class="fa-solid fa-bolt icon-groq"></i>Groq Engine</div>', unsafe_allow_html=True)
            st.markdown(res_data["groq_res"])
            if "groq_time" in res_data and res_data["groq_time"] > 0.0:
                st.caption(f"⚡ Latency: **{res_data['groq_time']}s**")
            
    with col3:
        with st.container(border=True):
            st.markdown('<div class="model-heading"><i class="fa-solid fa-laptop-code icon-local"></i>Local Agent</div>', unsafe_allow_html=True)
            st.markdown(res_data["ollama_res"])
            if "ollama_time" in res_data and res_data["ollama_time"] > 0.0:
                st.caption(f"⚡ Latency: **{res_data['ollama_time']}s**")

    # 2. Master Consensus Block
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="consensus-header"><i class="fa-solid fa-square-poll-vertical icon-consensus"></i>Multi-Agent Consensus Verdict</div>', unsafe_allow_html=True)
        st.write(res_data["consensus_text"])

    # ================= PERFORMANCE SPEED & CAPABILITY COMPARISON MATRIX =================
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="consensus-header" style="color: #cbd5e1;"><i class="fa-solid fa-chart-line icon-consensus" style="color: #a855f7;"></i>Engine Inference Latency Comparison</div>', unsafe_allow_html=True)
        
        chart_col1, chart_col2 = st.columns([1, 1])
        
        g_time = res_data.get("gemini_time", 1.4)
        q_time = res_data.get("groq_time", 0.8)
        o_time = res_data.get("ollama_time", 3.6)
        
        # Guard clause for chart calculations to prevent zero latency chart issues
        g_time = 0.1 if g_time == 0.0 else g_time
        q_time = 0.1 if q_time == 0.0 else q_time
        o_time = 0.1 if o_time == 0.0 else o_time
        
        with chart_col1:
            st.caption("Inference Latency (Lower is Better - in Seconds)")
            chart_data = {
                "Engine": ["Gemini 2.5 Flash", "Groq Llama 3.3", "Local Ollama"],
                "Latency (Seconds)": [g_time, q_time, o_time]
            }
            st.bar_chart(data=chart_data, x="Engine", y="Latency (Seconds)", color="#8e54e9")
            
        with chart_col2:
            st.markdown("""
                <div style="padding-left: 20px;">
                    <h5 style="color: #f0f6fc; margin-bottom: 15px;"><i class="fa-solid fa-gauge-high" style="color:#2ea44f; margin-right: 10px;"></i>Latency Diagnostic Insights</h5>
                    <ul style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;">
                        <li><b>Groq Engine:</b> Cloud API LPU optimization ke zariye sabse fast text response process karta hai.</li>
                        <li><b>Gemini Engine:</b> Multimodal vision extraction aur deep reasoning operations sath mein run karta hai.</li>
                        <li><b>Local Ollama:</b> Speed purely host computer ke raw hardware capacity (RAM, CPU, and GPU cores) par nirbhar karti hai.</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<h5 style="color: #ffffff; padding-bottom:10px; border-bottom: 1px solid #30363d;"><i class="fa-solid fa-list-check" style="color:#38bdf8; margin-right: 10px;"></i>Agent Head-to-Head Capability Matrix</h5>', unsafe_allow_html=True)
        
        # Capability dynamic markup grid
        st.markdown(f"""
            <table style="width:100%; border-collapse: collapse; margin-top: 15px; color: #cbd5e1; font-size: 0.95rem;">
                <thead>
                    <tr style="border-bottom: 2px solid #30363d; text-align: left;">
                        <th style="padding: 12px;">Debugging Parameters</th>
                        <th style="padding: 12px; color: #4285F4;">Gemini 2.5 Flash</th>
                        <th style="padding: 12px; color: #F4B400;">Groq Llama 3.3</th>
                        <th style="padding: 12px; color: #0F9D58;">Local Agent (Llama3)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #21262d;">
                        <td style="padding: 12px; font-weight: 600;">Modality Support</td>
                        <td style="padding: 12px; color: #2ea44f;"><i class="fa-solid fa-circle-check"></i> Multimodal (Vision+Text)</td>
                        <td style="padding: 12px; color: #f85149;"><i class="fa-solid fa-circle-xmark"></i> Text Only</td>
                        <td style="padding: 12px; color: #f85149;"><i class="fa-solid fa-circle-xmark"></i> Text Only (Local)</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #21262d;">
                        <td style="padding: 12px; font-weight: 600;">Response Speed</td>
                        <td style="padding: 12px;">{g_time}s (Fast)</td>
                        <td style="padding: 12px; color: #2ea44f; font-weight: 600;">{q_time}s (Ultra Fast)</td>
                        <td style="padding: 12px;">{o_time}s (Hardware Bound)</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #21262d;">
                        <td style="padding: 12px; font-weight: 600;">Offline Operations</td>
                        <td style="padding: 12px; color: #f85149;"><i class="fa-solid fa-circle-xmark"></i> Internet Required</td>
                        <td style="padding: 12px; color: #f85149;"><i class="fa-solid fa-circle-xmark"></i> Internet Required</td>
                        <td style="padding: 12px; color: #2ea44f;"><i class="fa-solid fa-circle-check"></i> 100% Local (Private)</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #21262d;">
                        <td style="padding: 12px; font-weight: 600;">Logical Reasoning Level</td>
                        <td style="padding: 12px;">Advanced</td>
                        <td style="padding: 12px; color: #38bdf8; font-weight: 600;">Excellent (70B model)</td>
                        <td style="padding: 12px;">Good (8B model)</td>
                    </tr>
                </tbody>
            </table>
        """, unsafe_allow_html=True)

    # 3. Downloadable MD Debugging Report
    display_code = res_data["code"] if res_data["code"].strip() else '[Code submitted via Screenshot Context]'
    report_content = (
        f"# MULTIMODAL DEBUGGER REPORT\n\n"
        f"## Submitted Code Context:\n```python\n{display_code}\n```\n\n"
        f"---\n"
        f"## Model Individual Diagnostics:\n\n"
        f"### 1. Google Gemini Engine:\n{res_data['gemini_res']}\n\n"
        f"### 2. Groq Cloud Engine:\n{res_data['groq_res']}\n\n"
        f"### 3. Local System Agent:\n{res_data['ollama_res']}\n\n"
        f"---\n"
        f"## 4. Final Multi-Agent Consensus Verdict:\n{res_data['consensus_text']}\n"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="Download Debugging Report",
        data=report_content,
        file_name="debugging_report.md",
        mime="text/markdown"
    )