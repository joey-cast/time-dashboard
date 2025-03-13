import streamlit as st

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Time Entry Analysis Dashboard",
    page_icon="⏱️",
    layout="wide"
)

import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import jwt
import json
import requests
import base64

# Enable debug mode
DEBUG = True

# Debug function
def debug(message):
    if DEBUG:
        st.write(f"DEBUG: {message}")

# Authentication options
AUTH_OPTIONS = {
    "google": "Google Authentication",
    "password": "Password Authentication"
}

# Get secrets or fallback
try:
    # Try to get from Streamlit secrets
    GOOGLE_CLIENT_ID = st.secrets["auth"]["google_client_id"]
    ALLOWED_DOMAINS = st.secrets["auth"]["allowed_domains"]
    ALLOWED_EMAILS = st.secrets["auth"]["allowed_emails"]
    APP_PASSWORD = st.secrets["auth"].get("password", "timecategorization")
    debug(f"Using Google Client ID from secrets: {GOOGLE_CLIENT_ID[:10]}...")
    debug(f"Current app URL: {st.runtime.get_instance_url()}")
except Exception as e:
    debug(f"Error accessing secrets: {str(e)}")
    # Fallback values
    GOOGLE_CLIENT_ID = "863808931763-veg0i2jpk5v0nuj6b3qde61kd0516cmi.apps.googleusercontent.com"
    ALLOWED_DOMAINS = ["castfinance.com"]
    ALLOWED_EMAILS = ["joey@castfinance.com", "matt@castfinance.com", "taylor@castfinance.com"]
    APP_PASSWORD = "timecategorization"
    debug("Using fallback authentication configuration")

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "auth_method" not in st.session_state:
    st.session_state.auth_method = "google"
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# Password authentication function
def password_auth():
    st.markdown("<h1 style='text-align: center;'>Time Entry Analysis Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please enter the dashboard password:</p>", unsafe_allow_html=True)
    
    password = st.text_input("Password", type="password", key="password_input")
    
    if st.button("Login"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.session_state.user_info = {"name": "Team Member", "email": "team@castfinance.com"}
            debug("Password authentication successful")
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
            debug("Password authentication failed")
    
    st.markdown("<p style='text-align: center;'>or</p>", unsafe_allow_html=True)
    if st.button("Try Google Authentication instead"):
        st.session_state.auth_method = "google"
        debug("Switching to Google authentication")
        st.rerun()

# Manual token entry function
def manual_token_auth():
    st.markdown("### Manual Token Entry")
    st.write("If the Google Sign-In button doesn't work, you can manually enter the JWT token.")
    token = st.text_area("Paste JWT Token here", height=100)
    
    if st.button("Submit Token"):
        if token:
            try:
                # Decode the JWT token
                payload = jwt.decode(token, options={"verify_signature": False})
                
                # Extract user information
                email = payload.get("email", "")
                domain = email.split("@")[-1] if "@" in email else ""
                
                # Check if user is authorized
                domain_authorized = domain in ALLOWED_DOMAINS
                email_authorized = email in ALLOWED_EMAILS
                is_authorized = domain_authorized or email_authorized
                
                debug(f"Email: {email}, Domain: {domain}")
                debug(f"Domain authorized: {domain_authorized}, Email authorized: {email_authorized}")
                
                if is_authorized:
                    st.session_state.authenticated = True
                    st.session_state.user_info = {
                        "email": email,
                        "name": payload.get("name", ""),
                        "picture": payload.get("picture", "")
                    }
                    debug("Manual token authentication successful")
                    st.rerun()
                else:
                    st.error(f"Access denied. Your email {email} is not authorized to view this dashboard.")
            except Exception as e:
                st.error(f"Invalid token: {str(e)}")
    
    st.markdown("<hr>", unsafe_allow_html=True)

# Google authentication function
def google_auth():
    st.markdown("<h1 style='text-align: center;'>Time Entry Analysis Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please sign in with your Google account to access the dashboard.</p>", unsafe_allow_html=True)
    
    # Get current URL for redirect
    current_url = st.runtime.get_instance_url()
    if current_url:
        debug(f"App URL for redirect: {current_url}")
    else:
        current_url = "https://time-dashboard-endqossszbbsxojpt95dct.streamlit.app"
        debug(f"Using hardcoded URL for redirect: {current_url}")
    
    # Create Google Sign-In button
    auth_html = f"""
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: 20px;">
        <div id="g_id_onload"
            data-client_id="{GOOGLE_CLIENT_ID}"
            data-callback="handleCredentialResponse"
            data-auto_prompt="false"
            data-ux_mode="redirect"
            data-login_uri="{current_url}">
        </div>
        <div class="g_id_signin"
            data-type="standard"
            data-size="large"
            data-theme="outline"
            data-text="sign_in_with"
            data-shape="rectangular"
            data-logo_alignment="left">
        </div>
        <p style="margin-top: 10px; font-size: 0.8em; color: #666;">
            If sign-in button doesn't work, try disabling popup blockers or privacy extensions.
        </p>
    </div>
    <script src="https://accounts.google.com/gsi/client" async defer></script>
    <script>
    function handleCredentialResponse(response) {{
        console.log("Received Google response");
        const credential = response.credential;
        
        // Try both methods to increase chances of success
        try {{
            // Method 1: Redirect with token in URL parameter
            window.location.href = window.location.pathname + "?credential=" + encodeURIComponent(credential);
        }} catch (e) {{
            console.error("Redirect failed:", e);
            // Method 2: Try to use localStorage as fallback
            try {{
                localStorage.setItem("google_credential", credential);
                window.location.reload();
            }} catch (e2) {{
                console.error("LocalStorage fallback failed:", e2);
            }}
        }}
    }}
    </script>
    """
    
    # Display the Google Sign-In button
    st.components.v1.html(auth_html, height=120)
    
    # Check for token in multiple places
    credential = None
    
    # 1. Check URL parameters
    url_credential = st.query_params.get("credential", None)
    if url_credential:
        debug("Found credential in URL parameters")
        credential = url_credential
    
    # 2. Check for token in the ID token response
    id_token_response = st.query_params.get("id_token", None) or st.query_params.get("token", None)
    if id_token_response and not credential:
        debug("Found credential in id_token parameter")
        credential = id_token_response
    
    # 3. Check for Google's response parameters
    for param in ['credential', 'id_token', 'token', 'code']:
        if param in st.query_params and not credential:
            debug(f"Found credential in {param} parameter")
            credential = st.query_params[param]
    
    debug(f"Credential found: {'Yes' if credential else 'No'}")
    
    if credential:
        try:
            # Decode the JWT token
            payload = jwt.decode(credential, options={"verify_signature": False})
            
            # Extract user information
            email = payload.get("email", "")
            domain = email.split("@")[-1] if "@" in email else ""
            
            # Check if user is authorized
            domain_authorized = domain in ALLOWED_DOMAINS
            email_authorized = email in ALLOWED_EMAILS
            is_authorized = domain_authorized or email_authorized
            
            debug(f"Email: {email}, Domain: {domain}")
            debug(f"Domain authorized: {domain_authorized}, Email authorized: {email_authorized}")
            
            if is_authorized:
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    "email": email,
                    "name": payload.get("name", ""),
                    "picture": payload.get("picture", "")
                }
                debug("Google authentication successful")
                # Clear the credential from URL
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"Access denied. Your email {email} is not authorized to view this dashboard.")
                debug(f"Access denied for {email}")
                if st.button("Try Again"):
                    st.query_params.clear()
                    st.rerun()
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            debug(f"Authentication error: {str(e)}")
            if st.button("Try Again"):
                st.query_params.clear()
                st.rerun()
    
    # Display manual token entry option for troubleshooting
    with st.expander("Having trouble? Try manual authentication"):
        manual_token_auth()
    
    st.markdown("<p style='text-align: center;'>or</p>", unsafe_allow_html=True)
    if st.button("Use Password Instead"):
        st.session_state.auth_method = "password"
        debug("Switching to password authentication")
        st.rerun()

