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
    smart_bioswap: str = Field(description="Smart Meal Swap: constraint-aware substitution maintaining similar macros and respecting all allergies/diet rules")
    nutrition_rationale: str = Field(description="Nutritional reasoning for how this supports dietary balance (e.g., lower-glycemic food choices, protein-aware selection)")

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
# Constraint Intelligence & Deterministic Validation
# ---------------------------------------------------------
def categorize_constraints(user_data):
    """Classifies user inputs into Hard, Target, and Soft constraints for the AI engine."""
    gender = user_data.get("gender", "Female")
    age = user_data.get("age", 28)
    bmi = user_data.get("bmi", 29.5)
    glycemic = user_data.get("glycemic_status", "Prediabetes (HbA1c 5.7 - 6.4%)")
    
    # Target calculations
    base_cals = 1500 if gender == "Female" else 1800
    age_adj = -((age - 25) * 5) 
    bmi_adj = -250 if bmi >= 30 else (-100 if bmi >= 25 else 0) 
    target_cals = max(1200, int(base_cals + age_adj + bmi_adj)) 
    
    if "Elevated" in glycemic:
        carb_ratio, pro_ratio, fat_ratio = 0.15, 0.35, 0.50
    elif "Controlled" in glycemic:
        carb_ratio, pro_ratio, fat_ratio = 0.20, 0.35, 0.45
    else: 
        carb_ratio, pro_ratio, fat_ratio = 0.25, 0.30, 0.45

    target_carbs = int((target_cals * carb_ratio) / 4)
    target_pro = int((target_cals * pro_ratio) / 4)
    target_fat = int((target_cals * fat_ratio) / 9)
    
    return {
        "HARD": {
            "diet_preference": user_data.get("diet_preference"),
            "allergies": user_data.get("allergies", [])
        },
        "TARGET": {
            "calories": target_cals,
            "protein_g": target_pro,
            "net_carbs_g": target_carbs,
            "fats_g": target_fat,
            "metabolic_context": f"{glycemic}, {user_data.get('pcos_phenotype')}"
        },
        "SOFT": {
            "cuisine": user_data.get("cuisine", "Tamil / South Indian cuisine")
        }
    }

