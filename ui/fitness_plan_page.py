import streamlit as st
import joblib
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def recommendations(text):
    text = text.strip()

    if "Here are some important tips:-" in text:
        intro, tips = text.split("Here are some important tips:-", 1)
        intro = intro.strip()
        tips = tips.strip()

        intro_lines = [line.strip() for line in intro.split('.') if line.strip()]
        intro_bullets = [f"- {line}." for line in intro_lines]

        tips_lines = [line.strip() for line in tips.replace("\n", ".").split('.') if line.strip()]
        tips_bullets = [f"- {line}." for line in tips_lines]

        full_text = "\n".join(intro_bullets) + "\n\n**Here are some important tips:**\n" + "\n".join(tips_bullets)
    else:
        lines = [line.strip() for line in text.split('.') if line.strip()]
        full_text = "\n".join(f"- {line}." for line in lines)

    return full_text

def bullet_points(text):
    text = text.replace(", and ", ", ")
    text = text.replace(" and ", ", ")

    items = [item.strip().capitalize() for item in text.split(",") if item.strip()]
    
    return "\n".join(f"- {item}" for item in items)

def diet_section(diet_text):   
    sections = [section.strip() for section in diet_text.split(";") if section.strip()]
    
    emojis = {
        "Vegetables": "🥕",
        "Protein Intake": "🍗",
        "Juice": "🍹"
    }
    
    formatted = []
    for section in sections:
        if ":" in section:
            key, value = section.split(":", 1)
            key = key.strip()
            value = value.strip().strip("()")
            emoji = emojis.get(key, "")
            formatted.append(f"    - {emoji} **{key}**: {value}\n  ")
        else:
            formatted.append(f"    - {section}  ")
    
    return "\n".join(formatted)

def get_gym_prediction(gym_prediction):
    encoders = joblib.load("encoders/gym_encoders.pkl")  
    fitness_plan_encoder = encoders['Fitness Plan'] 
    fitness_plan = fitness_plan_encoder.inverse_transform([gym_prediction])[0]

    fitness_plan_sections = fitness_plan.split(" | ")
    exercises = fitness_plan_sections[0]
    diet = fitness_plan_sections[1]
    equipment = fitness_plan_sections[2]
    recommendation = fitness_plan_sections[3]

    return exercises, diet, equipment, recommendation

def get_diet_type(diet_prediction):
    encoders = joblib.load("encoders/diet_encoders.pkl") 
    encoder = encoders['Diet_Recommendation'] 
    diet_type = encoder.inverse_transform([diet_prediction])[0]
    return diet_type

