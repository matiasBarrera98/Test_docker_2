import streamlit as st


st.set_page_config(page_title="Melanoma AI", page_icon="🔬", layout="wide")


url = "https://app.powerbi.com/reportEmbed?reportId=6a69df36-9fef-4026-8a7d-f08641184359&autoAuth=true&ctid=72fd0b5a-8a6a-4cff-89f6-bde961f7e250"

st.markdown("""
    <iframe title="Capstone Dashboard" width="100%" height="800" src="https://app.powerbi.com/reportEmbed?reportId=6a69df36-9fef-4026-8a7d-f08641184359&autoAuth=true&ctid=72fd0b5a-8a6a-4cff-89f6-bde961f7e250" frameborder="0" allowFullScreen="true"></iframe>
""", unsafe_allow_html=True)