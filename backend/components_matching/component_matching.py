"""
Component Matching Module

Takes bill of materials from component_analysis.py and enriches each component
with weight estimates and raw material composition from RAG database or OpenAI.

Usage:
    from component_matching import process_bill_of_materials
    
    bom = {"bill_of_materials": [...]}  # Output from component_analysis.py
    enriched_bom = process_bill_of_materials(bom)
"""

import os
import json
import re
from urllib.parse import quote_plus
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# Setup Clients
ai_client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

# Lazy MongoDB connection
_mongo_client = None
_collection = None


def _get_encoded_mongo_uri():
    """Encode special characters in MongoDB URI credentials."""
    uri = os.getenv("MONGO_STRING", "")
    if not uri:
        return None
    
    # Match mongodb+srv://user:password@host or mongodb://user:password@host pattern
    match = re.match(r'^(mongodb(?:\+srv)?://)([^:]+):(.+)@([^@]+)$', uri)
    if match:
        scheme, user, password, rest = match.groups()
        encoded_user = quote_plus(user)
        encoded_password = quote_plus(password)
        return f"{scheme}{encoded_user}:{encoded_password}@{rest}"
    return uri


def _get_collection():
    """Get MongoDB collection with lazy initialization."""
    global _mongo_client, _collection
    if _collection is None:
        uri = _get_encoded_mongo_uri()
        if uri:
            _mongo_client = MongoClient(uri)
            db = _mongo_client.cluster0
            _collection = db.products
    return _collection


def get_query_embedding(text: str) -> list:
    """Converts text into a vector embedding."""
    return ai_client.embeddings.create(
        input=[text], 
        model="text-embedding-3-small"
    ).data[0].embedding


def query_rag_database(search_term: str, material: str = None) -> dict | None:
    """
    Query MongoDB vector database for matching component.
    
    Returns the match with weight/material data if found, None otherwise.
    """
    try:
        collection = _get_collection()
        if collection is None:
            print("[WARNING] MongoDB not configured, skipping RAG query")
            return None
            
        # Build search query combining search term and material
        query_text = search_term
        if material:
            query_text = f"{search_term} {material}"
        
        query_vector = get_query_embedding(query_text)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": 100,
                    "limit": 1
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "part_number": 1,
                    "name": 1,
                    "price": 1,
                    "material": 1,
                    "weight": 1,
                    "weight_unit": 1,
                    "dimensions": 1,
                    "raw_materials": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        results = list(collection.aggregate(pipeline))
        
        if not results:
            return None

        best_match = results[0]
        
        # Threshold for considering a match valid
        if best_match.get("score", 0) < 0.75:
            return None

        return best_match
    
    except Exception as e:
        print(f"[WARNING] RAG database query failed: {e}")
        print("[INFO] Falling back to AI estimation...")
        return None


def estimate_with_openai(component: dict) -> dict:
    """
    Use OpenAI to estimate weight and raw material composition
    when component is not found in RAG database.
    """
    prompt = f"""Based on the following component specifications, estimate:
1. The weight in kg (single number)
2. The raw material composition as percentages

Component Details:
- Name: {component.get('component_name', 'Unknown')}
- Material Spec: {component.get('material_spec', 'Unknown')}
- Dimensions: {component.get('dimensions_estimate', 'Unknown')}
- Industrial Search Term: {component.get('industrial_search_term', 'Unknown')}
- Quantity: {component.get('quantity', 1)}

Return ONLY a JSON object with:
- "weight_kg": estimated weight per unit in kg (number)
- "weight_reasoning": brief explanation of weight calculation
- "raw_materials": object with material names as keys and percentage as values (must sum to 100)
  Common materials: wood, iron, steel, aluminum, plastic, rubber, glass, copper, brass, stainless_steel, mdf, plywood, hardwood, softwood, veneer, galvanized_steel

Example response:
{{
    "weight_kg": 2.5,
    "weight_reasoning": "Based on MDF panel dimensions 100x50x2cm, density ~750kg/m³",
    "raw_materials": {{
        "mdf": 85,
        "wood_veneer": 10,
        "adhesive": 5
    }}
}}"""

    response = ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an industrial materials expert. Provide accurate weight and material composition estimates for manufacturing components."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


