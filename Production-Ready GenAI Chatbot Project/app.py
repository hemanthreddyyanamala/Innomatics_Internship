import streamlit as st
import json
from datetime import datetime
import getpass
import os
from dotenv import load_dotenv

from langchain_ollama import OllamaLLM

def get_model():    
    
    model = OllamaLLM(
        model="qwen3:8b",
    )
    return model




# from langchain_google_genai import ChatGoogleGenerativeAI
# load_dotenv()



# if "GOOGLE_API_KEY" not in os.environ:
#     os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")
# def get_model():
#     return ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash-lite",
#     temperature=0.7
# )
st.title("Blog Assistant Chatbot")




system_prompt = '''
answer less than 3 lines and be concise and to the point.
You are a Blog Assistant specialized in generating content ideas, summaries, and promotional material for blog posts also you are the blog post generator.
Your expertise includes crafting engaging social media posts, concise summaries, email snippets, and extracting key takeaways from blog content.
Always provide clear, actionable insights that can help bloggers effectively promote their content and engage their audience. 
Reference past conversation context when relevant. Here are some must follow instructions for your responses:
if user ask to generate content, always ask follow-up questions to gather necessary information before generating content 
1. Ask user for a blog post title and summary, then generate social media posts to promote it.
2. Ask user for a platform (LinkedIn, Twitter, or Facebook) and generate a post for that platform.
3. Ask user for a blog post title and topic, then draft an email newsletter snippet to announce it.
4. Ask user to some key concepts or takeaways from a blog post for sharing on social media.
5. Ask user to paste their blog post text and extract key takeaways or quotable snippets for social media posts.
6. Always ask follow-up questions to gather necessary information before generating content.
7. Provide concise, engaging, and actionable content ideas that can help bloggers effectively promote their content and engage their audience.
8. Reference past conversation context when relevant to provide more personalized and relevant content suggestions.
9. Always ask follow-up questions to gather necessary information before generating content.
'''

# st.sidebar.title("Blog Assistant Chatbot")
# st.sidebar.selectbox("selecy your past conversation", options=["Conversation 1", "Conversation 2", "Conversation 3"])
# st.sidebar.download_button(
#     data="sample conversation",
#     file_name="sample_conversation.txt",
#     label="Download Sample Conversation",
# )





HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_conversation():
    history = load_history()
    new_conversation = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().isoformat(),
        "messages": st.session_state.messages.copy()
    }
    history.append(new_conversation)
    history = history[-10:]
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# Sidebar with New/Existing toggle
st.sidebar.title("📜 Conversation History")
history = load_history()

# SAFE Session selector (no KeyError)
session_options = ["➕ New Conversation"]
for conv in history[-5:]:
    conv_id = (conv.get('id') or conv.get('timestamp') or 'unknown')[:15] + "..."
    session_options.append(conv_id)

selected_session = st.sidebar.selectbox("Select conversation:", session_options)

# Initialize session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load or create conversation
if selected_session == "➕ New Conversation":
    st.session_state.messages = []  # NEW conversation - clear everything
else:
    # Load existing conversation safely
    session_id = selected_session.replace("...", "")
    for conv in history:
        conv_id = conv.get('id') or conv.get('timestamp') or ''
        if session_id in conv_id:
            st.session_state.messages = conv["messages"]
            st.sidebar.success(f"✅ Loaded conversation")
            break

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input with streaming
user_prompt = st.chat_input("💡 What can I help you with today?")
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    with st.chat_message("assistant"):
        model = get_model()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        full_response = st.write_stream(model.stream(messages))
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    save_conversation()

# Sidebar download
if history:
    st.sidebar.download_button(
        label="📥 Download History",
        data=json.dumps(history, indent=2),
        file_name="blog_assistant_history.json",
        mime="application/json"
    )
