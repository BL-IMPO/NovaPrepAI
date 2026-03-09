import json
import os
from dotenv import load_dotenv

from google import genai
from pydantic import BaseModel, Field, RootModel
from typing import List, Optional, Tuple, Dict


load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))


class TaskArray7(RootModel):
    root: Tuple[
        str,    # 0: Correct answer (e.g., "5.")
        str,    # 1: Answer A
        str,    # 2: Answer B
        str,    # 3: Answer C
        str,    # 4: Answer D
        float,  # 5: Points (1.3, 1.6, or 2.0)
        List[str] # 6: Extra data array (e.g., ["None"] or ["SVG_GRAPH", "<svg>..."])
    ] = Field(
        description="A flat array containing answers, points, and extra_data. Order is critical: [Correct, A, B, C, D, E, points, [TYPE, content]]"
    )


class AIQuestionOutput7(BaseModel):
    question_text: str = Field(description="The actual text of newly generated question.")
    task_array: TaskArray7

class TaskArray8(RootModel):
    root: Tuple[
        str,    # 0: Correct answer (e.g., "5.")
        str,    # 1: Answer A
        str,    # 2: Answer B
        str,    # 3: Answer C
        str,    # 4: Answer D
        str,    # 5: Answer E (For math_1, the AI can just output "None" here)
        float,  # 6: Points (1.3, 1.6, or 2.0)
        List[str] # 7: Extra data array (e.g., ["None"] or ["SVG_GRAPH", "<svg>..."])
    ] = Field(
        description="A flat array containing answers, points, and extra_data. Order is critical: [Correct, A, B, C, D, E, points, [TYPE, content]]"
    )


class AIQuestionOutput8(BaseModel):
    question_text: str = Field(description="The actual text of newly generated question.")
    task_array: TaskArray8


def generate_text(example_text: str):
    prompt = f"""
    You are an expert ORT (Общереспубликанское тестирование) exam creator.
    Your task is to generate EXACTLY ONE NEW, UNIQUE text that tests the same underlying skill as the example, but uses completely DIFFERENT data.

    CRITICAL RULES:
    1. VARY THE DATA: You MUST change the underlying numbers, percentages, equations, and variables in the question text. Do not just copy the example.
    2. TEXT MUST EXIST IN REAL WORLD: Text must be from a book or publication and must suit the original text mean meanings.
    3. POINT START: You must put a _start point and _pause or _continue if it's necessary as in examole text.
    
    EXAMPLE TO MIMIC AND VARY:
    {example_text}"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={
            "temperature": 0.7,
        },
    )

    return response.text



def generate_question_from_template(question_id: str, example_q_text: str, example_array: list, test_type = "default") -> dict:
    """Clones a specific question using Structured Outputs and the TaskArray RootModel."""
    example_dict = {example_q_text: example_array}
    example_json_str = json.dumps(example_dict, ensure_ascii=False, indent=2)

    required_points = next(item for item in reversed(example_array) if isinstance(item, float))

    selected_schema = AIQuestionOutput7.model_json_schema()

    # Dynamically select the schema
    if test_type == "math_2":
        selected_schema = AIQuestionOutput8.model_json_schema()
        rule_six = "6. You MUST provide 5 answer options (A, B, C, D, E)."
    elif test_type == "math_1":
        rule_six = '6. CRITICAL: If the question text in the example is exactly "none", your generated `question_text` MUST also be exactly the string "none" in lowercase. Do not write a real question, just output "none".'
    else:
        rule_six = "6. You MUST provide exactly 4 answer options."

    prompt = f"""
    You are an expert ORT (Общереспубликанское тестирование) exam creator.
    Your task is to generate EXACTLY ONE NEW, UNIQUE question that tests the same underlying skill as the example, but uses completely DIFFERENT data.

    CRITICAL RULES:
    1. VARY THE DATA: You MUST change the underlying numbers, percentages, equations, and variables in the question text. Do not just copy the example.
    2. UPDATE EXTRA DATA: If the `extra_data` array contains an SVG graph, HTML table, or text block, you MUST modify the values, numbers, and percentages inside that content to perfectly match your new question. 
       - For SVGs: Change the `<text>` values or coordinates to reflect the new math, but KEEP the SVG syntax valid.
       - For HTML Tables: Change the `<td>` numerical values.
    3. RECALCULATE ANSWERS: You must recalculate the correct answer and all distractors (Options A-D) based entirely on your newly generated numbers.
    4. POINTS: The points MUST remain exactly: {required_points}
    5. FORMAT: The `extra_data` format MUST preserve the original tag structure (e.g., ["SVG_GRAPH", "<svg>..."]).
    {rule_six}
    
    EXAMPLE TO MIMIC AND VARY:
    {example_json_str}
    """
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config={
            'response_mime_type': "application/json",
            'response_json_schema': selected_schema,
            'temperature': 0.7,
        },
    )

    ai_data = json.loads(response.text)

    return {
        question_id: {
            ai_data["question_text"]: ai_data["task_array"]
        }
    }
