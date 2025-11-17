"""
Visual Workflow Builder using Streamlit
Run: streamlit run workflow_builder_ui.py
"""

import streamlit as st
import yaml
import json
import requests
from typing import Dict, Any, List
import uuid

# Page config
st.set_page_config(
    page_title="Workflow Builder",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.step-card {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 4px solid #1f77b4;
}
.action-type {
    background-color: #1f77b4;
    color: white;
    padding: 5px 10px;
    border-radius: 5px;
    display: inline-block;
}
.step-number {
    background-color: #ff7f0e;
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'workflow' not in st.session_state:
    st.session_state.workflow = {
        'name': '',
        'description': '',
        'company_id': '',
        'version': 1,
        'variables': {},
        'inputs': [],
        'outputs': [],
        'steps': []
    }

if 'current_step_index' not in st.session_state:
    st.session_state.current_step_index = None

# Action type definitions
ACTION_TYPES = {
    'Basic Actions': {
        'navigate': {'params': ['url', 'wait_until'], 'icon': '🧭'},
        'click': {'params': ['selector', 'wait_for_navigation'], 'icon': '👆'},
        'type': {'params': ['selector', 'text', 'clear_first'], 'icon': '⌨️'},
        'upload_file': {'params': ['selector', 'file_path', 'wait_for_upload'], 'icon': '📤'},
        'extract': {'params': ['selector', 'attribute', 'save_to'], 'icon': '📥'},
        'screenshot': {'params': ['save_as'], 'icon': '📸'},
    },
    'AI Actions': {
        'ai_task': {'params': ['task', 'max_steps', 'extract_data'], 'icon': '🤖'},
        'login': {'params': ['username_selector', 'password_selector', 'submit_selector'], 'icon': '🔐'},
    },
    'Control Flow': {
        'conditional': {'params': ['condition', 'if_true', 'if_false'], 'icon': '🔀'},
        'foreach': {'params': ['items', 'item_name', 'steps', 'continue_on_error'], 'icon': '🔁'},
        'while': {'params': ['condition', 'steps', 'max_iterations'], 'icon': '♾️'},
        'switch': {'params': ['value', 'cases', 'default'], 'icon': '🔄'},
        'try_catch': {'params': ['try', 'catch', 'finally'], 'icon': '🛡️'},
    },
    'Data Actions': {
        'set_variable': {'params': ['name', 'value'], 'icon': '💾'},
        'append_to_array': {'params': ['array', 'value'], 'icon': '➕'},
        'increment': {'params': ['variable', 'amount'], 'icon': '⬆️'},
        'evaluate': {'params': ['expression', 'save_to'], 'icon': '🧮'},
    },
    'Integration Actions': {
        'http_request': {'params': ['method', 'url', 'headers', 'body'], 'icon': '🌐'},
        'send_notification': {'params': ['type', 'to', 'subject', 'body'], 'icon': '📧'},
    },
    'Utility Actions': {
        'sleep': {'params': ['milliseconds'], 'icon': '⏱️'},
        'fail': {'params': ['message'], 'icon': '❌'},
    }
}

# Sidebar - Workflow Metadata
with st.sidebar:
    st.title("🔧 Workflow Builder")

    st.header("Workflow Info")
    st.session_state.workflow['name'] = st.text_input(
        "Workflow Name",
        value=st.session_state.workflow['name'],
        placeholder="e.g., BlueVine Invoice Submission"
    )

    st.session_state.workflow['description'] = st.text_area(
        "Description",
        value=st.session_state.workflow['description'],
        placeholder="Describe what this workflow does..."
    )

    st.session_state.workflow['company_id'] = st.text_input(
        "Company ID",
        value=st.session_state.workflow['company_id'],
        placeholder="e.g., bluevine"
    )

    st.divider()

    # Inputs
    st.subheader("📥 Workflow Inputs")
    if st.button("➕ Add Input"):
        st.session_state.workflow['inputs'].append({
            'name': '',
            'type': 'string',
            'required': True
        })

    for i, inp in enumerate(st.session_state.workflow['inputs']):
        with st.expander(f"Input {i+1}: {inp.get('name', 'Unnamed')}"):
            inp['name'] = st.text_input(f"Name##input_{i}", value=inp.get('name', ''))
            inp['type'] = st.selectbox(
                f"Type##input_{i}",
                ['string', 'number', 'boolean', 'object', 'array', 'file'],
                index=['string', 'number', 'boolean', 'object', 'array', 'file'].index(inp.get('type', 'string'))
            )
            inp['required'] = st.checkbox(f"Required##input_{i}", value=inp.get('required', True))
            if st.button(f"🗑️ Delete##input_{i}"):
                st.session_state.workflow['inputs'].pop(i)
                st.rerun()

    st.divider()

    # Variables
    st.subheader("📊 Variables")
    variable_yaml = st.text_area(
        "Define variables (YAML)",
        value=yaml.dump(st.session_state.workflow['variables'], default_flow_style=False),
        height=100
    )
    try:
        st.session_state.workflow['variables'] = yaml.safe_load(variable_yaml) or {}
    except:
        st.error("Invalid YAML syntax")

    st.divider()

    # Actions
    st.subheader("⚡ Available Actions")
    for category, actions in ACTION_TYPES.items():
        with st.expander(category):
            for action_name, action_info in actions.items():
                st.markdown(f"{action_info['icon']} **{action_name}**")
                st.caption(f"Params: {', '.join(action_info['params'][:3])}")

# Main area - Workflow Steps
st.title("📋 Workflow Steps")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.metric("Total Steps", len(st.session_state.workflow['steps']))
with col2:
    if st.button("➕ Add Step", type="primary", use_container_width=True):
        new_step = {
            'id': str(uuid.uuid4()),
            'name': f'step_{len(st.session_state.workflow["steps"]) + 1}',
            'action': 'navigate',
            'params': {},
            'on_error': 'fail',
            'timeout': None
        }
        st.session_state.workflow['steps'].append(new_step)
        st.session_state.current_step_index = len(st.session_state.workflow['steps']) - 1
        st.rerun()
with col3:
    if st.button("📋 Import YAML", use_container_width=True):
        st.session_state.show_import = True

# Import YAML modal
if st.session_state.get('show_import', False):
    with st.container():
        st.subheader("Import Workflow from YAML")
        yaml_input = st.text_area("Paste YAML here:", height=300)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Import"):
                try:
                    imported = yaml.safe_load(yaml_input)
                    st.session_state.workflow = imported
                    st.session_state.show_import = False
                    st.success("Workflow imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {str(e)}")
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.show_import = False
                st.rerun()

# Display steps
if not st.session_state.workflow['steps']:
    st.info("👆 Click 'Add Step' to start building your workflow")
else:
    # Step list with drag-and-drop simulation
    for idx, step in enumerate(st.session_state.workflow['steps']):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 3, 2, 1, 1])

            with col1:
                st.markdown(f'<div class="step-number">{idx + 1}</div>', unsafe_allow_html=True)

            with col2:
                st.markdown(f"**{step.get('name', 'Unnamed Step')}**")

            with col3:
                action_info = None
                for category, actions in ACTION_TYPES.items():
                    if step['action'] in actions:
                        action_info = actions[step['action']]
                        break
                icon = action_info['icon'] if action_info else '⚙️'
                st.markdown(f'<span class="action-type">{icon} {step["action"]}</span>', unsafe_allow_html=True)

            with col4:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state.current_step_index = idx
                    st.rerun()

            with col5:
                if st.button("🗑️", key=f"delete_{idx}"):
                    st.session_state.workflow['steps'].pop(idx)
                    st.rerun()

            # Show step details when editing
            if st.session_state.current_step_index == idx:
                with st.expander("📝 Edit Step", expanded=True):
                    step['name'] = st.text_input(
                        "Step Name",
                        value=step.get('name', ''),
                        key=f"step_name_{idx}"
                    )

                    # Action type selector
                    action_categories = list(ACTION_TYPES.keys())
                    selected_category = st.selectbox(
                        "Action Category",
                        action_categories,
                        key=f"category_{idx}"
                    )

                    actions_in_category = list(ACTION_TYPES[selected_category].keys())
                    current_action_index = actions_in_category.index(step['action']) if step['action'] in actions_in_category else 0

                    step['action'] = st.selectbox(
                        "Action Type",
                        actions_in_category,
                        index=current_action_index,
                        key=f"action_{idx}"
                    )

                    st.divider()
                    st.subheader("Parameters")

                    # Get parameter definitions for this action
                    action_params = ACTION_TYPES[selected_category][step['action']]['params']

                    # Render parameter inputs based on action type
                    if step['action'] == 'navigate':
                        step['params']['url'] = st.text_input(
                            "URL",
                            value=step['params'].get('url', ''),
                            placeholder="https://example.com or {{ variables.portal_url }}",
                            key=f"param_url_{idx}"
                        )
                        step['params']['wait_until'] = st.selectbox(
                            "Wait Until",
                            ['networkidle', 'load', 'domcontentloaded'],
                            key=f"param_wait_{idx}"
                        )

                    elif step['action'] == 'click':
                        step['params']['selector'] = st.text_input(
                            "CSS Selector",
                            value=step['params'].get('selector', ''),
                            placeholder="#submit-button or .btn-primary",
                            key=f"param_selector_{idx}"
                        )
                        step['params']['wait_for_navigation'] = st.checkbox(
                            "Wait for navigation",
                            value=step['params'].get('wait_for_navigation', False),
                            key=f"param_wait_nav_{idx}"
                        )

                    elif step['action'] == 'type':
                        step['params']['selector'] = st.text_input(
                            "CSS Selector",
                            value=step['params'].get('selector', ''),
                            key=f"param_selector_{idx}"
                        )
                        step['params']['text'] = st.text_input(
                            "Text to Type",
                            value=step['params'].get('text', ''),
                            placeholder="Enter text or {{ inputs.invoice_number }}",
                            key=f"param_text_{idx}"
                        )
                        step['params']['clear_first'] = st.checkbox(
                            "Clear field first",
                            value=step['params'].get('clear_first', False),
                            key=f"param_clear_{idx}"
                        )

                    elif step['action'] == 'ai_task':
                        step['params']['task'] = st.text_area(
                            "AI Task Description",
                            value=step['params'].get('task', ''),
                            placeholder="Describe what the AI should do...",
                            height=150,
                            key=f"param_task_{idx}"
                        )
                        step['params']['max_steps'] = st.number_input(
                            "Max Steps",
                            value=step['params'].get('max_steps', 10),
                            min_value=1,
                            max_value=100,
                            key=f"param_max_steps_{idx}"
                        )

                        st.write("**Extract Data** (optional)")
                        extract_data_yaml = st.text_area(
                            "Define data to extract (YAML)",
                            value=yaml.dump(step['params'].get('extract_data', {}), default_flow_style=False),
                            key=f"param_extract_{idx}",
                            height=100
                        )
                        try:
                            step['params']['extract_data'] = yaml.safe_load(extract_data_yaml) or {}
                        except:
                            st.error("Invalid YAML syntax")

                    elif step['action'] == 'conditional':
                        step['params']['condition'] = st.text_input(
                            "Condition",
                            value=step['params'].get('condition', ''),
                            placeholder="{{ variables.status == 'success' }}",
                            key=f"param_condition_{idx}"
                        )

                        st.write("**If True Steps:**")
                        if_true_yaml = st.text_area(
                            "Steps to execute if condition is true (YAML)",
                            value=yaml.dump(step['params'].get('if_true', []), default_flow_style=False),
                            key=f"param_if_true_{idx}",
                            height=150
                        )
                        try:
                            step['params']['if_true'] = yaml.safe_load(if_true_yaml) or []
                        except:
                            st.error("Invalid YAML syntax")

                        st.write("**If False Steps:**")
                        if_false_yaml = st.text_area(
                            "Steps to execute if condition is false (YAML)",
                            value=yaml.dump(step['params'].get('if_false', []), default_flow_style=False),
                            key=f"param_if_false_{idx}",
                            height=150
                        )
                        try:
                            step['params']['if_false'] = yaml.safe_load(if_false_yaml) or []
                        except:
                            st.error("Invalid YAML syntax")

                    elif step['action'] == 'foreach':
                        step['params']['items'] = st.text_input(
                            "Items to iterate",
                            value=step['params'].get('items', ''),
                            placeholder="{{ inputs.invoices }}",
                            key=f"param_items_{idx}"
                        )
                        step['params']['item_name'] = st.text_input(
                            "Item variable name",
                            value=step['params'].get('item_name', 'item'),
                            key=f"param_item_name_{idx}"
                        )
                        step['params']['continue_on_error'] = st.checkbox(
                            "Continue on error",
                            value=step['params'].get('continue_on_error', False),
                            key=f"param_continue_{idx}"
                        )

                        st.write("**Loop Steps:**")
                        loop_steps_yaml = st.text_area(
                            "Steps to execute for each item (YAML)",
                            value=yaml.dump(step['params'].get('steps', []), default_flow_style=False),
                            key=f"param_steps_{idx}",
                            height=200
                        )
                        try:
                            step['params']['steps'] = yaml.safe_load(loop_steps_yaml) or []
                        except:
                            st.error("Invalid YAML syntax")

                    elif step['action'] == 'upload_file':
                        step['params']['selector'] = st.text_input(
                            "File input selector",
                            value=step['params'].get('selector', ''),
                            key=f"param_selector_{idx}"
                        )
                        step['params']['file_path'] = st.text_input(
                            "File path",
                            value=step['params'].get('file_path', ''),
                            placeholder="{{ inputs.invoice_pdf }}",
                            key=f"param_file_{idx}"
                        )

                    elif step['action'] == 'extract':
                        step['params']['selector'] = st.text_input(
                            "CSS Selector",
                            value=step['params'].get('selector', ''),
                            key=f"param_selector_{idx}"
                        )
                        step['params']['attribute'] = st.selectbox(
                            "Attribute",
                            ['text', 'value', 'href', 'src', 'class', 'id'],
                            key=f"param_attribute_{idx}"
                        )
                        step['params']['save_to'] = st.text_input(
                            "Save to variable",
                            value=step['params'].get('save_to', ''),
                            placeholder="outputs.confirmation_number",
                            key=f"param_save_to_{idx}"
                        )

                    else:
                        # Generic parameter editor for other actions
                        st.write("Edit parameters as YAML:")
                        params_yaml = st.text_area(
                            "Parameters (YAML)",
                            value=yaml.dump(step.get('params', {}), default_flow_style=False),
                            key=f"params_yaml_{idx}",
                            height=200
                        )
                        try:
                            step['params'] = yaml.safe_load(params_yaml) or {}
                        except:
                            st.error("Invalid YAML syntax")

                    st.divider()
                    st.subheader("Error Handling")

                    col1, col2 = st.columns(2)
                    with col1:
                        step['on_error'] = st.selectbox(
                            "On Error",
                            ['fail', 'retry', 'ignore'],
                            index=['fail', 'retry', 'ignore'].index(step.get('on_error', 'fail')),
                            key=f"on_error_{idx}"
                        )

                    with col2:
                        if step['on_error'] == 'retry':
                            step['retries'] = st.number_input(
                                "Retry count",
                                value=step.get('retries', 3),
                                min_value=1,
                                max_value=10,
                                key=f"retries_{idx}"
                            )

                    step['timeout'] = st.number_input(
                        "Timeout (milliseconds, 0 = no timeout)",
                        value=step.get('timeout', 0) or 0,
                        min_value=0,
                        key=f"timeout_{idx}"
                    )

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Save Step", key=f"save_{idx}", type="primary"):
                            st.session_state.current_step_index = None
                            st.success("Step saved!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_{idx}"):
                            st.session_state.current_step_index = None
                            st.rerun()
                    with col3:
                        if idx > 0:
                            if st.button("⬆️ Move Up", key=f"move_up_{idx}"):
                                st.session_state.workflow['steps'][idx], st.session_state.workflow['steps'][idx-1] = \
                                    st.session_state.workflow['steps'][idx-1], st.session_state.workflow['steps'][idx]
                                st.session_state.current_step_index = idx - 1
                                st.rerun()

