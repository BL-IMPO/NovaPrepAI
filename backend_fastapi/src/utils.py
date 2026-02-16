import json
from typing import Dict, List
import random
import os


class TestORT:
    def __init__(self):
        self.base_point = 1
        self.test_time_limits = {
            "math_1": 30 * 60, # in seconds
            "math_2": 60 * 60,
            "analogy": 30 * 60,
            "reading": 60 * 60,
            "grammar": 35 * 60,
            "full_test": 3 * 60 * 60, # 3 hours
            "special_math": 80 * 60,
            "special_biology": 60 * 60,
            "special_chemistry": 80 * 60,
            "special_english": 60 * 60,
            "special_history": 60 * 60,
            "special_physics": 80 * 60,
            "special_russian_grammar": 60 * 60,
            "special_kyrgyz_grammar": 60 * 60,
        }

    def _generate_answers(self, num_answers: int = 4) -> List[str]:
        """Generate answers with first being correct"""
        answers = []
        correct_answer = f"Correct Answer {random.randint(1, 100)}"
        answers.append(correct_answer)

        for i in range(1, num_answers):
            answers.append(f"Option {chr(64 + i)}")

        # We need to add more points if question is harder
        answers.append(self.base_point + random.random())

        return answers

    def get_test_data(self, test_type: str) -> Dict:
        """Get test data including time and questions"""
        if test_type not in self.test_time_limits:
            raise ValueError(f"Unknown test type: {test_type}")

        test_methods = {
            "math_1": self.standard_math_1_test,
            "math_2": self.standard_math_2_test,
            "analogy": self.standard_analogy_test,
            "reading": self.standard_reading_test,
            "grammar": self.standard_grammar_test,
            "full_test": self.standard_full_test,
            "special_math": self.special_math_test,
            "special_biology": self.special_biology_test,
            "special_chemistry": self.special_chemistry_test,
            "special_english": self.special_english_test,
            "special_history": self.special_history_test,
            "special_physics": self.special_physics_test,
            "special_russian_grammar": self.special_russian_grammar_test,
            "special_kyrgyz_grammar": self.special_kyrgyz_grammar_test,
        }

        if test_type == "full_test":
            test_data = {}
            test_data.update(self.standard_math_1_test())
            test_data.update(self.standard_math_2_test())
            test_data.update(self.standard_analogy_test())
            test_data.update(self.standard_reading_test())
            test_data.update(self.standard_grammar_test())

            return {
                "time_limit": self.test_time_limits[test_type],
                "questions": test_data,
            }
        else:
            test_func = test_methods[test_type]

            return {
                "time_limit": self.test_time_limits[test_type],
                "questions": test_func(),
            }

    def standard_math_1_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 31):
            if num % 2 == 0:
                extra_data = ["SVG_GRAPH", '<svg width="300" height="200" viewBox="0 0 300 200" xmlns="http://www.w3.org/2000/svg"> <rect x="10" y="10" width="280" height="180"  fill="#f0f0f0" stroke="black" stroke-width="3"/> <line x1="10" y1="10" x2="290" y2="190"  stroke="red" stroke-width="2" stroke-dasharray="5,5" /> <text x="140" y="90" font-family="Arial" font-size="16" fill="black">Diagonal</text> <text x="5" y="25" font-family="Arial" font-size="20" fill="black">A</text> <text x="285" y="205" font-family="Arial" font-size="20" fill="black">C</text> </svg>']
            else:
                extra_data = [None]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"MATH 1: Question {num}: Some question for test?"] = answers

        return test_data

    def standard_math_2_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 31):
            if num % 2 == 0:
                extra_data = ["SVG_GRAPH",'<svg width="300" height="200" viewBox="0 0 300 200" xmlns="http://www.w3.org/2000/svg"> <rect x="10" y="10" width="280" height="180"  fill="#f0f0f0" stroke="black" stroke-width="3"/> <line x1="10" y1="10" x2="290" y2="190"  stroke="red" stroke-width="2" stroke-dasharray="5,5" /> <text x="140" y="90" font-family="Arial" font-size="16" fill="black">Diagonal</text> <text x="5" y="25" font-family="Arial" font-size="20" fill="black">A</text> <text x="285" y="205" font-family="Arial" font-size="20" fill="black">C</text> </svg>']
            else:
                extra_data = [None]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"MATH 2: Question {num}: Some question for test?"] = answers


        return test_data

    def standard_analogy_test(self) -> Dict[str, List[str]]:
        test_data = {}
        extra_data = [None]
        for num in range(1, 31):
            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"ANALOGY: Question {num}: Some question for test?"] = answers

        return test_data

    def standard_reading_test(self) -> Dict[str, List[str]]:
        import temporary_tests
        test_data = {}
        for num in range(1, 31):
            if num > 0 and num < 11:
                extra_data = ["TEXT_BLOCK_LARGE", temporary_tests.text_1]
            if num > 10 and num < 21:
                extra_data = ["TEXT_BLOCK_LARGE", temporary_tests.text_2]
            if num > 20 and num < 31:
                extra_data = ["TEXT_BLOCK_LARGE", temporary_tests.text_3]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"READING: Question {num}: Some question for test?"] = answers

        return test_data

    def standard_grammar_test(self) -> Dict[str, List[str]]:
        test_data = {}
        extra_data = ["TEXT_BLOCK", "There was a big fire Some Times."]
        for num in range(1, 31):
            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"GRAMMAR: Question {num}: Some question for test?"] = answers

        return test_data

    def standard_full_test(self) -> Dict[str, List[str]]:
        full_test = {}
        full_test.update(self.standard_math_1_test())
        full_test.update(self.standard_math_2_test())
        full_test.update(self.standard_analogy_test())
        full_test.update(self.standard_reading_test())
        full_test.update(self.standard_grammar_test())
        return full_test

    def special_math_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 31):
            if num % 2 == 0:
                extra_data = ["SVG_GRAPH",
                              '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 260" width="100%" height="100%"><rect width="100%" height="100%" fill="white"/><defs><pattern id="v-stripes" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#ffffff"/><line x1="3" y1="0" x2="3" y2="6" stroke="#688ab3" stroke-width="1.2"/></pattern><pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#ffffff"/><circle cx="4" cy="4" r="1.2" fill="#5890d6"/></pattern><pattern id="d-stripes" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#ffffff"/><line x1="0" y1="0" x2="0" y2="7" stroke="#737373" stroke-width="1.5"/></pattern></defs><g stroke="black" stroke-width="1.2" stroke-linejoin="round"><path d="M 130 130 L 130 15 A 115 115 0 0 1 197.6 37.0 Z" fill="#8f8f8f"/><path d="M 130 130 L 197.6 37.0 A 115 115 0 1 1 32.9 191.6 Z" fill="#ffffff"/><path d="M 130 130 L 32.9 191.6 A 115 115 0 0 1 23.1 87.7 Z" fill="url(#v-stripes)"/><path d="M 130 130 L 23.1 87.7 A 115 115 0 0 1 97.9 19.6 Z" fill="url(#dots)"/><path d="M 130 130 L 97.9 19.6 A 115 115 0 0 1 130 15 Z" fill="url(#d-stripes)"/></g><g font-family="Times New Roman, serif" font-size="16" fill="black"><text x="160" y="65">10%</text><text x="175" y="185">56%</text><text x="45" y="145">15%</text></g><g transform="translate(290, 40)"><rect x="0" y="0" width="20" height="20" fill="#8f8f8f" stroke="black" stroke-width="1.2"/><text x="30" y="16" font-family="Times New Roman, serif" font-size="16" fill="black">Белки</text><rect x="0" y="32" width="20" height="20" fill="#ffffff" stroke="black" stroke-width="1.2"/><text x="30" y="48" font-family="Times New Roman, serif" font-size="16" fill="black">Углеводы</text><rect x="0" y="64" width="20" height="20" fill="url(#v-stripes)" stroke="black" stroke-width="1.2"/><text x="30" y="80" font-family="Times New Roman, serif" font-size="16" fill="black">Пищевые волокна</text><rect x="0" y="96" width="20" height="20" fill="url(#dots)" stroke="black" stroke-width="1.2"/> <text x="30" y="112" font-family="Times New Roman, serif" font-size="16" fill="black">Вода</text><rect x="0" y="128" width="20" height="20" fill="url(#d-stripes)" stroke="black" stroke-width="1.2"/><text x="30" y="144" font-family="Times New Roman, serif" font-size="16" fill="black">Прочее</text></g></svg>']
            else:
                extra_data = ["HTML_TABLE", '<table border="1" style="border-collapse: collapse; text-align: center; width: 200px;"><thead><tr><th style="padding: 10px; background-color: #f2f2f2;">x</th><th style="padding: 10px; background-color: #f2f2f2;">f(x)</th></tr></thead><tbody><tr><td style="padding: 10px;">1</td><td style="padding: 10px;">3</td></tr><tr><td style="padding: 10px;">2</td><td style="padding: 10px;">5</td></tr><tr><td style="padding: 10px;">3</td><td style="padding: 10px;">7</td></tr><tr><td style="padding: 10px;">4</td><td style="padding: 10px;">?</td></tr></tbody></table>']

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC MATH: Question {num}: Some question for test?"] = answers
        return test_data

    def special_biology_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            extra_data = ["IMAGE_URL", "/assets/img/arm_muscles.png"]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC BIO: Question{num}: Some question for test?"] = answers

        return test_data

    def special_chemistry_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            if num == 2:
                extra_data = ["FORMULA", "SOME ATOMIC STUFF OR FORMULAS"]
            extra_data = ["IMAGE_URL", "/assets/img/test_bank/arm_muscles.png"]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC CHEM: Question{num}: Some question for test?"] = answers

        return test_data

    def special_english_test(self) -> Dict[str, List[str]]:
        test_data = {}
        import temporary_tests
        for num in range(1, 50):
            if num == 40:
                extra_data = ["TEXT_BLOCK_LARGE", temporary_tests.text_1]
            else:
                extra_data = ["TEXT_BLOCK", "- SOME SENTENCES ____ ", "TEXT"]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC ENGLISH: Question{num}: Some question for test?"] = answers

        return test_data

    def special_history_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            extra_data = ["TEXT_BLOCK", "I. ANNANA \n II. SFDFSD"]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC HISTORY: Question{num}: Some question for test?"] = answers

        return test_data

    def special_physics_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            if num == 2:
                extra_data = ["FORMULA", "SOME ATOMIC STUFF OR FORMULAS"]
            else:
                extra_data = ["IMAGE_URL", "/assets/img/arm_muscles.png"]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC PHYSICS: Question{num}: Some question for test?"] = answers

        return test_data

    def special_kyrgyz_grammar_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            extra_data = ["TEXT_BLOCK", "There was a big fire Some Times."]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC KYRGYZ GRAMMAR: Question{num}: Some question for test?"] = answers

        return test_data

    def special_russian_grammar_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            extra_data = ["TEXT_BLOCK", "There was a big fire Some Times."]

            answers = self._generate_answers(4)
            answers.append(extra_data)
            test_data[f"SPEC RUS GRAMMAR: Question{num}: Some question for test?"] = answers

        return test_data

class Description:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "default_data_for_tests", "test_descriptions.json")

        try:
            with open("src/default_data_for_tests/tests_descriptions.json", "r") as f:
                self.descriptions = json.load(f)
        except FileNotFoundError:
            self.descriptions = {}
            print(f"Warning: Test descriptions file not found at {json_path}")

    def get_test_description(self, test_type: str) -> Dict[str, List[str]]:
        return self.descriptions[test_type]

    def get_test_types(self) -> list[str]:
        return self.descriptions.keys()

