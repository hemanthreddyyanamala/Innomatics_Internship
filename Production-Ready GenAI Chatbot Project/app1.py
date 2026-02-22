import streamlit as st

# Must be the very first Streamlit call
st.set_page_config(
    page_title="Blog Assistant",
    page_icon="",
    layout="centered",
    initial_sidebar_state="expanded",
)

import json
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import traceback

# === LOGGING SETUP ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


THEME_APPLE_DS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:        #0d1117;
    --surface:   #161b22;
    --border:    rgba(255,255,255,0.07);
    --text:      #e6edf3;
    --subdued:   #8b949e;
    --user-bg:   linear-gradient(135deg, #7c3aed, #4f46e5);
    --bot-bg:    rgba(22, 27, 34, 0.95);
    --accent:    #10b981;
}

/* ── layouts ── */
.stApp {
    background-color: var(--bg) !important;
    font-family: 'Inter', sans-serif !important;
    background-image:
        linear-gradient(rgba(124,58,237,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(124,58,237,0.03) 1px, transparent 1px),
        radial-gradient(ellipse at 12% 0%, rgba(124,58,237,0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 88% 100%, rgba(16,185,129,0.08) 0%, transparent 50%) !important;
    background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100% !important;
    background-attachment: fixed !important;
}

.main .block-container { padding: 1.5rem 2rem !important; max-width: 800px !important; }

h1 {
    font-weight: 700 !important;
    letter-spacing: -0.6px !important;
    text-align: center !important;
    background: linear-gradient(120deg, #a78bfa, #10b981) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
}

/* ── Chat Container ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 10px 0 !important;
    display: flex !important;
    align-items: flex-end !important;
}

/* Row alignment based on avatar */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse !important;
}

[data-testid="stChatMessageContent"] {
    max-width: 80% !important;
    margin: 0 !important;
}

/* Bubble Styling */
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    position: relative !important;
    padding: 12px 18px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    word-wrap: break-word !important;
}

/* User (Right) */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: var(--user-bg) !important;
    border-radius: 20px 20px 4px 20px !important;
    margin-right: 12px !important;
    color: white !important;
}
/* User Tail */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"]::after {
    content: "";
    position: absolute;
    bottom: 0px !important;
    right: -10px !important;
    width: 20px !important;
    height: 15px !important;
    background: #4f46e5 !important;
    clip-path: polygon(0 0, 0 100%, 100% 100%) !important;
    z-index: 100 !important;
}

/* Bot (Left) */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
    background: var(--bot-bg) !important;
    border-radius: 20px 20px 20px 4px !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid var(--accent) !important;
    margin-left: 12px !important;
    color: #e6edf3 !important;
    backdrop-filter: blur(10px);
}
/* Bot Tail */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"]::after {
    content: "";
    position: absolute;
    bottom: 0px !important;
    left: -10px !important;
    width: 20px !important;
    height: 15px !important;
    background: var(--bot-bg) !important;
    clip-path: polygon(100% 0, 0 100%, 100% 100%) !important;
    z-index: 100 !important;
}

[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    font-size: 15px !important;
    line-height: 1.5 !important;
}

