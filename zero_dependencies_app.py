import streamlit as st

st.set_page_config(
    page_title="Zero Dependencies App",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Zero Dependencies Test App")
st.write("This app has zero dependencies on any other code.")

# Simple sidebar
st.sidebar.title("Navigation")
options = ["Home", "About", "Contact"]
selection = st.sidebar.radio("Go to", options)

if selection == "Home":
    st.header("Home")
    st.write("Welcome to the home page!")
elif selection == "About":
    st.header("About")
    st.write("This is a test app with zero dependencies.")
else:
    st.header("Contact")
    st.write("Contact us at: example@example.com")

# Simple form
st.header("Test Form")
name = st.text_input("Name")
email = st.text_input("Email")
if st.button("Submit"):
    st.success(f"Thanks, {name}!")