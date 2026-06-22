# type: ignore

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []
    for field in ["name", "description", "system_prompt", "version", "techniques_applied"]:
        if field not in prompt_data:
            errors.append(f"Required field missing: '{field}'")
    system_prompt = prompt_data.get("system_prompt", "").strip()
    if not system_prompt:
        errors.append("'system_prompt' is empty")
    if "TODO" in system_prompt:
        errors.append("'system_prompt' still contains unfilled TODOs")
    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list) or len(techniques) < 2:
        errors.append(f"Minimum of 2 techniques required, found: {len(techniques) if isinstance(techniques, list) else 0}")
    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    system_prompt = prompt_data.get("system_prompt", "").strip()
    user_prompt_template = prompt_data.get("user_prompt_template", "{bug_report}").strip()
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(user_prompt_template),
    ])
    tags = prompt_data.get("tags", [])
    description = prompt_data.get("description", "")
    techniques = prompt_data.get("techniques_applied", [])
    print(f"\n   Pushing to: {prompt_name}")
    print(f"   Tags: {tags}")
    print(f"   Techniques: {len(techniques)}")
    try:
        url = hub.push(prompt_name, prompt_template, new_repo_is_public=True, new_repo_description=description, tags=tags)
        print("   ✓ Push successful!")
        print(f"   🔗 URL: {url}")
        return True
    except Exception as e:
        print(f"   ❌ Error pushing: {e}")
        return False


def main():
    print_section_header("PUSH OPTIMIZED PROMPTS TO LANGSMITH HUB")
    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB is empty in .env")
        return 1

    yaml_path = "prompts/bug_to_user_story_v2.yml"
    hub_name = f"{username}/bug_to_user_story_v2"

    print(f"\n{'=' * 50}")
    print(f"Processing: {yaml_path}")
    print("=" * 50)

    prompt_data = load_yaml(yaml_path)
    if not prompt_data:
        print(f"❌ Could not load: {yaml_path}")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Invalid prompt:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print("✓ Validation passed")
    success = push_prompt_to_langsmith(hub_name, prompt_data)

    print(f"\n{'=' * 50}")
    if success:
        print("✅ Prompt published successfully!")
        print("\nAccess the LangSmith dashboard to confirm:")
        print(f"  https://smith.langchain.com/hub/{username}")
        print("\nNext step:")
        print("  python src/evaluate.py")
    else:
        print("❌ Push failed. Check the errors above.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
