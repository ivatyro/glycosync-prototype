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
    smart_bioswap: str = Field(description="Alternative ingredient for glucose/androgen management")
    clinical_rationale: str = Field(description="Why this helps Insulin Resistance and PCOS")

class DailyNutritionPlan(BaseModel):
    target_macro_summary: str
    daily_calories: int
    daily_net_carbs_g: float
    daily_protein_g: float
    daily_fats_g: float
    simulated_target_met: str = Field(description="Evaluation if this plan meets clinical targets for the day")
    meals: List[MealItem]
    micronutrient_focus: List[str]
    clinical_safeguards: List[str]

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
        carb_rationale = "Severe carbohydrate restriction to blunt acute hyperglycemic spikes in elevated T2D."
    elif "Controlled" in glycemic:
        carb_ratio, pro_ratio, fat_ratio = 0.20, 0.35, 0.45
        gl_target = "Low (GL ~ 6)"
        carb_rationale = "Moderate complex carbohydrates to maintain stable HbA1c in controlled T2D."
    else: 
        carb_ratio, pro_ratio, fat_ratio = 0.25, 0.30, 0.45
        gl_target = "Low (GL ~ 8)"
        carb_rationale = "Controlled glycemic load to restore insulin sensitivity and reverse prediabetes."

    daily_carbs = int((target_cals * carb_ratio) / 4)
    daily_pro = int((target_cals * pro_ratio) / 4)
    daily_fat = int((target_cals * fat_ratio) / 9)

    micro_focus = []
    if gender == "Male":
        endo_rationale = "Zinc and Magnesium optimized to improve hepatic insulin clearance and protect testosterone from aromatization."
        micro_focus.append("Targeted Zinc (30mg) for visceral adiposity and hepatic insulin sensitivity.")
        snack_rationale = "Supports liver function and prevents metabolic syndrome progression."
    else:
        if pcos == "Insulin-Resistant PCOS":
            endo_rationale = "Inositol integration to sensitize ovarian insulin receptors and lower circulating androgens."
            micro_focus.append("Myo-Inositol & D-Chiro Inositol (40:1 ratio) for ovarian health.")
            snack_rationale = "Lowers insulin to prevent ovarian theca cells from overproducing testosterone."
        elif pcos == "Inflammatory PCOS":
            endo_rationale = "High-dose Omega-3s and antioxidants to reduce systemic hs-CRP and soothe inflamed follicles."
            micro_focus.append("High-dose Omega-3s (EPA/DHA) and Curcuminoids for inflammatory phenotype management.")
            snack_rationale = "Directly targets systemic inflammation pathways suppressing ovulation."
        elif pcos == "Adrenal PCOS":
            endo_rationale = "Adaptogenic support (Vitamin C, Magnesium) to blunt DHEA-S production and regulate HPA-axis stress."
            micro_focus.append("Magnesium Glycinate and Ashwagandha to regulate cortisol/DHEA-S spikes.")
            snack_rationale = "Stabilizes blood sugar to prevent secondary cortisol spikes from hypoglycemia."
        else:
            endo_rationale = "General metabolic support for female endocrine homeostasis."
            micro_focus.append("Calcium and Vitamin D3 for bone density and baseline metabolic rate.")
            snack_rationale = "Provides sustained energy without disrupting endocrine balance."

    bfast, lunch, snack, dinner = "Paneer Scramble", "Lentil Bowl", "Mixed Nuts", "Cauliflower Mash & Tofu"
    bfast_swap, lunch_swap = "Uses paneer instead of carbs.", "Uses lentils for fiber."

    is_nut_free = "Nut-Free" in allergies
    is_dairy_free = "Dairy-Free" in allergies

    if diet == "Omnivore / Non-Vegetarian":
        bfast = "South Indian Egg Appam with Coconut Stew"
        lunch = "Chettinad Pepper Chicken with Foxtail Millet"
        dinner = "Meen Kuzhambu (Fish Curry) with Quinoa & Sautéed Greens"
        snack = "Roasted Makhana (Fox Nuts) & Spiced Buttermilk"
        bfast_swap = "Swaps white rice batter for protein-rich egg appam to stabilize morning glucose."
        lunch_swap = "Swaps white rice for Foxtail Millet to lower GL while maintaining authentic South Indian flavor."
        if is_dairy_free: snack = "Roasted Makhana & Black Tea"
        
    elif diet == "Vegan":
        bfast = "Besan (Chickpea) Chilla with Mint Chutney"
        lunch = "Sprouted Moong Salad & Tempeh Curry"
        dinner = "Zucchini Noodles with Edamame & Peanut Sauce"
        snack = "Almond Butter with Celery Sticks"
        bfast_swap = "Swaps wheat paratha for chickpea flour to double protein."
        lunch_swap = "Swaps standard lentils for sprouted moong to increase bioavailability."
        if is_nut_free:
            dinner = "Zucchini Noodles with Edamame & Sunflower Seed Butter Sauce"
            snack = "Sunflower Seed Butter with Celery Sticks"
            
    elif diet == "Eggitarian":
        bfast = "Masala Omelette with Sautéed Spinach & Mushroom"
        lunch = "Quinoa & Boiled Egg Biryani"
        dinner = "Zucchini Noodles with Egg Drop Soup"
        snack = "Roasted Pumpkin Seeds"
        bfast_swap = "High protein breakfast to blunt dawn phenomenon."
        lunch_swap = "Swaps white rice biryani for quinoa to reduce glycemic load by 40%."

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

    return {
        "target_macro_summary": f"Targeting {target_cals} kcal tailored for {age}yo {gender} (BMI: {bmi}). Focus: {carb_rationale} {endo_rationale}",
        "daily_calories": target_cals,
        "daily_net_carbs_g": daily_carbs,
        "daily_protein_g": daily_pro,
        "daily_fats_g": daily_fat,
        "simulated_target_met": "✅ SUCCESS: Dietary protocol perfectly aligns with daily clinical targets.",
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
                "clinical_rationale": f"High morning protein blunts the dawn phenomenon. {carb_rationale}"
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
                "clinical_rationale": "Sustained amino acid release prevents afternoon insulin crashes."
            },
            {
                "meal_type": "Snack",
                "dish_name": snack,
                "portion_size": "1 clinical serving",
                "calories": int(target_cals * 0.15),
                "net_carbs_g": int(daily_carbs * 0.10),
                "protein_g": int(daily_pro * 0.10),
                "healthy_fats_g": int(daily_fat * 0.15),
                "glycemic_load_score": "Ultra-Low (GL < 2)",
                "smart_bioswap": "Avoids unbound fructose to protect hepatic glucose clearance.",
                "clinical_rationale": snack_rationale
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
                "clinical_rationale": f"Prioritizes metabolic clearing overnight. {endo_rationale}"
            }
        ],
        "micronutrient_focus": micro_focus,
        "clinical_safeguards": [
            "Monitor continuous glucose to ensure avoidance of nocturnal hypoglycemia.",
            "Maintain hydration to support renal clearance of metabolic byproducts."
        ]
    }

