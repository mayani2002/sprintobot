"""
Unit test for JSON parsing improvements (no API keys required)
Tests the markdown removal and JSON parsing logic
"""
import json
import re

def test_json_parsing():
    """Test that JSON parsing handles various formats"""

    print("\n" + "="*70)
    print("Testing JSON Parsing Logic")
    print("="*70)

    def clean_json_response(result_text):
        """
        Simulate the JSON cleaning logic from ai_service.py
        """
        result_text = result_text.strip()

        # Remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = re.sub(
                r'^```json?\s*|\s*```$',
                '',
                result_text,
                flags=re.MULTILINE
            ).strip()

        return result_text

    # Test Case 1: Pure JSON (ideal case)
    print("\n📝 Test Case 1: Pure JSON response")
    print("-" * 70)

    pure_json = '''
    {
        "complexity": "simple",
        "single_pass": true,
        "confidence": 0.95
    }
    '''

    cleaned = clean_json_response(pure_json)
    parsed = json.loads(cleaned)

    print(f"Input: {pure_json[:50]}...")
    print(f"Parsed: {parsed}")

    assert parsed["complexity"] == "simple"
    assert parsed["single_pass"] == True
    print("✅ Test Case 1 PASSED")

    # Test Case 2: Markdown-wrapped JSON
    print("\n📝 Test Case 2: Markdown-wrapped JSON")
    print("-" * 70)

    markdown_json = '''```json
    {
        "complexity": "moderate",
        "single_pass": false,
        "needs_discovery": true
    }
    ```'''

    cleaned2 = clean_json_response(markdown_json)
    parsed2 = json.loads(cleaned2)

    print(f"Input: {markdown_json[:50]}...")
    print(f"Cleaned: {cleaned2[:50]}...")
    print(f"Parsed: {parsed2}")

    assert parsed2["complexity"] == "moderate"
    assert parsed2["needs_discovery"] == True
    print("✅ Test Case 2 PASSED")

    # Test Case 3: Markdown without json tag
    print("\n📝 Test Case 3: Markdown without 'json' tag")
    print("-" * 70)

    markdown_simple = '''```
    {
        "complexity": "complex",
        "estimated_steps": 3
    }
    ```'''

    cleaned3 = clean_json_response(markdown_simple)
    parsed3 = json.loads(cleaned3)

    print(f"Input: {markdown_simple[:50]}...")
    print(f"Parsed: {parsed3}")

    assert parsed3["estimated_steps"] == 3
    print("✅ Test Case 3 PASSED")

    # Test Case 4: Complex nested JSON
    print("\n📝 Test Case 4: Complex nested structure")
    print("-" * 70)

    complex_json = '''```json
    {
        "complexity": "moderate",
        "missing_parameters": {
            "discoverable": ["owner", "repo"],
            "has_default": ["n"]
        },
        "discovery_steps": [
            {"step": 1, "action": "get_repos", "purpose": "Discovery"}
        ]
    }
    ```'''

    cleaned4 = clean_json_response(complex_json)
    parsed4 = json.loads(cleaned4)

    print(f"Parsed: {json.dumps(parsed4, indent=2)}")

    assert "discoverable" in parsed4["missing_parameters"]
    assert len(parsed4["discovery_steps"]) == 1
    assert parsed4["discovery_steps"][0]["action"] == "get_repos"
    print("✅ Test Case 4 PASSED")

    print("\n" + "="*70)
    print("✅ ALL JSON PARSING TESTS PASSED!")
    print("="*70)
    print("\n📊 Summary:")
    print("   ✓ Pure JSON parsed correctly")
    print("   ✓ Markdown-wrapped JSON cleaned and parsed")
    print("   ✓ Both ```json and ``` variants handled")
    print("   ✓ Complex nested structures work")
    print("\n🎯 The JSON parsing logic is working correctly!")
    print("   The response_mime_type='application/json' setting will")
    print("   prevent most markdown wrapping, and the cleanup handles edge cases.")
    print("="*70 + "\n")

if __name__ == "__main__":
    import sys
    try:
        test_json_parsing()
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON PARSE ERROR: {e}")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
