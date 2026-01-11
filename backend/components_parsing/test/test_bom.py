"""Test script for component analysis module."""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from component_analysis import analyze_components

# Test image path (same folder as this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(SCRIPT_DIR, "bed_test2.jpg")

print("=" * 50)
print("TEST 1: Basic analysis (no user context)")
print("=" * 50)

bom = analyze_components(IMAGE_PATH)
print(json.dumps(bom, indent=2))

print("\n")
print("=" * 50)
print("TEST 2: With user context")
print("=" * 50)

bom_with_context = analyze_components(IMAGE_PATH, "whole thing is made of wood and metal")
print(json.dumps(bom_with_context, indent=2))

