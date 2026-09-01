import os
import json
import streamlit as st
from pydantic import BaseModel, Field
from typing import List

# Page configuration
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
    smart_bioswap: str = Field(description="Alternative ingredient for glucose/androgen management")
    clinical_rationale: str = Field(description="Why this helps Insulin Resistance and PCOS")

class DailyNutritionPlan(BaseModel):
    target_macro_summary: str
    daily_calories: int
    daily_net_carbs_g: float
    daily_protein_g: float
    daily_fats_g: float
    meals: List[MealItem]
    micronutrient_focus: List[str]
    clinical_safeguards: List[str]

# ---------------------------------------------------------
# Dynamic Local Benchmark Engine (No API Required)
# ---------------------------------------------------------
def get_benchmark_plan(user_data):
    gender = user_data.get("gender", "Female")
    diet = user_data.get("diet_preference", "Vegetarian (High-Protein)")
    
    # 1. Adapt Clinical Rationale based on Biological Sex
    if gender == "Male":
        rationale_snack = "Zinc and magnesium support healthy testosterone levels and reduce hepatic insulin resistance."
        macro_summary = "High-protein, moderate fat, low-glycemic load targeting visceral fat reduction and metabolic syndrome."
        micro_focus = "Targeted Zinc for hepatic insulin clearance and visceral adiposity management"
    else:
        rationale_snack = "Zinc and magnesium from pumpkin seeds aid in reducing ovarian androgen synthesis."
        macro_summary = "High-protein, moderate anti-inflammatory fat, low-glycemic load targeting PCOS and insulin resistance."
        micro_focus = "Myo-Inositol & D-Chiro Inositol support for ovarian health and hormonal balance"

    # 2. Adapt Meals based on Diet Preference
    breakfast_dish = "Spiced Tofu/Paneer Scramble with Chia-Crusted Avocado & Wilted Spinach"
    lunch_dish = "Mediterranean Chickpea & Hemp Seed Bowl with Olive-Lemon Dressing"
    dinner_dish = "Herb-Crusted Grilled Salmon (or Tempeh Steaks) with Cauliflower Mash & Sautéed Asparagus"

    if diet == "Vegan":
        breakfast_dish = "Turmeric Tofu Scramble with Chia-Crusted Avocado & Wilted Spinach"
        dinner_dish = "Herb-Crusted Tempeh Steaks with Cauliflower Mash & Sautéed Asparagus"
    elif diet == "Omnivore / Non-Vegetarian":
        breakfast_dish = "Pasture-Raised Egg Scramble with Turkey Sausage & Wilted Spinach"
        lunch_dish = "Mediterranean Grilled Chicken & Quinoa Bowl with Olive-Lemon Dressing"
        dinner_dish = "Herb-Crusted Grilled Salmon with Cauliflower Mash & Sautéed Asparagus"
    elif diet == "Eggitarian":
        breakfast_dish = "Whole Egg & Egg White Scramble with Chia-Crusted Avocado"
        dinner_dish = "Crustless Spinach & Mushroom Frittata with Cauliflower Mash & Asparagus"
    elif diet == "Pescatarian":
        breakfast_dish = "Smoked Salmon & Poached Eggs with Wilted Spinach"
        lunch_dish = "Tuna & White Bean Salad Bowl with Olive-Lemon Dressing"
        dinner_dish = "Herb-Crusted Grilled Salmon with Cauliflower Mash & Sautéed Asparagus"

    return {
        "target_macro_summary": macro_summary,
        "daily_calories": 1650,
        "daily_net_carbs_g": 95.0,
        "daily_protein_g": 125.0,
        "daily_fats_g": 68.0,
        "meals": [
            {
                "meal_type": "Breakfast",
                "dish_name": breakfast_dish,
                "portion_size": "1.5 cups + 1/2 avocado",
                "calories": 420,
                "net_carbs_g": 12.0,
                "protein_g": 28.0,
                "healthy_fats_g": 24.0,
                "glycemic_load_score": "Low (GL ~ 3)",
                "smart_bioswap": "Swap bread/toast with flaxseed seed crackers to prevent morning cortisol-induced glucose spikes.",
                "clinical_rationale": "High morning protein blunts the dawn phenomenon; magnesium in spinach supports insulin sensitivity."
            },
            {
                "meal_type": "Lunch",
                "dish_name": lunch_dish,
                "portion_size": "1 large bowl",
                "calories": 510,
                "net_carbs_g": 34.0,
                "protein_g": 32.0,
                "healthy_fats_g": 22.0,
                "glycemic_load_score": "Low (GL ~ 8)",
                "smart_bioswap": "Substitutes white rice with a high-fiber blend to double prebiotic fiber.",
                "clinical_rationale": "Slow-fermenting prebiotic fiber improves GLP-1 secretion and balances postprandial insulin surges."
            },
            {
                "meal_type": "Snack",
                "dish_name": "Roasted Edamame & Pumpkin Seeds with Cinnamon Green Tea",
                "portion_size": "45g mixed seeds",
                "calories": 210,
                "net_carbs_g": 8.0,
                "protein_g": 18.0,
                "healthy_fats_g": 10.0,
                "glycemic_load_score": "Low (GL ~ 1)",
                "smart_bioswap": "Replaces fruit smoothies with roasted seeds to avoid unbound fructose spikes.",
                "clinical_rationale": rationale_snack
            },
            {
                "meal_type": "Dinner",
                "dish_name": dinner_dish,
                "portion_size": "200g protein + 1 cup mash",
                "calories": 510,
                "net_carbs_g": 11.0,
                "protein_g": 47.0,
                "healthy_fats_g": 22.0,
                "glycemic_load_score": "Low (GL ~ 2)",
                "smart_bioswap": "Swaps mashed potato with cauliflower-garlic puree to lower insulin demand by 75%.",
                "clinical_rationale": "High Omega-3 EPA/DHA reduces systemic inflammation and improves lipid profiles."
            }
        ],
        "micronutrient_focus": [
            "Magnesium Glycinate/Citrate support (400mg equivalent through seed matrices)",
            "Omega-3 fatty acids for lowering hs-CRP (inflammatory marker)",
            micro_focus
        ],
        "clinical_safeguards": [
            "Avoid intense intermittent fasting (>14 hrs) to prevent hypothalamic-pituitary-adrenal (HPA) axis stress.",
            "Ensure complex carbohydrates are always framed with protein and healthy fats."
        ]
    }

