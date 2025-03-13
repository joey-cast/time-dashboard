import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Time Entry Analysis Dashboard",
    page_icon="⏱️",
    layout="wide"
)

# Modern UI styling - inspired by shadcn/ui
st.markdown("""
<style>
    /* Modern Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600 !important;
    }
    
    /* Container styling */
    [data-testid="stVerticalBlock"] {
        border-radius: 8px;
    }
    
    /* Card-like components */
    .stPlotlyChart, div[data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Button styling */
    button[kind="primary"], .stButton>button {
        border-radius: 6px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton>button:hover {
        opacity: 0.9 !important;
        transform: translateY(-1px) !important;
    }
    
    /* Input styling */
    [data-baseweb="input"] {
        border-radius: 6px !important;
    }
    
    /* Dropdown styling */
    [data-baseweb="select"] {
        border-radius: 6px !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    /* Login container */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
        font-weight: 500;
    }
    
    /* Color scheme - Can be adjusted to match your brand */
    .main-accent {
        color: #6366f1;
    }
    
    .bg-accent {
        background-color: #6366f1;
    }
</style>
""", unsafe_allow_html=True)

# Get password from secrets or use default
try:
    # Try to get from Streamlit secrets
    APP_PASSWORD = st.secrets["auth"].get("password", "timecategorization")
except Exception as e:
    # Fallback password
    APP_PASSWORD = "timecategorization"

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# Password authentication function
def password_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 1.8rem;'>Time Entry Analysis Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Please enter the dashboard password to continue</p>", unsafe_allow_html=True)
        
        password = st.text_input("Password", type="password", key="password_input")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            login_button = st.button("Login", type="primary")
        
        if login_button:
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.user_info = {"name": "Team Member", "email": "team@castfinance.com"}
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        
        st.markdown("</div>", unsafe_allow_html=True)

# Handle authentication
if not st.session_state.authenticated:
    password_auth()
    # Stop app execution for unauthenticated users
    st.stop()

# App starts here for authenticated users

# Show user info and sign out button in sidebar
with st.sidebar:
    st.markdown(f"**Signed in as:** {st.session_state.user_info.get('name', 'User')}")
    if st.button("Sign Out", type="primary"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()

# Load and prepare data
@st.cache_data
def load_data():
    df = pd.read_csv('classified_timesheet.csv')
    df['date'] = pd.to_datetime(df['local_date'], errors='coerce')
    df['month_year'] = df['date'].dt.strftime('%Y-%m')
    return df

# Page header with improved styling
st.markdown("<h1 style='font-size: 2rem; margin-bottom: 0.5rem;'>Time Entry Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #6b7280; margin-bottom: 2rem;'>Analyze and visualize categorized time entries</p>", unsafe_allow_html=True)

# Load data
with st.spinner("Loading data..."):
    df = load_data()

# Date filter section with nicer styling
st.sidebar.markdown("## Filters")
st.sidebar.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

# Date range options
date_range_options = {
    'all': 'All Time',
    '3d': 'Last 3 Days',
    '1w': 'Last Week', 
    '1m': 'Last Month',
    '3m': 'Last 3 Months',
    'custom': 'Custom Range'
}

date_range = st.sidebar.selectbox(
    "Date Range",
    options=list(date_range_options.keys()),
    format_func=lambda x: date_range_options[x],
    index=0
)

# Function to get start date based on selection
def get_start_date(selection):
    today = datetime.now().date()
    if selection == '3d':
        return today - timedelta(days=3)
    elif selection == '1w':
        return today - timedelta(days=7)
    elif selection == '1m':
        return today - timedelta(days=30)
    elif selection == '3m':
        return today - timedelta(days=90)
    else:
        return None  # All time

# Custom date range if selected
start_date = None
end_date = None

if date_range == 'custom':
    min_date = df['date'].min().date() if not pd.isna(df['date'].min()) else datetime(2020, 1, 1).date()
    max_date = df['date'].max().date() if not pd.isna(df['date'].max()) else datetime.now().date()
    
    start_date = st.sidebar.date_input(
        "Start Date:",
        min_value=min_date,
        max_value=max_date,
        value=min_date
    )
    
    end_date = st.sidebar.date_input(
        "End Date:",
        min_value=min_date,
        max_value=max_date,
        value=max_date
    )
else:
    if date_range != 'all':
        start_date = get_start_date(date_range)
    else:
        # For 'all', use the min/max dates in the dataset
        start_date = df['date'].min().date() if not pd.isna(df['date'].min()) else None
    
    end_date = datetime.now().date()

# Filter data based on date selection
def filter_dataframe(df, date_range, start_date, end_date):
    filtered_df = df.copy()
    
    if date_range == 'all':
        pass  # No filtering needed
    elif date_range == 'custom':
        if start_date and end_date:
            # Add one day to end_date to make it inclusive
            end_date_inclusive = end_date + timedelta(days=1)
            filtered_df = filtered_df[(filtered_df['date'].dt.date >= start_date) & 
                                     (filtered_df['date'].dt.date < end_date_inclusive)]
    else:
        # Handle preset ranges
        if start_date:
            filtered_df = filtered_df[filtered_df['date'].dt.date >= start_date]
    
    return filtered_df

filtered_df = filter_dataframe(df, date_range, start_date, end_date)

# Summary statistics
st.sidebar.markdown("### Summary")
st.sidebar.markdown(f"**Total Hours:** {filtered_df['hours'].sum():.1f}")
st.sidebar.markdown(f"**Total Entries:** {len(filtered_df)}")
min_date_str = filtered_df['date'].min().strftime('%b %Y') if not pd.isna(filtered_df['date'].min()) else "N/A"
max_date_str = filtered_df['date'].max().strftime('%b %Y') if not pd.isna(filtered_df['date'].max()) else "N/A"
st.sidebar.markdown(f"**Date Range:** {min_date_str} to {max_date_str}")

# Create tabs with shadcn-inspired styling
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Category Analysis", 
    "Service Item Analysis", 
    "Time Trends",
    "User Analysis",
    "Data Explorer"
])

