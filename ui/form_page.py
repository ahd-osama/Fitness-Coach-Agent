import streamlit as st
import pandas as pd
import sqlite3
import joblib

def get_weight_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 24.9:
        return "Normal"
    elif 25 <= bmi < 29.9:
        return "Overweight"
    else:
        return "Obese"

def form_page():
    st.title(f"👋 Welcome, {st.session_state.name}!")
    st.markdown("#### Fill out the form below to get a customized fitness plan.")   
    st.divider()
    
    st.markdown("#### 🧑‍💻 Your Information")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("🗓️ Age", min_value=20)  
        gender = st.selectbox("🧑 Gender", ["Male", "Female"])

    with col2:  
        weight = st.number_input("🏋️ Weight (kg)", min_value=40)  
        height_cm = st.number_input("📏 Height (cm)", min_value=100)  
        height_m = height_cm / 100
        bmi = weight / pow(height_m, 2)
        bmi = round(bmi, 2)
        weight_category = get_weight_category(bmi)
    st.divider()

    st.markdown("#### 🏥 Health Information")  
    col1, col2 = st.columns(2)
    with col1:
        cholesterol = st.number_input("🧪 Cholesterol (mg/dL)", min_value=100)    
        disease = st.selectbox("🩺 Disease", ["None", "Hypertension", "Diabetes", "Obesity"])
        blood_pressure = st.number_input("💓 Blood Pressure (mmHg)", min_value=60)
    with col2:
        glucose = st.number_input("🩸 Glucose (mg/dL)", min_value=70)  
        severity = st.selectbox("📉 Severity", ["Mild", "Moderate", "Severe"])
    st.divider()

    st.markdown("#### 💪 Fitness Profile")  
    col1, col2 = st.columns(2)
    with col1:
        fitness_goal = st.selectbox("🎯 Fitness Goal", ["Weight Loss", "Weight Gain"])
        fitness_type = st.selectbox("🏋️‍♀️ Fitness Type", ["Cardio Fitness", "Muscular Fitness"])  
    with col2:
        daily_caloric_intake = st.number_input("🍔 Daily Caloric Intake (kcal)", min_value=1200)  
        physical_activity_level = st.selectbox("🚶‍♂️‍➡️ Physical Activity Level", ["Sedentary", "Moderate", "Active"]) 
         
    st.divider()

    st.markdown("#### 🥗 Dietary Preferences & Restrictions")  
    col1, col2 = st.columns(2)
    with col1:
        dietary_restrictions = st.selectbox("🚫 Dietary Restrictions", ["None", "Low Sodium", "Low Sugar"])  
        allergies = st.selectbox("⚠️ Allergies", ["None", "Gluten", "Peanuts"])
    with col2:  
        preferred_cuisine = st.selectbox("🍴 Preferred Cuisine", ["Chinese", "Indian", "Italian", "Mexican"])  
    st.divider()

    st.markdown("#### 🏃🏻‍➡️ Activity & Diet Adherence")  
    col1, col2 = st.columns(2)
    with col1:
        weekly_exercise_hours = st.number_input("⏱️ Weekly Exercise Hours", min_value=0)  
        adherence_to_diet_plan = st.number_input("🍽️ Adherence to Diet Plan (%)", min_value=0, max_value=100)  
    with col2:
        dietary_nutrient_imbalance_score = st.number_input("⚖️ Dietary Nutrient Imbalance Score (0-5)", min_value=0.0, max_value=5.0)  

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])  

    with col2:
        if st.button("🔍 Generate Fitness Plan"):
            gym_features = encode_gym_features(age, height_m, weight, gender, bmi, disease, weight_category, fitness_goal, fitness_type)
            gym_prediction = gym_predict(gym_features)
            gym_int = int(gym_prediction[0])

            diet_features = encode_diet_features(
                gender, disease, severity, physical_activity_level,
                dietary_restrictions, allergies, preferred_cuisine,
                age, height_cm, weight, bmi, cholesterol, blood_pressure, glucose, daily_caloric_intake,
                weekly_exercise_hours, adherence_to_diet_plan, dietary_nutrient_imbalance_score)   
            diet_prediction = diet_predict(diet_features)
            diet_int = int(diet_prediction[0])

            conn = sqlite3.connect('../database/FitnessCoach.db', check_same_thread=False)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO plan (user_id, gym_rec, diet_rec) VALUES (?, ?, ?)", 
                       (st.session_state.user_id, gym_int, diet_int))
            cursor.execute("""
                        INSERT INTO User_info (
                        user_id, Age, Gender, Weight, height, BMI, level,
                        "Fitness Goal", "Fitness Type", Disease_Type, Severity, Physical_Activity_Level,
                        Daily_Caloric_Intake, Cholesterol, Blood_Pressure, Glucose,
                        Dietary_Restrictions, Allergies, Preferred_Cuisine,
                        Weekly_Exercise_Hours, Adherence_to_Diet_Plan, Dietary_Nutrient_Imbalance_Score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                        st.session_state.user_id, age, gender, weight, height_cm, bmi, weight_category,
                        fitness_goal, fitness_type, disease, severity, physical_activity_level,
                        daily_caloric_intake, cholesterol, blood_pressure, glucose,
                        dietary_restrictions, allergies, preferred_cuisine,
                        weekly_exercise_hours, adherence_to_diet_plan, dietary_nutrient_imbalance_score
                    ))
            conn.commit()
            conn.close()
            return True

def encode_gym_features(age, height, weight, gender, bmi, disease, weight_category, fitness_goal, fitness_type):
    gender_map = {"Female": 0, "Male": 1}
    disease_map = {"None": [0, 0], "Hypertension": [1, 0], "Diabetes": [0, 1], "Obesity": [0, 0]} 
    level_map = {"Normal": 0, "Obese": 1, "Overweight": 2, "Underweight": 3}
    fitness_goal_map = {"Weight Gain": 0, "Weight Loss": 1}
    fitness_type_map = {"Cardio Fitness": 0, "Muscular Fitness": 1}

    sex_encoded = gender_map[gender]
    hypertension_encoded, diabetes_encoded = disease_map[disease]
    level_encoded = level_map[weight_category]
    fitness_goal_encoded = fitness_goal_map[fitness_goal]
    fitness_type_encoded = fitness_type_map[fitness_type]

    gym_features = pd.DataFrame([{
        "Sex": sex_encoded,
        "Age": age,
        "Height": height,
        "Weight": weight,
        "Hypertension": hypertension_encoded,
        "Diabetes": diabetes_encoded,   
        "BMI": bmi,
        "Level": level_encoded,
        "Fitness Goal": fitness_goal_encoded,
        "Fitness Type": fitness_type_encoded     
    }])

    return gym_features

def encode_diet_features(
    gender, disease, severity, physical_activity_level,
    dietary_restrictions, allergies, preferred_cuisine,
    age, height_cm, weight, bmi, cholesterol, blood_pressure, glucose, daily_caloric_intake,
    weekly_exercise_hours, adherence_to_diet_plan, dietary_nutrient_imbalance_score):

    gender_encoder = {"Female": 0, "Male": 1}
    disease_encoder = {"Diabetes": 0, "Hypertension": 1, "Obesity": 2, "None": 3} 
    severity_encoder = {"Mild": 0, "Moderate": 1, "Severe": 2}
    physical_activity_encoder = {"Active": 0, "Moderate": 1, "Sedentary": 2}
    dietary_restrictions_encoder = {"Low Sodium": 0, "Low Sugar": 1, "None": 2}  
    allergies_encoder = {"Gluten": 0, "Peanuts": 1, "None": 2} 
    preferred_cuisine_encoder = {"Chinese": 0, "Indian": 1, "Italian": 2, "Mexican": 3}

    gender_encoded = gender_encoder[gender]
    disease_encoded = disease_encoder[disease]
    severity_encoded = severity_encoder[severity]
    physical_activity_encoded = physical_activity_encoder[physical_activity_level]
    dietary_restrictions_encoded = dietary_restrictions_encoder[dietary_restrictions]
    allergies_encoded = allergies_encoder[allergies]
    preferred_cuisine_encoded = preferred_cuisine_encoder[preferred_cuisine]

    diet_features = pd.DataFrame([{
        "Age": age,
        "Gender": gender_encoded,
        "Weight_kg": weight,
        "Height_cm": height_cm,
        "BMI": bmi,
        "Disease_Type": disease_encoded,   
        "Severity": severity_encoded,
        "Physical_Activity_Level": physical_activity_encoded,
        "Daily_Caloric_Intake": daily_caloric_intake,
        "Cholesterol_mg/dL": cholesterol,
        "Blood_Pressure_mmHg": blood_pressure,
        "Glucose_mg/dL": glucose,
        "Dietary_Restrictions": dietary_restrictions_encoded,
        "Allergies": allergies_encoded,
        "Preferred_Cuisine": preferred_cuisine_encoded,
        "Weekly_Exercise_Hours": weekly_exercise_hours,
        "Adherence_to_Diet_Plan": adherence_to_diet_plan,
        "Dietary_Nutrient_Imbalance_Score": dietary_nutrient_imbalance_score,  
    }])

    return diet_features

def gym_predict(gym_features):
    gym_model = joblib.load("../models/gym_model.pkl")
    prediction = gym_model.predict(gym_features)
    return prediction

def diet_predict(diet_features):
    diet_model = joblib.load("../models/diet_model.pkl")
    prediction = diet_model.predict(diet_features)
    return prediction
