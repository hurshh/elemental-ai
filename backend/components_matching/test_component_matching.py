"""
Test script for component_matching.py

Tests the BOM enrichment with weight and material composition estimation.
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components_matching.component_matching import (
    process_bill_of_materials,
    process_component,
    query_rag_database,
    estimate_with_openai
)

# Sample BOM data (simulating output from component_analysis.py)
SAMPLE_BOM_1 = {
    "bill_of_materials": [
        {
            "component_name": "Flat Panel",
            "quantity": 1,
            "industrial_search_term": "wooden flat panel",
            "material_spec": "MDF or Veneer",
            "dimensions_estimate": "182.9 cm x 121.9 cm x 1.9 cm",
            "logic": "Serves as a primary support surface."
        },
        {
            "component_name": "Sliding Drawers",
            "quantity": 2,
            "industrial_search_term": "wood drawer slides",
            "material_spec": "Hardwood or Veneer",
            "dimensions_estimate": "40.6 cm x 81.3 cm x 12.7 cm",
            "logic": "Attached for storage purposes, dimensions inferred from visible side."
        },
        {
            "component_name": "Base Frame Slats",
            "quantity": 8,
            "industrial_search_term": "wooden slat",
            "material_spec": "Spruce or Fir",
            "dimensions_estimate": "30 cm x 40.6 cm x 2.5 cm",
            "logic": "Evenly distributed to support weight evenly."
        },
        {
            "component_name": "Hardware",
            "quantity": 40,
            "industrial_search_term": "furniture hardware",
            "material_spec": "Stainless Steel",
            "dimensions_estimate": "N/A",
            "logic": "Hardware includes screws, bolts, and other small parts."
        }
    ]
}

SAMPLE_BOM_2 = {
    "bill_of_materials": [
        {
            "component_name": "Side Panel",
            "quantity": 2,
            "industrial_search_term": "wooden side frame",
            "material_spec": "Hardwood Plywood panel",
            "dimensions_estimate": "64x18x3 cm",
            "logic": "Side panels are wooden based on context."
        },
        {
            "component_name": "Connecting Brackets",
            "quantity": 8,
            "industrial_search_term": "metal bracket connector",
            "material_spec": "Galvanized Steel",
            "dimensions_estimate": "10x5x0.5 cm",
            "logic": "Brackets are metal connectors joining wooden pieces."
        },
        {
            "component_name": "Drawer Slides",
            "quantity": 4,
            "industrial_search_term": "metal drawer slide",
            "material_spec": "Steel",
            "dimensions_estimate": "40x15x2 cm",
            "logic": "Metal slides allow smooth movement of drawers."
        }
    ]
}


def test_single_component():
    """Test processing a single component."""
    print("=" * 60)
    print("TEST 1: Single Component Processing")
    print("=" * 60)
    
    component = {
        "component_name": "Wooden Slat",
        "quantity": 6,
        "industrial_search_term": "wooden bed slats",
        "material_spec": "Hardwood",
        "dimensions_estimate": "85x5x1 cm",
        "logic": "Slats provide the base support for the mattress."
    }
    
    print(f"Input Component: {component['component_name']}")
    print(f"  Material: {component['material_spec']}")
    print(f"  Dimensions: {component['dimensions_estimate']}")
    print(f"  Quantity: {component['quantity']}")
    print("-" * 40)
    
    result = process_component(component)
    
    print(f"Result:")
    print(f"  Source: {result.get('source')}")
    print(f"  Weight per unit: {result.get('weight_kg')} kg")
    print(f"  Total weight: {result.get('weight_total_kg')} kg")
    print(f"  Raw materials: {json.dumps(result.get('raw_materials'), indent=4)}")
    if result.get('rag_match'):
        print(f"  RAG Match: {result.get('rag_match')}")
    if result.get('weight_reasoning'):
        print(f"  Weight reasoning: {result.get('weight_reasoning')}")
    
    print()
    return result


def test_full_bom_processing():
    """Test processing a complete BOM."""
    print("=" * 60)
    print("TEST 2: Full BOM Processing (Sample 1 - Bed Frame)")
    print("=" * 60)
    
    result = process_bill_of_materials(SAMPLE_BOM_1)
    
    print(f"\nProcessed {result['summary']['total_components']} components:")
    print(f"  - From database: {result['summary']['components_from_database']}")
    print(f"  - AI estimated: {result['summary']['components_ai_estimated']}")
    print(f"  - Total weight: {result['summary']['total_weight_kg']} kg")
    
    print("\nAggregate Raw Materials:")
    for material, percentage in result['summary']['aggregate_raw_materials'].items():
        print(f"  {material}: {percentage}%")
    
    print("\nComponent Details:")
    for comp in result['bill_of_materials']:
        print(f"\n  {comp['component_name']} (x{comp['quantity']}):")
        print(f"    Source: {comp['source']}")
        print(f"    Weight: {comp.get('weight_kg')} kg/unit, {comp.get('weight_total_kg')} kg total")
    
    print()
    return result


def test_second_bom():
    """Test with second sample BOM."""
    print("=" * 60)
    print("TEST 3: Full BOM Processing (Sample 2 - Mixed Materials)")
    print("=" * 60)
    
    result = process_bill_of_materials(SAMPLE_BOM_2)
    
    print(f"\nProcessed {result['summary']['total_components']} components:")
    print(f"  - From database: {result['summary']['components_from_database']}")
    print(f"  - AI estimated: {result['summary']['components_ai_estimated']}")
    print(f"  - Total weight: {result['summary']['total_weight_kg']} kg")
    
    print("\nAggregate Raw Materials:")
    for material, percentage in result['summary']['aggregate_raw_materials'].items():
        print(f"  {material}: {percentage}%")
    
    print()
    return result


def test_openai_estimation():
    """Test OpenAI estimation directly."""
    print("=" * 60)
    print("TEST 4: Direct OpenAI Estimation")
    print("=" * 60)
    
    component = {
        "component_name": "Corner Post",
        "quantity": 4,
        "industrial_search_term": "metal corner post",
        "material_spec": "Stainless Steel",
        "dimensions_estimate": "4x4x96 cm",
        "logic": "Metal posts provide structural support."
    }
    
    print(f"Component: {component['component_name']}")
    print(f"  Material: {component['material_spec']}")
    print(f"  Dimensions: {component['dimensions_estimate']}")
    print("-" * 40)
    
    estimate = estimate_with_openai(component)
    
    print(f"OpenAI Estimate:")
    print(f"  Weight: {estimate.get('weight_kg')} kg")
    print(f"  Reasoning: {estimate.get('weight_reasoning')}")
    print(f"  Raw materials: {json.dumps(estimate.get('raw_materials'), indent=4)}")
    
    print()
    return estimate


def test_rag_query():
    """Test RAG database query (will return None if not connected)."""
    print("=" * 60)
    print("TEST 5: RAG Database Query")
    print("=" * 60)
    
    search_terms = [
        ("wooden slat", "Hardwood"),
        ("metal bracket", "Steel"),
        ("drawer slide", "Aluminum"),
    ]
    
    for term, material in search_terms:
        print(f"\nSearching: '{term}' ({material})")
        try:
            result = query_rag_database(term, material)
            if result:
                print(f"  Found: {result.get('name')}")
                print(f"  Score: {result.get('score'):.3f}")
                print(f"  Price: {result.get('price')}")
            else:
                print("  No match found (below threshold or empty)")
        except Exception as e:
            print(f"  Error: {e}")
    
    print()


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("COMPONENT MATCHING TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        # Test 1: Single component
        test_single_component()
        
        # Test 2: Full BOM
        test_full_bom_processing()
        
        # Test 3: Second BOM
        test_second_bom()
        
        # Test 4: Direct OpenAI estimation
        test_openai_estimation()
        
        # Test 5: RAG query (may fail if DB not connected)
        test_rag_query()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test component_matching.py")
    parser.add_argument(
        "--test", "-t",
        choices=["single", "bom1", "bom2", "openai", "rag", "all"],
        default="all",
        help="Which test to run (default: all)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output full JSON result for BOM tests"
    )
    
    args = parser.parse_args()
    
    if args.test == "single":
        result = test_single_component()
        if args.json:
            print(json.dumps(result, indent=2))
    elif args.test == "bom1":
        result = test_full_bom_processing()
        if args.json:
            print(json.dumps(result, indent=2))
    elif args.test == "bom2":
        result = test_second_bom()
        if args.json:
            print(json.dumps(result, indent=2))
    elif args.test == "openai":
        test_openai_estimation()
    elif args.test == "rag":
        test_rag_query()
    else:
        exit(run_all_tests())

