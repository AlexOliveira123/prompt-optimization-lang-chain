# type: ignore

import json
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from utils import get_eval_llm

load_dotenv()


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end > start:
            try:
                return json.loads(response_text[start:end])
            except json.JSONDecodeError:
                pass
        print(f"⚠️  Could not extract JSON: {response_text[:200]}...")
        return {"score": 0.0, "reasoning": "Error processing response"}


def _call_evaluator(prompt_text: str, llm) -> Dict[str, Any]:
    response = llm.invoke([HumanMessage(content=prompt_text)])
    return extract_json_from_response(response.content)


def evaluate_f1_score(question: str, answer: str, reference: str, llm=None) -> Dict[str, Any]:
    if llm is None:
        llm = get_eval_llm(temperature=0)
    prompt = f"""You are an expert evaluator measuring semantic overlap between a model response and a reference answer.

TASK CONTEXT (input used to generate both responses):
{question}

REFERENCE ANSWER (ground truth):
{reference}

MODEL-GENERATED RESPONSE (to evaluate):
{answer}

Evaluate using these precise definitions:

PRECISION = What fraction of the key information in the MODEL RESPONSE is also present in the REFERENCE?
- List the key claims/criteria/requirements stated in the model response
- For each claim, check if the reference expresses the same idea (paraphrasing and synonyms COUNT as matches)
- Score = matched_claims / total_claims_in_model_response

RECALL = What fraction of the key information in the REFERENCE is covered by the MODEL RESPONSE?
- List the key claims/criteria/requirements stated in the reference
- For each reference claim, check if the model response covers the same idea (paraphrasing and synonyms COUNT as matches)
- Score = reference_claims_covered_by_model / total_claims_in_reference

Important rules:
- Semantic equivalence counts as a match even if wording differs
- Partial coverage of a claim counts as 0.5
- Ignore formatting differences (bullet points, line breaks, section headers)
- Focus on behavioral requirements and user value, not exact phrasing

Return ONLY valid JSON:
{{"precision": <0.0-1.0>, "recall": <0.0-1.0>, "reasoning": "<up to 100 words>"}}"""
    try:
        result = _call_evaluator(prompt, llm)
        precision = float(result.get("precision", 0.0))
        recall = float(result.get("recall", 0.0))
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        return {"score": round(f1, 4), "precision": round(precision, 4), "recall": round(recall, 4), "reasoning": result.get("reasoning", "")}
    except Exception as e:
        print(f"❌ Error evaluating F1-Score: {e}")
        return {"score": 0.0, "precision": 0.0, "recall": 0.0, "reasoning": str(e)}


def evaluate_clarity(question: str, answer: str, reference: str, llm=None) -> Dict[str, Any]:
    if llm is None:
        llm = get_eval_llm(temperature=0)
    prompt = f"""You are an evaluator measuring the CLARITY of an AI-generated user story.

QUESTION (bug report):
{question}

GENERATED RESPONSE:
{answer}

REFERENCE:
{reference}

Evaluate clarity on 4 criteria, each scored 0.0–1.0. Final score = average of 4:
1. Organization: Is the response well-structured with clear sections (Title, User Story, Acceptance Criteria, Notes)?
2. Simple language: Is it written in plain, professional language without excessive jargon?
3. Absence of ambiguity: Are requirements stated clearly and unambiguously?
4. Conciseness: Is information presented efficiently without unnecessary repetition?

Return ONLY valid JSON:
{{"score": <0.0-1.0>, "reasoning": "<up to 100 words>"}}"""
    try:
        result = _call_evaluator(prompt, llm)
        return {"score": round(float(result.get("score", 0.0)), 4), "reasoning": result.get("reasoning", "")}
    except Exception as e:
        print(f"❌ Error evaluating Clarity: {e}")
        return {"score": 0.0, "reasoning": str(e)}


def evaluate_precision(question: str, answer: str, reference: str, llm=None) -> Dict[str, Any]:
    if llm is None:
        llm = get_eval_llm(temperature=0)
    prompt = f"""You are an evaluator detecting HALLUCINATIONS and irrelevant content in AI responses.

QUESTION (bug report):
{question}

GENERATED RESPONSE:
{answer}

GROUND TRUTH:
{reference}

Evaluate on 3 criteria, each scored 0.0–1.0. Final score = average of 3:
1. Absence of hallucinations: Does the response avoid inventing facts, metrics, or requirements not present in the bug report or reasonably inferable from it?
2. Focus on the question: Does the response stay focused on the actual bug reported without drifting to unrelated topics?
3. Factual correctness: Are all stated facts consistent with the bug report and ground truth?

Note: Adding behavioral requirements that logically follow from the bug (even if not in the reference) should NOT be penalized if they are reasonable inferences.

Return ONLY valid JSON:
{{"score": <0.0-1.0>, "reasoning": "<up to 100 words>"}}"""
    try:
        result = _call_evaluator(prompt, llm)
        return {"score": round(float(result.get("score", 0.0)), 4), "reasoning": result.get("reasoning", "")}
    except Exception as e:
        print(f"❌ Error evaluating Precision: {e}")
        return {"score": 0.0, "reasoning": str(e)}