/* Sidebar & Other UI */
[data-testid="stSidebar"] { background: #0d1117 !important; color: white !important; }
.stButton button { background: var(--user-bg) !important; border: none !important; border-radius: 12px !important; color: white !important; }
.stTextInput input { background: #161b22 !important; border: 1px solid var(--border) !important; border-radius: 10px !important; color: white !important; }

/* Chat Input bar fixes */
[data-testid="stChatInput"] { background: #0d1117 !important; padding: 10px !important; border-top: 1px solid var(--border) !important; }
[data-testid="stChatInput"] textarea { background: #161b22 !important; border-radius: 15px !important; color: white !important; }
</style>
"""

# === CONFIG ===
USERS_FILE = "users.json"
with open("system_prompt.txt", "r") as f:
    system_prompt = f.read().strip()

# === USER MANAGEMENT ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_dir(username):
    user_dir = f"users/{username}"
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def get_user_history_file(username):
    return f"users/{username}/history.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False
    get_user_dir(username)
    users[username] = hash_password(password)
    save_users(users)
    return True

def login_user(username, password):
    users = load_users()
    return username in users and users[username] == hash_password(password)

# === GEMINI API MODULE ===
load_dotenv()
def get_model():
    api_key = os.getenv("GOOGLE_API_KEY") or st.session_state.get("google_api_key")
    if not api_key:
        st.error(" Set Google API Key")
        st.stop()
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

def safe_generate(model, messages):
    """Production-grade API call with error handling"""
    try:
        logger.info(f"API call - User: {st.session_state.username}, Messages: {len(messages)}")
        return model.stream(messages)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return [{"content": "Sorry, I'm having technical issues. Please try again."}]

# === MEMORY MANAGEMENT ===
def load_user_history(username):
    history_file = get_user_history_file(username)
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            return json.load(f)
    return []

def save_user_conversation(username):
    history_file = get_user_history_file(username)
    history = load_user_history(username)

    new_conversation = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "messages": st.session_state.messages.copy()
    }

    history.append(new_conversation)
    history = history[-10:]  # Keep last 10 conversations

    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

def build_conversation_context():
    """Build context with token optimization"""
    messages = [SystemMessage(content=system_prompt)]

    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(HumanMessage(content=msg["content"]))

    return messages

# === SESSION INIT ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "google_api_key" not in st.session_state:
    st.session_state.google_api_key = os.getenv("GOOGLE_API_KEY")

# Inject High-Fidelity Apple DS Theme
st.markdown(THEME_APPLE_DS, unsafe_allow_html=True)

# === LOGIN SCREEN ===
if not st.session_state.logged_in:
    st.title(" Blog Assistant — Login")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.messages = []
                st.success(" Login successful!")
                st.rerun()
            else:
                st.error(" Invalid credentials")

    with tab2:
        new_username = st.text_input("New Username", key="reg_user")
        new_password = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            if register_user(new_username, new_password):
                st.success(" Registration successful!")
            else:
                st.error(" Username exists")

    st.stop()

# === MAIN APP ===
st.title(" Blog Assistant")

# === SIDEBAR ===
with st.sidebar:
    st.title(f" {st.session_state.username}")

    st.divider()

    # ── API Key ──
    if not st.session_state.google_api_key:
        st.error(" No API Key!")
        api_key = st.text_input("Google API Key:", type="password")
        if st.button(" Save API Key"):
            if api_key.strip():
                st.session_state.google_api_key = api_key.strip()
                os.environ["GOOGLE_API_KEY"] = api_key.strip()
                st.success(" Saved!")
                st.rerun()
            else:
                st.error(" Empty key!")
    else:
        st.success(" Gemini Ready!")

    st.divider()

    # ── Conversation History ──
    st.title("📜 Conversations")
    history = load_user_history(st.session_state.username)

    session_options = ["New Conversation"]
    for conv in history[-5:]:
        conv_id = (conv.get('id') or conv.get('timestamp') or 'unknown')[:15] + "..."
        session_options.append(conv_id)

    selected = st.selectbox("Select:", session_options)
    if selected != "New Conversation":
        session_id = selected.replace("...", "")
        for conv in history:
            conv_id = conv.get('id') or conv.get('timestamp') or ''
            if session_id in conv_id[:15]:
                st.session_state.messages = conv["messages"].copy()
                st.success(" Loaded!")
                break

    if st.button(" Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🚪 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if history:
        st.download_button(
            "📥 Download History",
            data=json.dumps(history, indent=2),
            file_name=f"{st.session_state.username}_history.json",
            mime="application/json"
        )

# === CHAT DISPLAY ===
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# === CHAT INPUT ===
user_prompt = st.chat_input(" Ask me about blog content...")
if user_prompt:
    logger.info(f"New message from {st.session_state.username}: {user_prompt[:50]}")

    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            model = get_model()
            messages_with_context = build_conversation_context()

            response_container = st.empty()
            full_response = ""

            stream = safe_generate(model, messages_with_context)
            for chunk in stream:
                if hasattr(chunk, 'content') and chunk.content:
                    full_response += chunk.content
                    response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})

    save_user_conversation(st.session_state.username)
    logger.info(f"Response saved for {st.session_state.username}, length: {len(full_response)}")
