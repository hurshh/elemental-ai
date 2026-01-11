"""
Test script for tariff estimation module.
"""

import json
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tariff_estimation import estimate_tariffs, estimate_tariffs_from_materials, generate_tariff_summary


# Sample pipeline report (simulating output from pipeline.py)
SAMPLE_REPORT = {
    "report_metadata": {
        "generated_at": "2026-01-10T23:39:53.583401Z",
        "image_analyzed": "bed_sketch.jpg",
        "user_context": "wooden bed frame"
    },
    "components": [
        {
            "name": "Wooden Slats",
            "quantity": 20,
            "material": "Hardwood grade",
            "dimensions": "100cm x 5cm x 1cm",
            "weight_per_unit_kg": 1.5,
            "weight_total_kg": 30.0,
            "raw_materials": {"hardwood": 100}
        },
        {
            "name": "Wooden Beam",
            "quantity": 8,
            "material": "Spruce lumber",
            "dimensions": "110cm x 5cm x 5cm",
            "weight_per_unit_kg": 1.375,
            "weight_total_kg": 11.0,
            "raw_materials": {"softwood": 100}
        },
        {
            "name": "Steel Brackets",
            "quantity": 12,
            "material": "Galvanized Steel",
            "dimensions": "10cm x 5cm x 0.5cm",
            "weight_per_unit_kg": 0.3,
            "weight_total_kg": 3.6,
            "raw_materials": {"steel": 95, "zinc": 5}
        },
        {
            "name": "Hardware Pack",
            "quantity": 50,
            "material": "Stainless Steel",
            "dimensions": "Various",
            "weight_per_unit_kg": 0.02,
            "weight_total_kg": 1.0,
            "raw_materials": {"stainless_steel": 100}
        }
    ],
    "weight_summary": {
        "total_weight_kg": 45.6,
        "component_weights": [
            {"name": "Wooden Slats", "quantity": 20, "weight_total_kg": 30.0},
            {"name": "Wooden Beam", "quantity": 8, "weight_total_kg": 11.0},
            {"name": "Steel Brackets", "quantity": 12, "weight_total_kg": 3.6},
            {"name": "Hardware Pack", "quantity": 50, "weight_total_kg": 1.0}
        ]
    },
    "material_composition": {
        "aggregate_percentages": {
            "hardwood": 65.8,
            "softwood": 24.1,
            "steel": 7.5,
            "zinc": 0.4,
            "stainless_steel": 2.2
        }
    },
    "procurement_summary": {
        "total_components": 4,
        "total_items": 90
    }
}


def test_tariff_estimation_china_to_us():
    """Test tariff estimation for China to US import."""
    print("=" * 60)
    print("TEST 1: China → United States (Wooden Bed Frame)")
    print("=" * 60)
    
    tariff_report = estimate_tariffs(
        SAMPLE_REPORT,
        origin_country="China",
        destination_country="United States",
        declared_value_usd=500.00
    )
    
    # Print summary
    print(generate_tariff_summary(tariff_report))
    
    return tariff_report


def test_tariff_estimation_vietnam_to_us():
    """Test tariff estimation for Vietnam to US import."""
    print("\n" + "=" * 60)
    print("TEST 2: Vietnam → United States (Same Product)")
    print("=" * 60)
    
    tariff_report = estimate_tariffs(
        SAMPLE_REPORT,
        origin_country="Vietnam",
        destination_country="United States",
        declared_value_usd=500.00
    )
    
    print(generate_tariff_summary(tariff_report))
    
    return tariff_report


def test_tariff_estimation_china_to_eu():
    """Test tariff estimation for China to EU import."""
    print("\n" + "=" * 60)
    print("TEST 3: China → European Union")
    print("=" * 60)
    
    tariff_report = estimate_tariffs(
        SAMPLE_REPORT,
        origin_country="China",
        destination_country="European Union",
        declared_value_usd=500.00
    )
    
    print(generate_tariff_summary(tariff_report))
    
    return tariff_report


def test_direct_materials():
    """Test with direct material input."""
    print("\n" + "=" * 60)
    print("TEST 4: Direct Materials Input (Steel Product)")
    print("=" * 60)
    
    materials = {
        "carbon_steel": 70,
        "stainless_steel": 20,
        "rubber": 5,
        "plastic": 5
    }
    
    tariff_report = estimate_tariffs_from_materials(
        materials=materials,
        total_weight_kg=25.0,
        origin_country="China",
        destination_country="United States",
        declared_value_usd=200.00,
        product_description="Industrial steel components"
    )
    
    print(generate_tariff_summary(tariff_report))
    
    return tariff_report


def save_full_report():
    """Generate and save a full tariff report."""
    print("\n" + "=" * 60)
    print("Generating Full Tariff Report JSON")
    print("=" * 60)
    
    tariff_report = estimate_tariffs(
        SAMPLE_REPORT,
        origin_country="China",
        destination_country="United States",
        declared_value_usd=500.00
    )
    
    output_path = "sample_tariff_report.json"
    with open(output_path, "w") as f:
        json.dump(tariff_report, f, indent=2)
    
    print(f"\n✅ Report saved to: {output_path}")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test tariff estimation")
    parser.add_argument(
        "--test", "-t",
        choices=["china_us", "vietnam_us", "china_eu", "materials", "save", "all"],
        default="china_us",
        help="Which test to run"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output full JSON"
    )
    
    args = parser.parse_args()
    
    try:
        if args.test == "china_us":
            report = test_tariff_estimation_china_to_us()
        elif args.test == "vietnam_us":
            report = test_tariff_estimation_vietnam_to_us()
        elif args.test == "china_eu":
            report = test_tariff_estimation_china_to_eu()
        elif args.test == "materials":
            report = test_direct_materials()
        elif args.test == "save":
            save_full_report()
            report = None
        elif args.test == "all":
            test_tariff_estimation_china_to_us()
            test_tariff_estimation_vietnam_to_us()
            test_tariff_estimation_china_to_eu()
            test_direct_materials()
            save_full_report()
            report = None
        
        if args.json and report:
            print("\n" + "=" * 60)
            print("FULL JSON OUTPUT")
            print("=" * 60)
            print(json.dumps(report, indent=2))
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

