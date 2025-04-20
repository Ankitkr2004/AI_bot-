import streamlit as st
import os
from dotenv import load_dotenv
from chatbot import SmartBudgetAIChatbot
import traceback

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="FIN - Budgeting & Expense Estimation Planner",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'chatbot' not in st.session_state:
    try:
        st.session_state.chatbot = SmartBudgetAIChatbot()
    except Exception as e:
        st.error(f"Error initializing chatbot: {str(e)}")
        st.error(traceback.format_exc())

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #1f2937;
    }
    .chat-message .content {
        margin-top: 0.5rem;
    }
    .stTextInput>div>div>input {
        background-color: #1f2937;
    }
    .logo-text {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("💰 FIN - Budgeting & Expense Estimation Planner")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown('<div class="logo-text">💰 FIN</div>', unsafe_allow_html=True)
    st.markdown("### About FIN")
    st.markdown("""
    FIN is your AI-powered financial assistant that helps you:
    - Create and manage monthly budgets
    - Plan and optimize travel budgets
    - Track expenses and savings
    - Set financial goals
    - Get personalized financial advice
    """)
    st.markdown("---")
    st.markdown("Made by - Ankit Kumar 12312618")
    st.markdown("          DipeshKumar Joshi 12303249")
    st.markdown("          Daksh Gupta 12313179")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about your finances..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get bot response
    try:
        response = st.session_state.chatbot.get_ai_response(prompt)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.error(traceback.format_exc()) 
