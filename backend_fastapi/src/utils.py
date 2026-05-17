import json
import random
import os
import asyncio
from typing import Dict, List, Any

from tasks_generation import generate_question_from_template, generate_text, strict_structure_validation, ai_validate_question, validate_reading_text


class TestORT:
    def __init__(self):
        self.base_point = 1
        self.test_time_limits = {
            "math_1": 30 * 60,  # in seconds
            "math_2": 60 * 60,
            "analogy": 30 * 60,
            "reading": 60 * 60,
            "grammar": 35 * 60,
            "full_test": 3 * 60 * 60,  # 3 hours
            "special_math": 80 * 60,
            "special_biology": 60 * 60,
            "special_chemistry": 80 * 60,
            "special_english": 60 * 60,
            "special_history": 60 * 60,
            "special_physics": 80 * 60,
            "special_russian_grammar": 60 * 60,
            "special_kyrgyz_grammar": 60 * 60,
        }

    def initialize_default_file(self, test_type):
        default_files = {'analogy': 'default_analogy_tasks.json',
                         'math_1': 'default_math_1_tasks.json',
                         'math_2': 'default_math_2_tasks.json',
                         'reading': 'default_reading_tasks.json',
                         'russian_grammar': 'default_russian_grammar_tasks.json',
                         'texts': 'default_texts_reading_tasks.json'}

        try:
            with open("src/default_data_for_tests/" + default_files.get(test_type, ""), "r", encoding="utf-8") as f:
                data = json.load(f)
                test = data.get(test_type, {})
            print(f"Loaded {len(test)} {test_type}")
        except Exception as e:
            print(f"Could not load {test_type} tasks: {e}")
            test = {}

        return test

    async def _generate_tasks(self, qid: str, q_text: str, data: List, q_type="default"):
        """Asynchronously generates single tasks by given example."""
        MAX_ATTEMPTS = 2

        for attempt in range(MAX_ATTEMPTS):

            try:
                print(f"Generating AI version for {qid}...")

                ai_result = await generate_question_from_template(qid, q_text, data, q_type)

                new_q_text = list(ai_result[qid].keys())[0]
                new_data = ai_result[qid][new_q_text]

                # structure check
                ok, reason = strict_structure_validation(new_data, q_type)

                if not ok:
                    print(f"Missed structure for {qid}!")
                    continue

                # ai validation
                val1 = await ai_validate_question(new_q_text, new_data, q_type)

                if not val1.valid:
                    print(f"Problem on first validation for {qid}!")
                    print(f"PROBLEM: {val1.reason}")
                    continue

                print(f"Success for {qid}!")

                return new_q_text, new_data

            except Exception as e:
                print(f"AI generation failed for {qid}, using default. Error: {e}")

        return q_text, data

    def _prepare_answers(self, data: List, q_num: int, q_type: str):
        """Preparing answers for tasks."""
        val = str(data[0]).strip()
        answers = [str(data[i]).strip() for i in range(1, q_num + 1)]
        points = float(data[q_num + 1])
        extra_data = data[q_num + 2] if len(data) > 6 else ["None"]

        # Safely find correct index
        try:
            correct_index = answers.index(val)
        except ValueError:
            correct_index = 0

        if q_type != "math_1":
            return answers + [points, extra_data, correct_index]
        else:
            return [answers[0], answers[1], "", "", correct_index, points, extra_data]

    def _generate_answers(self, num_answers: int = 4) -> List[Any]:
        """Generate dummy answers with first being correct (for special tests)"""
        answers = []
        correct_answer = f"Correct Answer {random.randint(1, 100)}"
        answers.append(correct_answer)

        for i in range(1, num_answers):
            answers.append(f"Option {chr(64 + i)}")

        answers.append(0)
        answers.append(self.base_point + random.random())

        return answers

    async def get_test_data(self, test_type: str) -> Dict:
        """Get test data including time and a list of asynchronous question tasks"""
        if test_type not in self.test_time_limits:
            raise ValueError(f"Unknown test type: {test_type}")

        test_methods = {
            "math_1": self.standard_math_1_test,
            "math_2": self.standard_math_2_test,
            "analogy": self.standard_analogy_test,
            "reading": self.standard_reading_test,
            "grammar": self.standard_grammar_test,
            "special_math": self.special_math_test,
            "special_biology": self.special_biology_test,
            "special_chemistry": self.special_chemistry_test,
            "special_english": self.special_english_test,
            "special_history": self.special_history_test,
            "special_physics": self.special_physics_test,
            "special_russian_grammar": self.special_russian_grammar_test,
            "special_kyrgyz_grammar": self.special_kyrgyz_grammar_test,
        }

        tasks = []
        if test_type == "full_test":
            tasks.extend(await self.standard_math_1_test(len(tasks)))
            tasks.extend(await self.standard_math_2_test(len(tasks)))
            tasks.extend(await self.standard_analogy_test(len(tasks)))
            tasks.extend(await self.standard_reading_test(len(tasks)))
            tasks.extend(await self.standard_grammar_test(len(tasks)))
        else:
            tasks = await test_methods[test_type](0)

        # Return dict with time limit and the list of async tasks
        return {
            "time_limit": self.test_time_limits[test_type],
            "tasks": tasks,
        }

    async def _process_standard_q(self, global_idx: int, local_num: int, qid: str, q_text: str, data: List,
                                  test_category: str):
        """Helper to process individual standard questions asynchronously"""

        q_text, data = await self._generate_tasks(qid, q_text, data, test_category)

        if test_category == "math_1" and q_text.lower() == "none":
            question_text = f"{global_idx + 1}. Сравните значения в колонках А и Б"
        else:
            question_text = f"{global_idx + 1}. {q_text}"

        ans_count = 5 if test_category == "math_2" else 4
        answers = self._prepare_answers(data, ans_count, test_category)

        return {"index": global_idx, "question": question_text, "answers": answers}

    async def standard_math_1_test(self, start_idx=0) -> List:
        tasks_data = self.initialize_default_file('math_1')
        tasks = []
        local_num = 1
        for qid, inner_dict in tasks_data.items():
            for q_text, data in inner_dict.items():
                tasks.append(self._process_standard_q(start_idx, local_num, qid, q_text, data, "math_1"))
                start_idx += 1
                local_num += 1
        return tasks

    async def standard_math_2_test(self, start_idx=0) -> List:
        tasks_data = self.initialize_default_file('math_2')
        tasks = []
        local_num = 1
        for qid, inner_dict in tasks_data.items():
            for q_text, data in inner_dict.items():
                tasks.append(self._process_standard_q(start_idx, local_num, qid, q_text, data, "math_2"))
                start_idx += 1
                local_num += 1
        return tasks

    async def standard_analogy_test(self, start_idx=0) -> List:
        tasks_data = self.initialize_default_file('analogy')
        tasks = []
        local_num = 1
        for qid, inner_dict in tasks_data.items():
            for q_text, data in inner_dict.items():
                tasks.append(self._process_standard_q(start_idx, local_num, qid, q_text, data, "analogy"))
                start_idx += 1
                local_num += 1
        return tasks

    async def standard_grammar_test(self, start_idx=0) -> List:
        tasks_data = self.initialize_default_file('russian_grammar')
        tasks = []
        local_num = 1
        for qid, inner_dict in tasks_data.items():
            for q_text, data in inner_dict.items():
                tasks.append(self._process_standard_q(start_idx, local_num, qid, q_text, data, "russian_grammar"))
                start_idx += 1
                local_num += 1
        return tasks

    async def _process_reading_q(self, global_idx: int, local_num: int, qid: str, q_text: str, data: List, generated_texts: dict):
        """Helper to process reading questions with generated passages"""
        original_text_num = data[6][1]
        data_for_ai = data.copy()

        # Safely get the text, falling back to original if generation failed
        new_text_content = generated_texts.get(original_text_num,
                                               generated_texts.get(str(original_text_num), "Text generation error"))
        data_for_ai[6] = ["TEXT_BLOCK_LARGE", new_text_content]


        q_text, data_for_ai = await self._generate_tasks(qid, q_text, data_for_ai, "reading")

        question_text = f"{global_idx + 1}. {q_text}"
        answers = self._prepare_answers(data_for_ai, 4, "reading")
        return {"index": global_idx, "question": question_text, "answers": answers}

    async def standard_reading_test(self, start_idx=0) -> List:
        reading_tasks = self.initialize_default_file('reading')
        texts = self.initialize_default_file('texts')

        async def fetch_text(k, v):
            print(f"Generating new reading passage for {k}")
            #MAX_ATTEMPTS = 3
            #for _ in range(MAX_ATTEMPTS):
            new_text = await generate_text(v)

                # check validation
                #val = await validate_reading_text(new_text)

                #if not val.valid:
                    #print(f"Text validation failed for {k}!")
                    #continue

            return k, new_text

        # Generate texts concurrently
        text_coros = [fetch_text(k, v) for k, v in texts.items()]
        results = await asyncio.gather(*text_coros)
        generated_texts = dict(results)

        tasks = []
        local_num = 1
        for qid, inner_dict in reading_tasks.items():
            for q_text, data in inner_dict.items():
                tasks.append(self._process_reading_q(start_idx, local_num, qid, q_text, data, generated_texts))
                start_idx += 1
                local_num += 1
        print(tasks[-1])
        return tasks

    # ---------------- SPECIAL TESTS ---------------- #

    async def special_math_test(self, start_idx=0) -> List:
        tasks = []
        for num in range(1, 31):
            async def process(n=num, g=start_idx + num - 1):
                if n % 2 == 0:
                    extra_data = ["SVG_GRAPH",
                                  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 260" width="100%" height="100%"><rect width="100%" height="100%" fill="white"/><defs><pattern id="v-stripes" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#ffffff"/><line x1="3" y1="0" x2="3" y2="6" stroke="#688ab3" stroke-width="1.2"/></pattern><pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#ffffff"/><circle cx="4" cy="4" r="1.2" fill="#5890d6"/></pattern><pattern id="d-stripes" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#ffffff"/><line x1="0" y1="0" x2="0" y2="7" stroke="#737373" stroke-width="1.5"/></pattern></defs><g stroke="black" stroke-width="1.2" stroke-linejoin="round"><path d="M 130 130 L 130 15 A 115 115 0 0 1 197.6 37.0 Z" fill="#8f8f8f"/><path d="M 130 130 L 197.6 37.0 A 115 115 0 1 1 32.9 191.6 Z" fill="#ffffff"/><path d="M 130 130 L 32.9 191.6 A 115 115 0 0 1 23.1 87.7 Z" fill="url(#v-stripes)"/><path d="M 130 130 L 23.1 87.7 A 115 115 0 0 1 97.9 19.6 Z" fill="url(#dots)"/><path d="M 130 130 L 97.9 19.6 A 115 115 0 0 1 130 15 Z" fill="url(#d-stripes)"/></g><g font-family="Times New Roman, serif" font-size="16" fill="black"><text x="160" y="65">10%</text><text x="175" y="185">56%</text><text x="45" y="145">15%</text></g><g transform="translate(290, 40)"><rect x="0" y="0" width="20" height="20" fill="#8f8f8f" stroke="black" stroke-width="1.2"/><text x="30" y="16" font-family="Times New Roman, serif" font-size="16" fill="black">Белки</text><rect x="0" y="32" width="20" height="20" fill="#ffffff" stroke="black" stroke-width="1.2"/><text x="30" y="48" font-family="Times New Roman, serif" font-size="16" fill="black">Углеводы</text><rect x="0" y="64" width="20" height="20" fill="url(#v-stripes)" stroke="black" stroke-width="1.2"/><text x="30" y="80" font-family="Times New Roman, serif" font-size="16" fill="black">Пищевые волокна</text><rect x="0" y="96" width="20" height="20" fill="url(#dots)" stroke="black" stroke-width="1.2"/> <text x="30" y="112" font-family="Times New Roman, serif" font-size="16" fill="black">Вода</text><rect x="0" y="128" width="20" height="20" fill="url(#d-stripes)" stroke="black" stroke-width="1.2"/><text x="30" y="144" font-family="Times New Roman, serif" font-size="16" fill="black">Прочее</text></g></svg>']
                else:
                    extra_data = ["HTML_TABLE",
                                  '<table border="1" style="border-collapse: collapse; text-align: center; width: 200px;"><thead><tr><th style="padding: 10px; background-color: #f2f2f2;">x</th><th style="padding: 10px; background-color: #f2f2f2;">f(x)</th></tr></thead><tbody><tr><td style="padding: 10px;">1</td><td style="padding: 10px;">3</td></tr><tr><td style="padding: 10px;">2</td><td style="padding: 10px;">5</td></tr><tr><td style="padding: 10px;">3</td><td style="padding: 10px;">7</td></tr><tr><td style="padding: 10px;">4</td><td style="padding: 10px;">?</td></tr></tbody></table>']
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC MATH: Question {n}: Some question for test?", "answers": answers}

            tasks.append(process())
        return tasks

    async def special_biology_test(self, start_idx=0) -> List:
        tasks = []
        for num in range(1, 41):
            async def process(n=num, g=start_idx + num - 1):
                extra_data = ["IMAGE_URL", "/assets/img/arm_muscles.png"]
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC BIO: Question {n}: Some question for test?", "answers": answers}

            tasks.append(process())
        return tasks

    async def special_chemistry_test(self, start_idx=0) -> List:
        tasks = []
        for num in range(1, 41):
            async def process(n=num, g=start_idx + num - 1):
                if n == 2:
                    extra_data = ["FORMULA", "SOME ATOMIC STUFF OR FORMULAS"]
                else:
                    extra_data = ["IMAGE_URL", "/assets/img/test_bank/arm_muscles.png"]
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC CHEM: Question {n}: Some question for test?", "answers": answers}

            tasks.append(process())
        return tasks

    async def special_english_test(self, start_idx=0) -> List:
        try:
            import temporary_tests
            text_block = temporary_tests.text_1
        except ImportError:
            text_block = "Temporary English Text Block"

        tasks = []
        for num in range(1, 50):
            async def process(n=num, g=start_idx + num - 1):
                if n == 40:
                    extra_data = ["TEXT_BLOCK_LARGE", text_block]
                else:
                    extra_data = ["TEXT_BLOCK", "- SOME SENTENCES ____ ", "TEXT"]
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC ENGLISH: Question {n}: Some question for test?",
                        "answers": answers}

            tasks.append(process())
        return tasks

    async def special_history_test(self, start_idx=0) -> List:
        tasks = []
        for num in range(1, 41):
            async def process(n=num, g=start_idx + num - 1):
                extra_data = ["TEXT_BLOCK", "I. ANNANA \n II. SFDFSD"]
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC HISTORY: Question {n}: Some question for test?",
                        "answers": answers}

            tasks.append(process())
        return tasks

    async def special_physics_test(self, start_idx=0) -> List:
        tasks = []
        for num in range(1, 41):
            async def process(n=num, g=start_idx + num - 1):
                if n == 2:
                    extra_data = ["FORMULA", "SOME ATOMIC STUFF OR FORMULAS"]
                else:
                    extra_data = ["IMAGE_URL", "/assets/img/arm_muscles.png"]
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC PHYSICS: Question {n}: Some question for test?",
                        "answers": answers}

            tasks.append(process())
        return tasks

    async def special_kyrgyz_grammar_test(self, start_idx=0) -> List:
        tasks = []
        for num in range(1, 41):
            async def process(n=num, g=start_idx + num - 1):
                extra_data = ["TEXT_BLOCK", "There was a big fire Some Times."]
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC KYRGYZ GRAMMAR: Question {n}: Some question for test?",
                        "answers": answers}

            tasks.append(process())
        return tasks

    async def special_russian_grammar_test(self, start_idx=0) -> List:
        tasks = []
        for num in range(1, 41):
            async def process(n=num, g=start_idx + num - 1):
                extra_data = ["TEXT_BLOCK", "There was a big fire Some Times."]
                answers = self._generate_answers(4)
                answers.append(extra_data)
                return {"index": g, "question": f"SPEC RUS GRAMMAR: Question {n}: Some question for test?",
                        "answers": answers}

            tasks.append(process())
        return tasks


class Description:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "default_data_for_tests", "tests_descriptions.json")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.descriptions = json.load(f)
        except FileNotFoundError:
            self.descriptions = {}
            print(f"Warning: Test descriptions file not found at {json_path}")

    def get_test_description(self, test_type: str) -> Dict[str, Any]:
        return self.descriptions.get(test_type, {})

    def get_test_types(self) -> list[str]:
        return list(self.descriptions.keys())