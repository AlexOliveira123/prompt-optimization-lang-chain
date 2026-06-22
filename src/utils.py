# type: ignore

import os
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


def load_yaml(file_path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None


def check_env_vars(required_vars: list) -> bool:
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nConfigure them in the .env file before continuing.")
        return False
    return True


def print_section_header(title: str, char: str = "=", width: int = 50):
    print("\n" + char * width)
    print(title)
    print(char * width + "\n")


def get_llm(model: Optional[str] = None, temperature: float = 0.0):
    from langchain_openai import ChatOpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in .env")
    return ChatOpenAI(model=model or os.getenv('LLM_MODEL', 'gpt-4o-mini'), temperature=temperature, api_key=api_key)


def get_eval_llm(temperature: float = 0.0):
    from langchain_openai import ChatOpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in .env")
    return ChatOpenAI(model=os.getenv('EVAL_MODEL', 'gpt-4o'), temperature=temperature, api_key=api_key)
