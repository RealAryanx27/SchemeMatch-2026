import json
import os

class SchemeRuleEngine:
    def __init__(self, db_path="schemes.json"):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file '{db_path}' not found.")
        with open(db_path, "r", encoding="utf-8") as f:
            self.schemes = json.load(f)

    def evaluate_profile(self, user_profile: dict) -> list:
        """
        Evaluates user profile against schemes.
        Returns Top ranked schemes with matched reasons, missing information, and sources.
        """
        results = []

        user_age = int(user_profile.get("age", 0))
        user_income = float(user_profile.get("annual_income", 0))
        user_occupation = user_profile.get("occupation", "Other").title()
        user_gender = user_profile.get("gender", "All").title()
        user_extra_flags = user_profile.get("flags", {})

        for scheme in self.schemes:
            score = 0
            matched_reasons = []
            missing_info = []

            # 1. Occupation Check (40 points)
            if any(occ.lower() in user_occupation.lower() for occ in scheme["target_occupations"]):
                score += 40
                matched_reasons.append(f"Occupation '{user_occupation}' matches target group ({', '.join(scheme['target_occupations'])})")
            else:
                missing_info.append(f"Scheme specifically targets: {', '.join(scheme['target_occupations'])}")

            # 2. Income Check (30 points)
            if user_income <= scheme["max_income"]:
                score += 30
                matched_reasons.append(f"Annual income ₹{user_income:,.0f} is within eligible limit of ₹{scheme['max_income']:,.0f}")
            else:
                missing_info.append(f"Annual income exceeds scheme threshold of ₹{scheme['max_income']:,.0f}")

            # 3. Age Limit Check (20 points)
            if scheme["min_age"] <= user_age <= scheme["max_age"]:
                score += 20
                matched_reasons.append(f"Age {user_age} falls within allowed range ({scheme['min_age']}–{scheme['max_age']} years)")
            else:
                missing_info.append(f"Requires age between {scheme['min_age']} and {scheme['max_age']} years")

            # 4. Gender Check (10 points)
            if "All" in scheme["allowed_genders"] or user_gender in scheme["allowed_genders"]:
                score += 10
                matched_reasons.append(f"Gender criteria met ({user_gender})")

            # 5. Missing Field Triggers
            for field in scheme.get("required_fields", []):
                if field not in user_extra_flags:
                    missing_info.append(f"Pending verification for: '{field.replace('_', ' ').title()}'")

            results.append({
                "id": scheme["id"],
                "name": scheme["name"],
                "category": scheme["category"],
                "match_score": score,
                "benefit_summary": scheme["benefit_summary"],
                "official_source": scheme["official_source"],
                "matched_reasons": matched_reasons,
                "missing_info": missing_info,
                "required_documents": scheme["required_documents"]
            })

        # Sort descending by match_score and return Top 3
        ranked_schemes = sorted(results, key=lambda x: x["match_score"], reverse=True)
        return ranked_schemes[:3]


# Quick standalone test
if __name__ == "__main__":
    engine = SchemeRuleEngine()
    sample_user = {
        "age": 28,
        "annual_income": 120000,
        "occupation": "Street Vendor",
        "gender": "Male",
        "flags": {"has_bank_account": True}
    }
    top_matches = engine.evaluate_profile(sample_user)
    print("--- TOP 3 RECOMMENDED SCHEMES ---")
    for i, match in enumerate(top_matches, 1):
        print(f"\n{i}. {match['name']} (Match Score: {match['match_score']}%)")
        print(f"   Source: {match['official_source']}")
        print(f"   Reasons: {', '.join(match['matched_reasons'])}")
        print(f"   Missing Info: {', '.join(match['missing_info'])}")