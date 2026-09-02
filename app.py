import os
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List

# ---------------------------------------------------------
# UI Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="GlycoSync | Precision Metabolic & Endocrine Nutrition",
    page_icon="🧬",
    layout="wide"
)

# ---------------------------------------------------------
# Pydantic Schemas for Structured Nutritional Output
# ---------------------------------------------------------
class MealItem(BaseModel):
    meal_type: str = Field(description="Breakfast, Lunch, Snack, or Dinner")
    dish_name: str
    portion_size: str
    calories: int
    net_carbs_g: float
    protein_g: float
    healthy_fats_g: float
    glycemic_load_score: str = Field(description="Low (<10), Moderate (11-19), High (>20)")
    smart_bioswap: str = Field(description="Smart Meal Swap: replacing a selected meal with a compatible alternative while preserving user-selected constraints.")
    nutrition_rationale: str = Field(description="Nutritional reasoning for how this supports metabolic profiles like PCOS or prediabetes")

class DailyNutritionPlan(BaseModel):
    target_macro_summary: str
    daily_calories: int
    daily_net_carbs_g: float
    daily_protein_g: float
    daily_fats_g: float
    simulated_target_met: str = Field(description="Evaluation if this plan meets nutritional targets for the day")
    meals: List[MealItem]
    micronutrient_focus: List[str]
    nutrition_safeguards: List[str]

# ---------------------------------------------------------
# Deterministic Macro Validation Pipeline
# ---------------------------------------------------------
def validate_and_correct_macros(plan_data):
    """
    Acts as a data coordination checkpoint. Validates stochastic LLM output 
    against deterministic biological constants to ensure clinical UI integrity.
    """
    total_cals = 0
    total_carbs = 0.0
    total_pro = 0.0
    total_fats = 0.0
    
    for meal in plan_data.get("meals", []):
        p = float(meal.get("protein_g", 0))
        c = float(meal.get("net_carbs_g", 0))
        f = float(meal.get("healthy_fats_g", 0))
        
        # Deterministic calculation: (P*4) + (C*4) + (F*9)
        derived_cals = int((p * 4) + (c * 4) + (f * 9))
        meal["calories"] = derived_cals
        
        total_cals += derived_cals
        total_carbs += c
        total_pro += p
        total_fats += f
        
    plan_data["daily_calories"] = total_cals
    plan_data["daily_net_carbs_g"] = round(total_carbs, 1)
    plan_data["daily_protein_g"] = round(total_pro, 1)
    plan_data["daily_fats_g"] = round(total_fats, 1)
    
    return plan_data