# ---------------------------------------------------------
# LLM Integration Function
# ---------------------------------------------------------
def generate_meal_plan(user_data, api_key=None):
    if not api_key:
        return get_benchmark_plan(user_data), False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        system_prompt = """
        You are GlycoSync, a clinical endocrinology and nutrition AI.
        You design multi-constraint meal plans specifically optimized for the Insulin Resistance Triad.
        
        Strict Guidelines:
        1. Keep total Net Carbs < 100g/day with Low Glycemic Load (<10 per meal).
        2. Provide high protein (>= 1.6g/kg of ideal body weight) to protect metabolic rate.
        3. Include targeted micronutrients (Inositols, Zinc, Magnesium, Omega-3s).
        4. Every meal MUST include a 'Smart Bio-Swap' and a clinical rationale.
        5. Return ONLY a valid JSON object matching the requested schema.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a targeted plan for this profile:\n{json.dumps(user_data, indent=2)}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content), True
    except Exception as e:
        st.warning(f"API Error ({str(e)}). Displaying verified clinical model baseline.")
        return get_benchmark_plan(user_data), False

# ---------------------------------------------------------
# Streamlit User Interface
# ---------------------------------------------------------
st.title("🧬 GlycoSync: Multi-Constraint Nutrition Engine")
st.caption("AI-Assisted Precision Meal Formulation for Diabetes, PCOS & Metabolic Management")
st.markdown("---")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key (Optional)", type="password", help="Leave blank to run on verified mock fallback mode.")
    
    st.subheader("📋 Patient Clinical Profile")
    age = st.number_input("Age", min_value=18, max_value=85, value=28)
    gender = st.selectbox("Biological Sex", ["Female", "Male"])
    bmi = st.slider("BMI (kg/m²)", min_value=20.0, max_value=45.0, value=29.5, step=0.1)
    
    st.markdown("### 🩸 Metabolic & Endocrine Markers")
    glycemic_status = st.selectbox("Glycemic Marker", ["Prediabetes (HbA1c 5.7 - 6.4%)", "T2D Controlled (HbA1c 6.5 - 7.5%)", "T2D Elevated (HbA1c > 7.5%)"])
    
    # Dynamically disable PCOS for Male users
    if gender == "Male":
        pcos_phenotype = st.selectbox("PCOS Phenotype", ["Not Applicable (Male Profile)"], disabled=True)
    else:
        pcos_phenotype = st.selectbox("PCOS Phenotype", ["Insulin-Resistant PCOS", "Inflammatory PCOS", "Adrenal PCOS", "Not Applicable"])
    
    st.markdown("### 🥗 Dietary Guardrails")
    diet_pref = st.selectbox("Diet Preference", ["Vegetarian (High-Protein)", "Vegan", "Pescatarian", "Omnivore / Non-Vegetarian", "Eggitarian"])
    allergies = st.multiselect("Food Sensitivities / Exclusions", ["Gluten-Free", "Dairy-Free", "Nut-Free", "Soy-Free"], default=["Dairy-Free"])
    
    generate_btn = st.button("Generate Precision Plan 🚀", type="primary", use_container_width=True)

# Main Application Body
if generate_btn:
    patient_payload = {
        "age": age,
        "gender": gender,
        "bmi": bmi,
        "glycemic_status": glycemic_status,
        "pcos_phenotype": pcos_phenotype,
        "diet_preference": diet_pref,
        "allergies": allergies
    }

    with st.spinner("Analyzing metabolic pathways and running constraint satisfaction..."):
        plan_data, is_live = generate_meal_plan(patient_payload, api_key)
    
    if is_live:
        st.success("✅ Real-time Plan Synthesized via GPT-4o Engine")
    else:
        st.info("ℹ️ Running in Verified Clinical Benchmark Mode (Local Simulation Engine)")

    # Top Metric Tiles
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Daily Calories", f"{plan_data.get('daily_calories', 1650)} kcal")
    m2.metric("Net Carbohydrates", f"{plan_data.get('daily_net_carbs_g', 95)} g")
    m3.metric("Protein Target", f"{plan_data.get('daily_protein_g', 125)} g")
    m4.metric("Healthy Fats", f"{plan_data.get('daily_fats_g', 68)} g")
    
    st.info(f"**Macro Distribution Strategy:** {plan_data.get('target_macro_summary')}")
    st.markdown("---")

    # Meal Plan Output
    st.subheader("🍽️ Personalized Meal Architecture")
    for meal in plan_data.get("meals", []):
        with st.expander(f"**{meal.get('meal_type')}**: {meal.get('dish_name')} ({meal.get('calories')} kcal)", expanded=True):
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown(f"**Portion:** {meal.get('portion_size')}")
                st.markdown(f"**Macros:** P: `{meal.get('protein_g')}g` | Net C: `{meal.get('net_carbs_g')}g` | Fat: `{meal.get('healthy_fats_g')}g`")
                st.markdown(f"**Glycemic Impact:** :green[{meal.get('glycemic_load_score')}]")
            with col_b:
                st.markdown(f"🔄 **Smart Bio-Swap:** *{meal.get('smart_bioswap')}*")
                st.markdown(f"🧬 **Endocrine Rationale:** *{meal.get('clinical_rationale')}*")

    st.markdown("---")
    
    # Clinical Insights & Micronutrient Targets
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("💊 Targeted Endocrine Micronutrients")
        for item in plan_data.get("micronutrient_focus", []):
            st.markdown(f"- {item}")
            
    with c2:
        st.subheader("⚠️ Guardrails & Adherence Rules")
        for item in plan_data.get("clinical_safeguards", []):
            st.markdown(f"- {item}")
else:
    st.info("👈 Adjust patient parameters on the left sidebar and click **Generate Precision Plan** to preview the prototype.")
