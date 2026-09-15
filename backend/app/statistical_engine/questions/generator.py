import json
import random
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from app.statistical_engine.config import engine_settings
from app.statistical_engine.core.exceptions import QuestionGenerationException
from app.statistical_engine.stats.price_statistics import price_stats_module
from app.statistical_engine.questions.distractors import distractor_generator
from app.statistical_engine.questions.validator import question_validator
from app.statistical_engine.charts.generator import chart_generator
from app.statistical_engine.schemas.questions import (
    QuestionInstance,
    QuestionType,
    QuestionDifficulty,
    MCQOption
)

class QuestionInternalRecord:
    """Internal server representation containing answer keys and evaluation metadata."""
    def __init__(
        self,
        question_id: str,
        template_id: str,
        skill_id: str,
        competency_id: str,
        question_type: QuestionType,
        difficulty: QuestionDifficulty,
        prompt: str,
        parameters: Dict[str, Any],
        correct_answer: Union[float, int, str],
        tolerance: float,
        options_map: Dict[str, Tuple[Union[float, int, str], Optional[str]]], # option_id -> (value, misconception_id)
        correct_option_id: Optional[str],
        explanation: str,
        unit: str,
        chart: Optional[Any] = None,
        seed: Optional[int] = None
    ):
        self.question_id = question_id
        self.template_id = template_id
        self.skill_id = skill_id
        self.competency_id = competency_id
        self.question_type = question_type
        self.difficulty = difficulty
        self.prompt = prompt
        self.parameters = parameters
        self.correct_answer = correct_answer
        self.tolerance = tolerance
        self.options_map = options_map
        self.correct_option_id = correct_option_id
        self.explanation = explanation
        self.unit = unit
        self.chart = chart
        self.seed = seed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "template_id": self.template_id,
            "skill_id": self.skill_id,
            "competency_id": self.competency_id,
            "question_type": self.question_type.value,
            "difficulty": self.difficulty.value,
            "prompt": self.prompt,
            "parameters": self.parameters,
            "correct_answer": self.correct_answer,
            "tolerance": self.tolerance,
            "options_map": {k: list(v) for k, v in self.options_map.items()},
            "correct_option_id": self.correct_option_id,
            "explanation": self.explanation,
            "unit": self.unit,
            "chart": self.chart.model_dump() if self.chart is not None else None,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionInternalRecord":
        from app.statistical_engine.schemas.charts import ChartSpec
        return cls(
            question_id=data["question_id"],
            template_id=data["template_id"],
            skill_id=data["skill_id"],
            competency_id=data["competency_id"],
            question_type=QuestionType(data["question_type"]),
            difficulty=QuestionDifficulty(data["difficulty"]),
            prompt=data["prompt"],
            parameters=data["parameters"],
            correct_answer=data["correct_answer"],
            tolerance=data["tolerance"],
            options_map={k: tuple(v) for k, v in data["options_map"].items()},
            correct_option_id=data.get("correct_option_id"),
            explanation=data.get("explanation", ""),
            unit=data.get("unit", ""),
            chart=ChartSpec(**data["chart"]) if data.get("chart") else None,
            seed=data.get("seed"),
        )

