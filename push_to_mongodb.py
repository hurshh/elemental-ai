#!/usr/bin/env python3
"""
Script to push McMaster-Carr product data to MongoDB
"""

from pymongo import MongoClient
import json
import os
import sys

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from .env in the same directory as this script
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, rely on system environment variables
    pass


def push_to_mongodb(json_file_path: str, connection_uri: str, database_name: str, collection_name: str):
    """
    Push JSON data to MongoDB
    
    Args:
        json_file_path: Path to the JSON file
        connection_uri: MongoDB connection string
        database_name: Name of the database
        collection_name: Name of the collection
    """
    # Load JSON data
    print(f"Loading data from {json_file_path}...")
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Extract products array
    products = data.get('mcmaster_carr_products', [])
    print(f"Found {len(products)} products to insert")
    
    if not products:
        print("No products found in the JSON file!")
        return
    
    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
    client = MongoClient(connection_uri)
    
    # Get database and collection
    db = client[database_name]
    collection = db[collection_name]
    
    # Insert all products
    print(f"Inserting {len(products)} products into {database_name}.{collection_name}...")
    result = collection.insert_many(products)
    
    print(f"✅ Successfully inserted {len(result.inserted_ids)} documents!")
    print(f"   Database: {database_name}")
    print(f"   Collection: {collection_name}")
    
    # Close connection
    client.close()
    print("Connection closed.")


if __name__ == "__main__":
    # Configuration
    JSON_FILE = os.path.join(os.path.dirname(__file__), "extract-data-2026-01-11.json")
    
    # MongoDB connection string from environment variable (REQUIRED)
    MONGO_URI = os.environ.get("MONGODB_URI")
    if not MONGO_URI:
        print("❌ Error: MONGODB_URI environment variable is not set!")
        print("   Please set it in your .env file or export it:")
        print("   export MONGODB_URI='mongodb+srv://user:pass@cluster.mongodb.net/'")
        sys.exit(1)
    
    # Database and collection names
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "mcmaster_products")
    COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "products_firecrawl")
    
    push_to_mongodb(JSON_FILE, MONGO_URI, DATABASE_NAME, COLLECTION_NAME)
