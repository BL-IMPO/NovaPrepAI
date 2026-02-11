from typing import Dict, List
import random


class TestORT:
    def __init__(self):
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
            test_data[f"MATH 1: Question {num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def standard_math_2_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 31):
            test_data[f"MATH 2: Question {num}: Some question for test?"] = self._generate_answers(5)

        return test_data

    def standard_analogy_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 31):
            test_data[f"ANALOGY: Question {num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def standard_reading_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 31):
            test_data[f"READING: Question {num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def standard_grammar_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 31):
            test_data[f"GRAMMAR: Question {num}: Some question for test?"] = self._generate_answers(4)

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
        for num in range(1, 41):
            test_data[f"SPEC MATH: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def special_biology_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            test_data[f"SPEC BIO: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def special_chemistry_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            test_data[f"SPEC CHEM: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def special_english_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            test_data[f"SPEC ENGLISH: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def special_history_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            test_data[f"SPEC HISTORY: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def special_physics_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            test_data[f"SPEC PHYSICS: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def special_kyrgyz_grammar_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            test_data[f"SPEC KYRGYZ GRAMMAR: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data

    def special_russian_grammar_test(self) -> Dict[str, List[str]]:
        test_data = {}
        for num in range(1, 41):
            test_data[f"SPEC RUS GRAMMAR: Question{num}: Some question for test?"] = self._generate_answers(4)

        return test_data





