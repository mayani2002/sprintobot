"""
Debug: See the FULL Gemini response for the problematic query
"""
import asyncio
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def load_env_file():
    env_path = Path(__file__).parent.parent / "config" / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_env_file()

from app.services.ai_service import AIService

async def debug_query():
    """Debug the Gemini response"""

    print("\n" + "="*80)
    print("🔍 DEBUGGING GEMINI RESPONSE")
    print("="*80)

    service = AIService()
    query = "fetch latest prs from the user yt-dlp"

    print(f"\nQuery: '{query}'")
    print("-" * 80)

    # Call the complexity analysis directly
    analysis = await service._analyze_query_complexity(query)

    print("\n" + "="*80)
    print("📊 FULL GEMINI ANALYSIS")
    print("="*80)
    print(json.dumps(analysis, indent=2, default=str))

    print("\n" + "="*80)
    print("🔍 KEY FIELDS")
    print("="*80)

    print(f"\nSuggested Function: {analysis.get('suggested_function')}")
    print(f"Provided Parameters: {analysis.get('provided_parameters')}")
    print(f"Needs Discovery: {analysis.get('needs_discovery')}")

    discovery_steps = analysis.get('discovery_steps', [])
    print(f"\nDiscovery Steps ({len(discovery_steps)} total):")
    for i, step in enumerate(discovery_steps, 1):
        print(f"\n  Step {i}:")
        print(f"    Action: {step.get('action')}")
        print(f"    Purpose: {step.get('purpose')}")
        print(f"    Full step: {step}")

if __name__ == "__main__":
    asyncio.run(debug_query())
