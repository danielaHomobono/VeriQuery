"""
Test Suite for Ambiguity Detector and Multi-Query Generator
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src" / "backend" / "agents"))
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from ambiguity_detector import AmbiguityDetector, MetricType
from multi_query_generator import MultiQueryGenerator


def test_ambiguity_detector_mejor():
    """Test ambiguity detector with 'mejor' keyword"""
    detector = AmbiguityDetector()
    result = detector.detect("¿Cuál fue el mejor año?")
    
    assert result["is_ambiguous"] == True
    assert "mejor" in result["keywords_found"]
    assert len(result["clarifications"]) > 0
    assert result["confidence"] > 0.8
    print("✓ Test ambiguity_detector_mejor passed")


def test_ambiguity_detector_crecimiento():
    """Test ambiguity detector with 'crecimiento' keyword"""
    detector = AmbiguityDetector()
    result = detector.detect("¿Cuál fue el crecimiento?")
    
    assert result["is_ambiguous"] == True
    assert "crecimiento" in result["keywords_found"]
    assert len(result["clarifications"]) > 0
    print("✓ Test ambiguity_detector_crecimiento passed")


def test_ambiguity_detector_no_ambiguity():
    """Test ambiguity detector with clear query"""
    detector = AmbiguityDetector()
    result = detector.detect("¿Cuántos beneficiarios totales hay?")
    
    assert result["is_ambiguous"] == False
    assert len(result["keywords_found"]) == 0
    assert len(result["clarifications"]) == 0
    print("✓ Test ambiguity_detector_no_ambiguity passed")


def test_multi_query_generator_beneficiarios():
    """Test multi-query generator for beneficiarios metric"""
    generator = MultiQueryGenerator()
    result = generator.generate(
        user_question="¿Cuál fue el mejor año?",
        chosen_metric=MetricType.BENEFICIARIOS_COUNT,
        time_period="year"
    )
    
    assert result["chosen_metric"] == MetricType.BENEFICIARIOS_COUNT.value
    assert result["query_count"] > 0
    assert len(result["queries"]) > 0
    
    # Check first query (main query)
    main_query = result["queries"][0]
    assert main_query["type"] == "main"
    assert main_query["metric"] == MetricType.BENEFICIARIOS_COUNT.value
    assert "instruction" in main_query
    print(f"✓ Test multi_query_generator_beneficiarios passed ({result['query_count']} queries)")


def test_multi_query_generator_donaciones():
    """Test multi-query generator for donaciones metric"""
    generator = MultiQueryGenerator()
    result = generator.generate(
        user_question="¿Cuál fue el año con mayor presupuesto?",
        chosen_metric=MetricType.DONACIONES_SUM,
        time_period="year"
    )
    
    assert result["chosen_metric"] == MetricType.DONACIONES_SUM.value
    assert result["query_count"] > 0
    print(f"✓ Test multi_query_generator_donaciones passed ({result['query_count']} queries)")


def test_multi_query_generator_entregas():
    """Test multi-query generator for entregas metric"""
    generator = MultiQueryGenerator()
    result = generator.generate(
        user_question="¿Cuál fue el año con más entregas?",
        chosen_metric=MetricType.ENTREGAS_COUNT,
        time_period="year"
    )
    
    assert result["chosen_metric"] == MetricType.ENTREGAS_COUNT.value
    assert result["query_count"] > 0
    print(f"✓ Test multi_query_generator_entregas passed ({result['query_count']} queries)")


def test_integration_ambiguity_to_multiqueries():
    """Integration test: ambiguity detector -> multi-query generator"""
    detector = AmbiguityDetector()
    generator = MultiQueryGenerator()
    
    # Step 1: Detect ambiguity
    ambiguity_result = detector.detect("¿Cuál fue el mejor trimestre?")
    assert ambiguity_result["is_ambiguous"]
    
    # Step 2: Use first clarification to choose metric
    first_clarification = ambiguity_result["clarifications"][0]
    metric_value = first_clarification["metric"]
    metric = MetricType(metric_value)
    
    # Step 3: Generate queries for chosen metric
    queries_result = generator.generate(
        user_question="¿Cuál fue el mejor trimestre?",
        chosen_metric=metric,
        time_period="quarter"
    )
    
    assert queries_result["query_count"] > 0
    assert "QUARTER" in queries_result["queries"][0]["instruction"]
    print("✓ Integration test passed (ambiguity -> multiqueries)")


if __name__ == "__main__":
    print("Running tests...\n")
    
    try:
        # Ambiguity Detector Tests
        print("=== Ambiguity Detector Tests ===")
        test_ambiguity_detector_mejor()
        test_ambiguity_detector_crecimiento()
        test_ambiguity_detector_no_ambiguity()
        
        # Multi-Query Generator Tests
        print("\n=== Multi-Query Generator Tests ===")
        test_multi_query_generator_beneficiarios()
        test_multi_query_generator_donaciones()
        test_multi_query_generator_entregas()
        
        # Integration Tests
        print("\n=== Integration Tests ===")
        test_integration_ambiguity_to_multiqueries()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
