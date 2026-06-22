# type: ignore

import os
import sys
import json
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain import hub
from utils import check_env_vars, print_section_header, get_llm, get_eval_llm
from metrics import evaluate_f1_score, evaluate_clarity, evaluate_precision

load_dotenv()


def _format_score(score: float, threshold: float = 0.8) -> str:
    return f"{score:.2f} {'✓' if score >= threshold else '✗'}"


def load_dataset_from_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    examples = []
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    examples.append(json.loads(line))
        return examples
    except FileNotFoundError:
        print(f"❌ File not found: {jsonl_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSONL: {e}")
        return []
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return []


def create_evaluation_dataset(client: Client, dataset_name: str, jsonl_path: str) -> None:
    print(f"Creating evaluation dataset: {dataset_name}...")
    examples = load_dataset_from_jsonl(jsonl_path)
    if not examples:
        print("❌ No examples loaded from .jsonl file")
        return
    print(f"   ✓ Loaded {len(examples)} examples from {jsonl_path}")
    try:
        existing = next(
            (ds for ds in client.list_datasets(dataset_name=dataset_name) if ds.name == dataset_name),
            None,
        )
        if existing:
            # FIX: delete and recreate so references always stay in sync with the JSONL file
            client.delete_dataset(dataset_id=existing.id)
            print(f"   ✓ Deleted existing dataset '{dataset_name}' — recreating with updated references")

        dataset = client.create_dataset(dataset_name=dataset_name)
        for example in examples:
            client.create_example(dataset_id=dataset.id, inputs=example["inputs"], outputs=example["outputs"])
        print(f"   ✓ Dataset created with {len(examples)} examples")
    except Exception as e:
        print(f"   ⚠️  Error creating dataset: {e}")


def evaluate_prompt(prompt_name: str, dataset_name: str, client: Client) -> Dict[str, float]:
    print(f"\n🔍 Evaluating: {prompt_name}")
    try:
        print(f"   Pulling prompt from LangSmith Hub: {prompt_name}")
        prompt_template = hub.pull(prompt_name)
        print("   ✓ Prompt loaded successfully")
    except Exception as e:
        print(f"❌ Could not load prompt '{prompt_name}': {e}")
        raise

    try:
        examples = list(client.list_examples(dataset_name=dataset_name))
        print(f"   Dataset: {len(examples)} examples")

        llm = get_llm(temperature=0)
        eval_llm = get_eval_llm(temperature=0)
        chain = prompt_template | llm

        f1_scores, clarity_scores, precision_scores = [], [], []
        print("   Evaluating examples...")

        for i, example in enumerate(examples, 1):
            try:
                inputs = example.inputs if hasattr(example, 'inputs') else {}
                outputs = example.outputs if hasattr(example, 'outputs') else {}
                answer = chain.invoke(inputs).content
                reference = outputs.get("reference", "") if isinstance(outputs, dict) else ""
                question = inputs.get("question", inputs.get("bug_report", inputs.get("pr_title", "N/A"))) if isinstance(inputs, dict) else "N/A"
            except Exception as e:
                print(f"      ⚠️  Error on example {i}: {e}")
                continue

            if not answer:
                continue

            f1 = evaluate_f1_score(question, answer, reference, eval_llm)
            clarity = evaluate_clarity(question, answer, reference, eval_llm)
            precision = evaluate_precision(question, answer, reference, eval_llm)
            f1_scores.append(f1["score"])
            clarity_scores.append(clarity["score"])
            precision_scores.append(precision["score"])
            print(f"      [{i}/{len(examples)}] F1:{f1['score']:.2f} (P:{f1['precision']:.2f} R:{f1['recall']:.2f}) Clarity:{clarity['score']:.2f} Precision:{precision['score']:.2f}")

        avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
        avg_clarity = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0.0
        avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0

        return {
            "helpfulness": round((avg_clarity + avg_precision) / 2, 4),
            "correctness": round((avg_f1 + avg_precision) / 2, 4),
            "f1_score": round(avg_f1, 4),
            "clarity": round(avg_clarity, 4),
            "precision": round(avg_precision, 4),
        }
    except Exception as e:
        print(f"   ❌ Evaluation error: {e}")
        return {"helpfulness": 0.0, "correctness": 0.0, "f1_score": 0.0, "clarity": 0.0, "precision": 0.0}


def display_results(prompt_name: str, scores: Dict[str, float]) -> bool:
    print("\n" + "=" * 50)
    print(f"Prompt: {prompt_name}")
    print("=" * 50)
    print("\nDerived Metrics:")
    print(f"  - Helpfulness: {_format_score(scores['helpfulness'])}")
    print(f"  - Correctness: {_format_score(scores['correctness'])}")
    print("\nBase Metrics:")
    print(f"  - F1-Score:    {_format_score(scores['f1_score'])}")
    print(f"  - Clarity:     {_format_score(scores['clarity'])}")
    print(f"  - Precision:   {_format_score(scores['precision'])}")
    average = sum(scores.values()) / len(scores)
    print("\n" + "-" * 50)
    print(f"📊 OVERALL AVERAGE: {average:.4f}")
    print("-" * 50)
    passed = all(s >= 0.8 for s in scores.values()) and average >= 0.8
    if passed:
        print("\n✅ STATUS: PASSED - All metrics >= 0.8")
    else:
        failed = [name for name, s in scores.items() if s < 0.8]
        print("\n❌ STATUS: FAILED")
        if failed:
            print(f"⚠️  Metrics below 0.8: {', '.join(failed)}")
        print(f"⚠️  Current average: {average:.4f} | Required: 0.8000")
    return passed


def main():
    print_section_header("OPTIMIZED PROMPT EVALUATION")
    print(f"Main Model: {os.getenv('LLM_MODEL', 'gpt-4o-mini')}")
    print(f"Evaluation Model: {os.getenv('EVAL_MODEL', 'gpt-4o')}\n")

    if not check_env_vars(["LANGSMITH_API_KEY", "OPENAI_API_KEY"]):
        return 1

    jsonl_path = "datasets/bug_to_user_story_optimized.jsonl"
    if not Path(jsonl_path).exists():
        print(f"❌ Dataset file not found: {jsonl_path}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "")
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB not configured in .env")
        return 1

    client = Client()
    project_name = os.getenv("LANGSMITH_PROJECT", "prompt-optimization-challenge-resolved")
    dataset_name = f"{project_name}-eval"
    create_evaluation_dataset(client, dataset_name, jsonl_path)

    prompt_name = f"{username}/bug_to_user_story_v2"
    try:
        scores = evaluate_prompt(prompt_name, dataset_name, client)
        passed = display_results(prompt_name, scores)
    except Exception as e:
        print(f"\n❌ Failed to evaluate '{prompt_name}': {e}")
        passed = False

    print("\n" + "=" * 50)
    if passed:
        print("✅ All metrics >= 0.8!")
        print(f"\nCheck at: https://smith.langchain.com/projects/{project_name}")
        return 0
    else:
        print("⚠️  Some metrics are below 0.8")
        print("\nRefinement: edit the YAML → push → evaluate again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