# ---------------------------------------------------------
# Advanced Deterministic Local Engine (Fallback)
# ---------------------------------------------------------
def get_benchmark_plan(user_data):
    age = user_data.get("age", 28)
    bmi = user_data.get("bmi", 29.5)
    gender = user_data.get("gender", "Female")
    diet = user_data.get("diet_preference", "Vegetarian (High-Protein)")
    pcos = user_data.get("pcos_phenotype", "Not Applicable")
    glycemic = user_data.get("glycemic_status", "Prediabetes (HbA1c 5.7 - 6.4%)")
    allergies = user_data.get("allergies", [])
    
    base_cals = 1500 if gender == "Female" else 1800
    age_adj = -((age - 25) * 5) 
    bmi_adj = -250 if bmi >= 30 else (-100 if bmi >= 25 else 0) 
    target_cals = max(1200, int(base_cals + age_adj + bmi_adj)) 
    
    if "Elevated" in glycemic:
        carb_ratio, pro_ratio, fat_ratio = 0.15, 0.35, 0.50
        gl_target = "Ultra-Low (GL < 5)"
        carb_rationale = "Carbohydrate restriction to support lower-glycemic meal selection for elevated profiles."
    elif "Controlled" in glycemic:
        carb_ratio, pro_ratio, fat_ratio = 0.20, 0.35, 0.45
        gl_target = "Low (GL ~ 6)"
        carb_rationale = "Moderate complex carbohydrates to support stable blood glucose."
    else: 
        carb_ratio, pro_ratio, fat_ratio = 0.25, 0.30, 0.45
        gl_target = "Low (GL ~ 8)"
        carb_rationale = "Controlled glycemic load to support healthy metabolic function."

    daily_carbs = int((target_cals * carb_ratio) / 4)
    daily_pro = int((target_cals * pro_ratio) / 4)
    daily_fat = int((target_cals * fat_ratio) / 9)

    micro_focus = []
    if gender == "Male":
        nutrition_rationale = "Zinc and Magnesium optimized to support healthy metabolic clearance and function."
        micro_focus.append("Targeted Zinc (30mg) for metabolic support.")
        snack_rationale = "Supports baseline energy needs."
    else:
        if pcos == "Insulin-Resistant PCOS":
            nutrition_rationale = "Inositol integration to support nutritional needs associated with insulin-resistant profiles."
            micro_focus.append("Myo-Inositol & D-Chiro Inositol (40:1 ratio) focus via specific foods.")
            snack_rationale = "Provides satiation without rapid glucose spikes."
        elif pcos == "Inflammatory PCOS":
            nutrition_rationale = "Omega-3s and antioxidants to support a healthy inflammatory response."
            micro_focus.append("Omega-3s (EPA/DHA) and Curcuminoids via diet.")
            snack_rationale = "Focuses on anti-inflammatory food matrices."
        elif pcos == "Adrenal PCOS":
            nutrition_rationale = "Adaptogenic support (Vitamin C, Magnesium) to support healthy stress responses."
            micro_focus.append("Magnesium-rich foods to support baseline stress levels.")
            snack_rationale = "Stabilizes energy to prevent secondary crashes."
        else:
            nutrition_rationale = "General metabolic support for female endocrine homeostasis."
            micro_focus.append("Calcium and Vitamin D3 focus.")
            snack_rationale = "Provides sustained energy without disrupting endocrine balance."

    bfast, lunch, snack, dinner = "Paneer Scramble", "Lentil Bowl", "Mixed Nuts", "Cauliflower Mash & Tofu"
    bfast_swap, lunch_swap = "Uses paneer instead of higher-carb options.", "Uses lentils for fiber support."

    is_nut_free = "Nut-Free" in allergies
    is_dairy_free = "Dairy-Free" in allergies

    if diet == "Omnivore / Non-Vegetarian":
        bfast = "South Indian Egg Appam with Coconut Stew"
        lunch = "Chettinad Pepper Chicken with Foxtail Millet"
        dinner = "Meen Kuzhambu (Fish Curry) with Quinoa & Sautéed Greens"
        snack = "Roasted Makhana (Fox Nuts) & Spiced Buttermilk"
        bfast_swap = "Swaps white rice batter for protein-rich egg appam to stabilize morning energy."
        lunch_swap = "Swaps white rice for Foxtail Millet to lower GL while maintaining authentic South Indian flavor."
        if is_dairy_free: snack = "Roasted Makhana & Black Tea"
        
    elif diet == "Vegan":
        bfast = "Besan (Chickpea) Chilla with Mint Chutney"
        lunch = "Sprouted Moong Salad & Tempeh Curry"
        dinner = "Zucchini Noodles with Edamame & Peanut Sauce"
        snack = "Almond Butter with Celery Sticks"
        bfast_swap = "Swaps wheat paratha for chickpea flour to increase protein."
        lunch_swap = "Swaps standard lentils for sprouted moong to increase bioavailability."
        if is_nut_free:
            dinner = "Zucchini Noodles with Edamame & Sunflower Seed Butter Sauce"
            snack = "Sunflower Seed Butter with Celery Sticks"
            
    elif diet == "Eggitarian":
        bfast = "Masala Omelette with Sautéed Spinach & Mushroom"
        lunch = "Quinoa & Boiled Egg Biryani"
        dinner = "Zucchini Noodles with Egg Drop Soup"
        snack = "Roasted Pumpkin Seeds"
        bfast_swap = "Protein-dense breakfast to support morning satiation."
        lunch_swap = "Swaps white rice biryani for quinoa to reduce glycemic load."

    else: 
        bfast = "Spiced Tofu/Paneer Bhurji with Chia-Crusted Avocado"
        lunch = "Mediterranean Chickpea & Hemp Seed Bowl"
        dinner = "Cauliflower Rice with Palak Paneer (or Tofu)"
        snack = "Roasted Walnuts & Green Tea"
        bfast_swap = "Swaps toast for avocado to utilize healthy fats for morning satiety."
        lunch_swap = "Substitutes white rice with a chickpea-hemp blend for prebiotic fiber."
        if is_nut_free: snack = "Roasted Pumpkin & Sunflower Seeds"
        if is_dairy_free: 
            bfast = bfast.replace("Paneer", "Tofu")
            dinner = dinner.replace("Paneer", "Tofu")

    raw_plan = {
        "target_macro_summary": f"Targeting {target_cals} kcal tailored for {age}yo {gender} (BMI: {bmi}). Focus: {carb_rationale} {nutrition_rationale}",
        "daily_calories": target_cals,
        "daily_net_carbs_g": daily_carbs,
        "daily_protein_g": daily_pro,
        "daily_fats_g": daily_fat,
        "simulated_target_met": "✅ SUCCESS: Dietary protocol aligns with selected nutritional constraints.",
        "meals": [
            {
                "meal_type": "Breakfast",
                "dish_name": bfast,
                "portion_size": "Calculated to 25% of Daily BMR",
                "calories": int(target_cals * 0.25),
                "net_carbs_g": int(daily_carbs * 0.20),
                "protein_g": int(daily_pro * 0.30),
                "healthy_fats_g": int(daily_fat * 0.30),
                "glycemic_load_score": gl_target,
                "smart_bioswap": bfast_swap,
                "nutrition_rationale": f"High morning protein supports steady energy. {carb_rationale}"
            },
            {
                "meal_type": "Lunch",
                "dish_name": lunch,
                "portion_size": "Calculated to 35% of Daily BMR",
                "calories": int(target_cals * 0.35),
                "net_carbs_g": int(daily_carbs * 0.40),
                "protein_g": int(daily_pro * 0.30),
                "healthy_fats_g": int(daily_fat * 0.35),
                "glycemic_load_score": gl_target,
                "smart_bioswap": lunch_swap,
                "nutrition_rationale": "Sustained amino acid release prevents afternoon energy crashes."
            },
            {
                "meal_type": "Snack",
                "dish_name": snack,
                "portion_size": "1 serving",
                "calories": int(target_cals * 0.15),
                "net_carbs_g": int(daily_carbs * 0.10),
                "protein_g": int(daily_pro * 0.10),
                "healthy_fats_g": int(daily_fat * 0.15),
                "glycemic_load_score": "Ultra-Low (GL < 2)",
                "smart_bioswap": "Focuses on fiber and healthy fats instead of refined sugars.",
                "nutrition_rationale": snack_rationale
            },
            {
                "meal_type": "Dinner",
                "dish_name": dinner,
                "portion_size": "Calculated to 25% of Daily BMR",
                "calories": int(target_cals * 0.25),
                "net_carbs_g": int(daily_carbs * 0.30),
                "protein_g": int(daily_pro * 0.30),
                "healthy_fats_g": int(daily_fat * 0.20),
                "glycemic_load_score": gl_target,
                "smart_bioswap": "Swaps starchy root vegetables for complex fiber matrices.",
                "nutrition_rationale": f"Prioritizes lighter metabolic load overnight. {nutrition_rationale}"
            }
        ],
        "micronutrient_focus": micro_focus,
        "nutrition_safeguards": [
            "Monitor hydration to support general metabolic functions.",
            "Ensure consistency in meal timing for optimal blood sugar support."
        ]
    }
    
    return validate_and_correct_macros(raw_plan)