class QuestionGenerator:
    """
    Template-driven parameterized question generator with deterministic execution.
    """

    def __init__(self):
        self._templates_cache: Dict[str, Dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self):
        """Loads all question templates from content directory."""
        questions_dir = engine_settings.QUESTIONS_DIR
        if not questions_dir.exists():
            return

        for filepath in questions_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    domain = data.get("domain", "default")
                    for t in data.get("templates", []):
                        t_id = t["template_id"]
                        t["domain"] = domain
                        self._templates_cache[t_id] = t
            except Exception as e:
                print(f"[WARN] Failed to load templates from {filepath}: {e}")

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        return self._templates_cache.get(template_id)

    def find_templates_by_skill(
        self,
        skill_id: str,
        difficulty: Optional[QuestionDifficulty] = None,
        question_type: Optional[QuestionType] = None
    ) -> List[Dict[str, Any]]:
        matches = []
        for t in self._templates_cache.values():
            if t.get("skill_id") == skill_id:
                if difficulty and t.get("difficulty") != difficulty.value:
                    continue
                if question_type and t.get("type") != question_type.value:
                    continue
                matches.append(t)
        return matches

    def generate_parameters(
        self,
        param_defs: Dict[str, Any],
        rng: random.Random,
        max_attempts: int = 50
    ) -> Dict[str, Any]:
        """Generates random parameter dictionary satisfying declared ranges and constraints."""
        for _ in range(max_attempts):
            params = {}
            for name, spec in param_defs.items():
                p_type = spec.get("type", "integer")
                p_min = spec.get("min", 1)
                p_max = spec.get("max", 100)
                step = spec.get("step", 1)

                if p_type == "integer":
                    # Generate with step
                    steps_count = int((p_max - p_min) / step)
                    val = p_min + rng.randint(0, steps_count) * step
                    params[name] = int(val)
                elif p_type == "float":
                    steps_count = int((p_max - p_min) / step)
                    val = p_min + rng.randint(0, steps_count) * step
                    params[name] = round(float(val), 2)
                else:
                    params[name] = p_min

            # Check constraints
            all_valid = True
            for name, spec in param_defs.items():
                constraint = spec.get("constraint")
                if constraint:
                    try:
                        # Safe evaluation of basic inequalities
                        if not eval(constraint, {"__builtins__": None, "abs": abs}, params):
                            all_valid = False
                            break
                    except Exception:
                        all_valid = False
                        break

            if all_valid:
                return params

        # Fallback to defaults
        return {k: v.get("min", 1) for k, v in param_defs.items()}

    def generate_question(
        self,
        skill_id: str,
        difficulty: Optional[QuestionDifficulty] = None,
        question_type: Optional[QuestionType] = None,
        seed: Optional[int] = None
    ) -> Tuple[QuestionInstance, QuestionInternalRecord]:
        """
        Generates a validated question instance and its internal evaluation record.
        """
        templates = self.find_templates_by_skill(skill_id, difficulty, question_type)
        if not templates:
            # Difficulty is advisory for adaptive progression; question format is
            # a hard contract with the client. Retain it when relaxing the
            # difficulty so a requested graph item can never become an MCQ.
            templates = self.find_templates_by_skill(skill_id, question_type=question_type)
        if not templates:
            raise QuestionGenerationException(f"No question templates found for skill '{skill_id}'.")

        actual_seed = seed if seed is not None else random.randint(1, 10000000)
        rng = random.Random(actual_seed)
        template = rng.choice(templates)

        params = self.generate_parameters(template.get("parameters", {}), rng)
        operation = template.get("operation")

        # Deterministic Answer Calculation
        chart_obj = None
        if operation == "cpi_trend_max_jump":
            # Chart interpretation calculation
            cpi_2020 = params.get("cpi_2020", 100.0)
            cpi_2021 = params.get("cpi_2021", 105.0)
            cpi_2022 = params.get("cpi_2022", 115.0)
            cpi_2023 = params.get("cpi_2023", 122.0)

            diffs = {
                2021: round(cpi_2021 - cpi_2020, 2),
                2022: round(cpi_2022 - cpi_2021, 2),
                2023: round(cpi_2023 - cpi_2022, 2)
            }
            max_year = max(diffs, key=diffs.get)
            calc_result_value = str(max_year)
            params["diff_2021"] = diffs[2021]
            params["diff_2022"] = diffs[2022]
            params["diff_2023"] = diffs[2023]

            chart_obj = chart_generator.create_cpi_trend_chart(
                years=[2020, 2021, 2022, 2023],
                cpi_values=[cpi_2020, cpi_2021, cpi_2022, cpi_2023]
            )
        elif operation == "cpi_weighted_contribution_max":
            contributions = {
                "Food": round(params["rel_food"] * params["w_food"] / 100, 2),
                "Housing": round(params["rel_housing"] * params["w_housing"] / 100, 2),
                "Fuel & Light": round(params["rel_fuel"] * params["w_fuel"] / 100, 2),
            }
            calc_result_value = max(contributions, key=contributions.get)
            params.update({"food_contribution": contributions["Food"], "housing_contribution": contributions["Housing"], "fuel_contribution": contributions["Fuel & Light"]})
            chart_obj = chart_generator.create_spec(
                chart_type="bar",
                title="CPI basket contribution by commodity group",
                description="Weighted index-point contributions calculated from the expenditure basket.",
                x_field="category", x_label="Commodity group",
                y_field="contribution", y_label="Weighted contribution (index points)",
                data=[{"category": category, "contribution": value} for category, value in contributions.items()],
                unit="index_points",
            )
        else:
            calc_res = price_stats_module.calculate(operation=operation, inputs=params)
            calc_result_value = calc_res.result

        params["answer"] = calc_result_value

        # Format prompt and explanation
        try:
            prompt = template["prompt_template"].format(**params)
        except Exception as e:
            prompt = template["prompt_template"]

        try:
            explanation = template.get("explanation_template", "").format(**params)
        except Exception:
            explanation = f"Correct answer is {calc_result_value}."

        q_type_str = template.get("type", "numeric")
        q_type = QuestionType(q_type_str)
        q_diff = QuestionDifficulty(template.get("difficulty", "basic"))
        instance_id = f"{template['template_id']}-{actual_seed}"

        options_list: Optional[List[MCQOption]] = None
        options_map: Dict[str, Tuple[Union[float, int, str], Optional[str]]] = {}
        correct_option_id: Optional[str] = None

        if q_type in (QuestionType.MCQ, QuestionType.CHART_INTERPRETATION):
            if operation == "cpi_trend_max_jump":
                # Years options
                years_opts = ["2021", "2022", "2023", "2020"]
                correct_val_str = str(calc_result_value)
                rng.shuffle(years_opts)
                options_list = []
                for idx, y_str in enumerate(years_opts):
                    opt_id = chr(65 + idx) # A, B, C, D
                    options_list.append(MCQOption(id=opt_id, text=f"Year {y_str}"))
                    options_map[opt_id] = (y_str, "err.chart.wrong_year" if y_str != correct_val_str else None)
                    if y_str == correct_val_str:
                        correct_option_id = opt_id
            elif operation == "cpi_weighted_contribution_max":
                categories = ["Food", "Housing", "Fuel & Light"]
                rng.shuffle(categories)
                options_list = []
                for idx, category in enumerate(categories):
                    opt_id = chr(65 + idx)
                    options_list.append(MCQOption(id=opt_id, text=category))
                    options_map[opt_id] = (category, "err.chart.ignored_weight" if category != calc_result_value else None)
                    if category == calc_result_value:
                        correct_option_id = opt_id
            else:
                # Generate numerical distractors
                distractor_rules = template.get("distractor_rules", [])
                distractors = distractor_generator.generate_distractors(
                    template_id=template["template_id"],
                    operation=operation,
                    params=params,
                    correct_answer=float(calc_result_value),
                    distractor_rules=distractor_rules,
                    rng=rng
                )

                # Assemble 4 options (1 correct + 3 distractors)
                all_choices = [(float(calc_result_value), f"{float(calc_result_value):.2f}", None)]
                all_choices.extend(distractors)
                rng.shuffle(all_choices)

                options_list = []
                for idx, (val, text_val, mis_id) in enumerate(all_choices):
                    opt_id = chr(65 + idx)
                    options_list.append(MCQOption(id=opt_id, text=text_val))
                    options_map[opt_id] = (val, mis_id)
                    if mis_id is None:
                        correct_option_id = opt_id

            # Validate MCQ structure
            question_validator.validate_mcq_question(
                prompt=prompt,
                correct_option_id=correct_option_id,
                options=[{"id": o.id, "text": o.text} for o in options_list],
                correct_value=float(calc_result_value) if isinstance(calc_result_value, (int, float)) else 0.0
            )
        else:
            # Validate numeric
            question_validator.validate_numeric_question(
                prompt=prompt,
                answer=float(calc_result_value),
                params=params,
                tolerance=template.get("tolerance", 0.5)
            )

        # Validate Chart Spec if present
        if chart_obj:
            question_validator.validate_chart_spec(chart_obj.model_dump())

        client_instance = QuestionInstance(
            question_id=instance_id,
            skill_id=skill_id,
            competency_id=template.get("domain", "price_statistics"),
            type=q_type,
            difficulty=q_diff,
            prompt=prompt,
            data=params,
            options=options_list,
            chart=chart_obj,
            metadata={
                "template_id": template["template_id"],
                "unit": template.get("unit", "value"),
                "seed": actual_seed
            }
        )

        internal_record = QuestionInternalRecord(
            question_id=instance_id,
            template_id=template["template_id"],
            skill_id=skill_id,
            competency_id=template.get("domain", "price_statistics"),
            question_type=q_type,
            difficulty=q_diff,
            prompt=prompt,
            parameters=params,
            correct_answer=calc_result_value,
            tolerance=template.get("tolerance", 0.5),
            options_map=options_map,
            correct_option_id=correct_option_id,
            explanation=explanation,
            unit=template.get("unit", "value"),
            chart=chart_obj,
            seed=actual_seed
        )

        return client_instance, internal_record

question_generator = QuestionGenerator()
