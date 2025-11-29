import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from datetime import datetime
import json

# Configure the page
st.set_page_config(
    page_title="Multi-Region Recommendation System | Enterprise Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #2c3e50;
        --success-color: #27ae60;
        --warning-color: #f39c12;
        --danger-color: #e74c3c;
        --background-color: #f8f9fa;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary-color);
    }
    
    .region-card {
        background: #1e1e1e;
        color: #e0e0e0;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
        transition: transform 0.2s;
        min-height: 320px;
        display: flex;
        flex-direction: column;
        border: 1px solid #333;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .region-card h3 {
        font-size: 1.1rem;
        line-height: 1.3;
    }
    
    .region-card p {
        font-size: 0.9rem;
        line-height: 1.4;
        margin: 0.4rem 0;
    }
    
    .region-card a {
        font-size: 0.85rem;
    }
    
    .region-card strong {
        color: #ffffff;
    }
    
    .region-card hr {
        border-color: #444;
        margin: 0.8rem 0;
    }
    
    .region-card a {
        color: #64b5f6 !important;
        text-decoration: none;
    }
    
    .region-card a:hover {
        color: #90caf9 !important;
        text-decoration: underline;
    }
    
    .region-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        border-color: #555;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .status-online {
        background-color: #2e7d32;
        color: #e8f5e9;
    }
    
    .status-offline {
        background-color: #c62828;
        color: #ffebee;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #e0e0e0;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #444;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Info box */
    .info-box {
        background-color: #1e3a5f;
        border-left: 4px solid #64b5f6;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
        color: #e0e0e0;
    }
    
    .info-box strong {
        color: #ffffff;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Region configuration
REGIONS = {
    "8000": {"name": "US-West", "code": "USW", "color": "#3498db", "location": "California, USA"},
    "8001": {"name": "US-East", "code": "USE", "color": "#2ecc71", "location": "Virginia, USA"},
    "8002": {"name": "EU-West", "code": "EUW", "color": "#9b59b6", "location": "Ireland, EU"},
    "8003": {"name": "AP-South", "code": "APS", "color": "#e67e22", "location": "Mumbai, India"}
}

def check_region_health(port, timeout=3):
    """Check if a region is healthy"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "region": data.get("region", "unknown"),
                "message": data.get("message", ""),
                "latency": response.elapsed.total_seconds() * 1000
            }
    except requests.exceptions.RequestException:
        pass
    
    return {"status": "offline", "region": "unknown", "message": "Not responding", "latency": 0}

def get_recommendations(port, user_id, count=5):
    """Get recommendations from a specific region"""
    try:
        response = requests.post(
            f"http://localhost:{port}/api/v1/recommendations/user/{user_id}",
            json={"count": count},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None

def get_stats(port):
    """Get statistics from a specific region"""
    try:
        response = requests.get(f"http://localhost:{port}/api/v1/recommendations/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return None

def main():
    # Professional Header
    st.markdown("""
        <div class="main-header">
            <h1>Multi-Region E-Commerce Recommendation System</h1>
            <p>Enterprise Dashboard for Monitoring and Testing Distributed Recommendation Infrastructure</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("### Control Panel")
    st.sidebar.markdown("---")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("Refresh Now", use_container_width=True):
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### System Information")
    st.sidebar.info(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.sidebar.markdown("---")
    
    # Region Health Status
    st.markdown('<div class="section-header">Regional Infrastructure Status</div>', unsafe_allow_html=True)
    
    # Check all regions
    health_data = []
    cols = st.columns(4)
    
    for i, (port, info) in enumerate(REGIONS.items()):
        with cols[i]:
            with st.spinner(f"Checking {info['name']}..."):
                health = check_region_health(port)
                
            if health["status"] == "healthy":
                st.markdown(f"""
                    <div class="region-card">
                        <h3 style="color: {info['color']}; margin-top: 0;">{info['code']} | {info['name']}</h3>
                        <span class="status-badge status-online">ONLINE</span>
                        <hr style="margin: 1rem 0;">
                        <p><strong>Location:</strong> {info['location']}</p>
                        <p><strong>Latency:</strong> {health['latency']:.1f}ms</p>
                        <p><strong>Port:</strong> {port}</p>
                        <div style="margin-top: 1rem;">
                            <a href="http://localhost:{port}" target="_blank" style="margin-right: 1rem;">API Endpoint</a>
                            <a href="http://localhost:{port}/docs" target="_blank">Documentation</a>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="region-card" style="opacity: 0.6;">
                        <h3 style="color: {info['color']}; margin-top: 0;">{info['code']} | {info['name']}</h3>
                        <span class="status-badge status-offline">OFFLINE</span>
                        <hr style="margin: 1rem 0;">
                        <p><strong>Location:</strong> {info['location']}</p>
                        <p><strong>Status:</strong> Not Responding</p>
                        <p><strong>Port:</strong> {port}</p>
                    </div>
                """, unsafe_allow_html=True)
                
            health_data.append({
                "port": port,
                "region": info["name"],
                "status": health["status"],
                "latency": health["latency"],
                "location": info["location"]
            })
    
    # Health Summary Chart
    st.markdown('<div class="section-header">Performance Analytics</div>', unsafe_allow_html=True)
    
    healthy_regions = [h for h in health_data if h["status"] == "healthy"]
    
    if healthy_regions:
        df_health = pd.DataFrame(healthy_regions)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Latency chart
            fig_latency = px.bar(
                df_health,
                x="region",
                y="latency",
                color="region",
                title="Response Latency by Region",
                labels={"latency": "Latency (ms)", "region": "Region"},
                color_discrete_sequence=['#3498db', '#2ecc71', '#9b59b6', '#e67e22']
            )
            fig_latency.update_layout(
                showlegend=False,
                plot_bgcolor='#1e1e1e',
                paper_bgcolor='#262626',
                font=dict(size=12, color='#e0e0e0'),
                title_font=dict(size=16, color='#e0e0e0'),
                xaxis=dict(gridcolor='#444', color='#e0e0e0'),
                yaxis=dict(gridcolor='#444', color='#e0e0e0')
            )
            st.plotly_chart(fig_latency, use_container_width=True)
        
        with col2:
            # Status pie chart
            status_counts = pd.DataFrame(health_data)["status"].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Region Availability Status",
                color_discrete_map={"healthy": "#27ae60", "offline": "#e74c3c"}
            )
            fig_status.update_layout(
                plot_bgcolor='#1e1e1e',
                paper_bgcolor='#262626',
                font=dict(size=12, color='#e0e0e0'),
                title_font=dict(size=16, color='#e0e0e0')
            )
            st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.error("No regions are currently online. Please start the regional services.")
    
    st.markdown("---")
    
    # Recommendation Testing
    st.markdown('<div class="section-header">Recommendation Testing Interface</div>', unsafe_allow_html=True)
    
    if healthy_regions:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### Configuration Parameters")
            
            # User ID input
            user_id = st.text_input(
                "User ID",
                value="user123",
                help="Enter a user ID to get personalized recommendations"
            )
            
            # Number of recommendations
            rec_count = st.slider(
                "Recommendation Count",
                min_value=1,
                max_value=10,
                value=5,
                help="Number of recommendations to retrieve per region"
            )
            
            # Region selection
            available_ports = [h["port"] for h in healthy_regions]
            selected_regions = st.multiselect(
                "Target Regions",
                options=available_ports,
                default=available_ports,
                format_func=lambda x: f"{REGIONS[x]['code']} - {REGIONS[x]['name']}"
            )
            
            # Test button
            if st.button("Execute Recommendation Query", type="primary", use_container_width=True):
                if user_id and selected_regions:
                    st.session_state.test_results = {}
                    
                    for port in selected_regions:
                        with st.spinner(f"Querying {REGIONS[port]['name']} region..."):
                            result = get_recommendations(port, user_id, rec_count)
                            st.session_state.test_results[port] = result
                else:
                    st.error("Please provide a User ID and select at least one region")
        
        with col2:
            st.markdown("#### Query Results")
            
            if hasattr(st.session_state, 'test_results') and st.session_state.test_results:
                tabs = st.tabs([f"{REGIONS[port]['code']} | {REGIONS[port]['name']}" 
                               for port in st.session_state.test_results.keys()])
                
                for tab, (port, result) in zip(tabs, st.session_state.test_results.items()):
                    with tab:
                        if result:
                            st.success(f"Successfully retrieved recommendations from {REGIONS[port]['name']}")
                            
                            # Display metrics
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("User ID", result.get("user_id", "N/A"))
                            with col_b:
                                st.metric("Result Count", result.get("total_count", 0))
                            with col_c:
                                st.metric("Processing Time", f"{result.get('processing_time_ms', 0):.1f}ms")
                            
                            # Display recommendations
                            recommendations = result.get("recommendations", [])
                            if recommendations:
                                st.markdown("---")
                                st.markdown("##### Recommended Products")
                                
                                for idx, rec in enumerate(recommendations, 1):
                                    with st.expander(f"Product {idx}: {rec.get('product_name', rec.get('product_id'))}", expanded=(idx==1)):
                                        col_x, col_y = st.columns([2, 1])
                                        with col_x:
                                            st.markdown(f"**Product ID:** `{rec.get('product_id')}`")
                                            st.markdown(f"**Category:** {rec.get('category', 'N/A')}")
                                            if rec.get('price'):
                                                st.markdown(f"**Price:** ${rec.get('price'):.2f}")
                                        with col_y:
                                            st.metric("Confidence Score", f"{rec.get('score', 0):.3f}")
                                            st.markdown(f"**Source Region:** {rec.get('region', 'N/A')}")
                            else:
                                st.info("No recommendations available for this user")
                        else:
                            st.error(f"Failed to retrieve recommendations from {REGIONS[port]['name']}")
            else:
                st.markdown('<div class="info-box">Click <strong>Execute Recommendation Query</strong> to test the recommendation system across selected regions</div>', unsafe_allow_html=True)
    else:
        st.error("No regions are currently online. Please start the regional API services to enable recommendation testing.")
    
    st.markdown("---")
    
    # System Statistics
    st.markdown('<div class="section-header">System Statistics & Metrics</div>', unsafe_allow_html=True)
    
    if healthy_regions:
        stats_tabs = st.tabs([f"{REGIONS[port]['code']} | {REGIONS[port]['name']}" 
                             for port in [h["port"] for h in healthy_regions]])
        
        for tab, region_info in zip(stats_tabs, healthy_regions):
            with tab:
                port = region_info["port"]
                with st.spinner(f"Loading statistics from {REGIONS[port]['name']}..."):
                    stats = get_stats(port)
                
                if stats:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Machine Learning Model Statistics")
                        model_stats = stats.get("model_stats", {})
                        
                        # Model metrics
                        if model_stats:
                            st.metric("Total Users", f"{model_stats.get('user_count', 0):,}")
                            st.metric("Total Products", f"{model_stats.get('product_count', 0):,}")
                            st.metric("User-Product Interactions", f"{model_stats.get('total_interactions', 0):,}")
                            st.metric("Interaction Matrix Density", f"{model_stats.get('matrix_density', 0):.6f}")
                            
                            if model_stats.get('last_updated'):
                                st.info(f"Last Model Update: {model_stats.get('last_updated')}")
                        else:
                            st.warning("Model statistics are not available")
                    
                    with col2:
                        st.markdown("#### Cache Performance Metrics")
                        cache_stats = stats.get("cache_stats", {})
                        
                        if cache_stats:
                            st.metric("Cache Memory Usage", cache_stats.get('memory_used', 'N/A'))
                            st.metric("Cached Keys", f"{cache_stats.get('keys_count', 0):,}")
                            st.metric("Cache Hits", f"{cache_stats.get('cache_hits', 0):,}")
                            st.metric("Cache Misses", f"{cache_stats.get('cache_misses', 0):,}")
                            
                            # Cache hit ratio
                            hits = cache_stats.get('cache_hits', 0)
                            misses = cache_stats.get('cache_misses', 0)
                            total = hits + misses
                            hit_ratio = (hits / total * 100) if total > 0 else 0
                            st.metric("Cache Hit Ratio", f"{hit_ratio:.1f}%")
                        else:
                            st.warning("Cache statistics are not available")
                    
                    # Uptime
                    uptime = stats.get("uptime_seconds", 0)
                    if uptime > 0:
                        hours = int(uptime // 3600)
                        minutes = int((uptime % 3600) // 60)
                        seconds = int(uptime % 60)
                        st.markdown(f'<div class="info-box">System Uptime: {hours}h {minutes}m {seconds}s</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Unable to retrieve statistics from {REGIONS[port]['name']}")
    
    st.markdown("---")
    
    # Footer
    st.markdown('<div class="section-header">Technology Stack & Architecture</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Core Technologies
        - **Backend Framework:** FastAPI (Python 3.9+)
        - **Machine Learning:** Scikit-learn, Pandas, NumPy
        - **Storage:** MinIO (S3-Compatible Object Storage)
        - **Caching:** Redis
        - **Database:** PostgreSQL
        - **Dashboard:** Streamlit
        """)
    
    with col2:
        st.markdown("""
        #### Key Features
        - Real-time health monitoring across all regions
        - Interactive recommendation testing interface
        - Comprehensive performance analytics
        - Cross-region latency comparison
        - Distributed storage with MinIO
        - Scalable multi-region architecture
        """)
    
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #7f8c8d; padding: 1rem;">
            <p><strong>Multi-Region E-Commerce Recommendation System</strong></p>
            <p>Enterprise-grade distributed recommendation platform with global scalability</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
