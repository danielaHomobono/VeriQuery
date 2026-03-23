#!/usr/bin/env python
"""
Test NL2SQL generation directly without backend
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend"))

from nl2sql_generator import NL2SQLGenerator

def test_nl2sql():
    gen = NL2SQLGenerator()
    
    test_queries = [
        "¿Cuál fue el mejor año?",
        "¿Cuántos beneficiarios recibieron ayuda?",
        "¿Cuál es la cobertura por zonas?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        result = gen.generate_sql(query)
        
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Generated SQL:\n{result['sql']}")
            print(f"\nExplanation:\n{result['explanation']}")
            print(f"\nValid: {result['valid']}")

if __name__ == "__main__":
    test_nl2sql()