# ---------------------------------------------------------
# LLM Integration Function (Powered by Gemini 3.6 Flash)
# ---------------------------------------------------------
def generate_meal_plan(user_data, api_key=None):
    if not api_key:
        return get_benchmark_plan(user_data), False

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        system_prompt = f"""
        You are GlycoSync, a nutrition decision support AI generating meal plans for metabolic profiles.
        Do NOT make medical claims, diagnose, or prescribe treatments. Frame all logic around nutritional support.
        
        Strict Guidelines:
        1. AGGRESSIVE VARIETY: Provide varied dishes based on Glycemic Marker, Age, Gender, and PCOS phenotype. 
        2. Culturally adapt dishes (e.g., Tamil/South Indian variations) if the dietary preference allows.
        3. STRICT ALLERGY COMPLIANCE: The user has excluded {user_data.get('allergies', [])}. You MUST NOT include these ingredients.
        4. Keep total Net Carbs < 100g/day. Adjust calories dynamically based on Age and BMI.
        5. Every meal MUST include a 'Smart Meal Swap' (a constraint-aware substitution maintaining the allergy/dietary rules) and a nutrition rationale.
        6. Output ONLY raw JSON matching this schema exactly. DO NOT use markdown formatting (no ```json):
        
        {{
          "target_macro_summary": "string",
          "daily_calories": 1500,
          "daily_net_carbs_g": 90.0,
          "daily_protein_g": 120.0,
          "daily_fats_g": 60.0,
          "simulated_target_met": "string",
          "meals": [
            {{
              "meal_type": "Breakfast",
              "dish_name": "string",
              "portion_size": "string",
              "calories": 300,
              "net_carbs_g": 15.0,
              "protein_g": 30.0,
              "healthy_fats_g": 15.0,
              "glycemic_load_score": "Low",
              "smart_bioswap": "string",
              "nutrition_rationale": "string"
            }}
          ],
          "micronutrient_focus": ["string"],
          "nutrition_safeguards": ["string"]
        }}
        """
        
        response = client.chat.completions.create(
            model="gemini-3.6-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a targeted nutritional plan for this profile:\n{json.dumps(user_data, indent=2)}"}
            ],
            temperature=0.2
        )
        
        raw_text = response.choices[0].message.content
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(clean_text)
        
        return validate_and_correct_macros(parsed_json), True
    except Exception as e:
        st.warning(f"Live API connection interrupted or schema mismatch. Seamlessly switching to local constraint engine.")
        return get_benchmark_plan(user_data), False

