import os
import json
import streamlit as st
from ai_engine import GeminiAIEngine
from rule_engine import SchemeRuleEngine
from basket_engine import WelfareBasketEngine

# 1. Page Setup & Configuration
st.set_page_config(
    page_title="SchemeMatch AI - Public Welfare Engine",
    page_icon="🏛️",
    layout="wide"
)

# 2. Engine Initialization (Cached for performance)
@st.cache_resource
def load_backend_engines():
    ai = GeminiAIEngine()
    rule = SchemeRuleEngine()
    basket = WelfareBasketEngine()
    return ai, rule, basket

try:
    ai_engine, rule_engine, basket_engine = load_backend_engines()
except Exception as e:
    st.error(f"Failed to initialize backend engines: {e}")
    st.stop()

# Header Banner
st.title("🏛️ SchemeMatch AI")
st.caption("AI-Powered Zero-Hallucination Welfare Scheme Matching & Document Verification")

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs(["🎯 Scheme Matcher", "🧺 Welfare Basket Stacking", "🛡️ Pre-Rejection Shield"])

# ---------------------------------------------------------
# TAB 1: SCHEME MATCHER
# ---------------------------------------------------------
with tab1:
    st.subheader("1. Vernacular Profile Intake")
    voice_text = st.text_area(
        "Enter conversational prompt / voice transcript (Hindi, Hinglish, or English):",
        value="Namaste, mera naam Ramesh hai. Main Kanpur me rehne wala street vendor hu, saal ke lagbhag 1 lakh 20 hazar kamata hu aur meri umar 32 saal hai.",
        height=90
    )

    if st.button("✨ Extract Profile with AI", type="secondary"):
        with st.spinner("Extracting profile via Gemini..."):
            try:
                extracted = ai_engine.extract_profile_from_text(voice_text)
                st.session_state["extracted_profile"] = extracted
                st.success("Profile fields extracted successfully!")
            except Exception as e:
                st.error(f"Extraction failed: {e}")

    st.divider()
    st.subheader("2. Profile Details & Scheme Matching")

    # Load session profile state or fallback to defaults
    prof = st.session_state.get("extracted_profile", {
        "age": 32,
        "annual_income": 120000,
        "occupation": "Street Vendor",
        "gender": "Male",
        "flags": {"has_bank_account": True, "is_street_vendor": True}
    })

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        age = st.number_input("Age", min_value=0, max_value=100, value=int(prof.get("age", 30)))
    with col2:
        income = st.number_input("Annual Income (₹)", min_value=0, value=int(prof.get("annual_income", 100000)))
    with col3:
        occupation = st.selectbox(
            "Occupation", 
            ["Street Vendor", "Farmer", "Artisan / Craftsman", "Unemployed", "Student", "Other"],
            index=0 if prof.get("occupation") == "Street Vendor" else 5
        )
    with col4:
        gender = st.selectbox("Gender", ["Male", "Female", "All"], index=0)

    st.write("**Verification Flags:**")
    c1, c2 = st.columns(2)
    with c1:
        has_bank = st.checkbox("Has Bank Account", value=prof.get("flags", {}).get("has_bank_account", True))
    with c2:
        is_vendor = st.checkbox("Is Street Vendor", value=prof.get("flags", {}).get("is_street_vendor", True))

    active_profile = {
        "age": age,
        "annual_income": income,
        "occupation": occupation,
        "gender": gender,
        "flags": {
            "has_bank_account": has_bank,
            "is_street_vendor": is_vendor
        }
    }

    if st.button("🚀 Match Schemes", type="primary"):
        matches = rule_engine.evaluate_profile(active_profile)
        st.session_state["matched_schemes"] = matches
        st.session_state["active_profile"] = active_profile

    if "matched_schemes" in st.session_state:
        st.divider()
        st.subheader("Matched Welfare Schemes")
        matches = st.session_state["matched_schemes"]

        if not matches:
            st.warning("No eligible schemes found matching these criteria.")
        else:
            for match in matches:
                with st.expander(f"**{match['name']}** — Match Score: {match['match_score']}%", expanded=True):
                    st.write(f"**Category:** {match['category']}")
                    st.write(f"**Summary:** {match['benefit_summary']}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Eligible Criteria:**")
                        for reason in match['matched_reasons']:
                            st.write(f"✅ {reason}")
                    with col_b:
                        if match['missing_info']:
                            st.write("**Pending Verification:**")
                            for missing in match['missing_info']:
                                st.write(f"⚠️ {missing}")
                                
                    st.link_button("Visit Official Portal", match['official_source'])

# ---------------------------------------------------------
# TAB 2: WELFARE BASKET STACKING
# ---------------------------------------------------------
with tab2:
    st.subheader("🧺 Optimized Welfare Stacking Engine")
    st.write("Calculates non-conflicting schemes across distinct welfare domains to maximize cumulative financial benefit.")

    current_profile = st.session_state.get("active_profile", {
        "age": 32, "annual_income": 120000, "occupation": "Street Vendor", "gender": "Male",
        "flags": {"has_bank_account": True, "is_street_vendor": True}
    })

    if st.button("⚡ Generate Optimized Welfare Basket"):
        basket_data = basket_engine.generate_welfare_basket(current_profile)
        st.session_state["basket_data"] = basket_data

    if "basket_data" in st.session_state:
        basket = st.session_state["basket_data"]
        
        st.metric(
            label="Total Estimated Stacked Benefit", 
            value=f"₹{basket['total_stacked_benefit_value']:,}"
        )
        st.write(f"**Recommended Non-Conflicting Basket ({basket['basket_count']} Schemes):**")

        for item in basket["recommended_basket"]:
            st.info(
                f"**[{item['category']}] {item['name']}**\n\n"
                f"Est. Value: ₹{item['estimated_financial_value']:,} | Match: {item['match_score']}%"
            )

# ---------------------------------------------------------
# TAB 3: PRE-REJECTION SHIELD (VISION OCR)
# ---------------------------------------------------------
with tab3:
    st.subheader("🛡️ Pre-Rejection Shield (Vision Verification)")
    st.write("Scan physical identity and income documents for common errors before official submission.")

    doc_type = st.selectbox("Expected Document Type", ["Aadhaar Card", "Voter ID", "Vendor Certificate", "Bank Passbook"])
    uploaded_file = st.file_uploader("Upload Document Photo", type=["jpg", "jpeg", "png"])

    if uploaded_file and st.button("🔍 Verify Document Quality & Details"):
        temp_filename = f"temp_{uploaded_file.name}"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Scanning document with Gemini Vision..."):
            try:
                shield_result = ai_engine.verify_document_shield(temp_filename, doc_type)
                st.json(shield_result)
            except Exception as e:
                st.error(f"Document analysis failed: {e}")
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)