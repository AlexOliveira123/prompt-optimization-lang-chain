# type: ignore

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import load_yaml  # noqa: E402

PROMPT_V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


class TestPrompts:
    @pytest.fixture(autouse=True)
    def load_prompt_data(self):
        assert PROMPT_V2_PATH.exists(), (
            f"Prompt file not found: {PROMPT_V2_PATH}\n"
            "Run: python src/pull_prompts.py to create the base file, "
            "then create prompts/bug_to_user_story_v2.yml with the optimized prompt."
        )
        self.prompt_data = load_yaml(str(PROMPT_V2_PATH))
        assert self.prompt_data is not None, f"Failed to parse YAML: {PROMPT_V2_PATH}"

    def test_prompt_has_system_prompt(self):
        """Check that 'system_prompt' exists and has meaningful content."""
        system_prompt = self.prompt_data.get("system_prompt", "")
        assert isinstance(system_prompt, str) and len(system_prompt.strip()) > 50, (
            f"'system_prompt' is missing or too short ({len(system_prompt.strip())} chars). "
            "A quality prompt should have at least 50 characters."
        )

    def test_prompt_has_role_definition(self):
        """Check that the prompt defines a persona."""
        system_lower = self.prompt_data.get("system_prompt", "").lower()
        role_keywords = ["you are", "your role is", "act as", "your function is", "your responsibility is"]
        assert any(kw in system_lower for kw in role_keywords), (
            "The prompt does not define a persona/role for the model. "
            "Add a role definition such as: 'You are a senior Product Manager...'"
        )

    def test_prompt_mentions_format(self):
        """Check that the prompt specifies output format."""
        content = (
            self.prompt_data.get("system_prompt", "") + " " +
            self.prompt_data.get("user_prompt_template", "")
        ).lower()
        format_keywords = ["as a", "i want", "so that", "user story", "acceptance criteria",
                           "given", "when", "then", "format", "markdown"]
        matched = [kw for kw in format_keywords if kw in content]
        assert len(matched) >= 3, (
            f"The prompt mentions too few format indicators ({matched}). "
            "Include Given-When-Then, User Story structure, or Markdown format instructions."
        )

    def test_prompt_has_few_shot_examples(self):
        """Check that the prompt contains Few-shot examples."""
        content_lower = self.prompt_data.get("system_prompt", "").lower()
        indicators = ["example", "input:", "output:", "bug report:", "expected output"]
        matched = [ind for ind in indicators if ind in content_lower]
        assert len(matched) >= 2, (
            f"The prompt does not appear to contain Few-shot examples (found: {matched}). "
            "Add at least 1 complete example with input and expected output."
        )
        concrete_terms = ["button", "endpoint", "webhook", "api", "error"]
        assert any(term in content_lower for term in concrete_terms), (
            "The prompt does not appear to contain concrete bug report examples."
        )

    def test_prompt_no_todos(self):
        """Ensure no [TODO] placeholders were left in the text."""
        all_content = "".join([
            self.prompt_data.get("system_prompt", ""),
            self.prompt_data.get("user_prompt_template", ""),
            self.prompt_data.get("description", ""),
        ])
        found = [p for p in ["[TODO]", "[todo]", "TODO:", "# TODO", "<!-- TODO"] if p in all_content]
        assert not found, f"Unresolved TODOs found in the prompt: {found}."

    def test_minimum_techniques(self):
        """Check that at least 2 non-empty techniques were listed."""
        techniques = self.prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list) and len(techniques) >= 2, (
            f"Minimum of 2 techniques required, found: {len(techniques) if isinstance(techniques, list) else 0}. "
            "Add techniques such as: Few-shot Learning, Chain of Thought, Role Prompting."
        )
        non_empty = [t for t in techniques if t and str(t).strip()]
        assert len(non_empty) >= 2, "The techniques listed in 'techniques_applied' are empty."


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
