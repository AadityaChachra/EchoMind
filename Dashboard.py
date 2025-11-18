# Main Landing Page for EchoMind
import streamlit as st

# Configure page
st.set_page_config(
    page_title="EchoMind",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "EchoMind - Mental Health Monitoring and Support System"
    }
)

# Custom CSS for beautiful landing page and sidebar customization
st.markdown("""
<style>
    /* Set light background for main content area */
    .main .block-container {
        background-color: #ffffff;
        padding: 2rem;
    }
    
    /* Ensure all text is readable */
    .main h1, .main h2, .main h3, .main p, .main div {
        color: #1f1f1f !important;
    }
    
    /* Landing page styles */
    .main-header {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff !important;
        border-radius: 20px;
        margin-bottom: 3rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    
    .main-header p {
        font-size: 1.3rem;
        color: #ffffff !important;
        opacity: 0.95;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        border: 1px solid #e0e0e0;
    }
    
    .feature-card h3 {
        color: #667eea !important;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-card p {
        color: #333333 !important;
        line-height: 1.6;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .cta-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2.5rem;
        border-radius: 50px;
        font-size: 1.2rem;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        text-decoration: none;
        display: inline-block;
    }
    
    .cta-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    .stats-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
    }
    
    .stats-container h3 {
        color: #667eea !important;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .stats-container p {
        color: #333333 !important;
        line-height: 1.6;
    }
    
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
    }
    
    .hero-section h2 {
        color: #667eea !important;
        font-weight: 600;
    }
    
    .hero-section p {
        color: #333333 !important;
        line-height: 1.8;
    }
    
    /* Sidebar background */
    [data-testid="stSidebar"] {
        background: #1e1e2f !important;
    }

    /* Sidebar content area */
    [data-testid="stSidebar"] .css-1d391kg {
        background-color: #1e1e2f !important;
    }

    /* Sidebar customization */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="main-header">
    <h1>🧠 EchoMind</h1>
    <p>Mental Health Monitoring and Support System</p>
    <p style="font-size: 1rem; margin-top: 1rem;">Empathetic support, available 24/7</p>
</div>
""", unsafe_allow_html=True)

# Main Content
st.markdown("""
<div class="hero-section">
    <h2 style="color: #667eea !important; margin-bottom: 1rem; font-weight: 600;">Welcome to EchoMind</h2>
    <p style="font-size: 1.2rem; color: #333333 !important; max-width: 800px; margin: 0 auto 3rem; line-height: 1.8;">
        EchoMind is an intelligent mental health support system that provides compassionate, 
        evidence-based guidance whenever you need it. Our AI-powered chatbot is here to listen, 
        understand, and support you on your mental health journey.
    </p>
</div>
""", unsafe_allow_html=True)

# Features Section
st.markdown("### ✨ Key Features", help="Explore the powerful features of EchoMind")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">💬</div>
        <h3 style="color: #667eea !important; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem;">AI Chat Support</h3>
        <p style="color: #333333 !important; line-height: 1.6;">Engage in meaningful conversations with our AI-powered mental health specialist. 
        Get empathetic, evidence-based responses to your concerns.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔧</div>
        <h3 style="color: #667eea !important; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem;">Smart Tools</h3>
        <p style="color: #333333 !important; line-height: 1.6;">Access emergency calling support, find nearby therapists, and get personalized mental 
        health resources tailored to your needs.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3 style="color: #667eea !important; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem;">Progress Tracking</h3>
        <p style="color: #333333 !important; line-height: 1.6;">View your conversation history, track your mental health journey, and analyze 
        patterns over time with our comprehensive history feature.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Call to Action Section
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2 style="color: #667eea !important; margin-bottom: 1.5rem; font-weight: 600;">Ready to Get Started?</h2>
        <p style="font-size: 1.1rem; color: #333333 !important; margin-bottom: 2rem; line-height: 1.8;">
            Click on <strong style="color: #667eea;">Chat</strong> in the sidebar to begin your conversation, 
            or explore your <strong style="color: #667eea;">History</strong> to review past interactions.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Navigation Buttons
col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

with col3:
    col_left, col_right = st.columns(2)
    with col_left:
        if st.button("💬 Start Chatting", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Chat.py")
    with col_right:
        if st.button("📜 View History", use_container_width=True):
            st.switch_page("pages/2_History.py")

# Additional Information
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="stats-container">
        <h3 style="color: #667eea !important; font-weight: 600; margin-bottom: 1rem;">🔒 Privacy & Security</h3>
        <p style="color: #333333 !important; line-height: 1.6;">Your conversations are stored securely and privately. 
        All data is encrypted and accessible only to you.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stats-container">
        <h3 style="color: #667eea !important; font-weight: 600; margin-bottom: 1rem;">⚡ Always Available</h3>
        <p style="color: #333333 !important; line-height: 1.6;">EchoMind is available 24/7, providing support whenever you need it.</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666666 !important;">
    <p style="color: #666666 !important; font-size: 1rem;">💙 Built with care for your mental well-being</p>
    <p style="font-size: 0.9rem; color: #666666 !important;">EchoMind - Mental Health Monitoring and Support System</p>
</div>
""", unsafe_allow_html=True)