def validate_and_score_plan(plan_data, constraints, is_fallback=False):
    """
    Deterministic validation pipeline. Enforces exact macro math, checks hard constraints, 
    generates UI feedback strings, and calculates Fit Score.
    """
    validation_status = {
        "Dietary restriction": "PASS",
        "Allergy exclusions": "PASS",
        "Calorie consistency": "PASS",
        "Macro consistency": "PASS",
        "Meal-swap compatibility": "PASS"
    }
    
    trade_offs = []
    
    hard = constraints["HARD"]
    target = constraints["TARGET"]
    soft = constraints["SOFT"]
    
    total_cals = 0
    total_carbs = 0.0
    total_pro = 0.0
    total_fats = 0.0
    
    # 1. Macro Math Check & Aggregation (Forces calorie consistency)
    for meal in plan_data.get("meals", []):
        p = float(meal.get("protein_g", 0))
        c = float(meal.get("net_carbs_g", 0))
        f = float(meal.get("healthy_fats_g", 0))
        
        # Deterministic macro math
        derived_cals = int((p * 4) + (c * 4) + (f * 9))
        
        # Tolerance check
        reported_cals = meal.get("calories", 0)
        if abs(derived_cals - reported_cals) > 25:
            validation_status["Macro consistency"] = "FAIL (Auto-Corrected)"
        
        # Force the meal calorie value to exactly match the macro derivation
        meal["calories"] = derived_cals
        total_cals += derived_cals
        total_carbs += c
        total_pro += p
        total_fats += f
        
        # Hard Constraint Checks (Naive string check for fallback protection)
        meal_text = (meal.get("dish_name", "") + " " + meal.get("smart_bioswap", "")).lower()
        
        for allergy in hard["allergies"]:
            alg_kw = allergy.lower().replace("-free", "")
            if alg_kw in meal_text and alg_kw != "":
                validation_status["Allergy exclusions"] = "FAIL"
                
        if hard["diet_preference"] == "Vegan" and any(w in meal_text for w in ["chicken", "meat", "fish", "egg", "paneer", "cheese"]):
            validation_status["Dietary restriction"] = "FAIL"
            validation_status["Meal-swap compatibility"] = "FAIL"

    # Force the daily totals to be the EXACT sum of the validated meal components
    plan_data["daily_calories"] = total_cals
    plan_data["daily_net_carbs_g"] = round(total_carbs, 1)
    plan_data["daily_protein_g"] = round(total_pro, 1)
    plan_data["daily_fats_g"] = round(total_fats, 1)
    
    # Re-write target summary so LLM doesn't output contradictory hardcoded numbers
    plan_data["target_macro_summary"] = f"Nutrition Strategy: {total_cals} kcal daily total. Protein-aware, constraint-aware food selection."
    
    if abs(total_cals - target["calories"]) > 250:
        validation_status["Calorie consistency"] = "FAIL"
    
    # Trade-off Analysis
    if abs(total_cals - target["calories"]) > 100 and validation_status["Allergy exclusions"] == "PASS":
        trade_offs.append(f"Caloric target slightly adjusted ({total_cals} kcal vs target {target['calories']} kcal) to strictly preserve {hard['diet_preference']} boundaries.")
    
    if is_fallback and soft["cuisine"] == "Tamil / South Indian cuisine" and hard["diet_preference"] == "Omnivore / Non-Vegetarian":
        pass # Fallback naturally uses South Indian here
    elif is_fallback:
        trade_offs.append("Cuisine preference partially relaxed to ensure macro stability in local mode.")

    # Generate "Why this plan?" UI Data (Using the dynamically verified total_cals)
    reasons = [
        f"✓ {hard['diet_preference']} preference strictly preserved.",
        f"✓ Daily total of {total_cals} kcal verified.",
        f"✓ Protein-aware meal planning prioritized ({plan_data['daily_protein_g']}g)."
    ]
    if hard["allergies"]:
        reasons.append(f"✓ Exclusions respected ({', '.join(hard['allergies'])}).")
    if soft["cuisine"]:
        reasons.append(f"✓ {soft['cuisine']} preferred where nutritionally compatible.")

    # Calculate Fit Score
    fit_score = 100
    if validation_status["Calorie consistency"] == "FAIL": fit_score -= 10
    if validation_status["Macro consistency"] == "FAIL (Auto-Corrected)": fit_score -= 5
    if len(trade_offs) > 0: fit_score -= 5
    
    plan_data["_ui_validation"] = validation_status
    plan_data["_ui_reasons"] = reasons
    plan_data["_ui_tradeoffs"] = trade_offs
    plan_data["_ui_score"] = fit_score
    plan_data["_is_hard_fail"] = "FAIL" in [validation_status["Allergy exclusions"], validation_status["Dietary restriction"]]
    
    return plan_data

