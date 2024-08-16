import streamlit as st

st.title("User Information Form")

with st.form(key='user_info_form'):
    email = st.text_input("Email")
    phone_number = st.text_input("Phone Number")
    submit_button = st.form_submit_button(label='Submit')

if submit_button:
    st.success(f"Submitted successfully! Email: {email}, Phone Number: {phone_number}")