# ---------------------------------------------------------
# LLM Integration Function (Powered by Gemini 2.5 Flash)
# ---------------------------------------------------------
def generate_meal_plan(user_data, api_key=None):
    if not api_key:
        return get_benchmark_plan(user_data), False

    try:
        from openai import OpenAI
        # Routes the OpenAI library directly to Google's Gemini endpoint
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        system_prompt = """
        You are GlycoSync, a clinical endocrinology and nutrition AI.
        Design multi-constraint meal plans specifically optimized for the Insulin Resistance Triad.
        
        Strict Guidelines:
        1. AGGRESSIVE VARIETY: Completely change dishes, ingredients, and protein sources based on Glycemic Marker, Age, Gender, and PCOS phenotype. 
        2. Culturally adapt dishes (e.g., South Indian variations) if the dietary preference allows. Strictly obey allergy constraints.
        3. Keep total Net Carbs < 100g/day. Adjust calories dynamically based on Age and BMI.
        4. Every meal MUST include a 'Smart Bio-Swap' and a clinical rationale.
        5. Output ONLY raw JSON matching this schema exactly. DO NOT use markdown formatting (no ```json):
        
        {
          "target_macro_summary": "string",
          "daily_calories": 1500,
          "daily_net_carbs_g": 90.0,
          "daily_protein_g": 120.0,
          "daily_fats_g": 60.0,
          "simulated_target_met": "string",
          "meals": [
            {
              "meal_type": "Breakfast",
              "dish_name": "string",
              "portion_size": "string",
              "calories": 300,
              "net_carbs_g": 15.0,
              "protein_g": 30.0,
              "healthy_fats_g": 15.0,
              "glycemic_load_score": "Low",
              "smart_bioswap": "string",
              "clinical_rationale": "string"
            }
          ],
          "micronutrient_focus": ["string"],
          "clinical_safeguards": ["string"]
        }
        """
        
        response = client.chat.completions.create(
            model="gemini-2.5-flash", # Updated to the active, supported Gemini model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a targeted plan for this profile:\n{json.dumps(user_data, indent=2)}"}
            ],
            temperature=0.2
        )
        
        raw_text = response.choices[0].message.content
        clean_text = raw_text.replace("
