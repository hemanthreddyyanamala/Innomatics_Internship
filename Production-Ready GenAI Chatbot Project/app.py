import streamlit as st
import json
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import traceback

# === LOGGING SETUP (Production Requirement) ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

load_dotenv()
# === GEMINI API MODULE ===
def get_model():
    api_key = os.getenv("GOOGLE_API_KEY") or st.session_state.get("google_api_key")
    if not api_key:
        st.error("Set Google API Key")
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
    
    # Limit to last 20 messages (10 exchanges)
    for msg in st.session_state.messages[-20:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(HumanMessage(content=msg["content"]))  # Fixed: Use AIMessage
    
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

# === LOGIN SCREEN ===
if not st.session_state.logged_in:
    st.title("Blog Assistant - Login Required")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.messages = []
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    with tab2:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Register"):
            if register_user(new_username, new_password):
                st.success("Registration successful!")
            else:
                st.error("Username exists")
    
    st.stop()

# === MAIN APP ===
st.title("Blog Assistant Chatbot")

# === SIDEBAR ===
with st.sidebar:    
    st.title(f"👤 {st.session_state.username}")
    
    # API Key Management
    if not st.session_state.google_api_key:
        st.error("No API Key!")
        api_key = st.text_input("Google API Key:", type="password")
        if st.button("Save API Key"):
            if api_key.strip():
                st.session_state.google_api_key = api_key.strip()
                os.environ["GOOGLE_API_KEY"] = api_key.strip()
                st.success("Saved!")
                st.rerun()
            else:
                st.error("Empty key!")
    else:
        st.success("Gemini Ready!")
    
    # Conversation History
    st.title(" Conversations")
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
                st.success("Loaded!")
                break
    
    if st.button(" Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    if st.button(" Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Download History
    if history:
        st.download_button(
            "Download History",
            data=json.dumps(history, indent=2),
            file_name=f"{st.session_state.username}_history.json",
            mime="application/json"
        )

# === CHAT DISPLAY ===
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# === CHAT INPUT WITH PRODUCTION FEATURES ===
user_prompt = st.chat_input("Ask me about blog content...")
if user_prompt:
    logger.info(f"New message from {st.session_state.username}: {user_prompt[:50]}")
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    # Generate response with spinner + error handling
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
    
    # Save conversation
    save_user_conversation(st.session_state.username)
    logger.info(f"Response saved for {st.session_state.username}, length: {len(full_response)}")
