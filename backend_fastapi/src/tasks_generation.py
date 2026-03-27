import json
import os

from click import prompt
from dotenv import load_dotenv

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, RootModel
from typing import List, Optional, Tuple, Dict

from pyexpat.errors import messages

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv('OPEN_AI_GPT_5_MINI_API_KEY'))


class ValidationResult(BaseModel):
    valid: bool
    reason: str


class TaskDetails7(BaseModel):
    correct_answer: str = Field(description="Correct answer (e. g., '5.')")
    answer_a: str = Field(description="Answer A")
    answer_b: str = Field(description="Answer B")
    answer_c: str = Field(description="Answer C")
    answer_d: str = Field(description="Answer D")
    points: float = Field(description="Points (1.3, 1.6, or 2.0)")
    extra_data: List[str] = Field(description="Extra data array (e.g., ['None'] or ['SVG_GRAPH', '<svg>...'])")


class AIQuestionOutput7(BaseModel):
    question_text: str = Field(description="The exact text of the question ONLY. STRICT RULE: DO NOT add instructions like 'Выберите пару', 'Решите', or 'Найдите'. Mimic the exact formatting length of the example.")
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
    question_text: str = Field(description="The exact text of the question ONLY. STRICT RULE: DO NOT add instructions like 'Выберите пару', 'Решите', or 'Найдите'. Mimic the exact formatting length of the example.")
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