st.divider()

# Preview and Export
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 YAML Preview")
    workflow_yaml = yaml.dump(st.session_state.workflow, default_flow_style=False, sort_keys=False)
    st.code(workflow_yaml, language='yaml', line_numbers=True)

    st.download_button(
        label="📥 Download YAML",
        data=workflow_yaml,
        file_name=f"{st.session_state.workflow['name'] or 'workflow'}.yaml",
        mime="text/yaml"
    )

with col2:
    st.subheader("🚀 Deploy Workflow")

    api_url = st.text_input(
        "API URL",
        value="http://localhost:8000/api/v1/workflows/",
        placeholder="Your workflow API endpoint"
    )

    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="Your API key"
    )

    if st.button("🚀 Deploy to API", type="primary"):
        if not api_key:
            st.error("Please enter your API key")
        else:
            try:
                response = requests.post(
                    api_url,
                    json={
                        "name": st.session_state.workflow['name'],
                        "company_id": st.session_state.workflow['company_id'],
                        "definition": workflow_yaml,
                        "description": st.session_state.workflow['description']
                    },
                    headers={"X-API-Key": api_key}
                )

                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Workflow deployed successfully!")
                    st.json(result)
                else:
                    st.error(f"❌ Deployment failed: {response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.divider()

    st.subheader("🧪 Test Workflow")

    test_inputs_yaml = st.text_area(
        "Test Inputs (YAML)",
        value=yaml.dump({inp['name']: f"<{inp['type']}>" for inp in st.session_state.workflow['inputs']}, default_flow_style=False),
        height=150
    )

    if st.button("▶️ Run Test"):
        st.info("Test execution feature coming soon...")
        # This would trigger a test execution via the API