def get_rec_from_db():
    conn = sqlite3.connect('database/FitnessCoach.db', check_same_thread=False)
    cursor = conn.cursor()

    user_id = st.session_state.user_id 

    cursor.execute("SELECT gym_rec, diet_rec FROM plan WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    gym_rec, diet_rec = result

    return gym_rec, diet_rec

def fitness_plan():
    gym_prediction, diet_prediction = get_rec_from_db()

    exercises, diet, equipment, recommendation = get_gym_prediction(gym_prediction)
    diet_type = get_diet_type(diet_prediction)

    st.title("🏅 Your Personalized Fitness Plan")
    st.divider()

    st.markdown(f"<h3 style='color:#4caf50;'>🥗 Recommended Diet: <span style='color:#2e7d32;'><strong>{diet_type}</strong></span></h3>", unsafe_allow_html=True)
    st.success(diet_section(diet))

    col1, col2 = st.columns([2, 2])
    with col1:
        st.markdown("<h3 style='color:#0764a3;'>🏃🏻‍♂️‍➡️ Recommended Workouts</h3>", unsafe_allow_html=True)
        st.info(bullet_points(exercises))

    with col2:
        st.markdown("<h3 style='color:#e31f0e;'>🏋️‍♂️ Equipment Required</h3>", unsafe_allow_html=True)
        st.error(bullet_points(equipment))

    st.markdown("<h3 style='color:#db613b;'>💡 General Advice</h3>", unsafe_allow_html=True)
    st.warning(recommendations(recommendation))

def calculate_target_weight(height_cm, current_weight, fitness_goal):
    height_m = height_cm / 100
    current_bmi = current_weight / (height_m ** 2)

    if fitness_goal == "Weight Gain":
        if current_bmi < 18.5:
            target_bmi = 21.5
        elif current_bmi < 24.9:
            target_bmi = 24.9  
        else:
            return None, "You're above the healthy range. Weight gain is not suitable."

    elif fitness_goal == "Weight Loss":
        if current_bmi <= 18.5:
            return None, "You're already underweight. Weight loss is not recommended."
    
        if current_bmi > 25:
            target_bmi = 21.5
        else:
            target_bmi = 20
        
        if target_bmi >= current_bmi:
            return None, "You're already in a healthy range. Weight loss is not recommended."

    target_weight = round(target_bmi * (height_m ** 2), 1)
    return target_weight, None

def progress_tracking():
    st.title("📈 **Track Your Progress**")
    st.divider()
    conn = sqlite3.connect("database/FitnessCoach.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("SELECT height, Weight, \"Fitness Goal\" FROM User_info WHERE user_id = ?", (st.session_state.user_id,))
    user_info = cursor.fetchone()
    user_height, current_weight, fitness_goal = user_info

    target_weight, warning = calculate_target_weight(user_height, current_weight, fitness_goal)

    if warning:
        st.success(warning)
        progress_ratio = 1.0
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Current Weight: {current_weight} kg")
        with col2:
            st.success(f"🎯 Target Weight: {target_weight} kg")

        if fitness_goal == "Weight Loss":
            if current_weight <= target_weight:
                    progress_ratio = 1.0
            else:
                 start_weight = current_weight * 1.2
                 progress_ratio = (start_weight - current_weight) / (start_weight - target_weight)

        elif fitness_goal == "Weight Gain":
            if current_weight >= target_weight:
                progress_ratio = 1.0
            else:
                start_weight = current_weight * 0.8
                progress_ratio = (current_weight - start_weight) / (target_weight - start_weight)
                progress_ratio = max(0.0, min(progress_ratio, 1.0))


    col1, col2 = st.columns(2)
    with col1:
        st.markdown("###### Progress Toward Target Weight:")
        st.progress(progress_ratio)

    st.divider()

    st.subheader("Weight Update:")
    with st.form("weight_update"):
        new_weight = st.number_input(f"Enter new weight (kg):", min_value=40)
        update_date = st.date_input("Select the date of this update")
        submit = st.form_submit_button("Update")

    if submit:
        cursor.execute("UPDATE User_info SET Weight = ? WHERE user_id = ?", (new_weight, st.session_state.user_id))
        
        cursor.execute(
            "INSERT INTO Progress (user_id, previous_weight, new_weight, date) VALUES (?, ?, ?, ?)",
            (st.session_state.user_id, current_weight, new_weight, update_date.strftime("%d-%m-%Y"))
        )  
        conn.commit()

        st.success("Weight updated successfully!")
        st.rerun()

    st.divider()

    st.subheader("📈 Progress History")
    cursor.execute(
        "SELECT previous_weight, new_weight, date FROM progress WHERE user_id = ? ORDER BY date",
        (st.session_state.user_id,)
    )
    progress_data = cursor.fetchall()

    weight_timeline = []

    if progress_data:
        df = pd.DataFrame(progress_data, columns=["Previous Weight", "New Weight", "Date"])
        st.dataframe(df)

        df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
        start_date = df["Date"].iloc[0] - timedelta(days=1)
        weight_timeline.append((start_date, df["Previous Weight"].iloc[0]))

        for _, row in df.iterrows():
            weight_timeline.append((row["Date"], row["New Weight"]))

    else:
        st.info("No progress records yet. Start tracking your weight to see a detailed history!")
        weight_timeline.append((datetime.today(), current_weight))

    timeline_df = pd.DataFrame(weight_timeline, columns=["Date", "Weight"])
    timeline_df["Date"] = pd.to_datetime(timeline_df["Date"], dayfirst=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📉 Weight Change Over Time")
        
        import matplotlib.dates as mdates

        fig, ax = plt.subplots()

        ax.plot(timeline_df["Date"], timeline_df["Weight"], marker='o', linestyle='-')

        ax.set_xlabel("Date")
        ax.set_ylabel("Weight (kg)")
        ax.set_title("Weight Progress")
        ax.grid(True)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y')) 
        ax.xaxis.set_major_locator(mdates.AutoDateLocator()) 

        fig.autofmt_xdate(rotation=30)

        min_w = timeline_df["Weight"].min()
        max_w = timeline_df["Weight"].max()
        padding = 2
        ax.set_ylim(min_w - padding, max_w + padding)

        st.pyplot(fig)

    
