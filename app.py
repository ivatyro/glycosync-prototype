# ---------------------------------------------------------
# LLM Integration Function (Powered by Free Groq API)
# ---------------------------------------------------------
def generate_meal_plan(user_data, api_key=None):
    if not api_key:
        return get_benchmark_plan(user_data), False

    try:
        from openai import OpenAI
        # Diverts the OpenAI library to use Groq's super-fast free inference endpoints
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        system_prompt = """
        You are GlycoSync, a clinical endocrinology and nutrition AI.
        Design multi-constraint meal plans specifically optimized for the Insulin Resistance Triad.
        
        Strict Guidelines:
        1. AGGRESSIVE VARIETY: You MUST completely change the actual dishes, ingredients, and protein sources based on the patient's specific Glycemic Marker (Prediabetes vs Controlled vs Elevated T2D), Age, Gender, and PCOS phenotype. 
        2. Culturally adapt dishes (e.g., South Indian variations) if the dietary preference allows. Strictly obey all allergy constraints (e.g., nut-free).
        3. Keep total Net Carbs < 100g/day. Adjust calories dynamically based on Age and BMI.
        4. Every meal MUST include a 'Smart Bio-Swap' and a clinical rationale perfectly tailored to their specific HbA1c and phenotype.
        5. Return ONLY a valid JSON object matching the requested schema exactly. Include 'simulated_target_met' key evaluating the protocol.
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Updated to the latest Groq model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a targeted plan for this profile:\n{json.dumps(user_data, indent=2)}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content), True
    except Exception as e:
        # This will now print the exact error message to the screen
        st.warning(f"Live API Error ({str(e)}). Seamlessly switching to local constraint engine.")
        return get_benchmark_plan(user_data), False