# Tab 1: Category Analysis
with tab1:
    # Category data
    category_hours = filtered_df.groupby('classification')['hours'].sum().reset_index()
    category_hours = category_hours.sort_values('hours', ascending=False)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Hours by Category")
        fig = px.bar(
            category_hours, 
            x='classification', 
            y='hours',
            color='hours',
            labels={'classification': 'Category', 'hours': 'Total Hours'},
            title="Total Hours by Category",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(
            xaxis={'categoryorder':'total descending'},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif'},
            margin=dict(l=40, r=40, t=60, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Category Distribution")
        fig = px.pie(
            category_hours, 
            values='hours', 
            names='classification',
            title="Distribution of Hours by Category",
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig.update_layout(
            legend=dict(orientation="h", y=-0.2),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif'},
            margin=dict(l=20, r=20, t=60, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Category trends over time
    st.subheader("Category Trends Over Time")
    
    # Category selection with Select All button
    all_categories = sorted(filtered_df['classification'].unique())
    
    col1, col2 = st.columns([6, 1])
    with col1:
        selected_categories = st.multiselect(
            "Select Categories:",
            options=all_categories,
            default=category_hours['classification'].head(5).tolist()
        )
    
    with col2:
        if st.button("Select All"):
            selected_categories = all_categories
    
    if not selected_categories:
        selected_categories = category_hours['classification'].head(5).tolist()
    
    # Show trends chart
    time_category = filtered_df.groupby(['month_year', 'classification'])['hours'].sum().reset_index()
    filtered_time_category = time_category[time_category['classification'].isin(selected_categories)]
    
    fig = px.line(
        filtered_time_category, 
        x='month_year', 
        y='hours', 
        color='classification',
        markers=True,
        labels={'month_year': 'Month', 'hours': 'Hours', 'classification': 'Category'},
        title="Category Trends Over Time"
    )
    fig.update_layout(
        xaxis={'categoryorder':'array', 'categoryarray': sorted(filtered_time_category['month_year'].unique())},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif'},
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(l=40, r=40, t=60, b=80),
    )
    st.plotly_chart(fig, use_container_width=True)

# Tab 2: Service Item Analysis
with tab2:
    # Service item data
    service_hours = filtered_df.groupby('service item')['hours'].sum().reset_index()
    service_hours = service_hours.sort_values('hours', ascending=False).head(10)
    
    st.subheader("Hours by Service Item (Top 10)")
    fig = px.bar(
        service_hours, 
        x='service item', 
        y='hours',
        color='hours',
        labels={'service item': 'Service Item', 'hours': 'Total Hours'},
        title="Total Hours by Service Item (Top 10)",
        color_continuous_scale=px.colors.sequential.Plasma
    )
    fig.update_layout(
        xaxis={'categoryorder':'total descending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif'},
        margin=dict(l=40, r=40, t=60, b=40),
        hoverlabel=dict(font_family="Inter, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Category distribution by service item
    st.subheader("Category Distribution by Service Item")
    
    top_services = service_hours['service item'].tolist()
    selected_service = st.selectbox(
        "Select Service Item:",
        options=top_services,
        index=0
    )
    
    service_filtered_df = filtered_df[filtered_df['service item'] == selected_service]
    category_dist = service_filtered_df.groupby('classification')['hours'].sum().reset_index()
    category_dist = category_dist.sort_values('hours', ascending=False)
    
    fig = px.pie(
        category_dist, 
        values='hours', 
        names='classification',
        title=f"Category Distribution for {selected_service}",
        color_discrete_sequence=px.colors.sequential.Plasma
    )
    fig.update_layout(
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif'},
        margin=dict(l=20, r=20, t=60, b=20),
        hoverlabel=dict(font_family="Inter, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Time Trends
with tab3:
    # Monthly trend
    monthly_hours = filtered_df.groupby('month_year')['hours'].sum().reset_index()
    
    st.subheader("Monthly Hours Trend")
    fig = px.line(
        monthly_hours, 
        x='month_year', 
        y='hours',
        markers=True,
        labels={'month_year': 'Month', 'hours': 'Total Hours'},
        title="Total Hours by Month"
    )
    fig.update_layout(
        xaxis={'categoryorder':'array', 'categoryarray': sorted(monthly_hours['month_year'].unique())},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif'},
        margin=dict(l=40, r=40, t=60, b=40),
        hoverlabel=dict(font_family="Inter, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap
    st.subheader("Monthly Hours by Category Heatmap")
    time_category = filtered_df.groupby(['month_year', 'classification'])['hours'].sum().reset_index()
    
    fig = px.density_heatmap(
        time_category,
        x='month_year',
        y='classification',
        z='hours',
        labels={'month_year': 'Month', 'classification': 'Category', 'hours': 'Hours'},
        title="Hours by Category and Month",
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig.update_layout(
        xaxis={'categoryorder':'array', 'categoryarray': sorted(time_category['month_year'].unique())},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif'},
        margin=dict(l=60, r=40, t=60, b=40),
        hoverlabel=dict(font_family="Inter, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

# Tab 4: User Analysis
with tab4:
    # User hours
    user_hours = filtered_df.groupby(['fname', 'lname'])['hours'].sum().reset_index()
    user_hours['full_name'] = user_hours['fname'] + ' ' + user_hours['lname']
    user_hours = user_hours.sort_values('hours', ascending=False)
    
    st.subheader("Hours by User")
    fig = px.bar(
        user_hours.head(10), 
        x='full_name', 
        y='hours',
        color='hours',
        labels={'full_name': 'Employee', 'hours': 'Total Hours'},
        title="Total Hours by Employee (Top 10)",
        color_continuous_scale=px.colors.sequential.Turbo
    )
    fig.update_layout(
        xaxis={'categoryorder':'total descending'},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif'},
        margin=dict(l=40, r=40, t=60, b=40),
        hoverlabel=dict(font_family="Inter, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Category distribution by user
    st.subheader("Category Distribution by User")
    
    top_users = user_hours['full_name'].head(10).tolist()
    selected_user = st.selectbox(
        "Select Employee:",
        options=top_users,
        index=0 if len(top_users) > 0 else 0
    )
    
    if selected_user:
        fname, lname = selected_user.split(' ', 1)
        user_filtered_df = filtered_df[(filtered_df['fname'] == fname) & (filtered_df['lname'] == lname)]
        category_dist = user_filtered_df.groupby('classification')['hours'].sum().reset_index()
        category_dist = category_dist.sort_values('hours', ascending=False)
        
        fig = px.pie(
            category_dist, 
            values='hours', 
            names='classification',
            title=f"Category Distribution for {selected_user}",
            color_discrete_sequence=px.colors.sequential.Turbo
        )
        fig.update_layout(
            legend=dict(orientation="h", y=-0.2),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif'},
            margin=dict(l=20, r=20, t=60, b=20),
            hoverlabel=dict(font_family="Inter, sans-serif")
        )
        st.plotly_chart(fig, use_container_width=True)

# Tab 5: Data Explorer
with tab5:
    st.subheader("Filter and Explore Time Entries")
    
    # Create a card-like container for filters
    st.markdown("""
    <div style="background-color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_category = st.selectbox(
            "Category:",
            options=['All'] + sorted(filtered_df['classification'].unique().tolist()),
            index=0
        )
    
    with col2:
        filter_service = st.selectbox(
            "Service Item:",
            options=['All'] + sorted(filtered_df['service item'].unique().tolist()[:20]),
            index=0
        )
    
    with col3:
        sort_options = {
            'date_desc': 'Date (Newest First)',
            'date_asc': 'Date (Oldest First)',
            'hours_desc': 'Hours (Highest First)',
            'hours_asc': 'Hours (Lowest First)'
        }
        sort_by = st.selectbox(
            "Sort By:",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            index=0
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Apply filters
    table_df = filtered_df.copy()
    table_df['employee'] = table_df['fname'] + ' ' + table_df['lname']
    
    if filter_category != 'All':
        table_df = table_df[table_df['classification'] == filter_category]
    
    if filter_service != 'All':
        table_df = table_df[table_df['service item'] == filter_service]
    
    # Apply sorting
    if sort_by == 'date_desc':
        table_df = table_df.sort_values('date', ascending=False)
    elif sort_by == 'date_asc':
        table_df = table_df.sort_values('date', ascending=True)
    elif sort_by == 'hours_desc':
        table_df = table_df.sort_values('hours', ascending=False)
    elif sort_by == 'hours_asc':
        table_df = table_df.sort_values('hours', ascending=True)
    
    # Display table with record count info
    record_count = len(table_df)
    st.markdown(f"<p style='margin-bottom: 10px;'>Showing {min(record_count, 1000)} of {record_count} records</p>", unsafe_allow_html=True)
    
    # Display table
    display_cols = ['local_date', 'employee', 'hours', 'service item', 'notes', 'classification', 'classification_reason']
    st.dataframe(table_df[display_cols].head(1000), use_container_width=True)

# Add footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <p style="color: #6b7280; font-size: 0.9rem;">
        Dashboard powered by NLP time entry categorization
    </p>
    <p style="color: #9ca3af; font-size: 0.8rem;">
        © 2023 Cast Financial
    </p>
</div>
""", unsafe_allow_html=True) 