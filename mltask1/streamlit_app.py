import streamlit as st
import pickle

# Page config
st.set_page_config(
    page_title="Product Review Sentiment Analysis",
    page_icon="🛒",
    layout="centered"
)

# Flipkart Theme CSS with Vertical Centering
st.markdown("""
<style>
    /* Import Roboto font (Flipkart's font) */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Remove default padding */
    .main .block-container {
        padding-top: 0;
        padding-bottom: 0;
    }
    
    /* Main app background - Flipkart Blue */
    .stApp {
        background: linear-gradient(135deg, #2874f0 0%, #1e5bc6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
    }
    
    /* Force vertical centering for the main container */
    [data-testid="stAppViewContainer"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 100vh;
    }
    
    [data-testid="stAppViewContainer"] > div:first-child {
        width: 100%;
    }
    
    /* Main container card - Flipkart style white card */
    .block-container {
        padding: 3rem 2.5rem !important;
        max-width: 650px !important;
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 2px 16px rgba(0, 0, 0, 0.15);
        margin: auto !important;
    }
    
    /* Flipkart logo style title */
    h1 {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
        text-align: center;
        text-shadow: none !important;
        opacity: 1 !important;
    }
    
    /* Remove the badge if it's causing issues */
    h1::after {
        content: '';
    }
    
    /* Subtitle text */
    p, .stMarkdown {
        color: #878787 !important;
        font-size: 1rem;
        text-align: center;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }
    
    /* Force all text to be visible */
    .stMarkdown, .stMarkdown p, h1, h2, h3 {
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Text area - Flipkart input style */
    .stTextArea {
        margin-bottom: 1.5rem;
    }
    
    .stTextArea textarea {
        border: 1px solid #c2c2c2;
        border-radius: 2px;
        padding: 16px;
        font-size: 15px;
        color: #ffffff;
        background-color: #2874f0;
        box-shadow: none;
        transition: all 0.2s ease;
        min-height: 150px;
        text-align: center;
    }
    
    .stTextArea textarea:focus {
        border-color: #2874f0;
        box-shadow: 0 0 4px rgba(40, 116, 240, 0.3);
        outline: none;
    }
    
    .stTextArea textarea::placeholder {
        color: #e0e0e0;
        font-size: 14px;
    }
    
    /* Button - Flipkart orange button */
    .stButton {
        display: flex;
        justify-content: center;
        margin-top: 1rem;
    }
    
    .stButton button {
        background: #000000;
        color: #ffffff;
        border: none;
        border-radius: 2px;
        padding: 14px 40px;
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        width: 100%;
        max-width: 300px;
    }
    
    .stButton button:hover {
        background: #ff8c00;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* Success message (Positive) - Flipkart green */
    .stSuccess {
        background: #f0f9ff;
        border: 1px solid #388e3c;
        border-left: 4px solid #388e3c;
        border-radius: 4px;
        padding: 16px;
        color: #1e7e34;
        font-weight: 500;
        text-align: center;
        margin-top: 1.5rem;
        animation: slideIn 0.4s ease;
    }
    
    .stSuccess::before {
        content: '✓ ';
        font-weight: 900;
        font-size: 1.2rem;
        color: #388e3c;
    }
    
    /* Error message (Negative) - Flipkart red */
    .stError {
        background: #fff4f4;
        border: 1px solid #d32f2f;
        border-left: 4px solid #d32f2f;
        border-radius: 4px;
        padding: 16px;
        color: #c62828;
        font-weight: 500;
        text-align: center;
        margin-top: 1.5rem;
        animation: slideIn 0.4s ease;
    }
    
    .stError::before {
        content: '✗ ';
        font-weight: 900;
        font-size: 1.2rem;
        color: #d32f2f;
    }
    
    /* Warning message - Flipkart yellow */
    .stWarning {
        background: #fffbf0;
        border: 1px solid #ff9800;
        border-left: 4px solid #ff9800;
        border-radius: 4px;
        padding: 16px;
        color: #e65100;
        font-weight: 500;
        text-align: center;
        margin-top: 1.5rem;
        animation: slideIn 0.4s ease;
    }
    
    .stWarning::before {
        content: '⚠ ';
        font-weight: 900;
        font-size: 1.2rem;
        color: #ff9800;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Label text - Flipkart style */
    .stTextArea label {
        color: #878787;
        font-weight: 500;
        font-size: 15px;
        margin-bottom: 8px;
        text-align: center;
        width: 100%;
        display: block;
    }
    
    /* Flipkart badge decoration */
    .block-container::before {
        content: 'Flipkart';
        position: absolute;
        top: 10px;
        right: 10px;
        background: #ffe500;
        color: #2874f0;
        padding: 4px 12px;
        border-radius: 2px;
        font-size: 12px;
        font-weight: 700;
        font-style: italic;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Load model using pickle
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as file:
        model = pickle.load(file)
    return model

model = load_model()

# UI
st.title(" Product Review Sentiment Analysis")
st.write("This app predicts whether a product review is **Positive** or **Negative**.")

# Input
review_text = st.text_area(
    "Enter a Product Review ",
    height=150,
    placeholder="Example: The product quality is amazing and worth the price"
)

# Predict
if st.button("Analyze Sentiment"):
    if review_text.strip() == "":
        st.warning("Please enter a review first!")
    else:
        # Direct prediction (string output)
        prediction = model.predict([review_text])[0]

        # Display result directly
        if prediction.lower() == "positive":
            st.success(f" **{prediction} Review** ")
        else:
            st.error(f" **{prediction} Review** ")