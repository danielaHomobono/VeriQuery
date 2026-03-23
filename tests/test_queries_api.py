#!/usr/bin/env python
"""
Test specific failing query
"""
import sys
import os
from pathlib import Path
import json
import requests

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend"))

def test_query(question):
    """Test a specific query through the API"""
    url = "http://localhost:8888/api/query"
    
    payload = {
        "question": question,
        "user_id": "test_user",
        "organization_id": 1
    }
    
    print(f"\nTesting query: {question}")
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"\nStatus Code: {response.status_code}")
        
        result = response.json()
        print(f"\nResponse:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success'):
            print("\n✅ SUCCESS")
            print(f"SQL: {result.get('sql')}")
            print(f"Answer: {result.get('answer')}")
            print(f"Rows: {result.get('row_count')}")
        else:
            print(f"\n❌ FAILED")
            print(f"Error: {result.get('error')}")
            print(f"SQL: {result.get('sql')}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test the failing queries
    test_queries = [
        "What was the best year",
        "año con menos beneficiarios atendidos",
        "How many customers do we have",
    ]
    
    for query in test_queries:
        test_query(query)
        input("\nPress Enter to test next query...")