# Handle authentication
if not st.session_state.authenticated:
    if st.session_state.auth_method == "google":
        google_auth()
    else:
        password_auth()
    
    # Stop app execution for unauthenticated users
    st.stop()

# App starts here for authenticated users
debug("User authenticated, displaying dashboard")

# Show user info in sidebar
with st.sidebar:
    st.write(f"Signed in as: {st.session_state.user_info.get('name', 'User')}")
    if st.button("Sign Out"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.query_params.clear()
        debug("User signed out")
        st.rerun()

# Load and prepare data
@st.cache_data
def load_data():
    df = pd.read_csv('classified_timesheet.csv')
    df['date'] = pd.to_datetime(df['local_date'], errors='coerce')
    df['month_year'] = df['date'].dt.strftime('%Y-%m')
    return df

st.title("Time Entry Analysis Dashboard")
st.markdown("### Analyze categorized time entries")

# Load data
with st.spinner("Loading data..."):
    df = load_data()

# Date filter section
st.sidebar.header("Date Filter")

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
    "Select Date Range:",
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

# Create tabs
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
        fig.update_layout(xaxis={'categoryorder':'total descending'})
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
    fig.update_layout(xaxis={'categoryorder':'total descending'})
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
        st.plotly_chart(fig, use_container_width=True)

# Tab 5: Data Explorer
with tab5:
    st.subheader("Filter and Explore Time Entries")
    
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
    
    # Display table
    display_cols = ['local_date', 'employee', 'hours', 'service item', 'notes', 'classification', 'classification_reason']
    st.dataframe(table_df[display_cols].head(1000), use_container_width=True)

# Add footer
st.markdown("---")
st.markdown("Dashboard powered by NLP time entry categorization") 