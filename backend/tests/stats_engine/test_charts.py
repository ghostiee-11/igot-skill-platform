import pytest
from app.statistical_engine.charts.generator import chart_generator
from app.statistical_engine.questions.generator import question_generator
from app.statistical_engine.schemas.questions import QuestionType

def test_chart_spec_creation():
    spec = chart_generator.create_cpi_trend_chart(
        years=[2020, 2021, 2022, 2023],
        cpi_values=[100.0, 105.5, 112.0, 118.4]
    )
    assert spec.type == "line"
    assert spec.xAxis.field == "year"
    assert spec.yAxis.field == "cpi"
    assert len(spec.data) == 4
    assert spec.data[0]["year"] == 2020
    assert spec.data[0]["cpi"] == 100.0

def test_chart_question_generation():
    q, r = question_generator.generate_question(
        skill_id="price.cpi.weighted_price_relatives",
        question_type=QuestionType.CHART_INTERPRETATION,
        seed=777
    )
    assert q.type == QuestionType.CHART_INTERPRETATION
    assert q.chart is not None
    assert q.chart.type in {"line", "bar"}
    assert len(q.options) >= 3


def test_bar_chart_question_generation():
    """The visual-question bank includes an interpretable CPI basket bar graph."""
    for seed in range(1, 30):
        q, _ = question_generator.generate_question(
            skill_id="price.cpi.weighted_price_relatives",
            question_type=QuestionType.CHART_INTERPRETATION,
            seed=seed,
        )
        if q.chart and q.chart.type == "bar":
            assert q.chart.xAxis.field == "category"
            assert q.chart.yAxis.field == "contribution"
            assert len(q.options) == 3
            return
    pytest.fail("No bar-chart template was selected from the visual question bank")
