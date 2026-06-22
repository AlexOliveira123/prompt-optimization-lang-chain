# type: ignore

import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith():
    print_section_header("PULL PROMPTS FROM LANGSMITH HUB")
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return False

    prompt_name = "leonanluppi/bug_to_user_story_v1"
    output_path = Path("prompts/bug_to_user_story_v1.yml")

    print(f"Pulling: {prompt_name}")
    try:
        prompt = hub.pull(prompt_name)
        print("✓ Prompt loaded successfully")
    except Exception as e:
        print(f"❌ Error pulling prompt '{prompt_name}': {e}")
        print("\nCheck:")
        print("  - LANGSMITH_API_KEY is valid and not expired")
        print(f"  - The prompt '{prompt_name}' exists on LangSmith Hub")
        print("  - Your internet connection is working")
        return False

    system_prompt = ""
    user_prompt_template = "{bug_report}"
    for msg in prompt.messages:
        role = msg.__class__.__name__.lower()
        if "system" in role:
            system_prompt = msg.prompt.template if hasattr(msg, 'prompt') else str(msg.content)
        elif "human" in role:
            user_prompt_template = msg.prompt.template if hasattr(msg, 'prompt') else str(msg.content)

    prompt_data = {
        "name": "bug_to_user_story_v1",
        "description": "Initial low-quality prompt to convert bug reports into user stories",
        "version": "1.0",
        "source": prompt_name,
        "techniques_applied": [],
        "tags": ["bug", "user-story", "v1"],
        "system_prompt": system_prompt,
        "user_prompt_template": user_prompt_template,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(prompt_data, f, allow_unicode=True, sort_keys=False, indent=2)

    print(f"✓ Prompt saved to: {output_path}")
    print("\nSystem prompt content:")
    print("-" * 40)
    preview = system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt
    print(preview)
    return True


def main():
    return 0 if pull_prompts_from_langsmith() else 1


if __name__ == "__main__":
    sys.exit(main())
