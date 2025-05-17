import streamlit as st
from streamlit_option_menu import option_menu
from authentication import authentication_page
from form_page import form_page
from fitness_plan_page import fitness_plan, progress_tracking
from database_page import database

st.set_page_config(page_title="Fitness Coach Agent", layout='wide')

with st.sidebar:
    selected = option_menu(
        menu_title="Fitness Coach Agent",  
        options=["My Fitness Plan", "Database"],  
        icons=["calendar-check-fill", "database"], 
        menu_icon="heart-pulse",  
        default_index=0,
        styles={
            "nav-link-selected": {
                "background-color": "#0a7cc9",  
            },
        }
    )
    if 'user_id' in st.session_state:
        with st.expander(f"👤\u00A0\u00A0\u00A0\u00A0{st.session_state.name}"):
            if st.button("Log Out", use_container_width=True):
                st.session_state.clear()
                st.session_state.page = "auth"
                st.rerun()

if "page" not in st.session_state:
    st.session_state.page = "auth"  

if selected == "My Fitness Plan":
    if st.session_state.page == "auth":
        authentication_page()

    elif st.session_state.page == "form_page":
        submitted = form_page() 
        if submitted: 
            st.session_state.page = "fitness_page"
            st.rerun()

    elif st.session_state.page == "fitness_page":
        fitness_plan()
        progress_tracking()

elif selected == "Database":
    database()