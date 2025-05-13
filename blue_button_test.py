import streamlit as st

# Inject custom CSS
st.markdown("""
<style>
/* Target the button element directly */
.stButton button {
    background-color: #4a6bf2 !important;
    border-color: #4a6bf2 !important;
    color: white !important;
}

/* Make sure hover state is also blue */
.stButton button:hover {
    background-color: #3a5be2 !important;
    border-color: #3a5be2 !important;
    color: white !important;
}

/* Target every possible button class */
button, 
button[kind=primary], 
button[data-baseweb=button],
button[data-baseweb=button][kind=primary],
.element-container button {
    background-color: #4a6bf2 !important;
    border-color: #4a6bf2 !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Blue Button Test")
st.write("This test app forces blue buttons with direct CSS overrides.")

# Show different button types for testing
standard = st.button("Standard Button")
primary = st.button("Primary Button", type="primary")
secondary = st.button("Secondary Button", type="secondary")

# Show a form with a button
with st.form("test_form"):
    st.text_input("Test input")
    submit = st.form_submit_button("Submit", type="primary")

st.write("If any buttons above are still red, please let me know!")