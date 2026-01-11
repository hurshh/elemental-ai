"""
Component Analysis Module

Analyze images for component breakdown and bill of materials generation.

Usage:
    from component_analysis import analyze_components
    
    # Basic usage
    bom = analyze_components("image.jpg")
    
    # With user context
    bom = analyze_components("image.jpg", "whole thing is made of wood")
"""

import base64
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Lazy-initialized client
_client = None

def _get_client():
    """Get or initialize the OpenRouter client."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPEN_RAILS_KEY"),
        )
    return _client


def _encode_image(image_path: str) -> str:
    """Encode image to base64 for API transmission."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_components(image_path: str, user_context: str = None) -> dict:
    """
    Analyze an image for component breakdown with optional user context.
    
    Args:
        image_path: Path to the image file
        user_context: Optional supplemental description from user 
                     (e.g., "whole thing is made of wood", "vintage 1960s piece")
    
    Returns:
        dict: Bill of materials with component details
        
    Example:
        >>> bom = analyze_components("bed_sketch.jpg")
        >>> bom = analyze_components("chair.png", "steel frame, aluminum fasteners")
    """
    base64_image = _encode_image(image_path)
    
    # Base procurement analysis prompt
    base_prompt = """Analyze this image for a procurement teardown to identify sub-components for replication or repair.

Return ONLY a JSON object with a 'bill_of_materials' array containing objects with:
- 'component_name': accurate engineering name
- 'quantity': count of this item visible or required
- 'industrial_search_term': 3-5 word supplier search string
- 'material_spec': probable material grade
- 'dimensions_estimate': metric dimensions
- 'logic': reasoning for this assessment

Focus strictly on parts found in mechanical catalogs like McMaster-Carr."""

    # Incorporate user context if provided
    if user_context and user_context.strip():
        full_prompt = f"""{base_prompt}

IMPORTANT USER CONTEXT: {user_context.strip()}
Use this additional information to refine your material assessments, dimensions, and component identification. This context should override visual assumptions where applicable."""
    else:
        full_prompt = base_prompt
    
    client = _get_client()
    response = client.chat.completions.create(
        model="qwen/qwen-2.5-vl-72b-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


# CLI support
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze image for component breakdown")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument(
        "--context", "-c",
        help="Supplemental description (e.g., 'whole thing is made of wood')",
        default=None
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image):
        print(f"Error: Image not found at {args.image}")
        exit(1)
    
    print(f"Analyzing: {args.image}")
    if args.context:
        print(f"User context: {args.context}")
    print("-" * 40)
    
    bom = analyze_components(args.image, args.context)
    print(json.dumps(bom, indent=2))