async def generate_additional_data(data_type: str, description: str) -> str:
    """
    Acts as a specialized rendere. Takes a description of a graph/table and returns ONLY the raw SVG or HTML code.
    """

    if data_type == "SVG_GRAPH":
        system_instructions = """
                    You are an expert SVG developer for math and physics exams.
                    Your task is to generate clean, highly accurate, and scalable SVG code based on the user's description.

                    CRITICAL RULES:
                    1. Output ONLY the raw <svg>...</svg> code. No markdown formatting (do not use ```xml or ```svg).
                    2. Do not include any conversational text.
                    3. You MUST calculate the extreme bounds of all elements (including text labels) and set an accurate `viewBox` with at least 20px padding.
                    4. NEVER hardcode absolute `width` and `height` (e.g., width="500"). ALWAYS use width="100%" height="100%".
                    5. Add `overflow="visible"` to the <svg> tag.
                    6. Use standard math conventions (e.g., right angle squares, clear axes, neat text labels for vertices/sides).
                    7. AESTHETIC RULE: NEVER draw Cartesian coordinates (like "(50,110)") next to vertex labels. Just draw the letter itself (e.g., "A", "B").
                    8. AESTHETIC RULE: Ensure text elements DO NOT OVERLAP. Space labels and values cleanly.
                    """
    elif data_type == "HTML_TABLE":
        system_instructions = """
            You are an expert HTML developer.
            Your task is to generate a clean Bootstrap 5 HTML table based on the user's description.

            CRITICAL RULES:
            1. Output ONLY the raw <table>...</table> code. No markdown formatting.
            2. Do not include any conversational text.
            3. Add standard bootstrap classes: class="table table-bordered table-hover text-center align-middle".
            """
    else:
        # Fallback for FORMULA or TEXT_BLOCK, though usually the main LLM can handle these easily.
        return description

    prompt = f"Description of the required visual:\n{description}"


    response = await client.chat.completions.create(
        model="gpt-5",  # or gpt-4o depending on your client setup
        messages=[
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
    )

    raw_output = response.choices[0].message.content.strip()
    if raw_output.startswith("```"):
        lines = raw_output.split("\n")
        raw_output = "\n".join(lines[1:-1])

    return raw_output.strip()



async def generate_question_from_template(question_id: str, example_q_text: str, example_array: list, test_type="default") -> dict:
    """Clones a specific question using Structured Outputs and tailored rules per test type."""
    example_dict = {example_q_text: example_array}
    example_json_str = json.dumps(example_dict, ensure_ascii=False, indent=2)

    # Determine schema based on required number of options
    if test_type == "math_2":
        selected_schema = AIQuestionOutput8
    else:
        selected_schema = AIQuestionOutput7

    # --- DOMAIN-SPECIFIC RULES ENGINE ---
    type_specific_rules = ""

    if test_type == "analogy":
        type_specific_rules = """
            CRITICAL TASK CONCEPT: VERBAL ANALOGIES & SENTENCE COMPLETION (Аналогии и дополнение предложений)
            - STRICT STRUCTURAL CLONE RULE: You MUST analyze the format of the example and mimic its exact task type:
              * IF the example is a word pair (e.g., "слово : другое слово"), generate a new word pair analogy. NO NUMBERS OR MATH ALLOWED.
              * IF the example is a text/sentence with missing words (e.g., "_____ пошел в _____"), generate a sentence completion task testing vocabulary/logic.
            - Use Russian words. Maintain the exact formatting of the example.
            - The relationship (synonyms, antonyms) or contextual fit must be logically sound and unambiguous.
            - You MUST generate exactly 4 answer options.
            - Answer options MUST NOT contain the same pair of words as in question. And MUST NOT contain any of words from question in answers.
            
            CRITICAL EXTRA_DATA RULES: 
            If extra_data is needed, write the ACTUAL raw content (e.g., exact text). DO NOT write descriptions.
            """

    elif test_type == "russian_grammar":
        type_specific_rules = """
            CRITICAL TASK CONCEPT: RUSSIAN GRAMMAR & SPELLING (Практическая грамматика)
            - STRICT STRUCTURAL CLONE RULE: Identify the specific grammatical rule tested in the example (e.g., commas, prefixes, finding the incorrect sentence, missing letters). Your generated question MUST test the EXACT SAME grammatical rule and use the SAME format.
            - Focus purely on Russian syntax, punctuation, spelling, or vocabulary context.
            - Keep the difficulty appropriate for high school graduation exams.
            - You MUST generate exactly 4 answer options.
            
            CRITICAL EXTRA_DATA RULES: 
            If extra_data is needed, write the ACTUAL raw content (e.g., exact text). DO NOT write descriptions.
            """
    elif test_type == "reading":
        type_specific_rules = """
            CRITICAL TASK CONCEPT: READING COMPREHENSION (Чтение и понимание)
            - STRICT STRUCTURAL CLONE RULE: Your question MUST match the exact sub-type of the example (e.g., if the example asks for the "main idea", you ask for the main idea; if it asks for "the meaning of a word in line X", you ask for a word's meaning in a specific line).
            - The generated question MUST relate directly to the provided TEXT_BLOCK in the extra_data.
            - Do not ask general knowledge questions; the answer must be derived purely from the text.
            - You MUST generate exactly 4 answer options.
            
            CRITICAL EXTRA_DATA RULES: 
            If extra_data is needed, write the ACTUAL raw content (e.g., exact text). DO NOT write descriptions.
            """
    elif test_type == "math_1":
        type_specific_rules = """
                    CRITICAL TASK CONCEPT: QUANTITATIVE COMPARISON (Количественное сравнение)
                    - This is NOT a standard multiple-choice question. Do not ask a direct question.
                    - STRICT FIELD MAPPING:
                      - 'question_text': The SHARED CONTEXT (e.g., "x > 5"). If the example's question_text is "none", your question_text MUST exactly be "none".
                      - 'answer_a': ONLY the raw mathematical expression for Column A.
                      - 'answer_b': ONLY the raw mathematical expression for Column B.
                      - 'answer_c' & 'answer_d': Remaining distractors/text (usually "=" or empty).
                    - STRICT ZERO-BOILERPLATE FOR COLUMNS: DO NOT label the columns.
                    - You MUST generate exactly 4 options.
                    
                    CRITICAL MATHJAX/LATEX FORMATTING:
                    - You MUST format ALL mathematical expressions, fractions, powers, and equations using LaTeX wrapped in \\( and \\). 
                    - BAD: 0,75^2
                    - GOOD: \\( 0,75^2 \\)
                    - BAD: 9/16
                    - GOOD: \\( \\frac{9}{16} \\)
                    
                    CRITICAL EXTRA_DATA RULES (DELEGATED RENDERING):
                    If the task requires an SVG_GRAPH or HTML_TABLE, DO NOT WRITE RAW CODE. 
                    Instead, set the extra_data tag (e.g., "SVG_GRAPH") and for the content, write a highly detailed, explicit instruction prompt for a visual developer. 
                    Include exact coordinates, vertex names, side lengths, and what specific geometry or data must be drawn to make the problem solvable.
                    """
    elif test_type == "math_2":
        type_specific_rules = """
                    CRITICAL TASK CONCEPT: STANDARD MATHEMATICS (Математика)
                    - STRICT STRUCTURAL CLONE RULE: Identify the mathematical sub-topic in the example. Your generated question MUST test the EXACT SAME sub-topic.
                    - You MUST generate exactly 5 answer options (A, B, C, D, E).
                    - Ensure calculations are accurate and only one correct option exists.
                    
                    CRITICAL MATHJAX/LATEX FORMATTING:
                    - You MUST format ALL mathematical expressions, fractions, powers, and equations in the question text and answer options using LaTeX wrapped in \\( and \\). 
                    - Example: \\( x^2 + 2x = 0 \\) or \\( \\frac{1}{2} \\).
                    
                    CRITICAL EXTRA_DATA RULES (DELEGATED RENDERING):
                    If the task requires an SVG_GRAPH or HTML_TABLE, DO NOT WRITE RAW CODE. 
                    Instead, set the extra_data tag (e.g., "SVG_GRAPH") and for the content, write a highly detailed, explicit instruction prompt for a visual developer. 
                    Include exact coordinates, vertex names, side lengths, and what specific geometry or data must be drawn to make the problem solvable.
                    """
    else:
        type_specific_rules = """
            CRITICAL TASK CONCEPT: GENERAL MULTIPLE CHOICE
            - STRICT STRUCTURAL CLONE RULE: Generate a question matching the exact subject, sub-topic, and structure of the example.
            - You MUST generate exactly 4 answer options.
            """

    prompt = f"""
    You are an expert ORT exam creator.

    Your task is to generate ONE new question based on the example.

    IMPORTANT GENERATION PROCESS:
    Step 1 — Analyze the example question's core skill, format (e.g., analogy vs. fill-in-the-blank), and difficulty.
    Step 2 — Decide if the task requires extra_data (SVG_GRAPH, HTML_TABLE, TEXT_BLOCK, FORMULA).
    Step 3 — If extra_data exists, modify the values so it matches the new question.
    Step 4 — Write the new question, recalculate the correct answer, and create plausible distractors.

    CRITICAL RULES:
    1. STRUCTURAL CLONE: You MUST NOT change the fundamental type of task. If the example is a sentence-completion task, your output must be a sentence-completion task. If it is a geometry problem, make a geometry problem.
    2. Change all core variables, numbers, or words to create a truly unique question.
    3. Ensure exactly ONE correct answer.
    4. If extra_data is used, the question MUST depend on it. If it is removed, the problem must become unsolvable.
    5. ZERO-BOILERPLATE POLICY: DO NOT add conversational instructions.
       - BAD: "Выберите правильный вариант: кошка : мяукать"
       - GOOD: "кошка : мяукать"
       - BAD: "Решите уравнение: 2x = 4"
       - GOOD: "2x = 4"
       Match the exact brevity and style of the example string.

    {type_specific_rules}

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

    final_extra_data = details.extra_data

    if final_extra_data and isinstance(final_extra_data, list) and len(final_extra_data) >= 2:
        data_tag = final_extra_data[0]
        data_description = final_extra_data[1]

        if data_tag in ["SVG_GRAPH", "HTML_TABLE"]:
            generated_code = await generate_additional_data(data_tag, data_description)

            final_extra_data = [data_tag, generated_code]

    if test_type == "math_2":
        task_array = [
            details.correct_answer, details.answer_a, details.answer_b,
            details.answer_c, details.answer_d, details.answer_e,
            details.points, final_extra_data,
        ]
    else:
        task_array = [
            details.correct_answer, details.answer_a, details.answer_b,
            details.answer_c, details.answer_d,
            details.points, final_extra_data,
        ]

    return {
        question_id: {
            ai_data.question_text: task_array
        }
    }


async def ai_chat_response(task_context: str, chat_history_list: list):
    system_blueprint = f"""
    You are an expert ORT (Общереспубликанское тестирование) tutor.
    Your goal is to help the student understand their mistake on this specific task.

    TASK CONTEXT:
    {task_context}

    STRICT RULES FOR YOUR BEHAVIOR:
    1. ANALYZE THE CONVERSATION HISTORY FIRST:
       - IF THIS IS THE VERY FIRST MESSAGE: Give the correct answer, explain why it's right (using formulas/rules), and ask exactly ONE guiding question to test their understanding.
       - IF THIS IS A FOLLOW-UP MESSAGE: DO NOT repeat the initial solution. Directly address the student's new reply. Answer their specific question, correct their logic if they are wrong, or praise them if they figured it out. 
    2. Keep your explanations short and focused (under 3-4 sentences).
    3. Be encouraging but firm about the rules of the subject.
    4. Always respond in Russian.
    5. Act as a natural conversational partner. Let the dialogue flow logically.
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
    )

    return response.choices[0].message.content


