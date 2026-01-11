"""
Tariff Estimation Module

Analyzes component materials and provides detailed tariff estimates,
HS code classifications, and AI-powered trade insights.

Usage:
    from tariff_estimation import estimate_tariffs
    
    # From pipeline report
    tariff_report = estimate_tariffs(pipeline_report)
    
    # Direct from materials
    tariff_report = estimate_tariffs_from_materials(materials_dict, total_weight_kg)
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Setup OpenAI client
ai_client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))


def estimate_tariffs(
    report: dict,
    origin_country: str = "China",
    destination_country: str = "United States",
    declared_value_usd: Optional[float] = None
) -> dict:
    """
    Estimate tariffs from a pipeline report.
    
    Args:
        report: Pipeline report with components and materials
        origin_country: Country of manufacture/export
        destination_country: Country of import
        declared_value_usd: Optional declared customs value
        
    Returns:
        Detailed tariff estimation report
    """
    # Extract relevant data from report
    components = report.get("components", [])
    total_weight_kg = report.get("weight_summary", {}).get("total_weight_kg", 0)
    aggregate_materials = report.get("material_composition", {}).get("aggregate_percentages", {})
    
    # Build component summary for AI
    component_summary = []
    for comp in components:
        component_summary.append({
            "name": comp.get("name"),
            "quantity": comp.get("quantity"),
            "material": comp.get("material"),
            "weight_kg": comp.get("weight_total_kg"),
            "raw_materials": comp.get("raw_materials")
        })
    
    return _generate_tariff_report(
        components=component_summary,
        aggregate_materials=aggregate_materials,
        total_weight_kg=total_weight_kg,
        origin_country=origin_country,
        destination_country=destination_country,
        declared_value_usd=declared_value_usd
    )


def estimate_tariffs_from_materials(
    materials: dict,
    total_weight_kg: float,
    origin_country: str = "China",
    destination_country: str = "United States",
    declared_value_usd: Optional[float] = None,
    product_description: str = "Furniture components"
) -> dict:
    """
    Estimate tariffs directly from material composition.
    
    Args:
        materials: Dict of material names to percentages
        total_weight_kg: Total weight in kg
        origin_country: Country of manufacture
        destination_country: Country of import
        declared_value_usd: Optional declared value
        product_description: Description of the product
        
    Returns:
        Tariff estimation report
    """
    return _generate_tariff_report(
        components=[{"name": product_description, "raw_materials": materials}],
        aggregate_materials=materials,
        total_weight_kg=total_weight_kg,
        origin_country=origin_country,
        destination_country=destination_country,
        declared_value_usd=declared_value_usd
    )


def _generate_tariff_report(
    components: list,
    aggregate_materials: dict,
    total_weight_kg: float,
    origin_country: str,
    destination_country: str,
    declared_value_usd: Optional[float]
) -> dict:
    """Generate comprehensive tariff report using OpenAI."""
    
    # Build the prompt
    prompt = f"""You are an international trade and customs expert specializing in tariff classification and duty calculations. Analyze the following product components and provide a detailed tariff estimation report.

PRODUCT DETAILS:
- Total Weight: {total_weight_kg} kg
- Origin Country: {origin_country}
- Destination Country: {destination_country}
- Declared Value: {f"${declared_value_usd:,.2f} USD" if declared_value_usd else "Not provided - estimate based on materials"}

COMPONENTS:
{json.dumps(components, indent=2)}

AGGREGATE MATERIAL COMPOSITION:
{json.dumps(aggregate_materials, indent=2)}

IMPORTANT INSTRUCTIONS FOR BASE DUTY RATE:
1. The "base_duty_rate_percent" MUST be the actual MFN (Most Favored Nation) rate from the Harmonized Tariff Schedule
2. This is the MINIMUM standard duty rate that applies to ALL imports, regardless of origin country
3. For US imports, look up the actual Column 1 General rate for the HS code
4. Common base rates for furniture: 0% to 5.3% depending on material
5. Common base rates for wooden articles: 0% to 8.6%
6. Common base rates for metal articles: 0% to 6.5%
7. DO NOT report 0% base rate unless it is actually duty-free under the HTS
8. The base_duty_usd should be calculated as: product_value * (base_duty_rate_percent / 100)

Provide a comprehensive tariff analysis in the following JSON structure:

{{
    "hs_code_classification": {{
        "primary_hs_code": "XXXX.XX.XXXX",
        "hs_code_description": "Description of the HS code",
        "classification_reasoning": "Why this HS code applies",
        "alternative_codes": [
            {{"code": "XXXX.XX", "description": "Alternative if classified differently"}}
        ]
    }},
    "tariff_rates": {{
        "base_duty_rate_percent": X.X,
        "mfn_rate_source": "HTS Chapter XX, Subheading XXXX.XX - Column 1 General Rate",
        "additional_duties": [
            {{"name": "Section 301 Tariff", "rate_percent": X.X, "applies": true/false, "reason": "..."}}
        ],
        "effective_total_rate_percent": X.X,
        "rate_type": "ad valorem / specific / compound"
    }},
    "estimated_duties": {{
        "estimated_product_value_usd": X.XX,
        "base_duty_usd": X.XX,
        "additional_duties_usd": X.XX,
        "total_estimated_duty_usd": X.XX,
        "duty_per_kg_usd": X.XX
    }},
    "material_tariff_breakdown": [
        {{
            "material": "material_name",
            "percentage_of_product": X.X,
            "applicable_hs_chapter": "XX",
            "material_duty_rate": X.X,
            "notes": "Special considerations for this material"
        }}
    ],
    "trade_agreement_analysis": {{
        "applicable_agreements": ["List of relevant trade agreements"],
        "potential_duty_savings": X.XX,
        "requirements_for_preference": "What's needed to qualify",
        "certificate_of_origin_required": true/false
    }},
    "compliance_requirements": [
        {{
            "requirement": "Requirement name",
            "description": "What needs to be done",
            "agency": "Responsible agency",
            "documentation_needed": ["List of documents"]
        }}
    ],
    "ai_insights": {{
        "cost_optimization_suggestions": [
            "Suggestion 1 for reducing tariff burden",
            "Suggestion 2..."
        ],
        "risk_factors": [
            "Potential risk 1",
            "Potential risk 2..."
        ],
        "market_considerations": "Analysis of current trade environment",
        "recommendation_summary": "Overall recommendation for this import"
    }},
    "disclaimers": [
        "Important disclaimer 1",
        "Rates subject to change..."
    ]
}}

Be specific with HS codes and duty rates based on current {destination_country} import regulations for products from {origin_country}. Consider any special tariffs, anti-dumping duties, or trade restrictions that may apply."""

    response = ai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system", 
                "content": "You are an expert customs broker and international trade consultant with deep knowledge of HS codes, tariff schedules, and trade agreements. Provide accurate, actionable tariff estimations."
            },
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    tariff_data = json.loads(response.choices[0].message.content)
    
    # Add metadata to the report
    return {
        "tariff_estimation": tariff_data,
        "request_parameters": {
            "origin_country": origin_country,
            "destination_country": destination_country,
            "total_weight_kg": total_weight_kg,
            "declared_value_usd": declared_value_usd,
            "materials_analyzed": list(aggregate_materials.keys())
        }
    }


def generate_tariff_summary(tariff_report: dict) -> str:
    """Generate a human-readable summary of the tariff report."""
    
    tariff = tariff_report.get("tariff_estimation", {})
    params = tariff_report.get("request_parameters", {})
    
    hs = tariff.get("hs_code_classification", {})
    rates = tariff.get("tariff_rates", {})
    duties = tariff.get("estimated_duties", {})
    insights = tariff.get("ai_insights", {})
    
    summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                    TARIFF ESTIMATION REPORT                   ║
╠══════════════════════════════════════════════════════════════╣
║  Origin: {params.get('origin_country', 'N/A'):20} → Destination: {params.get('destination_country', 'N/A'):15} ║
║  Total Weight: {params.get('total_weight_kg', 0):.2f} kg                                        ║
╚══════════════════════════════════════════════════════════════╝

📋 HS CODE CLASSIFICATION
   Code: {hs.get('primary_hs_code', 'N/A')}
   Description: {hs.get('hs_code_description', 'N/A')}

💰 DUTY RATES
   Base Rate: {rates.get('base_duty_rate_percent', 0):.1f}%
   Total Effective Rate: {rates.get('effective_total_rate_percent', 0):.1f}%

💵 ESTIMATED DUTIES
   Product Value: ${duties.get('estimated_product_value_usd', 0):,.2f}
   Base Duty: ${duties.get('base_duty_usd', 0):,.2f}
   Additional Duties: ${duties.get('additional_duties_usd', 0):,.2f}
   ─────────────────────────────────
   TOTAL DUTY: ${duties.get('total_estimated_duty_usd', 0):,.2f}
   (${duties.get('duty_per_kg_usd', 0):.2f} per kg)

💡 AI INSIGHTS
"""
    
    for suggestion in insights.get("cost_optimization_suggestions", [])[:3]:
        summary += f"   • {suggestion}\n"
    
    summary += f"\n📌 RECOMMENDATION\n   {insights.get('recommendation_summary', 'N/A')}\n"
    
    return summary


# CLI support
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Estimate tariffs for imported goods")
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to pipeline report JSON, or '-' for stdin"
    )
    parser.add_argument(
        "--origin", "-o",
        default="China",
        help="Origin country (default: China)"
    )
    parser.add_argument(
        "--destination", "-d",
        default="United States",
        help="Destination country (default: United States)"
    )
    parser.add_argument(
        "--value", "-v",
        type=float,
        default=None,
        help="Declared value in USD"
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Print human-readable summary"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    args = parser.parse_args()
    
    # Read input
    if args.input and args.input != "-":
        with open(args.input, "r") as f:
            report = json.load(f)
    else:
        import sys
        report = json.load(sys.stdin)
    
    # Generate tariff estimation
    print("Analyzing tariffs...")
    tariff_report = estimate_tariffs(
        report,
        origin_country=args.origin,
        destination_country=args.destination,
        declared_value_usd=args.value
    )
    
    if args.summary:
        print(generate_tariff_summary(tariff_report))
    
    if args.pretty:
        print(json.dumps(tariff_report, indent=2))
    elif not args.summary:
        print(json.dumps(tariff_report))