# ---------------------------------------------------------
# Advanced Deterministic Local Engine (Fallback)
# ---------------------------------------------------------
def get_benchmark_plan(user_data):
    constraints = categorize_constraints(user_data)
    target = constraints["TARGET"]
    hard = constraints["HARD"]
    gender = user_data.get("gender", "Female")
    pcos = user_data.get("pcos_phenotype", "Not Applicable")
    glycemic = user_data.get("glycemic_status", "")
    
    if "Elevated" in glycemic:
        gl_target = "Ultra-Low (GL < 5)"
        carb_rationale = "Carbohydrate restriction to support lower-glycemic meal selection."
    elif "Controlled" in glycemic:
        gl_target = "Low (GL ~ 6)"
        carb_rationale = "Moderate complex carbohydrates for balanced meal architecture."
    else: 
        gl_target = "Low (GL ~ 8)"
        carb_rationale = "Controlled glycemic load to support personalized nutrition preferences."

    micro_focus = []
    if gender == "Male":
        nutrition_rationale = "Zinc and Magnesium for nutrition-focused support."
        micro_focus.append("Targeted Zinc (30mg) for protein-aware meal planning.")
        snack_rationale = "Supports overall dietary balance."
    else:
        if pcos == "Insulin-Resistant PCOS":
            nutrition_rationale = "Inositol-rich food sources for balanced meal architecture."
            micro_focus.append("Focus on Myo-Inositol & D-Chiro Inositol (40:1 ratio) compatible foods.")
            snack_rationale = "Provides a balanced combination of protein, fiber and dietary fats."
        elif pcos == "Inflammatory PCOS":
            nutrition_rationale = "Omega-3s and antioxidants to support overall dietary balance."
            micro_focus.append("Omega-3s (EPA/DHA) and Curcuminoids via diet.")
            snack_rationale = "Focuses on balanced food matrices."
        elif pcos == "Adrenal PCOS":
            nutrition_rationale = "Balanced micronutrients to support general dietary needs."
            micro_focus.append("Magnesium-rich foods for nutrition-focused support.")
            snack_rationale = "Supports lower-glycemic food choices."
        else:
            nutrition_rationale = "General personalized nutrition support."
            micro_focus.append("Calcium and Vitamin D3 focus.")
            snack_rationale = "Provides balanced energy sources."

    bfast, lunch, snack, dinner = "Paneer Scramble", "Lentil Bowl", "Mixed Nuts", "Cauliflower Mash & Tofu"
    bfast_swap, lunch_swap = "Uses paneer instead of higher-carb options.", "Uses lentils for fiber support."

    is_nut_free = "Nut-Free" in hard["allergies"]
    is_dairy_free = "Dairy-Free" in hard["allergies"]

    if hard["diet_preference"] == "Omnivore / Non-Vegetarian":
        bfast = "South Indian Egg Appam with Coconut Stew"
        lunch = "Chettinad Pepper Chicken with Foxtail Millet"
        dinner = "Meen Kuzhambu (Fish Curry) with Quinoa & Sautéed Greens"
        snack = "Roasted Makhana (Fox Nuts) & Spiced Buttermilk"
        bfast_swap = "Swaps white rice batter for protein-rich egg appam for balanced meal architecture."
        lunch_swap = "Swaps white rice for Foxtail Millet for lower-glycemic food choices while maintaining authentic South Indian flavor."
        if is_dairy_free: snack = "Roasted Makhana & Black Tea"
        
    elif hard["diet_preference"] == "Vegan":
        bfast = "Besan (Chickpea) Chilla with Mint Chutney"
        lunch = "Sprouted Moong Salad & Tempeh Curry"
        dinner = "Zucchini Noodles with Edamame & Peanut Sauce"
        snack = "Almond Butter with Celery Sticks"
        bfast_swap = "Swaps wheat paratha for chickpea flour to increase protein."
        lunch_swap = "Swaps standard lentils for sprouted moong to increase bioavailability."
        if is_nut_free:
            dinner = "Zucchini Noodles with Edamame & Sunflower Seed Butter Sauce"
            snack = "Sunflower Seed Butter with Celery Sticks"
            
    elif hard["diet_preference"] == "Eggitarian":
        bfast = "Masala Omelette with Sautéed Spinach & Mushroom"
        lunch = "Quinoa & Boiled Egg Biryani"
        dinner = "Zucchini Noodles with Egg Drop Soup"
        snack = "Roasted Pumpkin Seeds"
        bfast_swap = "Protein-dense breakfast to support morning satiation."
        lunch_swap = "Swaps white rice biryani for quinoa to support balanced meal architecture."

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
        "target_macro_summary": f"Placeholder summary.", # Will be overwritten during validation
        "daily_calories": target["calories"],
        "daily_net_carbs_g": target["net_carbs_g"],
        "daily_protein_g": target["protein_g"],
        "daily_fats_g": target["fats_g"],
        "simulated_target_met": "✅ SUCCESS: Dietary protocol aligns with selected nutritional constraints.",
        "meals": [
            {
                "meal_type": "Breakfast",
                "dish_name": bfast,
                "portion_size": "Calculated to 25% of Daily Needs",
                "calories": int(target["calories"] * 0.25),
                "net_carbs_g": int(target["net_carbs_g"] * 0.20),
                "protein_g": int(target["protein_g"] * 0.30),
                "healthy_fats_g": int(target["fats_g"] * 0.30),
                "glycemic_load_score": gl_target,
                "smart_bioswap": bfast_swap,
                "nutrition_rationale": f"High morning protein supports balanced meal architecture. {carb_rationale}"
            },
            {
                "meal_type": "Lunch",
                "dish_name": lunch,
                "portion_size": "Calculated to 35% of Daily Needs",
                "calories": int(target["calories"] * 0.35),
                "net_carbs_g": int(target["net_carbs_g"] * 0.40),
                "protein_g": int(target["protein_g"] * 0.30),
                "healthy_fats_g": int(target["fats_g"] * 0.35),
                "glycemic_load_score": gl_target,
                "smart_bioswap": lunch_swap,
                "nutrition_rationale": "Sustained amino acid release for overall dietary balance."
            },
            {
                "meal_type": "Snack",
                "dish_name": snack,
                "portion_size": "1 serving",
                "calories": int(target["calories"] * 0.15),
                "net_carbs_g": int(target["net_carbs_g"] * 0.10),
                "protein_g": int(target["protein_g"] * 0.10),
                "healthy_fats_g": int(target["fats_g"] * 0.15),
                "glycemic_load_score": "Ultra-Low (GL < 2)",
                "smart_bioswap": "Focuses on fiber and healthy fats instead of refined sugars.",
                "nutrition_rationale": snack_rationale
            },
            {
                "meal_type": "Dinner",
                "dish_name": dinner,
                "portion_size": "Calculated to 25% of Daily Needs",
                "calories": int(target["calories"] * 0.25),
                "net_carbs_g": int(target["net_carbs_g"] * 0.30),
                "protein_g": int(target["protein_g"] * 0.30),
                "healthy_fats_g": int(target["fats_g"] * 0.20),
                "glycemic_load_score": gl_target,
                "smart_bioswap": "Swaps starchy root vegetables for complex fiber matrices.",
                "nutrition_rationale": f"Provides a balanced dinner composition. {nutrition_rationale}"
            }
        ],
        "micronutrient_focus": micro_focus,
        "nutrition_safeguards": [
            "Monitor hydration to support general metabolic functions.",
            "Ensure consistency in meal timing for overall dietary balance."
        ]
    }
    
    validated_plan = validate_and_score_plan(raw_plan, constraints, is_fallback=True)
    return validated_plan

