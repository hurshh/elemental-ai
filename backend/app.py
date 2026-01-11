"""
Flask API for Component Analysis Pipeline

Endpoints:
- POST /api/analyze - Analyze an image and get full report with tariff estimation
- GET /api/health - Health check
"""

import os
import json
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from pipeline import generate_report
from tariff_estimation import estimate_tariffs, generate_tariff_summary

app = Flask(__name__)
CORS(app)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """
    Analyze an uploaded image and return full report with tariff estimation.
    
    Form data:
        - image: Image file
        - context: (optional) User context for better analysis
        - origin_country: (optional) Country of origin for tariffs
        - destination_country: (optional) Destination country for tariffs
        - declared_value: (optional) Declared value in USD
    """
    # Check if image was uploaded
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # Get optional parameters
    context = request.form.get('context', None)
    origin_country = request.form.get('origin_country', 'China')
    destination_country = request.form.get('destination_country', 'United States')
    declared_value = request.form.get('declared_value', None)
    
    if declared_value:
        try:
            declared_value = float(declared_value)
        except ValueError:
            declared_value = None
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            file.save(tmp.name)
            temp_path = tmp.name
        
        # Step 1: Generate component report
        report = generate_report(temp_path, context=context)
        
        # Step 2: Generate tariff estimation
        tariff_report = estimate_tariffs(
            report,
            origin_country=origin_country,
            destination_country=destination_country,
            declared_value_usd=declared_value
        )
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Combine into final response
        response = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "analysis": {
                "report": report,
                "tariff_estimation": tariff_report
            },
            "parameters": {
                "context": context,
                "origin_country": origin_country,
                "destination_country": destination_country,
                "declared_value_usd": declared_value
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/demo', methods=['GET'])
def get_demo_report():
    """Return a demo report for testing the frontend."""
    demo_report = {
        "success": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "analysis": {
            "report": {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "image_analyzed": "demo_product.jpg",
                    "user_context": "Wooden loft bed with ladder"
                },
                "components": [
                    {
                        "name": "Main Frame Rails",
                        "quantity": 4,
                        "material": "Solid Pine Wood",
                        "dimensions": "208cm x 10cm x 5cm",
                        "search_term": "structural wood beam",
                        "weight_per_unit_kg": 8.5,
                        "weight_total_kg": 34.0,
                        "raw_materials": {"softwood": 100},
                        "data_source": "ai_estimated",
                        "identification_logic": "Primary structural members forming the bed frame perimeter"
                    },
                    {
                        "name": "Bed Slats",
                        "quantity": 12,
                        "material": "Birch Plywood",
                        "dimensions": "100cm x 8cm x 2cm",
                        "search_term": "bed support slats",
                        "weight_per_unit_kg": 1.2,
                        "weight_total_kg": 14.4,
                        "raw_materials": {"plywood": 85, "adhesive": 15},
                        "data_source": "ai_estimated",
                        "identification_logic": "Support slats for mattress platform"
                    },
                    {
                        "name": "Guard Rails",
                        "quantity": 2,
                        "material": "Maple Hardwood",
                        "dimensions": "180cm x 15cm x 3cm",
                        "search_term": "safety guard rail",
                        "weight_per_unit_kg": 4.2,
                        "weight_total_kg": 8.4,
                        "raw_materials": {"hardwood": 100},
                        "data_source": "ai_estimated",
                        "identification_logic": "Safety rails to prevent falls"
                    },
                    {
                        "name": "Ladder Assembly",
                        "quantity": 1,
                        "material": "Oak Wood",
                        "dimensions": "150cm x 40cm x 5cm",
                        "search_term": "wooden ladder",
                        "weight_per_unit_kg": 6.8,
                        "weight_total_kg": 6.8,
                        "raw_materials": {"hardwood": 100},
                        "data_source": "ai_estimated",
                        "identification_logic": "Access ladder with 5 rungs"
                    },
                    {
                        "name": "Corner Brackets",
                        "quantity": 8,
                        "material": "Galvanized Steel",
                        "dimensions": "10cm x 10cm x 3cm",
                        "search_term": "metal corner bracket",
                        "weight_per_unit_kg": 0.4,
                        "weight_total_kg": 3.2,
                        "raw_materials": {"steel": 95, "zinc": 5},
                        "data_source": "ai_estimated",
                        "identification_logic": "Structural corner reinforcements"
                    },
                    {
                        "name": "Hardware Kit",
                        "quantity": 60,
                        "material": "Stainless Steel",
                        "dimensions": "Various",
                        "search_term": "furniture hardware screws",
                        "weight_per_unit_kg": 0.015,
                        "weight_total_kg": 0.9,
                        "raw_materials": {"stainless_steel": 100},
                        "data_source": "ai_estimated",
                        "identification_logic": "Screws, bolts, and assembly hardware"
                    }
                ],
                "weight_summary": {
                    "total_weight_kg": 67.7,
                    "component_weights": [
                        {"name": "Main Frame Rails", "quantity": 4, "weight_total_kg": 34.0},
                        {"name": "Bed Slats", "quantity": 12, "weight_total_kg": 14.4},
                        {"name": "Guard Rails", "quantity": 2, "weight_total_kg": 8.4},
                        {"name": "Ladder Assembly", "quantity": 1, "weight_total_kg": 6.8},
                        {"name": "Corner Brackets", "quantity": 8, "weight_total_kg": 3.2},
                        {"name": "Hardware Kit", "quantity": 60, "weight_total_kg": 0.9}
                    ]
                },
                "material_composition": {
                    "aggregate_percentages": {
                        "softwood": 50.2,
                        "hardwood": 22.4,
                        "plywood": 18.1,
                        "steel": 4.5,
                        "stainless_steel": 1.3,
                        "adhesive": 2.7,
                        "zinc": 0.8
                    },
                    "by_component": [
                        {"name": "Main Frame Rails", "materials": {"softwood": 100}},
                        {"name": "Bed Slats", "materials": {"plywood": 85, "adhesive": 15}},
                        {"name": "Guard Rails", "materials": {"hardwood": 100}},
                        {"name": "Ladder Assembly", "materials": {"hardwood": 100}},
                        {"name": "Corner Brackets", "materials": {"steel": 95, "zinc": 5}},
                        {"name": "Hardware Kit", "materials": {"stainless_steel": 100}}
                    ]
                },
                "procurement_summary": {
                    "total_components": 6,
                    "total_items": 87,
                    "components_from_database": 0,
                    "components_ai_estimated": 6,
                    "unique_materials": ["softwood", "hardwood", "plywood", "steel", "stainless_steel", "adhesive", "zinc"]
                }
            },
            "tariff_estimation": {
                "tariff_estimation": {
                    "hs_code_classification": {
                        "primary_hs_code": "9403.50.9045",
                        "hs_code_description": "Wooden furniture of a kind used in bedrooms",
                        "classification_reasoning": "Product is a wooden loft bed, primarily composed of wood materials, classified under bedroom furniture",
                        "alternative_codes": [
                            {"code": "9403.50.9080", "description": "Other wooden bedroom furniture"},
                            {"code": "9403.90.8041", "description": "Parts of wooden furniture"}
                        ]
                    },
                    "tariff_rates": {
                        "base_duty_rate_percent": 2.5,
                        "mfn_rate_source": "HTS Chapter 94, Subheading 9403.50 - Column 1 General Rate",
                        "additional_duties": [
                            {"name": "Section 301 Tariff", "rate_percent": 25.0, "applies": True, "reason": "Product manufactured in China, subject to Section 301 tariffs on Chinese goods (List 4A)"},
                            {"name": "Anti-Dumping Duty", "rate_percent": 0.0, "applies": False, "reason": "No anti-dumping orders on wooden bedroom furniture from China"}
                        ],
                        "effective_total_rate_percent": 27.5,
                        "rate_type": "ad valorem"
                    },
                    "estimated_duties": {
                        "estimated_product_value_usd": 450.0,
                        "base_duty_usd": 11.25,
                        "additional_duties_usd": 112.50,
                        "total_estimated_duty_usd": 123.75,
                        "duty_per_kg_usd": 1.83
                    },
                    "material_tariff_breakdown": [
                        {"material": "softwood", "percentage_of_product": 50.2, "applicable_hs_chapter": "44", "material_duty_rate": 0.0, "notes": "Coniferous wood - generally duty-free under HTS 4407.10"},
                        {"material": "hardwood", "percentage_of_product": 22.4, "applicable_hs_chapter": "44", "material_duty_rate": 0.0, "notes": "Tropical/temperate hardwood - duty-free under HTS 4407.2x"},
                        {"material": "plywood", "percentage_of_product": 18.1, "applicable_hs_chapter": "44", "material_duty_rate": 8.0, "notes": "Hardwood plywood from China subject to 8% duty under HTS 4412"},
                        {"material": "steel", "percentage_of_product": 4.5, "applicable_hs_chapter": "73", "material_duty_rate": 2.9, "notes": "Steel articles (brackets/screws) - 2.9% under HTS 7318"},
                        {"material": "stainless_steel", "percentage_of_product": 1.3, "applicable_hs_chapter": "73", "material_duty_rate": 0.0, "notes": "Stainless steel fasteners - duty-free under HTS 7318.15"}
                    ],
                    "trade_agreement_analysis": {
                        "applicable_agreements": ["USMCA (if rerouted through Mexico/Canada)"],
                        "potential_duty_savings": 112.50,
                        "requirements_for_preference": "Product must meet rules of origin, substantial transformation in USMCA country",
                        "certificate_of_origin_required": True
                    },
                    "compliance_requirements": [
                        {"requirement": "TSCA Compliance", "description": "Timber products must comply with Toxic Substances Control Act", "agency": "EPA", "documentation_needed": ["Lacey Act Declaration", "TSCA certification"]},
                        {"requirement": "CBP Entry", "description": "Standard customs entry documentation required", "agency": "U.S. Customs and Border Protection", "documentation_needed": ["Commercial Invoice", "Packing List", "Bill of Lading", "Entry Summary (CBP Form 7501)"]},
                        {"requirement": "CPSC Safety", "description": "Furniture must meet consumer product safety standards", "agency": "Consumer Product Safety Commission", "documentation_needed": ["GCC (General Certificate of Conformity)", "Test reports"]}
                    ],
                    "ai_insights": {
                        "cost_optimization_suggestions": [
                            "Consider sourcing from Vietnam or Malaysia to avoid Section 301 tariffs (potential savings of $112.50)",
                            "Explore Foreign Trade Zone (FTZ) entry for duty deferral on re-exported goods",
                            "Request binding ruling from CBP to confirm HS classification and avoid penalties",
                            "Consider manufacturing in a USMCA country for preferential treatment"
                        ],
                        "risk_factors": [
                            "Section 301 tariffs may be subject to change based on trade negotiations",
                            "Misclassification risk if steel content exceeds wood content by value",
                            "Lacey Act violations carry significant penalties - ensure proper timber documentation"
                        ],
                        "market_considerations": "Current trade tensions between US and China continue to affect furniture imports. Monitor USTR announcements for potential tariff changes.",
                        "recommendation_summary": "Product faces 25% additional tariff due to China origin. Consider alternative sourcing from SE Asia or exploring USMCA supply chains to reduce landed cost. Ensure Lacey Act compliance for all wood components."
                    },
                    "disclaimers": [
                        "This is an AI-generated estimate based on current tariff schedules and may not reflect recent changes",
                        "Actual duties may vary based on CBP classification decisions and product specifications",
                        "Consult with a licensed customs broker for official duty calculations",
                        "Section 301 tariffs are subject to change based on trade policy developments"
                    ]
                },
                "request_parameters": {
                    "origin_country": "China",
                    "destination_country": "United States",
                    "total_weight_kg": 67.7,
                    "declared_value_usd": 450.0,
                    "materials_analyzed": ["softwood", "hardwood", "plywood", "steel", "stainless_steel", "adhesive", "zinc"]
                }
            }
        },
        "parameters": {
            "context": "Wooden loft bed with ladder",
            "origin_country": "China",
            "destination_country": "United States",
            "declared_value_usd": 450.0
        }
    }
    
    return jsonify(demo_report)


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')

