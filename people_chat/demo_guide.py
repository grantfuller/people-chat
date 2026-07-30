"""
Guided demo tour for People Chat.
Runs through pre-canned queries showing different HR analytics capabilities.
"""

from .formatter import format_result, format_without_rich
from .query_engine import ask

GUIDED_QUESTIONS = [
    {
        "question": "How many active employees do we have?",
        "capability": "Simple numeric answers — headcount with employee status filtering"
    },
    {
        "question": "What's the average salary by department?",
        "capability": "Grouped aggregations — department-level compensation analysis with sorting"
    },
    {
        "question": "Show me the salary distribution by Radford level",
        "capability": "Multi-dimensional analysis — salary ranges across career levels (Support → Professional → Management → Executive)"
    },
    {
        "question": "How many employees are in each employment status?",
        "capability": "Categorical breakdowns — understanding workforce composition"
    },
    {
        "question": "Who are the top 10 highest paid employees?",
        "capability": "Ranked lists — sorting, limiting, and filtering for executive compensation"
    },
    {
        "question": "What is the average tenure in years by department?",
        "capability": "Date calculations — tenure analysis using hire dates and termination dates"
    },
]


def run_guided_tour(db_path: str, glossary_path: str | None = None):
    """Run through pre-canned questions showing what People Chat can do."""
    print()
    print("  🎮 Guided Tour — Let's see what People Chat can do!")
    print("  ════════════════════════════════════════════════════")
    input("\n  Press Enter to start the tour → ")
    print()

    for i, step in enumerate(GUIDED_QUESTIONS, 1):
        print(f"\n  ── Step {i} ────────────────────────────────────────")
        print(f"  📝 {step['question']}")
        print(f"  🔍 {step['capability']}")
        print()

        try:
            result = ask(step["question"], db_path, glossary_path=glossary_path)
            formatted = format_result(result, show_sql=False)
            output = format_without_rich(formatted['text'])

            for line in output.split('\n'):
                if line.strip():
                    print(f"  {line.strip()}")
        except Exception as e:  # noqa: BLE001  # noqa: BLE001
            print(f"  ⚠️  Query failed: {e}")

        print()
        if i < len(GUIDED_QUESTIONS):
            input("  Press Enter for next step → ")
        print()

    print("  ════════════════════════════════════════════════════")
    print("  🎉 Tour complete! Now try your own questions above.")
    print()
