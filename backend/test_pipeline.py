"""
Test script for the complete pipeline.
"""

import json
import os
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import generate_report, generate_report_json


def test_with_bed_sketch():
    """Test pipeline with the bed sketch image."""
    print("=" * 60)
    print("PIPELINE TEST: Bed Sketch Analysis")
    print("=" * 60)
    
    image_path = "components_parsing/test/bed_sketch.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return None
    
    # Generate report with context
    report = generate_report(
        image_path,
        context="wooden bed frame with storage drawers"
    )
    
    print("\n" + "=" * 60)
    print("REPORT SUMMARY")
    print("=" * 60)
    
    print(f"\nImage: {report['report_metadata']['image_analyzed']}")
    print(f"Generated: {report['report_metadata']['generated_at']}")
    
    print(f"\n📦 Components Found: {report['procurement_summary']['total_components']}")
    print(f"📊 Total Items: {report['procurement_summary']['total_items']}")
    print(f"⚖️  Total Weight: {report['weight_summary']['total_weight_kg']} kg")
    
    print("\n📋 Component Breakdown:")
    for comp in report['components']:
        print(f"  • {comp['name']} (x{comp['quantity']})")
        print(f"    Material: {comp['material']}")
        print(f"    Weight: {comp['weight_per_unit_kg']} kg/unit, {comp['weight_total_kg']} kg total")
        print(f"    Source: {comp['data_source']}")
    
    print("\n🧪 Material Composition:")
    for material, pct in report['material_composition']['aggregate_percentages'].items():
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {material:20} {bar} {pct:.1f}%")
    
    return report


def test_with_bed_test2():
    """Test pipeline with the second bed image."""
    print("\n" + "=" * 60)
    print("PIPELINE TEST: Bed Test 2 Analysis")
    print("=" * 60)
    
    image_path = "components_parsing/test/bed_test2.jpg"
    
    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return None
    
    # Generate report without context
    report = generate_report(image_path)
    
    print("\n" + "=" * 60)
    print("REPORT SUMMARY")
    print("=" * 60)
    
    print(f"\nImage: {report['report_metadata']['image_analyzed']}")
    print(f"📦 Components: {report['procurement_summary']['total_components']}")
    print(f"⚖️  Total Weight: {report['weight_summary']['total_weight_kg']} kg")
    
    print("\n📋 Weight Breakdown:")
    for item in report['weight_summary']['component_weights']:
        print(f"  • {item['name']} (x{item['quantity']}): {item['weight_total_kg']} kg")
    
    return report


def save_full_report():
    """Generate and save a full JSON report."""
    print("\n" + "=" * 60)
    print("Generating Full JSON Report")
    print("=" * 60)
    
    image_path = "components_parsing/test/bed_sketch.jpg"
    output_path = "components_matching/sample_report.json"
    
    report_json = generate_report_json(
        image_path,
        context="wooden bed frame",
        include_reasoning=True,
        pretty=True
    )
    
    with open(output_path, "w") as f:
        f.write(report_json)
    
    print(f"\n✅ Report saved to: {output_path}")
    print(f"   Size: {len(report_json)} bytes")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the pipeline")
    parser.add_argument(
        "--test", "-t",
        choices=["bed1", "bed2", "save", "all"],
        default="bed1",
        help="Which test to run"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output full JSON"
    )
    
    args = parser.parse_args()
    
    if args.test == "bed1":
        report = test_with_bed_sketch()
        if args.json and report:
            print("\n" + "=" * 60)
            print("FULL JSON OUTPUT")
            print("=" * 60)
            print(json.dumps(report, indent=2))
    elif args.test == "bed2":
        report = test_with_bed_test2()
        if args.json and report:
            print("\n" + json.dumps(report, indent=2))
    elif args.test == "save":
        save_full_report()
    elif args.test == "all":
        test_with_bed_sketch()
        test_with_bed_test2()
        save_full_report()

