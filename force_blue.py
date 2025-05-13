import streamlit as st

# Force everything blue instead of red
st.markdown("""
<style>
/* Overriding with !important as well as browser inspection styles */
.stButton > button,
.stButton > button:hover,
.stButton > button[kind=primary],
.stButton > button[kind=primary]:hover,
button[kind=primary],
button[kind=primary]:hover,
button[data-baseweb="button"][kind="primary"],
button[data-baseweb="button"][kind="primary"]:hover,
.element-container button[kind=primary],
.element-container button[kind=primary]:hover {
    background-color: #4a6bf2 !important;
    border-color: #4a6bf2 !important;
    color: white !important;
}

/* Using inline style attribute */
button {
    background-color: #4a6bf2 !important;
    border-color: #4a6bf2 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Force Blue Test")

# Test with different button types
st.button("Standard Button")
st.button("Primary Button", type="primary")

# Test with a Form
with st.form("test_form"):
    st.write("Test Form")
    submit = st.form_submit_button("Submit Form", type="primary")

# Content type selector demo
st.subheader("Content Type Selector")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.button("🔗 URL", type="primary", use_container_width=True)