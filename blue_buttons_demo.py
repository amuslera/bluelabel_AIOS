import streamlit as st

# Configure the page
st.set_page_config(
    page_title="Blue Buttons Demo",
    layout="wide"
)

# Apply custom CSS with stronger selectors
css = """
/* Override ALL red buttons to use blue instead */
button[kind="primary"],
button[data-baseweb="button"][kind="primary"] {
    background-color: #4a6bf2 !important;
    border-color: #4a6bf2 !important;
}

button[kind="primary"]:hover,
button[data-baseweb="button"][kind="primary"]:hover {
    background-color: #3a5be2 !important;
    border-color: #3a5be2 !important;
}

/* Make Streamlit tabs use blue */
.st-emotion-cache-6qob1r.eczjsme3,
.st-ae.st-af.st-ag.st-ah.st-ai.st-aj.st-bq.st-bp.st-ce {
    background-color: #4a6bf2 !important;
    color: white !important;
}

/* Make the tab indicator blue */
.st-emotion-cache-1n76uvr.eczjsme4,
.st-bv.st-bp.st-ce {
    background-color: #4a6bf2 !important;
}

/* Override radio buttons to use blue */
.st-emotion-cache-1inwz65,
.st-bs.st-ee.st-eb.st-bp.st-ce.st-e8 {
    color: #4a6bf2 !important;
}

/* Apply blue to all progress bars */
.stProgress .st-emotion-cache-17z6hbz,
.stProgress > div > div > div > div {
    background-color: #4a6bf2 !important;
}
"""

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Title
st.title("Button Color Testing")

# Test different button styles
st.subheader("Button Types")
col1, col2, col3 = st.columns(3)

with col1:
    st.button("Standard Button")
    
with col2:
    st.button("Primary Button", type="primary")
    
with col3:
    st.button("Secondary Button", type="secondary")

# Test tabs
st.subheader("Tabs")
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1:
    st.write("Content in Tab 1")
    
with tab2:
    st.write("Content in Tab 2")
    
with tab3:
    st.write("Content in Tab 3")

# Test form with buttons
st.subheader("Form with Buttons")
with st.form("test_form"):
    st.text_input("Test Input")
    submit = st.form_submit_button("Submit", type="primary")
    cancel = st.form_submit_button("Cancel")

# Test radio buttons
st.subheader("Radio Buttons")
radio = st.radio("Select an option", ["Option 1", "Option 2", "Option 3"])

# Test progress bar
st.subheader("Progress Bar")
progress = st.progress(75)

# Test multiple columns with buttons
st.subheader("Content Type Selector")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.button("🔗 URL", type="primary", use_container_width=True)
    
with col2:
    st.button("📝 Text", use_container_width=True)
    
with col3:
    st.button("📄 PDF", use_container_width=True)
    
with col4:
    st.button("🔊 Audio", use_container_width=True)
    
with col5:
    st.button("📱 Social", use_container_width=True)