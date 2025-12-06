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

# Modern Dark Theme CSS
st.markdown("""
<style>
    /* Dark theme base */
    .stApp {
        background: #0a0e27;
    }
    
    .main .block-container {
        background: #0a0e27;
        padding: 2rem 1rem;
        max-width: 1200px;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Hero Section */
    .hero-container {
        text-align: center;
        padding: 4rem 2rem;
        margin-bottom: 4rem;
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: #ffffff;
        font-weight: 300;
        margin-bottom: 0.5rem;
    }
    
    .hero-description {
        font-size: 1.1rem;
        color: #e2e8f0;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        margin: 3rem 0;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #1a1f3a 0%, #16213e 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
    }
    
    .feature-card:hover::before {
        transform: scaleX(1);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.75rem;
    }
    
    .feature-description {
        font-size: 0.95rem;
        color: #ffffff;
        line-height: 1.6;
        margin: 0;
    }
    
    /* Quick Actions */
    .action-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
        margin: 3rem 0;
    }
    
    .action-btn {
        padding: 0.875rem 2rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
    }
    
    
    .action-btn-secondary {
        background: rgba(102, 126, 234, 0.1);
        color: #667eea;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .action-btn-secondary:hover {
        background: rgba(102, 126, 234, 0.2);
        transform: translateY(-2px);
    }
    
    /* Stats Section */
    .stats-section {
        background: linear-gradient(135deg, #1a1f3a 0%, #16213e 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 20px;
        padding: 3rem 2rem;
        margin: 3rem 0;
        text-align: center;
    }
    
    .stats-title {
        font-size: 2rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 2rem;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 2rem;
    }
    
    .stat-item {
        padding: 1.5rem;
    }
    
    .stat-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #ffffff;
        margin-top: 0.5rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 3rem 2rem;
        color: #e2e8f0;
        font-size: 0.9rem;
    }
    
    /* Text colors for Streamlit */
    h1, h2, h3, h4, h5, h6 {
        color: #e2e8f0 !important;
    }
    
    p, div, span {
        color: #e2e8f0 !important;
    }
    
    /* Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        margin: 3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🧠 EchoMind</div>
    <div class="hero-subtitle">Mental Health Monitoring and Support System</div>
    <div class="hero-description">
        Intelligent support, emotion analysis, and compassionate guidance—all in one place. 
        Track your mental health journey with cutting-edge AI technology.
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Action Buttons
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("💬 Chat", width='stretch', use_container_width=True):
        st.switch_page("pages/1_Chat.py")

with col2:
    if st.button("🎤 Voice", width='stretch', use_container_width=True):
        st.switch_page("pages/3_Voice.py")

with col3:
    if st.button("😊 Face", width='stretch', use_container_width=True):
        st.switch_page("pages/2_Face.py")

with col4:
    if st.button("📊 History", width='stretch', use_container_width=True):
        st.switch_page("pages/4_History.py")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Features Section
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h2 style="font-size: 2.5rem; font-weight: 600; color: #ffffff !important; margin-bottom: 0.5rem;">Features</h2>
    <p style="color: #e2e8f0 !important; font-size: 1.1rem;">Comprehensive tools for your mental well-being</p>
</div>
""", unsafe_allow_html=True)

# Feature Cards
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <span class="feature-icon">💬</span>
        <div class="feature-title">AI Chat Support</div>
        <div class="feature-description">
            Engage in meaningful conversations with our AI-powered mental health specialist. 
            Get empathetic, evidence-based responses powered by advanced language models.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <span class="feature-icon">😊</span>
        <div class="feature-title">Facial Emotion Analysis</div>
        <div class="feature-description">
            Capture photos or videos to analyze facial expressions and emotions. 
            Get insights into your emotional state with AI-powered facial recognition.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <span class="feature-icon">📊</span>
        <div class="feature-title">Analytics & Reports</div>
        <div class="feature-description">
            Comprehensive analytics dashboard with sentiment trends, emotion tracking, 
            weekly/monthly reports, and visual insights into your mental health journey.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <span class="feature-icon">🎤</span>
        <div class="feature-title">Voice Emotion Recognition</div>
        <div class="feature-description">
            Record your voice and analyze emotional tone through advanced speech emotion recognition. 
            Get instant feedback on your vocal emotional patterns.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <span class="feature-icon">📜</span>
        <div class="feature-title">History & Tracking</div>
        <div class="feature-description">
            View your complete conversation history with advanced filtering, sorting, 
            and search capabilities. Track your progress over time.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <span class="feature-icon">🚨</span>
        <div class="feature-title">Emergency Support</div>
        <div class="feature-description">
            Automatic crisis detection with emergency calling support and therapist finder. 
            Get immediate help when you need it most.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# Stats/Info Section
st.markdown("""
<div class="stats-section">
    <div class="stats-title">Why Choose EchoMind?</div>
    <div class="stats-grid">
        <div class="stat-item">
            <div class="stat-icon">🔒</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #e2e8f0;">Privacy First</div>
            <div class="stat-label">Your data is encrypted and secure</div>
        </div>
        <div class="stat-item">
            <div class="stat-icon">⚡</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #e2e8f0;">24/7 Available</div>
            <div class="stat-label">Support whenever you need it</div>
        </div>
        <div class="stat-item">
            <div class="stat-icon">🤖</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #e2e8f0;">AI-Powered</div>
            <div class="stat-label">Advanced ML models for accurate analysis</div>
        </div>
        <div class="stat-item">
            <div class="stat-icon">📈</div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #e2e8f0;">Track Progress</div>
            <div class="stat-label">Monitor your mental health journey</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p style="color: #ffffff !important; font-size: 1rem; margin-bottom: 0.5rem;">💙 Built with care for your mental well-being</p>
    <p style="color: #e2e8f0 !important; font-size: 0.85rem;">EchoMind - Mental Health Monitoring and Support System</p>
</div>
""", unsafe_allow_html=True)