def strict_structure_validation(task_array, test_type):
    # Determine expected array length based on test type
    if test_type == "math_2":
        expected_length = 8  # correct, A, B, C, D, E, points, extra_data
    else:
        expected_length = 7  # correct, A, B, C, D, points, extra_data

    # 1. Check if the array has the correct number of elements
    if len(task_array) != expected_length:
        return False, f"wrong array length. Expected {expected_length}, got {len(task_array)}"

    # 2. Check if points is a float
    if not isinstance(task_array[-2], float):
        # Attempt to cast it if the AI returned an int or string by accident
        try:
            task_array[-2] = float(task_array[-2])
        except (ValueError, TypeError):
            return False, "points could not be converted to float"

    # 3. Check if extra_data is a list
    if not isinstance(task_array[-1], list):
        return False, "extra_data is not a list"

    return True, "ok"


async def ai_validate_question(question, task_array, test_type="default"):
    # Cleanly extract the components for the AI
    correct_ans = task_array[0]
    options = task_array[1:-2]
    extra_data = task_array[-1]

    options_formatted = "\n".join([f"- {opt}" for opt in options])

    prompt = f"""
You are a practical ORT exam reviewer. Your ONLY job is to check if a student can solve this task.

QUESTION:
{question}

OPTIONS:
{options_formatted}

INTENDED CORRECT ANSWER:
{correct_ans}

EXTRA DATA (Graphs/Tables/Text):
{extra_data}

RULES FOR VALIDATION:
1. Solvability: Is the problem mathematically/logically solvable based on the question and extra data?
2. Extra Data Integration: If EXTRA DATA is present, does it correctly align with the question?
3. DO NOT fail the question for minor formatting issues, typos, or duplicate placeholder options (e.g., multiple '=' signs). 
4. If test_type is "math_1", the question text might be 'none'. This is perfectly valid.

If the core logic is sound and a student could figure it out, return valid=true.
Return JSON.
"""
    response = await client.beta.chat.completions.parse(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=ValidationResult
    )

    return response.choices[0].message.parsed


async def validate_reading_text(text):

    prompt = f"""
Check this reading passage.

{text}

Reject if:
- nonsense
- grammar errors
- unreadable

Return JSON valid true/false.
"""
    response = await client.beta.chat.completions.parse(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format=ValidationResult
    )

    return response.choices[0].message.parsed