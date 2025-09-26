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
    page_title="Multi-Region Recommendation System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Region configuration
REGIONS = {
    "8000": {"name": "US-West", "flag": "🌴", "color": "#FF6B6B", "location": "California"},
    "8001": {"name": "US-East", "flag": "🗽", "color": "#4ECDC4", "location": "New York"},
    "8002": {"name": "EU-West", "flag": "🇪🇺", "color": "#45B7D1", "location": "Ireland"},
    "8003": {"name": "AP-South", "flag": "🌏", "color": "#96CEB4", "location": "Mumbai"}
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
    # Header
    st.title("Multi-Region E-commerce Recommendation System")
    st.markdown("**Real-time dashboard for monitoring and testing the distributed recommendation system**")
    
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        time.sleep(30)
        st.experimental_rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.experimental_rerun()
    
    st.sidebar.markdown("---")
    
    # Region Health Status
    st.header("Region Health Status")
    
    # Check all regions
    health_data = []
    cols = st.columns(4)
    
    for i, (port, info) in enumerate(REGIONS.items()):
        with cols[i]:
            with st.spinner(f"Checking {info['name']}..."):
                health = check_region_health(port)
                
            if health["status"] == "healthy":
                st.success(f"{info['flag']} **{info['name']}**")
                st.metric(
                    label="Latency",
                    value=f"{health['latency']:.1f}ms",
                    help=f"Response time from {info['location']}"
                )
                st.markdown(f"📍 {info['location']}")
                st.markdown(f"🌐 [Open API](<http://localhost:{port}>)")
                st.markdown(f"📖 [Docs](<http://localhost:{port}/docs>)")
            else:
                st.error(f"{info['flag']} **{info['name']}**")
                st.markdown("❌ **Offline**")
                st.markdown(f"📍 {info['location']}")
                
            health_data.append({
                "port": port,
                "region": info["name"],
                "status": health["status"],
                "latency": health["latency"],
                "location": info["location"]
            })
    
    # Health Summary Chart
    st.subheader("Region Performance")
    
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
                labels={"latency": "Latency (ms)", "region": "Region"}
            )
            fig_latency.update_layout(showlegend=False)
            st.plotly_chart(fig_latency, use_container_width=True)
        
        with col2:
            # Status pie chart
            status_counts = pd.DataFrame(health_data)["status"].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Region Availability",
                color_discrete_map={"healthy": "#2ECC71", "offline": "#E74C3C"}
            )
            st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.warning("🔴 No regions are currently online")
    
    st.markdown("---")
    
    # Recommendation Testing
    st.header("Recommendation Testing")
    
    if healthy_regions:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🎛️ Test Parameters")
            
            # User ID input
            user_id = st.text_input(
                "User ID",
                value="user123",
                help="Enter a user ID to get recommendations for"
            )
            
            # Number of recommendations
            rec_count = st.slider(
                "Number of Recommendations",
                min_value=1,
                max_value=10,
                value=5,
                help="How many recommendations to retrieve"
            )
            
            # Region selection
            available_ports = [h["port"] for h in healthy_regions]
            selected_regions = st.multiselect(
                "Test Regions",
                options=available_ports,
                default=available_ports,
                format_func=lambda x: f"{REGIONS[x]['flag']} {REGIONS[x]['name']}"
            )
            
            # Test button
            if st.button("🚀 Get Recommendations", type="primary"):
                if user_id and selected_regions:
                    st.session_state.test_results = {}
                    
                    for port in selected_regions:
                        with st.spinner(f"Getting recommendations from {REGIONS[port]['name']}..."):
                            result = get_recommendations(port, user_id, rec_count)
                            st.session_state.test_results[port] = result
                else:
                    st.error("Please enter a user ID and select at least one region")
        
        with col2:
            st.subheader("Recommendation Results")
            
            if hasattr(st.session_state, 'test_results') and st.session_state.test_results:
                tabs = st.tabs([f"{REGIONS[port]['flag']} {REGIONS[port]['name']}" 
                               for port in st.session_state.test_results.keys()])
                
                for tab, (port, result) in zip(tabs, st.session_state.test_results.items()):
                    with tab:
                        if result:
                            st.success(f"✅ Recommendations from {REGIONS[port]['name']}")
                            
                            # Display metrics
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("User ID", result.get("user_id", "N/A"))
                            with col_b:
                                st.metric("Count", result.get("total_count", 0))
                            with col_c:
                                st.metric("Processing Time", f"{result.get('processing_time_ms', 0):.1f}ms")
                            
                            # Display recommendations
                            recommendations = result.get("recommendations", [])
                            if recommendations:
                                rec_df = pd.DataFrame(recommendations)
                                
                                for idx, rec in enumerate(recommendations, 1):
                                    with st.expander(f"{idx}. {rec.get('product_name', rec.get('product_id'))}"):
                                        col_x, col_y = st.columns([2, 1])
                                        with col_x:
                                            st.write(f"**Product ID:** {rec.get('product_id')}")
                                            st.write(f"**Category:** {rec.get('category', 'N/A')}")
                                            if rec.get('price'):
                                                st.write(f"**Price:** ${rec.get('price'):.2f}")
                                        with col_y:
                                            st.metric("Score", f"{rec.get('score', 0):.3f}")
                                            st.write(f"Region: {rec.get('region', 'N/A')}")
                            else:
                                st.info("No recommendations returned")
                        else:
                            st.error(f"❌ Failed to get recommendations from {REGIONS[port]['name']}")
            else:
                st.info("Click 'Get Recommendations' to test the system")
    else:
        st.error("🔴 No regions are online to test recommendations")
    
    st.markdown("---")
    
    # System Statistics
    st.header("System Statistics")
    
    if healthy_regions:
        stats_tabs = st.tabs([f"{REGIONS[port]['flag']} {REGIONS[port]['name']}" 
                             for port in [h["port"] for h in healthy_regions]])
        
        for tab, region_info in zip(stats_tabs, healthy_regions):
            with tab:
                port = region_info["port"]
                with st.spinner(f"Loading stats from {REGIONS[port]['name']}..."):
                    stats = get_stats(port)
                
                if stats:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("🤖 Model Statistics")
                        model_stats = stats.get("model_stats", {})
                        
                        # Model metrics
                        if model_stats:
                            st.metric("Users", f"{model_stats.get('user_count', 0):,}")
                            st.metric("Products", f"{model_stats.get('product_count', 0):,}")
                            st.metric("Interactions", f"{model_stats.get('total_interactions', 0):,}")
                            st.metric("Matrix Density", f"{model_stats.get('matrix_density', 0):.6f}")
                        else:
                            st.info("Model statistics not available")
                    
                    with col2:
                        st.subheader("⚡ Cache Statistics")
                        cache_stats = stats.get("cache_stats", {})
                        
                        if cache_stats:
                            st.metric("Memory Used", cache_stats.get('memory_used', 'N/A'))
                            st.metric("Keys Count", f"{cache_stats.get('keys_count', 0):,}")
                            st.metric("Cache Hits", f"{cache_stats.get('cache_hits', 0):,}")
                            st.metric("Cache Misses", f"{cache_stats.get('cache_misses', 0):,}")
                            
                            # Cache hit ratio
                            hits = cache_stats.get('cache_hits', 0)
                            misses = cache_stats.get('cache_misses', 0)
                            total = hits + misses
                            hit_ratio = (hits / total * 100) if total > 0 else 0
                            st.metric("Hit Ratio", f"{hit_ratio:.1f}%")
                        else:
                            st.info("Cache statistics not available")
                    
                    # Uptime
                    uptime = stats.get("uptime_seconds", 0)
                    if uptime > 0:
                        hours = int(uptime // 3600)
                        minutes = int((uptime % 3600) // 60)
                        st.info(f"⏱️ Uptime: {hours}h {minutes}m")
                else:
                    st.error(f"Failed to load statistics from {REGIONS[port]['name']}")
    
    st.markdown("---")
    
    # Footer
    st.markdown("### Multi-Region E-commerce Recommendation System")
    st.markdown("""
    **Built with:**
    - **Python** & **FastAPI** for the backend APIs
    - **Scikit-learn** for machine learning algorithms  
    - **MinIO** for distributed object storage
    - **Streamlit** for this interactive dashboard
    - **Multi-region architecture** for global scalability
    
    **Features:**
    - ✅ Real-time health monitoring
    - ✅ Interactive recommendation testing
    - ✅ Performance analytics
    - ✅ Cross-region comparison
    """)

if __name__ == "__main__":
    main()
