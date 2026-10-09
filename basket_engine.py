from rule_engine import SchemeRuleEngine

class WelfareBasketEngine:
    def __init__(self, db_path="schemes.json"):
        self.rule_engine = SchemeRuleEngine(db_path)

    def generate_welfare_basket(self, user_profile: dict) -> dict:
        """
        Combines top eligible schemes across different categories 
        to maximize total financial/welfare impact without category collision.
        """
        matched_schemes = self.rule_engine.evaluate_profile(user_profile)
        
        selected_basket = []
        seen_categories = set()
        total_estimated_value = 0

        # Estimated values for basket calculation
        benefit_value_map = {
            "SCH_001": 50000,   # PM SVANidhi Loan
            "SCH_002": 500000,  # PM-JAY Health Cover
            "SCH_003": 315000,  # PM Vishwakarma
            "SCH_004": 6000,    # PM Kisan
            "SCH_005": 50000    # PM Mudra
        }

        for scheme in matched_schemes:
            if scheme.get("match_score", 0) < 50:
                continue

            category = scheme.get("category", "General")
            
            # Avoid duplicate categories to prevent policy collision
            if category not in seen_categories:
                seen_categories.add(category)
                scheme_id = scheme.get("id", "")
                est_val = benefit_value_map.get(scheme_id, 10000)
                
                selected_basket.append({
                    "id": scheme_id,
                    "name": scheme["name"],
                    "category": category,
                    "match_score": scheme["match_score"],
                    "benefit_summary": scheme["benefit_summary"],
                    "estimated_financial_value": est_val,
                    "official_source": scheme["official_source"]
                })
                total_estimated_value += est_val

        return {
            "basket_count": len(selected_basket),
            "total_stacked_benefit_value": total_estimated_value,
            "recommended_basket": selected_basket
        }


if __name__ == "__main__":
    basket_engine = WelfareBasketEngine()
    
    sample_user = {
        "age": 32,
        "annual_income": 120000,
        "occupation": "Street Vendor",
        "gender": "Male",
        "flags": {"has_bank_account": True, "is_street_vendor": True}
    }
    
    basket = basket_engine.generate_welfare_basket(sample_user)
    print("Optimized Basket Test Success:", basket["basket_count"], "schemes included.")