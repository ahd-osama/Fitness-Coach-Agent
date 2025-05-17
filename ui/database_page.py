import streamlit as st
import pandas as pd
import sqlite3

def database(): 
    conn = sqlite3.connect("../database/FitnessCoach.db", check_same_thread=False)

    st.title("📊 Database")

    table = st.selectbox("Choose a table to view:", ["plan", "User", "User_info", "progress"])

    query = f"SELECT * FROM {table}"
    df = pd.read_sql_query(query, conn)
    df.reset_index(drop=True, inplace=True)

    st.subheader(f"`{table}` Table")
    st.dataframe(df)