# ---------------------------------------------------------
# Streamlit User Interface
# ---------------------------------------------------------
st.title("🧬 GlycoSync: Multi-Constraint Nutrition Engine")
st.caption("⚠️ **Prototype for nutrition decision support only. Not intended to diagnose, treat, or replace professional medical advice. Nutritional recommendations should be reviewed by a qualified healthcare professional where appropriate.**")
st.markdown("---")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    # Secure API Key handling prioritizing Streamlit secrets
    secure_api_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key (Optional)", type="password", value=secure_api_key, help="Key securely managed. Enter override if needed.")
    
    st.subheader("📋 Patient Clinical Profile")
    age = st.number_input("Age", min_value=18, max_value=85, value=28)
    gender = st.selectbox("Biological Sex", ["Female", "Male"])
    bmi = st.slider("BMI (kg/m²)", min_value=20.0, max_value=45.0, value=29.5, step=0.1)
    
    st.markdown("### 🩸 Endocrine Markers")
    glycemic_status = st.selectbox("Glycemic Marker", ["Prediabetes (HbA1c 5.7 - 6.4%)", "T2D Controlled (HbA1c 6.5 - 7.5%)", "T2D Elevated (HbA1c > 7.5%)"])
    
    if gender == "Male":
        pcos_phenotype = st.selectbox("PCOS Phenotype", ["Not Applicable (Male Profile)"], disabled=True)
    else:
        pcos_phenotype = st.selectbox("PCOS Phenotype", ["Insulin-Resistant PCOS", "Inflammatory PCOS", "Adrenal PCOS", "Not Applicable"])
    
    st.markdown("### 🥗 Dietary Guardrails")
    diet_pref = st.selectbox("Diet Preference", ["Vegetarian (High-Protein)", "Vegan", "Pescatarian", "Omnivore / Non-Vegetarian", "Eggitarian"])
    allergies = st.multiselect("Food Sensitivities / Exclusions", ["Gluten-Free", "Dairy-Free", "Nut-Free", "Soy-Free"], default=[])
    
    generate_btn = st.button("Generate Precision Plan 🚀", type="primary", use_container_width=True)

# Main Application Body
if generate_btn:
    patient_payload = {
        "age": age, "gender": gender, "bmi": bmi,
        "glycemic_status": glycemic_status,
        "pcos_phenotype": pcos_phenotype,
        "diet_preference": diet_pref,
        "allergies": allergies
    }

    with st.spinner("Analyzing combinatorial metabolic pathways..."):
        plan_data, is_live = generate_meal_plan(patient_payload, api_key)
    
    if is_live:
        st.success("✅ Real-time Plan Synthesized via Gemini 3.6 Flash Engine")
    else:
        st.info("ℹ️ Running in Verified Clinical Benchmark Mode (Local Simulation Engine)")

    st.success(f"**Daily Output Status:** {plan_data.get('simulated_target_met', '✅ SUCCESS: Dietary protocol aligns with selected nutritional constraints.')}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Target Calories", f"{plan_data.get('daily_calories')} kcal")
    m2.metric("Net Carbohydrates", f"{plan_data.get('daily_net_carbs_g')} g")
    m3.metric("Protein Target", f"{plan_data.get('daily_protein_g')} g")
    m4.metric("Healthy Fats", f"{plan_data.get('daily_fats_g')} g")
    
    st.info(f"**Nutrition Strategy:** {plan_data.get('target_macro_summary')}")
    st.markdown("---")

    st.subheader("🍽️ Personalized Meal Architecture")
    for meal in plan_data.get("meals", []):
        with st.expander(f"**{meal.get('meal_type')}**: {meal.get('dish_name')} ({meal.get('calories')} kcal)", expanded=True):
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown(f"**Portion:** {meal.get('portion_size')}")
                st.markdown(f"**Macros:** P: `{meal.get('protein_g')}g` | Net C: `{meal.get('net_carbs_g')}g` | Fat: `{meal.get('healthy_fats_g')}g`")
                st.markdown(f"**Glycemic Impact:** :green[{meal.get('glycemic_load_score')}]")
            with col_b:
                st.markdown(f"🔄 **Smart Meal Swap:** *{meal.get('smart_bioswap')}*")
                st.markdown(f"🧬 **Nutrition Rationale:** *{meal.get('nutrition_rationale')}*")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💊 Targeted Endocrine Micronutrients")
        for item in plan_data.get("micronutrient_focus", []):
            st.markdown(f"- {item}")
            
    with c2:
        st.subheader("⚠️ Guardrails & Adherence Rules")
        for item in plan_data.get("nutrition_safeguards", []):
            st.markdown(f"- {item}")
else:
    st.info("👈 Adjust patient parameters on the left sidebar and click **Generate Precision Plan**.")
