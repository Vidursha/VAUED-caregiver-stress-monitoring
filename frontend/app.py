import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

# ==========================================
# 1. UX DESIGN & PAGE CONFIGURATION
# ==========================================
# Fulfills UX requirement: Consistent layout, clear visual hierarchy
st.set_page_config(
    page_title="Care-Sync AI | Stress Monitor", 
    page_icon="🩺", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. DATA LOADING (ETL)
# ==========================================
@st.cache_data
def load_data():
    """
    Attempts to fetch data from the Flask API.
    Falls back to local CSV if the server is offline.
    """
    try:
        # Try fetching from your Flask Backend
        response = requests.get("http://127.0.0.1:5000/api/caregivers", timeout=2)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
        else:
            raise Exception("API returned non-200 status")
    except:
        # Fallback: Load directly from CSV for the prototype
        current_dir = os.path.dirname(__file__)
        csv_path = os.path.join(current_dir, '..', 'data', 'caregiver_stress_prediction_sensor_data.csv')
        df = pd.read_csv(csv_path)
    
    # Clean data types
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Map numerical labels to readable categories (0: Low, 1: Medium, 2: High)
    if 'label' in df.columns:
        df['Stress_Category'] = df['label'].map({0: 'Low', 1: 'Medium', 2: 'High'})
        
    return df

df = load_data()

# ==========================================
# 3. NAVIGATION & PERSONA (UX Flow)
# ==========================================
st.sidebar.title("🩺 Care-Sync AI")
st.sidebar.markdown("**Role:** Hospital Administrator / Head Nurse")
st.sidebar.info(
    "**Analytical Goal:**\n"
    "Identify high-risk caregivers, monitor real-time physiological metrics, "
    "and allocate resources to prevent staff burnout."
)

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "📍 Navigation",
    ["📊 Executive Overview", "📈 Deep-Dive Analytics", "🤖 AI Chatbot Assistant"]
)

# Color theory map for consistency across all charts
color_map = {'Low': '#2ca02c', 'Medium': '#ff7f0e', 'High': '#d62728'}

# ==========================================
# 4. EXECUTIVE OVERVIEW (Visual Analytics)
# ==========================================
if menu == "📊 Executive Overview":
    st.title("Caregiver Stress Monitoring Dashboard")
    st.markdown("A high-level view of hospital staff physiological well-being.")
    
    if not df.empty:
        # --- Data-Ink Ratio Optimized KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Heart Rate (HR)", f"{df['HR'].mean():.1f} bpm")
        col2.metric("Avg Electrodermal Activity", f"{df['EDA'].mean():.2f} μS")
        col3.metric("Avg Body Temp", f"{df['TEMP'].mean():.1f} °C")
        
        high_stress_pct = (len(df[df['Stress_Category'] == 'High']) / len(df)) * 100
        col4.metric("Critical Burnout Risk", f"{high_stress_pct:.1f}%", delta="Requires Action", delta_color="inverse")
        
        st.markdown("---")
        
        # --- Interactive Feature: Filtering ---
        st.subheader("Physiological Time-Series Analysis")
        selected_id = st.selectbox("Filter by Caregiver ID:", df['id'].unique())
        filtered_df = df[df['id'] == selected_id]
        
        # Coordinated Visualizations
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            fig_hr = px.line(filtered_df, x='datetime', y='HR', title=f"Heart Rate Trends (ID: {selected_id})",
                             color_discrete_sequence=['#ff4b4b'])
            st.plotly_chart(fig_hr, use_container_width=True)
            
        with chart_col2:
            fig_eda = px.line(filtered_df, x='datetime', y='EDA', title=f"EDA Stress Signal (ID: {selected_id})",
                              color_discrete_sequence=['#1f77b4'])
            st.plotly_chart(fig_eda, use_container_width=True)

# ==========================================
# 5. DEEP-DIVE ANALYTICS (Brushing & Linking)
# ==========================================
elif menu == "📈 Deep-Dive Analytics":
    st.title("Exploratory Visual Analytics")
    st.markdown("Identify correlations between movement, vital signs, and predicted stress levels.")
    
    if not df.empty:
        # --- Interactive Feature: Brushing and Linking ---
        st.subheader("Heart Rate vs. EDA Correlation")
        st.markdown("*Gestalt Principle applied: Similarity (grouping by color to pre-attentively identify stress levels).*")
        
        # Plotly natively supports brushing (box select tool on the chart menu)
        fig_scatter = px.scatter(
            df, x='HR', y='EDA', color='Stress_Category', 
            color_discrete_map=color_map,
            hover_data=['id', 'MovementMagnitude', 'TEMP'],
            title="Interactive Scatter: Drag to Brush/Select Datapoints",
            opacity=0.7
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.markdown("---")
        
        # --- Drill-down / Comparative Views ---
        col_box1, col_box2 = st.columns(2)
        with col_box1:
            fig_box_move = px.box(df, x='Stress_Category', y='MovementMagnitude', color='Stress_Category',
                                  color_discrete_map=color_map, title="Movement Magnitude by Stress Level")
            st.plotly_chart(fig_box_move, use_container_width=True)
            
        with col_box2:
            fig_box_temp = px.box(df, x='Stress_Category', y='TEMP', color='Stress_Category',
                                  color_discrete_map=color_map, title="Body Temperature by Stress Level")
            st.plotly_chart(fig_box_temp, use_container_width=True)

# ==========================================
# 6. CONVERSATIONAL AGENT (LLM Integration)
# ==========================================
elif menu == "🤖 AI Chatbot Assistant":
    st.title("Care-Sync Conversational Agent")
    st.markdown("Ask natural language questions to interpret the visual analytics and dataset.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello Administrator. I am analyzing the latest wearable sensor data. What insights are you looking for today?"}
        ]

    # Render previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input Box
    if prompt := st.chat_input("Ask: What factors influence stress levels the most?"):
        
        # 1. Display User Message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 2. Generate LLM Response (Mock logic for prototype)
        # Note: Replace this block with your actual LLM API call (e.g., OpenAI or LangChain)
        if "factors influence" in prompt.lower() or "influence stress" in prompt.lower():
            response = "Based on our multi-dimensional analysis, **Electrodermal Activity (EDA)** and **Heart Rate (HR)** are the primary physiological indicators. A sudden spike in EDA (>4.0) coupled with elevated HR (>85 bpm) while movement is low strongly correlates with the 'High' stress classification."
        elif "explain" in prompt.lower() or "trend" in prompt.lower():
            response = "Looking at the Time-Series data, Caregiver 15 shows consistent stress spikes during the final 2 hours of their shift. This trend suggests fatigue accumulation."
        else:
            response = "I can help analyze the sensor data. Try asking me about factors influencing stress, or ask me to explain a specific trend in the dashboard visuals."

        # 3. Display Assistant Message
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})