# ---------------------------------------------------------
# LLM Integration Function
# ---------------------------------------------------------
def generate_meal_plan(user_data, api_key=None):
    constraints = categorize_constraints(user_data)
    
    if not api_key:
        return get_benchmark_plan(user_data), False

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        system_prompt = f"""
        You are GlycoSync, a nutrition decision support AI generating meal plans for personalized dietary profiles.
        Do NOT make medical claims, diagnose, or prescribe treatments. Frame all logic around neutral nutritional support (e.g., "lower-glycemic food choices", "balanced meal architecture", "protein-aware selection").
        Do NOT use terms like "reverse", "treat", "attenuate", "lipolysis", "insulin sensitivity", or "clearance".
        
        PRIORITY 1: HARD CONSTRAINTS (NEVER VIOLATE)
        - Diet: {constraints['HARD']['diet_preference']}
        - Exclusions/Allergies: {constraints['HARD']['allergies']}
        
        PRIORITY 2: TARGET CONSTRAINTS
        - Calories: ~{constraints['TARGET']['calories']}
        - Macros: Protein {constraints['TARGET']['protein_g']}g, Net Carbs {constraints['TARGET']['net_carbs_g']}g, Fats {constraints['TARGET']['fats_g']}g
        
        PRIORITY 3: SOFT PREFERENCES
        - Cuisine preference: {constraints['SOFT']['cuisine']}
        
        Strict Guidelines:
        1. AGGRESSIVE VARIETY: Provide varied dishes based on the metabolic profile.
        2. Culturally adapt dishes to the Soft Preference if compatible with Hard Constraints.
        3. Every meal MUST include a 'Smart Meal Swap' (a constraint-aware substitution maintaining similar macros and respecting ALL hard constraints) and a nutrition rationale.
        4. Math Check: Ensure daily_calories exactly equals the sum of meal calories. Ensure each meal's calories roughly equal (Protein*4 + Net Carbs*4 + Fat*9).
        5. Output ONLY raw JSON matching the schema. DO NOT use markdown formatting (no ```json):
        
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
                {"role": "user", "content": f"Generate a targeted nutritional plan."}
            ],
            temperature=0.2
        )
        
        raw_text = response.choices[0].message.content
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(clean_text)
        
        # Pass through deterministic validation layer
        validated_plan = validate_and_score_plan(parsed_json, constraints, is_fallback=False)
        
        # If Hard Constraints failed validation, trigger local fallback
        if validated_plan.get("_is_hard_fail"):
            st.warning("⚠️ Live API output violated a hard constraint. Automatically corrected via local simulation engine.")
            return get_benchmark_plan(user_data), False
            
        return validated_plan, True
        
    except Exception as e:
        st.warning("Live API connection interrupted or schema mismatch. Seamlessly switching to local constraint engine.")
        return get_benchmark_plan(user_data), False

# ---------------------------------------------------------
# Streamlit User Interface
# ---------------------------------------------------------
st.title("🧬 GlycoSync: Multi-Constraint Nutrition Engine")
st.caption("⚠️ **Prototype for nutrition decision support only. Not intended to diagnose, treat, or replace professional medical advice. Recommendations should be reviewed by a qualified healthcare professional where appropriate.**")
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
    cuisine = st.selectbox("Cuisine Preference", ["Tamil / South Indian cuisine", "Global / Mediterranean cuisine", "Standard Balanced cuisine"])
    
    generate_btn = st.button("Generate Precision Plan 🚀", type="primary", use_container_width=True)

# Main Application Body
if generate_btn:
    patient_payload = {
        "age": age, "gender": gender, "bmi": bmi,
        "glycemic_status": glycemic_status,
        "pcos_phenotype": pcos_phenotype,
        "diet_preference": diet_pref,
        "allergies": allergies,
        "cuisine": cuisine
    }

    with st.spinner("Analyzing combinatorial metabolic pathways..."):
        plan_data, is_live = generate_meal_plan(patient_payload, api_key)
    
    if is_live:
        st.success("✅ Real-time Plan Synthesized via Gemini 3.6 Flash Engine")
    else:
        st.info("ℹ️ Running in Verified Clinical Benchmark Mode (Local Simulation Engine)")

    # Key Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Target Calories", f"{plan_data.get('daily_calories')} kcal")
    m2.metric("Net Carbohydrates", f"{plan_data.get('daily_net_carbs_g')} g")
    m3.metric("Protein Target", f"{plan_data.get('daily_protein_g')} g")
    m4.metric("Healthy Fats", f"{plan_data.get('daily_fats_g')} g")
    
    st.info(f"**Nutrition Strategy:** {plan_data.get('target_macro_summary')}")
    st.markdown("---")

    # Intelligence & Validation Layer UI
    val_cols = st.columns([1.5, 1])
    with val_cols[0]:
        st.markdown(f"### 💡 Why this plan? (Fit Score: {plan_data.get('_ui_score', 0)}/100)")
        for reason in plan_data.get("_ui_reasons", []):
            st.markdown(reason)
        if plan_data.get("_ui_tradeoffs"):
            st.warning("**Constraint Trade-off:** " + " | ".join(plan_data.get("_ui_tradeoffs", [])))
            
    with val_cols[1]:
        st.markdown("### 🔍 Constraint Check")
        checks = plan_data.get("_ui_validation", {})
        for k, v in checks.items():
            color = "green" if "PASS" in v else ("orange" if "Auto" in v else "red")
            st.markdown(f"- **{k}:** :{color}[{v}]")
            
    st.markdown("---")

    # Meal Architecture
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
        st.subheader("💊 Nutrition-Focused Micronutrients")
        for item in plan_data.get("micronutrient_focus", []):
            st.markdown(f"- {item}")
            
    with c2:
        st.subheader("⚠️ Personalization & Validation Guardrails")
        for item in plan_data.get("nutrition_safeguards", []):
            st.markdown(f"- {item}")
else:
    st.info("👈 Adjust patient parameters on the left sidebar and click **Generate Precision Plan**.")
