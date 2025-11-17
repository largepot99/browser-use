"""
Multi-Task Management Dashboard
Run: streamlit run task_dashboard.py
"""

import streamlit as st
import requests
import yaml
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Task Automation Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load templates catalog
with open('workflow_templates_catalog.yaml', 'r') as f:
    catalog = yaml.safe_load(f)

# API Configuration
API_BASE = st.sidebar.text_input("API URL", "http://localhost:8000/api/v1")
API_KEY = st.sidebar.text_input("API Key", type="password")

# Sidebar Navigation
st.sidebar.title("🎯 Task Dashboard")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "📋 My Tasks", "➕ Create Task", "📅 Schedule", "📥 Extracted Data", "📚 Templates"]
)

# Helper function to make API calls
def api_call(endpoint, method="GET", data=None):
    headers = {"X-API-Key": API_KEY}
    url = f"{API_BASE}{endpoint}"

    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, json=data, headers=headers)
    elif method == "PUT":
        response = requests.put(url, json=data, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        st.error(f"API Error: {response.text}")
        return None

# ============= PAGE: OVERVIEW =============
if page == "📊 Overview":
    st.title("📊 Task Automation Overview")

    # Stats cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Tasks", "12", "+2")
    with col2:
        st.metric("Scheduled", "8", "0")
    with col3:
        st.metric("Executed Today", "34", "+12")
    with col4:
        st.metric("Success Rate", "98.5%", "+1.2%")

    st.divider()

    # Task categories overview
    st.subheader("📦 Task Categories")

    categories = catalog['categories']

    # Display categories in grid
    cols = st.columns(3)
    for idx, category in enumerate(categories):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"""
                <div style="padding: 20px; border-radius: 10px; background-color: #f0f2f6; margin: 10px 0;">
                    <h3>{category['icon']} {category['name']}</h3>
                    <p>Click to view tasks in this category</p>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Recent executions
    st.subheader("🕐 Recent Executions")

    # Mock data - replace with actual API call
    recent_data = pd.DataFrame({
        'Task': ['Daily ELD Extraction', 'Invoice Submission', 'Insurance Check', 'Fuel Report'],
        'Status': ['✅ Success', '✅ Success', '⚠️ Warning', '✅ Success'],
        'Duration': ['2m 34s', '1m 12s', '3m 45s', '1m 58s'],
        'Time': ['6:00 AM', '9:15 AM', '9:00 AM', '8:30 AM']
    })

    st.dataframe(recent_data, use_container_width=True, hide_index=True)

    # Execution trend chart
    st.subheader("📈 Execution Trends")

    # Mock data
    dates = pd.date_range(end=datetime.now(), periods=7)
    trend_data = pd.DataFrame({
        'Date': dates,
        'Successful': [45, 52, 48, 55, 50, 58, 61],
        'Failed': [2, 1, 3, 2, 1, 2, 1]
    })

    fig = px.line(trend_data, x='Date', y=['Successful', 'Failed'],
                  title='Daily Task Executions (Last 7 Days)')
    st.plotly_chart(fig, use_container_width=True)

# ============= PAGE: MY TASKS =============
elif page == "📋 My Tasks":
    st.title("📋 My Active Tasks")

    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"] + [cat['name'] for cat in catalog['categories']]
        )
    with col2:
        filter_frequency = st.selectbox(
            "Filter by Frequency",
            ["All", "Daily", "Weekly", "Monthly", "On-Demand"]
        )
    with col3:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Active", "Paused", "Inactive"]
        )

    st.divider()

    # Mock task list - replace with API call
    tasks = [
        {
            'name': 'Daily ELD Extraction',
            'category': 'ELD & Hours of Service',
            'frequency': 'Daily (6:00 AM)',
            'status': 'Active',
            'last_run': '2 hours ago',
            'next_run': '22 hours',
            'success_rate': '100%'
        },
        {
            'name': 'Invoice Submission to BlueVine',
            'category': 'Invoice Management',
            'frequency': 'On-Demand',
            'status': 'Active',
            'last_run': '3 hours ago',
            'next_run': '-',
            'success_rate': '98.5%'
        },
        {
            'name': 'Weekly Insurance Check',
            'category': 'Compliance & Safety',
            'frequency': 'Weekly (Mon 9:00 AM)',
            'status': 'Active',
            'last_run': '2 days ago',
            'next_run': '5 days',
            'success_rate': '95.2%'
        },
        {
            'name': 'Monthly Financial Report',
            'category': 'Reports & Analytics',
            'frequency': 'Monthly (1st)',
            'status': 'Active',
            'last_run': '15 days ago',
            'next_run': '15 days',
            'success_rate': '100%'
        },
        {
            'name': 'Driver Hours Monitor',
            'category': 'ELD & Hours of Service',
            'frequency': 'Every 30 min',
            'status': 'Active',
            'last_run': '25 min ago',
            'next_run': '5 min',
            'success_rate': '99.8%'
        }
    ]

    for task in tasks:
        with st.expander(f"{task['name']} - {task['frequency']}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**Category:** {task['category']}")
                st.write(f"**Status:** {task['status']}")
                st.write(f"**Last Run:** {task['last_run']}")
                st.write(f"**Next Run:** {task['next_run']}")
                st.write(f"**Success Rate:** {task['success_rate']}")

            with col2:
                if st.button("▶️ Run Now", key=f"run_{task['name']}"):
                    st.success("Task queued for execution!")

                if st.button("⏸️ Pause", key=f"pause_{task['name']}"):
                    st.info("Task paused")

                if st.button("⚙️ Edit", key=f"edit_{task['name']}"):
                    st.info("Opening editor...")

                if st.button("📊 History", key=f"history_{task['name']}"):
                    st.info("Loading execution history...")

# ============= PAGE: CREATE TASK =============
elif page == "➕ Create Task":
    st.title("➕ Create New Task")

    # Step 1: Choose template
    st.subheader("Step 1: Choose Template")

    # Category selector
    selected_category = st.selectbox(
        "Select Category",
        [cat['name'] for cat in catalog['categories']]
    )

    # Filter templates by category
    category_id = next(cat['id'] for cat in catalog['categories'] if cat['name'] == selected_category)
    templates = [t for t in catalog['templates'] if t['category'] == category_id]

    # Display templates
    selected_template = st.selectbox(
        "Select Template",
        options=templates,
        format_func=lambda x: f"{x['name']} - {x['description']}"
    )

    if selected_template:
        st.info(f"**Use Case:** {selected_template['use_case']}")
        st.info(f"**Suggested Frequency:** {selected_template['frequency']}")

    st.divider()

    # Step 2: Configure task
    st.subheader("Step 2: Configure Task")

    task_name = st.text_input("Task Name", value=selected_template['name'] if selected_template else "")

    col1, col2 = st.columns(2)

    with col1:
        company_portal = st.text_input("Company/Portal", placeholder="e.g., KeepTruckin, BlueVine")

        st.write("**Credentials:**")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

    with col2:
        st.write("**Schedule:**")
        schedule_type = st.radio(
            "Execution Type",
            ["On-Demand", "Scheduled (Cron)", "Interval"]
        )

        if schedule_type == "Scheduled (Cron)":
            cron_preset = st.selectbox(
                "Schedule Preset",
                ["Daily at 6 AM", "Weekly on Monday", "Monthly on 1st", "Custom"]
            )
            if cron_preset == "Custom":
                cron_expr = st.text_input("Cron Expression", "0 6 * * *")

        elif schedule_type == "Interval":
            interval = st.number_input("Interval (minutes)", min_value=1, value=30)

    st.divider()

    # Step 3: Test & Deploy
    st.subheader("Step 3: Test & Deploy")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧪 Test Run", type="secondary", use_container_width=True):
            with st.spinner("Running test..."):
                st.success("✅ Test completed successfully!")
                st.json({
                    "status": "success",
                    "duration": "2m 34s",
                    "records_extracted": 45
                })

    with col2:
        if st.button("💾 Save Draft", type="secondary", use_container_width=True):
            st.success("Draft saved!")

    with col3:
        if st.button("🚀 Deploy", type="primary", use_container_width=True):
            st.success("✅ Task deployed successfully!")
            st.balloons()

# ============= PAGE: SCHEDULE =============
elif page == "📅 Schedule":
    st.title("📅 Task Schedule")

    # Calendar view
    st.subheader("Scheduled Tasks Calendar")

    # Mock schedule data
    schedule_data = pd.DataFrame({
        'Task': [
            'Daily ELD Extraction',
            'Weekly Insurance Check',
            'Monthly Financial Report',
            'Invoice Submission',
            'Driver Hours Monitor'
        ],
        'Frequency': ['Daily', 'Weekly', 'Monthly', 'On-Demand', 'Every 30min'],
        'Next Run': [
            '6:00 AM Tomorrow',
            'Mon 9:00 AM',
            'Dec 1, 12:00 AM',
            '-',
            '25 minutes'
        ],
        'Enabled': [True, True, True, True, True]
    })

    st.dataframe(schedule_data, use_container_width=True, hide_index=True)

    st.divider()

    # Timeline view
    st.subheader("Today's Schedule")

    # Create timeline visualization
    timeline_data = [
        {"Task": "Daily ELD Extraction", "Start": "06:00", "End": "06:03", "Status": "Completed"},
        {"Task": "Fuel Report Download", "Start": "08:30", "End": "08:32", "Status": "Completed"},
        {"Task": "Driver Hours Check", "Start": "09:00", "End": "09:02", "Status": "Completed"},
        {"Task": "Invoice Submission", "Start": "09:15", "End": "09:17", "Status": "Completed"},
        {"Task": "Driver Hours Check", "Start": "09:30", "End": "09:32", "Status": "Completed"},
        {"Task": "Driver Hours Check", "Start": "10:00", "End": "10:02", "Status": "Running"},
    ]

    df_timeline = pd.DataFrame(timeline_data)
    st.dataframe(df_timeline, use_container_width=True, hide_index=True)

# ============= PAGE: EXTRACTED DATA =============
elif page == "📥 Extracted Data":
    st.title("📥 Extracted Data")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        data_type = st.selectbox(
            "Data Type",
            ["All", "ELD Logs", "Invoices", "Reports", "Insurance", "Fuel Transactions"]
        )

    with col2:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now())
        )

    with col3:
        export_format = st.selectbox("Export As", ["CSV", "JSON", "Excel"])

    st.divider()

    # Data summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", "1,234")
    with col2:
        st.metric("Today", "156")
    with col3:
        st.metric("This Week", "892")
    with col4:
        st.metric("Storage Used", "234 MB")

    st.divider()

    # Data table
    st.subheader("Extracted Records")

    # Mock data
    extracted_data = pd.DataFrame({
        'Date': ['2025-11-17 06:00', '2025-11-17 06:00', '2025-11-16 06:00'],
        'Type': ['ELD Logs', 'ELD Logs', 'Fuel Report'],
        'Records': [45, 45, 23],
        'Source': ['KeepTruckin', 'KeepTruckin', 'WEX Fuel'],
        'Status': ['✅ Synced', '✅ Synced', '✅ Synced']
    })

    st.dataframe(extracted_data, use_container_width=True, hide_index=True)

    # Export button
    if st.button(f"📥 Export as {export_format}"):
        st.success(f"Exported {len(extracted_data)} records as {export_format}")

# ============= PAGE: TEMPLATES =============
elif page == "📚 Templates":
    st.title("📚 Workflow Templates Library")

    st.markdown("""
    Browse and use pre-built templates for common automation tasks.
    Templates are ready to deploy - just configure your credentials and schedule!
    """)

    # Search
    search = st.text_input("🔍 Search templates", placeholder="e.g., ELD, invoice, compliance")

    st.divider()

    # Display templates by category
    for category in catalog['categories']:
        category_templates = [t for t in catalog['templates'] if t['category'] == category['id']]

        if category_templates:
            with st.expander(f"{category['icon']} {category['name']} ({len(category_templates)} templates)", expanded=False):
                for template in category_templates:
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.markdown(f"**{template['name']}**")
                        st.caption(template['description'])
                        st.caption(f"💡 {template['use_case']}")

                    with col2:
                        frequency_badge = {
                            'daily': '🟢 Daily',
                            'weekly': '🔵 Weekly',
                            'monthly': '🟣 Monthly',
                            'on_demand': '⚪ On-Demand',
                            'interval': '🟡 Interval',
                            'quarterly': '🟤 Quarterly',
                            'biweekly': '🟠 Bi-weekly'
                        }
                        st.markdown(frequency_badge.get(template['frequency'], template['frequency']))

                    with col3:
                        if st.button("Use Template", key=f"use_{template['id']}"):
                            st.success("Template loaded! Configure and deploy.")

                    st.divider()

# Footer
st.sidebar.divider()
st.sidebar.markdown("""
---
**Task Automation Engine v1.0**
Powered by browser-use + AI
""")
