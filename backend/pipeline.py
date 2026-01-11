"""
Component Analysis Pipeline

End-to-end pipeline that:
1. Analyzes an image to extract bill of materials (component_parsing)
2. Enriches each component with weight and material data (component_matching)
3. Generates a comprehensive procurement report

Usage:
    from pipeline import generate_report
    
    # From image
    report = generate_report("furniture.jpg")
    
    # With user context
    report = generate_report("chair.jpg", context="wooden frame with metal legs")
"""

import json
import os
from datetime import datetime
from typing import Optional

from components_parsing.component_analysis import analyze_components
from components_matching.component_matching import process_bill_of_materials


def generate_report(
    image_path: str,
    context: Optional[str] = None,
    include_reasoning: bool = True
) -> dict:
    """
    Generate a comprehensive procurement report from an image.
    
    Args:
        image_path: Path to the image file to analyze
        context: Optional user context (e.g., "made of oak wood", "vintage 1960s")
        include_reasoning: Whether to include AI reasoning in output
        
    Returns:
        Complete report with components, weights, materials, and summary
    """
    # Validate image exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Step 1: Analyze image to get bill of materials
    print(f"[1/3] Analyzing image: {image_path}")
    if context:
        print(f"      User context: {context}")
    
    bom = analyze_components(image_path, context)
    component_count = len(bom.get("bill_of_materials", []))
    print(f"      Found {component_count} components")
    
    # Step 2: Enrich components with weight and material data
    print(f"[2/3] Enriching components with weight & material data...")
    enriched_bom = process_bill_of_materials(bom)
    
    db_matches = enriched_bom["summary"]["components_from_database"]
    ai_estimated = enriched_bom["summary"]["components_ai_estimated"]
    print(f"      Database matches: {db_matches}, AI estimated: {ai_estimated}")
    
    # Step 3: Build final report
    print(f"[3/3] Generating report...")
    
    # Clean up components for report
    components = []
    for comp in enriched_bom["bill_of_materials"]:
        component_data = {
            "name": comp.get("component_name"),
            "quantity": comp.get("quantity"),
            "material": comp.get("material_spec"),
            "dimensions": comp.get("dimensions_estimate"),
            "search_term": comp.get("industrial_search_term"),
            "weight_per_unit_kg": comp.get("weight_kg"),
            "weight_total_kg": comp.get("weight_total_kg"),
            "raw_materials": comp.get("raw_materials"),
            "data_source": comp.get("source"),
        }
        
        # Include database match info if available
        if comp.get("rag_match"):
            component_data["database_match"] = comp["rag_match"]
        
        # Optionally include reasoning
        if include_reasoning:
            if comp.get("logic"):
                component_data["identification_logic"] = comp["logic"]
            if comp.get("weight_reasoning"):
                component_data["weight_reasoning"] = comp["weight_reasoning"]
        
        components.append(component_data)
    
    # Build report
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "image_analyzed": os.path.basename(image_path),
            "user_context": context,
        },
        "components": components,
        "weight_summary": {
            "total_weight_kg": enriched_bom["summary"]["total_weight_kg"],
            "component_weights": [
                {
                    "name": c["name"],
                    "quantity": c["quantity"],
                    "weight_total_kg": c["weight_total_kg"]
                }
                for c in components
            ]
        },
        "material_composition": {
            "aggregate_percentages": enriched_bom["summary"]["aggregate_raw_materials"],
            "by_component": [
                {
                    "name": c["name"],
                    "materials": c["raw_materials"]
                }
                for c in components if c.get("raw_materials")
            ]
        },
        "procurement_summary": {
            "total_components": enriched_bom["summary"]["total_components"],
            "total_items": sum(c["quantity"] for c in components),
            "components_from_database": db_matches,
            "components_ai_estimated": ai_estimated,
            "unique_materials": list(enriched_bom["summary"]["aggregate_raw_materials"].keys())
        }
    }
    
    print(f"      Report complete!")
    return report


def generate_report_json(
    image_path: str,
    context: Optional[str] = None,
    include_reasoning: bool = True,
    pretty: bool = True
) -> str:
    """
    Generate report and return as JSON string.
    
    Args:
        image_path: Path to the image file
        context: Optional user context
        include_reasoning: Whether to include AI reasoning
        pretty: Whether to pretty-print the JSON
        
    Returns:
        JSON string of the report
    """
    report = generate_report(image_path, context, include_reasoning)
    if pretty:
        return json.dumps(report, indent=2)
    return json.dumps(report)


def batch_generate_reports(
    image_paths: list[str],
    contexts: Optional[list[str]] = None
) -> list[dict]:
    """
    Generate reports for multiple images.
    
    Args:
        image_paths: List of image file paths
        contexts: Optional list of contexts (one per image)
        
    Returns:
        List of reports
    """
    reports = []
    contexts = contexts or [None] * len(image_paths)
    
    for i, (image_path, context) in enumerate(zip(image_paths, contexts)):
        print(f"\n{'='*60}")
        print(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
        print(f"{'='*60}")
        
        try:
            report = generate_report(image_path, context)
            reports.append({
                "status": "success",
                "image": image_path,
                "report": report
            })
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            reports.append({
                "status": "error",
                "image": image_path,
                "error": str(e)
            })
    
    return reports


# CLI support
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate procurement report from image"
    )
    parser.add_argument(
        "image",
        help="Path to image file"
    )
    parser.add_argument(
        "--context", "-c",
        help="User context (e.g., 'made of oak wood')",
        default=None
    )
    parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Exclude AI reasoning from output"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
        default=None
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Output compact JSON (no indentation)"
    )
    
    args = parser.parse_args()
    
    # Generate report
    try:
        report_json = generate_report_json(
            args.image,
            context=args.context,
            include_reasoning=not args.no_reasoning,
            pretty=not args.compact
        )
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(report_json)
            print(f"\nReport saved to: {args.output}")
        else:
            print("\n" + "="*60)
            print("REPORT OUTPUT")
            print("="*60)
            print(report_json)
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

