from typing import Any
from pydantic import BaseModel, Field
class QuestionIn(BaseModel):
    text:str; options:list[Any]; correct_option_index:int; explanation:str=""; competency_code:str|None=None; order:int=0
class AssessmentCreate(BaseModel):
    id:int|None=None; course_id:int; title:str; description:str=""; engine:str="course_quiz"; time_limit_minutes:int=30; pass_threshold_percent:float=70; questions:list[QuestionIn]
class SubmitAssessmentRequest(BaseModel): answers:dict[str,int]
class SessionStart(BaseModel):
    engine:str
    assessment_id:int
class SessionAnswer(BaseModel): answer:dict
class CalculationRequest(BaseModel):
    module:str="price_statistics";operation:str;inputs:dict[str,Any]
class ChartRequest(BaseModel):
    chart_type:str;title:str="";data:list[dict[str,Any]];x_field:str;y_fields:list[str]
