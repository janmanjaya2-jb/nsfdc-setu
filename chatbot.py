import streamlit as st
from deep_translator import GoogleTranslator

# 1. Setup the Translator
def translate_text(text, lang_code):
    """Translates text to the target language seamlessly."""
    try:
        if lang_code == 'en': 
            return text
        return GoogleTranslator(source='auto', target=lang_code).translate(text)
    except Exception:
        return text 

# 2. Comprehensive Chatbot Logic (Fully Loaded Vocabulary)
def chatbot_reply(user_message):
    """Checks user input against a master list of project keywords."""
    msg = user_message.lower()
    
    # Category 1: Greetings & Politeness
    if any(word in msg for word in ["hello", "hi", "hey", "namaste", "pranam", "good morning", "good evening"]):
        return "Hello! I am the NSFDC Setu guide. I can help you find loan schemes, calculate EMIs, or locate channel partners. How can I assist you?"
    
    if any(word in msg for word in ["thank", "thanks", "dhanyavad", "great"]):
        return "You're very welcome! Let me know if you need to check anything else."
    
    if any(word in msg for word in ["help", "confused", "stuck", "how to"]):
        return "Don't worry. I can help you with three things: finding a loan scheme, calculating your EMI, or locating a branch. Which one would you like to do?"

    # Category 2: General NSFDC & Eligibility Knowledge
    if any(word in msg for word in ["what is nsfdc", "about nsfdc", "full form"]):
        return "NSFDC stands for National Scheduled Castes Finance and Development Corporation. It provides concessional loans to SC entrepreneurs to support their businesses and education."
    
    if any(word in msg for word in ["eligible", "qualify", "who can apply", "income limit"]):
        return "To be eligible, the applicant must belong to the Scheduled Caste (SC) community and their annual family income must be up to ₹5.00 Lakhs. Tell me your project cost to see which scheme fits you."

    if any(word in msg for word in ["what schemes", "list schemes", "types of loan"]):
        return "We offer three main schemes: the Micro Finance Scheme (up to ₹1.40 Lakh), the Term Loan Scheme (up to ₹50 Lakh), and the Educational Loan Scheme."

    # Category 3: Core Project Modules (Waiting for Backend Integration)
    if any(word in msg for word in ["emi", "monthly", "calculate", "interest", "calculator", "repayment"]):
        return "I can calculate that for you! Just tell me your total project cost and I will estimate your monthly EMI."
    
    if any(word in msg for word in ["nearest", "branch", "where", "locate", "bank", "partner", "map"]):
        return "I can find the closest bank or channel partner for you. What district are you located in?"
    
    if any(word in msg for word in ["scheme", "loan", "project", "education"]):
        return "Tell me if your loan is for a business project or for education, and your estimated cost, and I will recommend the right scheme."
    
    # Category 4: Default Fallback
    return "I am here to help you navigate NSFDC schemes. Would you like to find a scheme, calculate an EMI, or locate a nearby branch?"

# 3. Setup the Streamlit Web Interface
st.title("🏦 NSFDC Setu Chatbot")

# Sidebar for Language Selection
st.sidebar.header("Language Settings")
language = st.sidebar.selectbox("Choose Language:", ["English", "Hindi", "Odia"])
lang_map = {"English": "en", "Hindi": "hi", "Odia": "or"}
target_lang = lang_map[language]

# Initialize chat history memory
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your NSFDC guide. How can I help you today?"}]

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept new user input
if prompt := st.chat_input("Ask me about schemes, EMI, or nearest branches..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Generate bot response and translate it
    english_reply = chatbot_reply(prompt)
    final_reply = translate_text(english_reply, target_lang)
    
    # Show bot response
    with st.chat_message("assistant"):
        st.markdown(final_reply)
    st.session_state.messages.append({"role": "assistant", "content": final_reply})