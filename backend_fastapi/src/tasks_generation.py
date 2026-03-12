import json
import os
from dotenv import load_dotenv

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, RootModel
from typing import List, Optional, Tuple, Dict

from pyexpat.errors import messages

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv('OPEN_AI_GPT_5_MINI_API_KEY'))


class TaskDetails7(BaseModel):
    correct_answer: str = Field(description="Correct answer (e. g., '5.')")
    answer_a: str = Field(description="Answer A")
    answer_b: str = Field(description="Answer B")
    answer_c: str = Field(description="Answer C")
    answer_d: str = Field(description="Answer D")
    points: float = Field(description="Points (1.3, 1.6, or 2.0)")
    extra_data: List[str] = Field(description="Extra data array (e.g., ['None'] or ['SVG_GRAPH', '<svg>...'])")


class AIQuestionOutput7(BaseModel):
    question_text: str = Field(description="The actual text of newly generated question.")
    task_details: TaskDetails7

class TaskDetails8(BaseModel):
    correct_answer: str = Field(description="Correct answer (e. g., '5.')")
    answer_a: str = Field(description="Answer A")
    answer_b: str = Field(description="Answer B")
    answer_c: str = Field(description="Answer C")
    answer_d: str = Field(description="Answer D")
    answer_e: str = Field(description="Answer E")
    points: float = Field(description="Points (1.3, 1.6, or 2.0)")
    extra_data: List[str] = Field(description="Extra data array (e.g., ['None'] or ['SVG_GRAPH', '<svg>...'])")


class AIQuestionOutput8(BaseModel):
    question_text: str = Field(description="The actual text of newly generated question.")
    task_details: TaskDetails8


async def generate_text(example_text: str):
    prompt = f"""
    You are an expert ORT exam text creator.
    
    Generate ONE new unique text similar in skill to the example.
    
    Rules:
    1. TEXT MUST EXIST IN REAL WORLD: Text must be from a book or publication and must suit the original text mean meanings.
    2. Preserve the structure and difficulty.
    3. Keep realistic language suitable for textbooks.
    4. Maintain _start, _pause, _continue markers if needed.
    
    Example:
    {example_text}
    """

    response = await client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        #temperature=0.9,
    )

    return response.choices[0].message.content

async def generate_question_from_template(question_id: str, example_q_text: str, example_array: list, test_type = "default") -> dict:
    """Clones a specific question using Structured Outputs and the TaskArray RootModel."""
    example_dict = {example_q_text: example_array}
    example_json_str = json.dumps(example_dict, ensure_ascii=False, indent=2)

    required_points = next(item for item in reversed(example_array) if isinstance(item, float))

    selected_schema = AIQuestionOutput7

    # Dynamically select the schema
    if test_type == "math_2":
        selected_schema = AIQuestionOutput8
        rule_six = "You MUST generate 5 answers (A,B,C,D,E)."
    elif test_type == "math_1":
        rule_six = """
        CRITICAL TASK CONCEPT: QUANTITATIVE COMPARISON (Количественное сравнение)
        This is NOT a standard multiple-choice question. Do not ask a direct question.
        The student's goal is to compare the value of Column A against the value of Column B.

        STRICT FIELD MAPPING FOR MATH_1:
        - 'question_text': This is the SHARED CONTEXT or CONDITION (e.g., "x > 5 and y < 10", or describing a geometric figure). It is NEVER a direct question. If the example's question_text is "none", your generated question_text MUST exactly be "none".
        - 'answer_a': This represents "Колонка А" (Column A). It must be an expression, formula, or statement to be evaluated (e.g., "90% от числа 45"). DO NOT put the final calculated number here if the challenge is to calculate it.
        - 'answer_b': This represents "Колонка Б" (Column B). It must be the second expression to be compared against Column A.
        - 'answer_c' and 'answer_d': These will hold the remaining text or distractors as formatted in the example.

        THE RULE: The puzzle is in the columns. You provide the context in 'question_text', and the two expressions to compare in 'answer_a' and 'answer_b'.
                """
    else:
        rule_six = "You MUST generate exactly 4 answer options."

    prompt = f"""
You are an expert ORT exam creator.

Your task is to generate ONE new question based on the example.

IMPORTANT GENERATION PROCESS:

Step 1 — Analyze the example question.
Step 2 — Decide if the task requires extra_data
    Possible types:
    SVG_GRAPH
    HTML_TABLE
    TEXT_BLOCK
    FORMULA
    IMAGE_URL
    LARGE_TEXT

Step 3 — If extra_data exists:
Modify the values so it matches the new question.

Examples:
SVG_GRAPH → change coordinates, numbers, labels
HTML_TABLE → change <td> numeric values
FORMULA → modify variables or constants

Step 4 — Write the question referencing the extra data.

CRITICAL RULES:

1. Change ALL numbers and variables.
2. Recalculate correct answer and distractors.
3. Points MUST remain exactly: {required_points}
4. Keep the exact tuple format for task_array.
5. extra_data structure must stay the same.

If extra_data is used, the question MUST depend on it.

If the diagram/table is removed, the problem must become unsolvable.

{rule_six}

EXAMPLE QUESTION:
{example_json_str}
    """
    response = await client.beta.chat.completions.parse(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=selected_schema,
       # temperature=0.9,
    )

    ai_data = response.choices[0].message.parsed
    details = ai_data.task_details

    if test_type == "math_2":
        task_array = [
            details.correct_answer, details.answer_a, details.answer_b,
            details.answer_c, details.answer_d, details.answer_e,
            details.points, details.extra_data,
        ]
    else:
        task_array = [
            details.correct_answer, details.answer_a, details.answer_b,
            details.answer_c, details.answer_d,
            details.points, details.extra_data,
        ]

    return {
        question_id: {
            ai_data.question_text: task_array
        }
    }


async def ai_chat_response(task_context: str, chat_history_list: list):
    system_blueprint = f"""
    You are an expert ORT (Общереспубликанское тестирование) tutor.
    Your goal is to help the student understand their mistake on this specific task:

    TASK CONTEXT:
    {task_context}

    STRICT RULES:
    1. GIVE THE RIGHT ANSWER and explain why it's the right one. Give formulas or examples.
    2. Ask a guiding question to help the student find the logic error themselves.
    3. Keep your explanations under 3 sentences.
    4. Be encouraging but firm about the rules of the subject.
    5. Response in Russian language.
    """

    messages = [
        {"role": "system", "content": system_blueprint}
    ]

    for msg in chat_history_list:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    response = await client.chat.completions.create(
        model="gpt-5-mini",
        messages=messages,
        #temperature=0.9,
    )

    return response.choices[0].message.content