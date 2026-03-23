#!/usr/bin/env python
"""
Debug script to see exact SQL generation for different queries
"""
import sys
import os
from pathlib import Path
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend"))

from nl2sql_generator import NL2SQLGenerator

def test_queries():
    gen = NL2SQLGenerator()
    
    test_queries = [
        "What was the best year",
        "cual fue el peor año",
        "año con menos beneficiarios atendidos",
        "¿Cuál fue el mejor año?",
        "¿Cuántos beneficiarios recibieron ayuda?",
        "¿Cuál es la cobertura por zonas?",
        "what was the worst year",
        "año con más donaciones",
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        result = gen.generate_sql(query)
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            results.append({
                "query": query,
                "success": False,
                "error": result['error']
            })
        else:
            sql = result['sql']
            print(f"SQL:\n{sql}\n")
            print(f"Valid: {result['valid']}")
            print(f"Explanation: {result['explanation']}")
            
            # Check for common issues
            issues = []
            if "LIMIT" in sql.upper():
                issues.append("[ISSUE] Uses LIMIT (not SQL Server compatible)")
            if "[Net Price]" in sql or "[Order Date]" in sql:
                issues.append("[OK] Uses brackets for columns with spaces")
            if "Invalid object name" in result.get('validation_notes', ''):
                issues.append("[ISSUE] References non-existent tables")
            
            if issues:
                for issue in issues:
                    print(issue)
            
            results.append({
                "query": query,
                "success": True,
                "sql": sql,
                "valid": result['valid'],
                "issues": issues
            })
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total queries: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    
    # Print results as JSON for easy parsing
    print("\n\nDETAILED RESULTS (JSON):")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_queries()
