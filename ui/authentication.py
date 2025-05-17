import streamlit as st
import sqlite3
import hashlib

conn = sqlite3.connect('/Users/ahdosama/Downloads/fitness_coach_agent/database/FitnessCoach.db', check_same_thread=False)
cursor = conn.cursor()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(name, username, password):
    try:
        hashed_pw = hash_password(password)
        cursor.execute("INSERT INTO User (Name, Username, Password) VALUES (?, ?, ?)", 
                       (name, username, hashed_pw))
        conn.commit()

        cursor.execute("SELECT User_ID FROM User WHERE Username = ?", (username,))
        user_id = cursor.fetchone()[0]

        st.session_state.user_id = user_id
        st.session_state.name = name

        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."

def login_user(username, password):
    hashed_pw = hash_password(password)
    cursor.execute("SELECT User_ID, Name FROM User WHERE Username = ? AND Password = ?", 
                   (username, hashed_pw))
    result = cursor.fetchone()
    if result:
        st.session_state.user_id = result[0]  
        st.session_state.name = result[1]
        return True  
    else:
        return False 

def has_plan(user_id):
    cursor.execute("SELECT 1 FROM plan WHERE user_id = ?", (user_id,))
    return (cursor.fetchone() is not None)

def show_signup_form():
    st.title("Sign Up")
    name = st.text_input("Name", key="signup_name")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")

    if st.button("Sign Up", use_container_width=True):
        if not name or not username or not password:
            st.error("All fields are required.")
        else:
            success, message = signup_user(name, username, password)
            if success:
                st.success(message)
                st.session_state.page = "form_page"  
                st.rerun()
            else:
                st.error(message)

def show_login_form():
    st.title("Log In")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log In", use_container_width=True):
        if not username or not password:
            st.warning("Please fill in both fields.")
        else:
            user = login_user(username, password)
            if user:
                if has_plan(st.session_state.user_id):
                    st.session_state.page = "fitness_page"
                else:
                    st.session_state.page = "form_page"

                st.rerun()
            else:
                st.error("Incorrect username or password.")

def authentication_page():
    st.markdown("<h1 style='text-align: center; color: #0764a3;'>🏃🏻‍♂️‍➡️ Fitness Coach Agent</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Sign Up", "Log In"])

        with tab1:
            show_signup_form()

        with tab2:
            show_login_form()
