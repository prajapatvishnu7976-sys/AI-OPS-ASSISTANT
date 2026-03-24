import streamlit as st
import asyncio
import json
import time
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from agents.verifier import VerifierAgent
from core.state_machine import ResearchSwarmOrchestrator
from core.memory import memory

# Page config
st.set_page_config(
    page_title="AI Operations Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔥 ROYAL BLUE & BLACK PREMIUM CSS
st.markdown("""
<style>
    /* ============ GLOBAL STYLES ============ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0a0f 100%) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ============ MAIN HEADER ============ */
    .main-header {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 40px rgba(59, 130, 246, 0.5);
        letter-spacing: -1px;
    }
    
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    .sub-header span {
        color: #3b82f6;
        font-weight: 600;
    }
    
    /* ============ GLASS CARDS ============ */
    .glass-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.15) 0%, rgba(15, 23, 42, 0.9) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(59, 130, 246, 0.5);
        box-shadow: 
            0 12px 40px rgba(59, 130, 246, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transform: translateY(-2px);
    }
    
    /* ============ AGENT CARDS ============ */
    .agent-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.8) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 0.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }
    
    .agent-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #1e3a8a, #3b82f6, #60a5fa);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .agent-card:hover {
        transform: translateY(-8px) scale(1.02);
        border-color: #3b82f6;
        box-shadow: 
            0 20px 40px rgba(59, 130, 246, 0.3),
            0 0 60px rgba(59, 130, 246, 0.1);
    }
    
    .agent-card:hover::before {
        opacity: 1;
    }
    
    .agent-icon {
        font-size: 3rem;
        margin-bottom: 0.75rem;
        display: block;
    }
    
    .agent-name {
        color: #60a5fa;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .agent-desc {
        color: #94a3b8;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    
    .agent-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 1rem;
        padding: 4px 12px;
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 20px;
        font-size: 0.75rem;
        color: #22c55e;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-dot {
        width: 6px;
        height: 6px;
        background: #22c55e;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
    
    /* ============ STEP BOX ============ */
    .step-box {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.2) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-left: 4px solid #3b82f6;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        color: #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .step-box:hover {
        border-color: rgba(59, 130, 246, 0.5);
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.3) 0%, rgba(15, 23, 42, 0.95) 100%);
    }
    
    .step-box b {
        color: #60a5fa;
    }
    
    /* ============ METRIC CARDS ============ */
    .metric-card {
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 58, 138, 0.2) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: scale(1.05);
        border-color: #3b82f6;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        color: #64748b;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* ============ WEATHER CARD ============ */
    .weather-card {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.3) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }
    
    .weather-card::before {
        content: '☀️';
        position: absolute;
        right: 20px;
        top: 20px;
        font-size: 4rem;
        opacity: 0.3;
    }
    
    .weather-city {
        font-size: 2rem;
        font-weight: 700;
        color: #60a5fa;
        margin-bottom: 0.5rem;
    }
    
    .weather-temp {
        font-size: 3.5rem;
        font-weight: 800;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }
    
    .weather-desc {
        color: #94a3b8;
        font-size: 1.1rem;
        text-transform: capitalize;
    }
    
    /* ============ REPO CARD ============ */
    .repo-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.8) 100%);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .repo-card:hover {
        border-color: #3b82f6;
        transform: translateX(10px);
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.15);
    }
    
    .repo-name {
        font-size: 1.25rem;
        font-weight: 700;
        color: #60a5fa;
        margin-bottom: 0.5rem;
    }
    
    .repo-stats {
        display: flex;
        gap: 1.5rem;
        margin: 0.75rem 0;
    }
    
    .repo-stat {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    .repo-desc {
        color: #cbd5e1;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-top: 0.75rem;
    }
    
    .repo-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-top: 1rem;
        padding: 8px 16px;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        border-radius: 8px;
        color: white !important;
        text-decoration: none !important;
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .repo-link:hover {
        transform: translateX(5px);
        box-shadow: 0 5px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* ============ INPUT STYLING ============ */
    .stTextInput > div > div > input {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 2px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        padding: 1rem 1.25rem !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }
    
    /* ============ BUTTON STYLING ============ */
    .stButton > button {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* ============ SIDEBAR STYLING ============ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0f 0%, #0d1117 100%) !important;
        border-right: 1px solid rgba(59, 130, 246, 0.2) !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(30, 58, 138, 0.3) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        width: 100% !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(59, 130, 246, 0.2) !important;
        border-color: #3b82f6 !important;
    }
    
    /* ============ PROGRESS BAR ============ */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%) !important;
        border-radius: 10px !important;
    }
    
    /* ============ EXPANDER STYLING ============ */
    .streamlit-expanderHeader {
        background: rgba(30, 58, 138, 0.2) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
        color: #60a5fa !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* ============ DIVIDER ============ */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.3), transparent) !important;
        margin: 2rem 0 !important;
    }
    
    /* ============ SUCCESS/ERROR/INFO BOXES ============ */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        color: #22c55e !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        color: #ef4444 !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        color: #60a5fa !important;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        color: #f59e0b !important;
    }
    
    /* ============ FOOTER ============ */
    .footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(59, 130, 246, 0.2);
        color: #64748b;
    }
    
    .footer a {
        color: #3b82f6;
        text-decoration: none;
    }
    
    .footer-brand {
        font-size: 1.1rem;
        font-weight: 600;
        color: #60a5fa;
        margin-bottom: 0.5rem;
    }
    
    /* ============ ANIMATIONS ============ */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-fade-in {
        animation: fadeInUp 0.6s ease forwards;
    }
    
    @keyframes glow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        }
        50% {
            box-shadow: 0 0 40px rgba(59, 130, 246, 0.6);
        }
    }
    
    .glow {
        animation: glow 2s ease-in-out infinite;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "current_query" not in st.session_state:
    st.session_state.current_query = ""

# ============ HEADER ============
st.markdown('<h1 class="main-header">🤖 AI Operations Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Multi-Agent Research Swarm powered by <span>LangGraph</span> & <span>Gemini</span></p>', unsafe_allow_html=True)

# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    model_choice = st.selectbox(
        "🤖 LLM Model",
        ["Gemini 1.5 Flash (FREE)", "GPT-3.5-turbo"],
        index=0
    )
    
    max_iterations = st.slider("🔄 Max Iterations", 1, 5, 2)
    
    st.markdown("---")
    
    st.markdown("### 📚 Example Queries")
    example_queries = [
        "Weather in Tokyo and top 3 Python repos",
        "Seattle weather",
        "Top 5 Rust repos on GitHub",
        "Weather in Paris and 2 JavaScript repos",
        "Mumbai temperature"
    ]
    
    for i, example in enumerate(example_queries):
        if st.button(f"💡 {example}", key=f"example_{i}", use_container_width=True):
            st.session_state.current_query = example
            st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 📊 System Status")
    st.markdown("""
    <div class="glass-card" style="padding: 1rem;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <span class="status-dot"></span>
            <span style="color: #22c55e; font-weight: 600;">All Systems Online</span>
        </div>
        <div style="color: #64748b; font-size: 0.85rem;">
            4 Agents Active • 0 Errors
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============ AGENT CARDS ============
st.markdown("### 🧠 Active Agents")
agent_cols = st.columns(4)

agents = [
    {"icon": "🧠", "name": "Planner", "desc": "Converts queries to structured execution plans"},
    {"icon": "⚙️", "name": "Executor", "desc": "Runs API calls in parallel with retry logic"},
    {"icon": "🎭", "name": "Critic", "desc": "Validates data quality and completeness"},
    {"icon": "✅", "name": "Verifier", "desc": "Formats and structures final output"}
]

for i, agent in enumerate(agents):
    with agent_cols[i]:
        st.markdown(f"""
        <div class="agent-card">
            <span class="agent-icon">{agent['icon']}</span>
            <div class="agent-name">{agent['name']}</div>
            <div class="agent-desc">{agent['desc']}</div>
            <div class="agent-status">
                <span class="status-dot"></span>
                Ready
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ============ QUERY INPUT ============
st.markdown("### 🔍 Enter Your Query")

col1, col2 = st.columns([5, 1])

with col1:
    query = st.text_input(
        "Query",
        placeholder="e.g., Weather in Tokyo and top 5 Python repos...",
        value=st.session_state.current_query,
        key="query_input",
        label_visibility="collapsed"
    )
    
    if query != st.session_state.current_query:
        st.session_state.current_query = query

with col2:
    run_button = st.button("🚀 Execute", type="primary", use_container_width=True)

# Clear button
col_clear, col_space = st.columns([1, 5])
with col_clear:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.current_query = ""
        st.rerun()

# ============ EXECUTION ============
if run_button and query:
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    start_time = time.time()
    
    async def run_query():
        try:
            status_container.info("🔧 Initializing agents...")
            progress_bar.progress(10)
            
            planner = PlannerAgent()
            critic = CriticAgent()
            verifier = VerifierAgent()
            
            progress_bar.progress(25)
            
            async with ExecutorAgent() as executor:
                status_container.info("🎯 Creating orchestrator...")
                orch = ResearchSwarmOrchestrator(planner, executor, critic, verifier, memory)
                
                progress_bar.progress(40)
                status_container.info("🚀 Executing query...")
                
                result = await orch.run(query, max_iterations=max_iterations)
                
                progress_bar.progress(100)
                status_container.success("✅ Query completed successfully!")
                
                return result
        
        except Exception as e:
            status_container.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    result = asyncio.run(run_query())
    
    if result:
        execution_time = time.time() - start_time
        
        st.markdown("---")
        
        # ============ METRICS ============
        st.markdown("### 📊 Execution Metrics")
        
        metric_cols = st.columns(4)
        
        output = result.get("final_output", {})
        meta = output.get("metadata", {})
        
        metrics = [
            {"icon": "⏱️", "value": f"{execution_time:.2f}s", "label": "Execution Time"},
            {"icon": "📊", "value": f"{meta.get('steps_completed', 0)}/{meta.get('total_steps', 0)}", "label": "Steps"},
            {"icon": "💰", "value": "$0.0000", "label": "Total Cost"},
            {"icon": "🔧", "value": str(len(meta.get('tools_used', []))), "label": "Tools Used"}
        ]
        
        for i, metric in enumerate(metrics):
            with metric_cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <span class="metric-icon">{metric['icon']}</span>
                    <div class="metric-value">{metric['value']}</div>
                    <div class="metric-label">{metric['label']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ============ RESULTS ============
        result_col1, result_col2 = st.columns(2)
        
        # WEATHER RESULTS
        with result_col1:
            if "weather" in output:
                weather = output["weather"]
                st.markdown("### 🌤️ Weather Data")
                st.markdown(f"""
                <div class="weather-card">
                    <div class="weather-city">📍 {weather.get('city', 'Unknown')}, {weather.get('country', '')}</div>
                    <div class="weather-temp">{weather.get('temperature', 'N/A')}</div>
                    <div class="weather-desc">{weather.get('description', 'N/A')}</div>
                    <div class="repo-stats" style="margin-top: 1.5rem;">
                        <div class="repo-stat">💨 {weather.get('wind_speed', 'N/A')}</div>
                        <div class="repo-stat">💧 {weather.get('humidity', 'N/A')}</div>
                        <div class="repo-stat">☁️ {weather.get('clouds', 'N/A')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # GITHUB RESULTS
        with result_col2:
            if "repositories" in output:
                repos = output["repositories"]
                st.markdown("### 🐙 GitHub Repositories")
                
                for i, repo in enumerate(repos[:5], 1):
                    st.markdown(f"""
                    <div class="repo-card">
                        <div class="repo-name">{i}. {repo.get('name', 'Unknown')}</div>
                        <div class="repo-stats">
                            <div class="repo-stat">⭐ {repo.get('stars', 0):,}</div>
                            <div class="repo-stat">🍴 {repo.get('forks', 0):,}</div>
                            <div class="repo-stat">💻 {repo.get('language', 'N/A')}</div>
                        </div>
                        <div class="repo-desc">{repo.get('description', 'No description')[:100]}...</div>
                        <a href="{repo.get('url', '#')}" target="_blank" class="repo-link">
                            🔗 View on GitHub
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # EXECUTION LOGS
        col_plan, col_logs = st.columns(2)
        
        with col_plan:
            st.markdown("### 📋 Execution Plan")
            plan = result.get("plan", [])
            for step in plan:
                status_icon = "✅" if step.get("status") == "completed" else "⏳"
                st.markdown(f"""
                <div class="step-box">
                    {status_icon} <b>Step {step.get('id', 0)}</b><br>
                    🔧 Tool: {step.get('tool', 'unknown')}<br>
                    ⚡ Action: {step.get('action', '')}<br>
                    ⏱️ Time: {step.get('execution_time_ms', 0)}ms
                </div>
                """, unsafe_allow_html=True)
        
        with col_logs:
            st.markdown("### 📝 Execution Logs")
            logs = result.get("logs", [])
            for log in logs[-6:]:
                content = log.get("content", str(log)) if isinstance(log, dict) else str(log)
                if "✅" in content:
                    st.success(content)
                elif "❌" in content:
                    st.error(content)
                elif "⚠️" in content:
                    st.warning(content)
                else:
                    st.info(content)
        
        # RAW JSON
        with st.expander("📄 View Raw JSON Response"):
            st.json(output)

else:
    # ============ WELCOME SCREEN ============
    st.markdown("---")
    st.info("👆 Enter a query above and click **Execute** to get started!")
    
    st.markdown("### 🎯 What can you ask?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #60a5fa;">🌤️ Weather Queries</h4>
            <ul style="color: #94a3b8;">
                <li>Seattle weather</li>
                <li>Temperature in Tokyo</li>
                <li>Weather in Mumbai</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #60a5fa;">🐙 GitHub Queries</h4>
            <ul style="color: #94a3b8;">
                <li>Top 5 Python repos</li>
                <li>Trending Rust projects</li>
                <li>10 JavaScript repos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="glass-card">
            <h4 style="color: #60a5fa;">🔀 Multi-Tool Queries</h4>
            <ul style="color: #94a3b8;">
                <li>Weather in Paris and 3 Go repos</li>
                <li>Tokyo temp and Python repos</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ============ FOOTER ============
st.markdown("""
<div class="footer">
    <div class="footer-brand">🤖 AI Operations Assistant</div>
    <div>Built with LangGraph • Gemini 1.5 Flash • FastAPI • Streamlit</div>
    <div style="margin-top: 0.5rem;">Multi-Agent Research Swarm | Parallel Execution | Zero Cost</div>
</div>
""", unsafe_allow_html=True)