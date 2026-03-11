import streamlit as st
from streamlit.components.v1 import html

st.set_page_config(layout="wide")

html("""
<iframe src="http://127.0.0.1:9000" 
        style="width:100%; height:100vh; border:none;">
</iframe>
""", height=1000)
    