def process_component(component: dict) -> dict:
    """
    Process a single component - try RAG first, fallback to OpenAI estimation.
    
    Returns enriched component with weight and material composition.
    """
    search_term = component.get('industrial_search_term', component.get('component_name', ''))
    material = component.get('material_spec', '')
    
    # Try to find in RAG database
    rag_result = query_rag_database(search_term, material)
    
    enriched = {
        **component,
        "source": None,
        "weight_kg": None,
        "weight_total_kg": None,
        "raw_materials": None,
        "rag_match": None
    }
    
    if rag_result:
        # Found in database
        enriched["source"] = "database"
        enriched["rag_match"] = {
            "part_number": rag_result.get("part_number"),
            "name": rag_result.get("name"),
            "price": rag_result.get("price"),
            "match_score": rag_result.get("score")
        }
        
        # Extract weight from database if available
        if "weight" in rag_result:
            weight = rag_result["weight"]
            unit = rag_result.get("weight_unit", "kg")
            # Convert to kg if needed
            if unit == "g":
                weight = weight / 1000
            elif unit == "lb":
                weight = weight * 0.453592
            enriched["weight_kg"] = weight
            
        if "raw_materials" in rag_result:
            enriched["raw_materials"] = rag_result["raw_materials"]
            
        # If weight not in database, still estimate with OpenAI
        if enriched["weight_kg"] is None:
            estimate = estimate_with_openai(component)
            enriched["weight_kg"] = estimate.get("weight_kg")
            enriched["weight_reasoning"] = estimate.get("weight_reasoning")
            if enriched["raw_materials"] is None:
                enriched["raw_materials"] = estimate.get("raw_materials")
    else:
        # Not found - use OpenAI estimation
        enriched["source"] = "ai_estimated"
        estimate = estimate_with_openai(component)
        enriched["weight_kg"] = estimate.get("weight_kg")
        enriched["weight_reasoning"] = estimate.get("weight_reasoning")
        enriched["raw_materials"] = estimate.get("raw_materials")
    
    # Calculate total weight based on quantity
    quantity = component.get("quantity", 1)
    if enriched["weight_kg"] is not None:
        enriched["weight_total_kg"] = round(enriched["weight_kg"] * quantity, 3)
    
    return enriched


def process_bill_of_materials(bom: dict) -> dict:
    """
    Process entire bill of materials from component_analysis.py output.
    
    Args:
        bom: Dict with 'bill_of_materials' array from component_analysis.py
        
    Returns:
        Enriched BOM with weight estimates and material compositions
    """
    components = bom.get("bill_of_materials", [])
    
    enriched_components = []
    total_weight = 0
    aggregate_materials = {}
    
    for component in components:
        enriched = process_component(component)
        enriched_components.append(enriched)
        
        # Aggregate total weight
        if enriched.get("weight_total_kg"):
            total_weight += enriched["weight_total_kg"]
        
        # Aggregate raw materials (weighted by component weight)
        if enriched.get("raw_materials") and enriched.get("weight_total_kg"):
            component_weight = enriched["weight_total_kg"]
            for material, percentage in enriched["raw_materials"].items():
                material_weight = (percentage / 100) * component_weight
                aggregate_materials[material] = aggregate_materials.get(material, 0) + material_weight
    
    # Convert aggregate materials to percentages
    material_percentages = {}
    if total_weight > 0:
        for material, weight in aggregate_materials.items():
            material_percentages[material] = round((weight / total_weight) * 100, 2)
    
    return {
        "bill_of_materials": enriched_components,
        "summary": {
            "total_components": len(enriched_components),
            "total_weight_kg": round(total_weight, 3),
            "components_from_database": sum(1 for c in enriched_components if c.get("source") == "database"),
            "components_ai_estimated": sum(1 for c in enriched_components if c.get("source") == "ai_estimated"),
            "aggregate_raw_materials": material_percentages
        }
    }


# CLI support
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enrich BOM with weight and material data")
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to JSON file with BOM, or '-' for stdin"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty print output"
    )
    
    args = parser.parse_args()
    
    # Read input
    if args.input and args.input != "-":
        with open(args.input, "r") as f:
            bom = json.load(f)
    else:
        import sys
        bom = json.load(sys.stdin)
    
    # Process
    result = process_bill_of_materials(bom)
    
    # Output
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
