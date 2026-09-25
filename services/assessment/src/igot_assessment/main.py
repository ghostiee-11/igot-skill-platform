import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime,timezone
from uuid import uuid4
import httpx
from fastapi import Depends,FastAPI,File,Form,Header,HTTPException,Query,UploadFile
from pydantic import BaseModel
from sqlalchemy import func,select,text
from sqlalchemy.orm import Session
from .config import get_settings
from .behavioural import CASES,DOCUMENTS,all_cases,find_case,find_document
from .database import Assessment,Attempt,CyberSandboxChallenge,GeneratedBehaviouralCase,GeneratedQuiz,GeneratedQuizQuestion,OutboxEvent,Question,QuizAttempt,SessionRecord,StatEngineMastery,StatEngineQuestion,TechnicalLabTemplate,get_db,initialize_database,engine
from .adaptive import next_question,public_question,submit_answer
from .case_generation import build_case
from .engines import REGISTRY,public_state
from .interview import PHASES,build_report,report_ai_request,start_state,submit_turn,turn_ai_request
from .schemas import AssessmentCreate,CalculationRequest,ChartRequest,SessionAnswer,SessionStart,SubmitAssessmentRequest
from .security import Principal,current_principal,require_admin
from .scenarios import answer as answer_scenario,catalogue as scenario_catalogue,start as start_scenario_state,start_response as scenario_start_response,summaries as scenario_summaries,summary as scenario_summary_data
from .statistical import StatisticalInputError,calculate,chart_spec
from .technical_labs import find_template,present_template,template_catalogue
from .quiz_generation import generate_questions
@asynccontextmanager
async def lifespan(app:FastAPI): initialize_database(); yield
app=FastAPI(title="iGOT Assessment Service",version="1.0",lifespan=lifespan)
logger=logging.getLogger(__name__)

class QuizSubmission(BaseModel):
    answers: dict[int,int]

class BehaviouralSessionStart(BaseModel):
    case_id:str|None=None

class BehaviouralAnswer(BaseModel):
    question_id:str
    selected_option_id:str

class BehaviouralCaseGeneration(BaseModel):
    raw_text:str
    document_title:str
    document_type:str="Government Notice"
    issuing_authority:str="Department of Personnel & Training (DoPT)"
    statutory_reference:str="CCS (Conduct) Rules / GFR 2017"

class CourseCaseGeneration(BaseModel):
    custom_notice_text:str|None=None

class NextQuestionRequest(BaseModel):
    user_id:str|None=None
    competency_id:str="price_statistics"
    preferred_skill_id:str|None=None
    current_difficulty:str|None=None
    question_type:str|None=None

class GenerateQuestionRequest(BaseModel):
    skill_id:str
    difficulty:str|None=None
    question_type:str|None=None
    seed:int|None=None

class SubmitQuestionRequest(BaseModel):
    user_id:str|None=None
    question_id:str
    submitted_answer:str|float|int
    time_taken_seconds:int|None=None

class InterviewStart(BaseModel):
    course_id:int
    officer_name:str="Officer"
    target_duration_minutes:int=30

class InterviewTurn(BaseModel):
    session_id:str
    officer_response:str
    elapsed_seconds:int=0
    speaking_pace_wpm:float|None=None
    eye_contact_percent:float|None=None
    composure_score:float|None=None
    voice_clarity_score:float|None=None
    posture_stability_score:float|None=None
    head_movement_rate:float|None=None
    fidgeting_index:float|None=None
    filler_words_count:int|None=None
    pauses_count:int|None=None
    coherence_score:float|None=None
    face_presence_percent:float|None=None
    speaking_seconds:float|None=None
    input_mode:str|None=None

class InterviewEnd(BaseModel):
    session_id:str

class ScenarioStart(BaseModel):
    scenario_id:str|None=None

class ScenarioAnswer(BaseModel):
    option_id:str

class LabSubmission(BaseModel):
    code:str

class LabAssistantRequest(BaseModel):
    message:str
    current_code:str=""
    active_output:str|None=None
    history:list[dict]=[]

MAX_DICTATION_BYTES=25*1024*1024
SARVAM_STT_URL="https://api.sarvam.ai/speech-to-text"

def _sarvam_error(response:httpx.Response)->str:
    try:
        body=response.json()
        if isinstance(body,dict):
            error=body.get("error")
            return str(error.get("message") if isinstance(error,dict) else body.get("message") or response.text)
    except ValueError:pass
    return response.text or f"HTTP {response.status_code}"

def _quiz_or_404(db:Session,quiz_id:int)->GeneratedQuiz:
    quiz=db.get(GeneratedQuiz,quiz_id)
    if not quiz:raise HTTPException(404,"Quiz not found")
    return quiz

def _serialize_quiz(quiz:GeneratedQuiz,principal:Principal,include_questions:bool=True)->dict:
    can_manage=principal.role=="admin" or quiz.user_id==principal.user_id
    questions=[]
    if include_questions:
        for q in quiz.questions:
            item={"id":q.id,"order":q.order,"question":q.question_text,"options":q.options,"concept":q.concept}
            if can_manage:item.update(correct_index=q.correct_option_index,explanation=q.explanation)
            questions.append(item)
    return {"id":quiz.id,"title":quiz.title,"source_name":quiz.source_name,"source_type":quiz.source_type,"difficulty":quiz.difficulty,"generator":quiz.generator,"created_at":quiz.created_at.isoformat() if quiz.created_at else None,"creator_name":None,"can_manage":can_manage,"question_count":len(quiz.questions),**({"questions":questions} if include_questions else {})}
@app.get("/v1/health")
def health(): return {"status":"ok","service":"assessment"}
@app.get("/v1/ready")
def ready():
    try:
        with engine.connect() as c: c.execute(text("SELECT 1"))
        return {"status":"ready"}
    except Exception as exc: raise HTTPException(503,f"database unavailable: {type(exc).__name__}")
@app.get("/v1/engines")
def list_engines(_:Principal=Depends(current_principal)): return {"engines":list(REGISTRY)}
@app.get("/v1/stats-engine/health")
def stats_health():return {"status":"ok","module":"price_statistics"}
@app.post("/v1/stats/calculate")
def stats_calculate(req:CalculationRequest,_:Principal=Depends(current_principal)):
    if req.module!="price_statistics":raise HTTPException(422,"unsupported statistical module")
    try:return calculate(req.operation,req.inputs)
    except (StatisticalInputError,TypeError) as exc:raise HTTPException(422,str(exc))
@app.post("/v1/charts/generate")
def generate_chart(req:ChartRequest,_:Principal=Depends(current_principal)):
    try:return chart_spec(req.chart_type,req.title,req.data,req.x_field,req.y_fields)
    except StatisticalInputError as exc:raise HTTPException(422,str(exc))

@app.post("/v1/questions/next")
def adaptive_next(req:NextQuestionRequest,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    return next_question(db,principal.user_id,req.competency_id,req.preferred_skill_id,req.current_difficulty,req.question_type)

@app.post("/v1/questions/generate")
def adaptive_generate(req:GenerateQuestionRequest,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    rows=db.scalars(select(StatEngineQuestion).where(StatEngineQuestion.skill_id==req.skill_id)).all()
    rows=[q for q in rows if (not req.question_type or q.question_type==req.question_type) and (not req.difficulty or q.difficulty==req.difficulty)]
    if not rows:raise HTTPException(404,"No question matches the requested skill and format")
    return public_question(rows[0])

@app.post("/v1/questions/submit")
def adaptive_submit(req:SubmitQuestionRequest,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    return submit_answer(db,principal.user_id,req.question_id,req.submitted_answer,req.time_taken_seconds)

@app.get("/v1/competencies")
def adaptive_competencies(_:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    rows=db.scalars(select(StatEngineQuestion)).all()
    return [{"id":code,"domain":"statistical","name":code.replace("_"," ").title(),"skills":sorted({q.skill_id for q in rows if q.competency_id==code})} for code in sorted({q.competency_id for q in rows})]

@app.get("/v1/competencies/{competency_id}")
def adaptive_competency(competency_id:str,_:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    rows=db.scalars(select(StatEngineQuestion).where(StatEngineQuestion.competency_id==competency_id)).all()
    if not rows:raise HTTPException(404,"Competency not found")
    return {"id":competency_id,"domain":"statistical","name":competency_id.replace("_"," ").title(),"skills":sorted({q.skill_id for q in rows})}

@app.get("/v1/users/{user_id}/competencies")
def adaptive_user_competencies(user_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    if user_id not in {str(principal.user_id),principal.full_name} and principal.role!="admin":raise HTTPException(403,"Cannot read another learner's mastery")
    return [{"skill_id":row.skill_id,"score":row.score,"level":"master" if row.score>=90 else "advanced" if row.score>=75 else "intermediate" if row.score>=50 else "basic" if row.score>=25 else "novice","attempts_count":row.attempts_count,"correct_count":row.correct_count} for row in db.scalars(select(StatEngineMastery).where(StatEngineMastery.user_id==principal.user_id)).all()]

@app.get("/v1/quiz")
def list_quizzes(principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    quizzes=db.scalars(select(GeneratedQuiz).order_by(GeneratedQuiz.created_at.desc())).all()
    best=dict(db.execute(select(QuizAttempt.quiz_id,func.max(QuizAttempt.score_percent)).where(QuizAttempt.user_id==principal.user_id).group_by(QuizAttempt.quiz_id)).all())
    return [{**_serialize_quiz(quiz,principal,False),"best_score":best.get(quiz.id)} for quiz in quizzes]

@app.post("/v1/quiz/generate",status_code=201)
async def generate_quiz(file:UploadFile|None=File(None),text:str|None=Form(None),title:str|None=Form(None),num_questions:int=Form(10),difficulty:str=Form("intermediate"),principal:Principal=Depends(current_principal),db:Session=Depends(get_db),authorization:str|None=Header(None)):
    if not 1<=num_questions<=30:raise HTTPException(400,"num_questions must be between 1 and 30")
    if difficulty not in {"beginner","intermediate","advanced"}:raise HTTPException(400,"Unsupported quiz difficulty")
    if file is None and not (text and text.strip()):raise HTTPException(400,"Upload a file or paste learning material")
    if file is not None:
        payload=await file.read(20*1024*1024+1)
        if len(payload)>20*1024*1024:raise HTTPException(413,"File too large (max 20 MB)")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                extracted=await client.post(f"{get_settings().content_service_url}/v1/extract/text",headers={"Authorization":authorization or ""},files={"file":(file.filename or "upload.txt",payload,file.content_type or "application/octet-stream")})
                extracted.raise_for_status();content=extracted.json()["text"]
        except httpx.HTTPStatusError as exc:raise HTTPException(exc.response.status_code,exc.response.text) from exc
        except (httpx.RequestError,ValueError,KeyError) as exc:raise HTTPException(503,"Document extraction is unavailable") from exc
        source_name=file.filename or "Upload";source_type=source_name.rsplit(".",1)[-1].lower()
    else:
        content=text or "";source_name="Pasted text";source_type="text"
    if len(content.strip())<200:raise HTTPException(422,"At least 200 readable characters are required")
    questions,generator=await generate_questions(content,num_questions,difficulty,authorization,get_settings().ai_service_url)
    if not questions:raise HTTPException(422,"Could not generate questions from this material")
    quiz=GeneratedQuiz(user_id=principal.user_id,title=(title or "").strip() or f"Quiz: {source_name.rsplit('.',1)[0]}",source_name=source_name,source_type=source_type,source_excerpt=content.strip()[:1000],difficulty=difficulty,generator=generator)
    quiz.questions=[GeneratedQuizQuestion(order=index,question_text=item["question"],options=item["options"],correct_option_index=item["correct_index"],explanation=item["explanation"],concept=item["concept"]) for index,item in enumerate(questions,start=1)]
    db.add(quiz);db.commit();db.refresh(quiz)
    return _serialize_quiz(quiz,principal)

@app.get("/v1/quiz/{quiz_id}")
def get_quiz(quiz_id:int,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    return _serialize_quiz(_quiz_or_404(db,quiz_id),principal)

@app.post("/v1/quiz/{quiz_id}/submit")
def submit_quiz(quiz_id:int,req:QuizSubmission,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    quiz=_quiz_or_404(db,quiz_id);results=[];correct=0;review=[]
    for question in quiz.questions:
        selected=req.answers.get(question.id);is_correct=selected==question.correct_option_index;correct+=int(is_correct)
        if not is_correct and question.concept and question.concept not in review:review.append(question.concept)
        results.append({"question_id":question.id,"selected_index":selected,"correct_index":question.correct_option_index,"is_correct":is_correct,"explanation":question.explanation,"concept":question.concept})
    total=len(quiz.questions);score=round(100*correct/total,1) if total else 0.0
    if score>=85:band,feedback="Excellent","Strong command of this material. Try an advanced quiz next."
    elif score>=60:band,feedback="Proficient","Good grasp overall. Review the explanations for the questions you missed."
    else:band,feedback="Needs review","Revisit the source material, then retake the quiz."
    attempt=QuizAttempt(quiz_id=quiz.id,user_id=principal.user_id,answers={str(k):v for k,v in req.answers.items()},correct_count=correct,total_questions=total,score_percent=score);db.add(attempt);db.commit();db.refresh(attempt)
    return {"attempt_id":attempt.id,"score_percent":score,"correct_count":correct,"total_questions":total,"band":band,"feedback":feedback,"concepts_to_review":review,"results":results}

@app.get("/v1/quiz/{quiz_id}/attempts")
def list_quiz_attempts(quiz_id:int,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    _quiz_or_404(db,quiz_id);attempts=db.scalars(select(QuizAttempt).where(QuizAttempt.quiz_id==quiz_id,QuizAttempt.user_id==principal.user_id).order_by(QuizAttempt.submitted_at.desc())).all()
    return [{"id":item.id,"score_percent":item.score_percent,"correct_count":item.correct_count,"total_questions":item.total_questions,"submitted_at":item.submitted_at.isoformat()} for item in attempts]

@app.delete("/v1/quiz/{quiz_id}")
def delete_quiz(quiz_id:int,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    quiz=_quiz_or_404(db,quiz_id)
    if principal.role!="admin" and quiz.user_id!=principal.user_id:raise HTTPException(403,"Only the quiz creator or an administrator can delete this quiz")
    db.delete(quiz);db.commit();return {"success":True}

@app.get("/v1/technical-courses/templates")
def technical_templates(_:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    return [{"id":item.id,"title":item.title,"skill":item.skill,"language":item.language,"difficulty":item.difficulty,"lab_type":item.lab_type,"tags":item.tags} for item in db.scalars(select(TechnicalLabTemplate).order_by(TechnicalLabTemplate.title)).all()]

@app.get("/v1/technical-courses/labs")
def technical_labs(_:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    return [present_template(number,template) for number,template in template_catalogue(db)]

@app.get("/v1/technical-courses/labs/{lab_id}")
def technical_lab(lab_id:int,_:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    template=find_template(db,lab_id)
    if not template:raise HTTPException(404,"Lab not found")
    return present_template(lab_id,template,detail=True)

@app.post("/v1/technical-courses/labs/{lab_id}/execute")
async def grade_technical_lab(lab_id:int,req:LabSubmission,_:Principal=Depends(current_principal),db:Session=Depends(get_db),authorization:str|None=Header(None)):
    template=find_template(db,lab_id)
    if not template:raise HTTPException(404,"Lab not found")
    if len(req.code)>12000:raise HTTPException(413,"Submitted code is too large")
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response=await client.post(f"{get_settings().labs_service_url}/v1/code/grade",headers={"Authorization":authorization or "","X-Internal-Secret":get_settings().internal_event_secret},json={"code":req.code,"tests":template.test_cases_template or []})
            response.raise_for_status();result=response.json()
    except httpx.HTTPStatusError as exc:raise HTTPException(exc.response.status_code,exc.response.text) from exc
    except (httpx.RequestError,ValueError) as exc:raise HTTPException(503,"Lab runtime is unavailable") from exc
    passed=result["passed_tests_count"];total=result["total_tests_count"]
    return {"lab_id":lab_id,**result,"feedback":"All test cases passed!" if passed==total and total else f"{passed} of {total} test cases passed."}

@app.post("/v1/technical-courses/labs/{lab_id}/assistant")
async def technical_lab_assistant(lab_id:int,req:LabAssistantRequest,_:Principal=Depends(current_principal),db:Session=Depends(get_db),authorization:str|None=Header(None)):
    template=find_template(db,lab_id)
    if not template:raise HTTPException(404,"Lab not found")
    prompt=f"Lab: {template.title}\nInstructions: {template.instructions_template}\nConstraints: {template.constraints}\nCurrent code:\n{req.current_code[:4000]}\nLatest output: {(req.active_output or '')[:1000]}\nLearner question: {req.message[:1000]}"
    messages=[{"role":"system","content":"You are a Socratic Python lab coach. Give one conceptual hint and one next action. Never provide completed code, hidden tests, or the reference solution. Keep it under 140 words."},{"role":"user","content":prompt}]
    response,provider=await _interview_ai(messages,{"response":"one concise coaching hint"},authorization)
    hint=str(response.get("response") or "").strip() if response else ""
    if not hint or "```" in hint:
        hint="Check the failing output, identify which requirement it violates, and test one small input before changing your function."
        provider="guided-fallback"
    return {"response":hint[:1600],"source":provider,"suggestions":["Explain my latest error","Give me a smaller hint","What should I test next?"]}

@app.get("/v1/digital-governance/sandbox/challenges")
def cyber_challenges(db:Session=Depends(get_db)):
    return [{"id":item.id,"title":item.title,"category":item.category,"difficulty":item.difficulty,"points":item.points,"duration_minutes":item.duration_minutes,"is_flagship":item.is_flagship,"solved":False,"competency_id":item.competency_id,"tags":item.tags,"mitre_techniques":item.mitre_techniques,"objectives":item.objectives} for item in db.scalars(select(CyberSandboxChallenge).order_by(CyberSandboxChallenge.title)).all()]

@app.get("/v1/internal/cyber-challenges/{challenge_id}")
def internal_cyber_challenge(challenge_id:str,x_internal_secret:str|None=Header(None),db:Session=Depends(get_db)):
    if not get_settings().internal_event_secret or x_internal_secret!=get_settings().internal_event_secret:raise HTTPException(401,"Invalid internal service credential")
    challenge=db.get(CyberSandboxChallenge,challenge_id)
    if not challenge:raise HTTPException(404,"Challenge not found")
    return {"id":challenge.id,"title":challenge.title,"category":challenge.category,"difficulty":challenge.difficulty,"points":challenge.points,"duration_minutes":challenge.duration_minutes,"competency_id":challenge.competency_id,"objectives":challenge.objectives,"scenario_md":challenge.scenario_markdown,"hints":challenge.hints,"artifacts":challenge.artifacts,"notebook_code":challenge.notebook_code,"flag":challenge.flag}

@app.get("/v1/digital-governance/scenarios")
def digital_scenarios():return scenario_summaries()

@app.get("/v1/digital-governance/scenarios/{scenario_id}")
def digital_scenario(scenario_id:str):
    scenario=scenario_catalogue().get(scenario_id)
    if not scenario:raise HTTPException(404,"Scenario not found")
    return scenario

def _scenario_session(session_id:str,principal:Principal,db:Session)->tuple[SessionRecord,dict]:
    record=db.get(SessionRecord,session_id)
    if not record or record.user_id!=principal.user_id or record.engine!="digital_governance_scenario":raise HTTPException(404,"Scenario session not found")
    scenario=scenario_catalogue().get(record.state.get("scenario_id"))
    if not scenario:raise HTTPException(409,"Scenario definition is unavailable")
    return record,scenario

@app.post("/v1/digital-governance/scenarios/session/start")
def start_digital_scenario(req:ScenarioStart|None=None,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    scenario_id=req.scenario_id if req and req.scenario_id else "dg-sec-01-ransomware-treasury"
    scenario=scenario_catalogue().get(scenario_id)
    if not scenario:raise HTTPException(404,"Scenario not found")
    state=start_scenario_state(scenario)
    record=SessionRecord(user_id=principal.user_id,engine="digital_governance_scenario",state=state);db.add(record);db.commit()
    return scenario_start_response(record.id,scenario,state)

@app.post("/v1/digital-governance/scenarios/session/{session_id}/answer")
def submit_digital_scenario_answer(session_id:str,req:ScenarioAnswer,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record,scenario=_scenario_session(session_id,principal,db)
    if record.status!="active":raise HTTPException(409,"Scenario session is complete")
    try:state,response=answer_scenario(record.id,scenario,dict(record.state),req.option_id)
    except ValueError as exc:raise HTTPException(400,str(exc))
    record.state=state;record.status="completed" if state["is_terminal"] else "active";db.commit();return response

@app.get("/v1/digital-governance/scenarios/session/{session_id}/summary")
def digital_scenario_summary(session_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record,scenario=_scenario_session(session_id,principal,db)
    if not record.state.get("is_terminal"):raise HTTPException(409,"Scenario session is still active")
    return scenario_summary_data(record.id,scenario,record.state)

@app.get("/v1/behavioural/courses")
async def behavioural_courses(behavioural_only:bool=False):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response=await client.get(f"{get_settings().learning_url}/v1/discover/courses",params={"limit":200})
            response.raise_for_status();courses=response.json().get("courses",[])
    except (httpx.HTTPError,ValueError) as exc:
        raise HTTPException(503,"Learning catalogue unavailable") from exc
    if behavioural_only: courses=[course for course in courses if "behavio" in course.get("category","").lower()]
    return [{"course_id":course["id"],"title":course["title"],"organization":course.get("organization","") ,"category":course.get("category","") ,"overview":course.get("overview","") ,"mapped_notices":[doc["title"] for doc in DOCUMENTS if course["id"]==1],"case_count":len(all_cases(course["id"]))} for course in courses]

@app.get("/v1/behavioural/corpus")
def behavioural_corpus(): return DOCUMENTS

@app.get("/v1/behavioural/corpus/{document_id}")
def behavioural_document(document_id:str):
    document=find_document(document_id)
    if not document:raise HTTPException(404,"Government document not found")
    return document

def _case_or_none(case_id:str,principal:Principal,db:Session)->dict|None:
    authored=find_case(case_id)
    if authored:return authored
    generated=db.get(GeneratedBehaviouralCase,case_id)
    return generated.definition if generated and (generated.user_id==principal.user_id or principal.role=="admin") else None

@app.get("/v1/behavioural/cases")
def behavioural_cases(course_id:int|None=Query(None),principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    records=db.scalars(select(GeneratedBehaviouralCase).where(GeneratedBehaviouralCase.user_id==principal.user_id)).all()
    return all_cases(course_id)+[row.definition for row in records if course_id is None or row.course_id==course_id]

@app.post("/v1/behavioural/cases/generate",status_code=201)
def generate_behavioural_case(req:BehaviouralCaseGeneration,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    if len(req.raw_text.strip())<50:raise HTTPException(400,"Document text must contain at least 50 characters")
    case=build_case(req.raw_text,req.document_title,req.document_type,req.issuing_authority,req.statutory_reference)
    db.add(GeneratedBehaviouralCase(id=case["id"],user_id=principal.user_id,definition=case));db.commit();return case

@app.get("/v1/behavioural/cases/{case_id}")
def behavioural_case(case_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    case=_case_or_none(case_id,principal,db)
    if not case:raise HTTPException(404,"Case scenario not found")
    return case

@app.get("/v1/behavioural/courses/{course_id}/cases")
def behavioural_course_cases(course_id:int,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    return behavioural_cases(course_id,principal,db)

@app.post("/v1/behavioural/courses/{course_id}/generate-case",status_code=201)
async def generate_course_case(course_id:int,req:CourseCaseGeneration,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    metadata=await course_metadata(str(course_id))
    notice=(req.custom_notice_text or "").strip() or str(metadata.get("material") or metadata.get("overview") or "").strip()
    if len(notice)<50:raise HTTPException(400,"Provide at least 50 characters of notice or course material")
    title=str(metadata.get("title") or f"Course {course_id}")
    case=build_case(notice,title,"Course notice",str(metadata.get("organization") or "Course provider"),"",course_id,title,str(metadata.get("organization") or ""))
    db.add(GeneratedBehaviouralCase(id=case["id"],user_id=principal.user_id,course_id=course_id,definition=case));db.commit();return case

@app.post("/v1/behavioural/session/start",status_code=201)
def start_behavioural_session(req:BehaviouralSessionStart,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    case=_case_or_none(req.case_id,principal,db) if req.case_id else (all_cases()[0] if all_cases() else None)
    if not case:raise HTTPException(404,"Case scenario not found")
    question=case["questions"][case["root_question_id"]];state={"case_id":case["id"],"case_snapshot":case,"question_id":question["id"],"trail":[],"completed":False}
    record=SessionRecord(user_id=principal.user_id,engine="behavioural_carryforward",state=state);db.add(record);db.commit()
    return {"session_id":record.id,"case_id":case["id"],"case_title":case["title"],"document_title":case["document_title"],"document_type":case["document_type"],"initial_context":case["initial_context"],"current_question":question}

def _behavioural_record(session_id:str,principal:Principal,db:Session)->tuple[SessionRecord,dict]:
    record=db.get(SessionRecord,session_id)
    if not record or record.user_id!=principal.user_id or record.engine!="behavioural_carryforward":raise HTTPException(404,"Session not found")
    case=record.state.get("case_snapshot") or _case_or_none(record.state["case_id"],principal,db)
    if not case:raise HTTPException(409,"Session case is unavailable")
    return record,case

@app.get("/v1/behavioural/session/{session_id}/current")
def current_behavioural_question(session_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record,case=_behavioural_record(session_id,principal,db);question=case["questions"].get(record.state.get("question_id"))
    return {"session_id":record.id,"case_id":case["id"],"case_title":case["title"],"session_completed":record.state.get("completed",False),"total_steps":len(record.state.get("trail",[])),"optimal_steps":sum(item["is_optimal"] for item in record.state.get("trail",[])),"current_question":question}

@app.post("/v1/behavioural/session/{session_id}/submit")
def submit_behavioural_answer(session_id:str,req:BehaviouralAnswer,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record,case=_behavioural_record(session_id,principal,db);state=dict(record.state)
    if state.get("completed"):raise HTTPException(409,"Session is complete")
    question=case["questions"].get(state.get("question_id"))
    if not question or question["id"]!=req.question_id:raise HTTPException(409,"Question is not current")
    option=next((item for item in question["options"] if item["option_id"]==req.selected_option_id),None)
    if not option:raise HTTPException(422,"Unknown option")
    trail=[*state.get("trail",[]),{"question_id":question["id"],"stage_type":question["stage_type"],"question_prompt":question["prompt"],"selected_option_id":option["option_id"],"selected_option_text":option["text"],"is_optimal":option["is_optimal"],"is_satisfactory_terminal":option["is_satisfactory_terminal"],"consequence_summary":option["consequence_summary"],"statutory_rationale":option["statutory_rationale"]}];next_id=option.get("next_question_id");completed=not next_id;state.update(trail=trail,question_id=next_id,completed=completed);record.state=state;record.status="completed" if completed else "active";db.commit();score=round(sum(item["is_optimal"] for item in trail)*100/len(trail),1)
    return {"is_optimal":option["is_optimal"],"is_satisfactory_terminal":option["is_satisfactory_terminal"],"consequence_summary":option["consequence_summary"],"statutory_rationale":option["statutory_rationale"],"carryforward_active":bool(next_id),"scenario_completed":completed,"session_completed":completed,"current_score":score,"total_steps_taken":len(trail),"next_question":case["questions"].get(next_id),"next_case_id":None}

@app.get("/v1/behavioural/session/{session_id}/summary")
def behavioural_summary(session_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record,case=_behavioural_record(session_id,principal,db);trail=record.state.get("trail",[]);score=round(sum(item["is_optimal"] for item in trail)*100/max(len(trail),1),1)
    return {"session_id":record.id,"case_id":case["id"],"case_title":case["title"],"document_title":case["document_title"],"document_type":case["document_type"],"total_steps":len(trail),"optimal_steps":sum(item["is_optimal"] for item in trail),"procedural_compliance_score":score,"resolved_satisfactorily":bool(trail and trail[-1]["is_satisfactory_terminal"]),"decision_trail":trail,"competency_scores":{"procedural fairness":score},"competency_results":[],"strengths":["Procedural reasoning"] if score>=70 else [],"weaknesses":[] if score>=70 else ["Review mandatory safeguards"],"recommended_upskilling":[],"key_takeaways":case["learning_objectives"]}

def _interview_record(session_id:str,principal:Principal,db:Session)->SessionRecord:
    record=db.get(SessionRecord,session_id)
    if not record or record.user_id!=principal.user_id or record.engine!="behavioural_interview":raise HTTPException(404,"Interview session not found")
    return record

async def _interview_ai(messages:list[dict[str,str]],schema_hint:dict,authorization:str|None)->tuple[dict|None,str|None]:
    if not authorization:return None,None
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response=await client.post(f"{get_settings().ai_service_url}/v1/generate/json",headers={"Authorization":authorization},json={"messages":messages,"schema_hint":schema_hint,"preferred_provider":"groq"})
            response.raise_for_status();payload=response.json();data=payload.get("data")
            if not isinstance(data,dict) or not data:return None,None
            return data,str(payload.get("provider") or "groq")
    except httpx.HTTPStatusError as exc:
        logger.warning("Interview AI request failed with status %s",exc.response.status_code)
        return None,None
    except (httpx.RequestError,ValueError,TypeError) as exc:
        logger.warning("Interview AI request failed: %s",type(exc).__name__)
        return None,None

async def _interview_course_context(course_id:int)->dict:
    cfg=get_settings()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response=await client.get(f"{cfg.learning_url}/v1/internal/courses/{course_id}/interview-context",headers={"X-Internal-Secret":cfg.internal_event_secret})
            response.raise_for_status();return response.json()
    except (httpx.HTTPError,ValueError):
        logger.warning("Interview course context unavailable for course %s",course_id)
        return await course_metadata(course_id)

@app.post("/v1/behavioural/interview/transcribe")
async def transcribe_interview(audio:UploadFile=File(...),_:Principal=Depends(current_principal)):
    api_key=get_settings().sarvam_api_key
    if not api_key:raise HTTPException(503,"Dictation transcription is not configured. Set SARVAM_API_KEY and restart the assessment service.")
    payload=await audio.read(MAX_DICTATION_BYTES+1)
    if not payload:raise HTTPException(400,"No audio was recorded")
    if len(payload)>MAX_DICTATION_BYTES:raise HTTPException(413,"The recording is too large to transcribe")
    filename=audio.filename or "dictation.wav";content_type=(audio.content_type or "audio/wav").split(";",1)[0].lower()
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response=await client.post(SARVAM_STT_URL,headers={"api-subscription-key":api_key},data={"model":"saaras:v4","language_code":"en-IN"},files={"file":(filename,payload,content_type)})
            response.raise_for_status();result=response.json()
    except httpx.HTTPStatusError as exc:raise HTTPException(502,f"Speech transcription was rejected: {_sarvam_error(exc.response)}") from exc
    except (httpx.RequestError,ValueError) as exc:raise HTTPException(502,"Speech transcription is temporarily unavailable") from exc
    transcript=str(result.get("transcript") or "").strip()
    if not transcript:raise HTTPException(422,"No speech was detected. Please speak clearly and try again.")
    return {"text":transcript,"provider":"sarvam","request_id":result.get("request_id")}

@app.post("/v1/behavioural/interview/start",status_code=201)
async def start_interview(req:InterviewStart,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    if req.target_duration_minutes<25 or req.target_duration_minutes>35:raise HTTPException(422,"Interview duration must be between 25 and 35 minutes")
    metadata=await _interview_course_context(req.course_id);title=str(metadata.get("title") or f"Course {req.course_id}")
    state=start_state(req.course_id,title,req.officer_name.strip() or principal.full_name or "Officer",req.target_duration_minutes)
    state.update(organization=metadata.get("organization") or "iGOT Karmayogi",overview=metadata.get("overview") or "",modules=metadata.get("modules") or [],material=metadata.get("material") or "")
    record=SessionRecord(user_id=principal.user_id,engine="behavioural_interview",state=state);db.add(record);db.commit()
    return {"session_id":record.id,"course_id":req.course_id,"course_title":title,"officer_name":state["officer_name"],"target_duration_minutes":req.target_duration_minutes,"initial_ai_question":state["transcript"][0]["content"],"current_phase":PHASES[0][0],"primary_competency":PHASES[0][1]}

@app.post("/v1/behavioural/interview/turn")
async def interview_turn(req:InterviewTurn,principal:Principal=Depends(current_principal),db:Session=Depends(get_db),authorization:str|None=Header(None)):
    record=_interview_record(req.session_id,principal,db)
    if record.status!="active":raise HTTPException(409,"Interview session is already complete")
    metrics=req.model_dump(exclude={"session_id","officer_response","elapsed_seconds"})
    messages,schema=turn_ai_request(dict(record.state),req.officer_response);ai_result,provider=await _interview_ai(messages,schema,authorization)
    if not isinstance(ai_result,dict) or not str(ai_result.get("reply") or "").strip():ai_result,provider=None,None
    try:state,response=submit_turn(dict(record.state),req.officer_response,req.elapsed_seconds,metrics,ai_result,provider)
    except ValueError as exc:raise HTTPException(409,str(exc))
    record.state=state;db.commit();return response

async def _finish_interview(session_id:str,principal:Principal,db:Session,authorization:str|None)->dict:
    record=_interview_record(session_id,principal,db);state=dict(record.state)
    if state.get("final_report"):return state["final_report"]
    messages,schema=report_ai_request(state);ai_result,provider=await _interview_ai(messages,schema,authorization)
    if not isinstance(ai_result,dict) or not isinstance(ai_result.get("competency_scores"),dict):ai_result,provider=None,None
    report=build_report(record.id,state,ai_result,provider);state["final_report"]=report;record.state=state;record.status="completed";db.commit();return report

@app.post("/v1/behavioural/interview/end")
async def end_interview_by_body(req:InterviewEnd,principal:Principal=Depends(current_principal),db:Session=Depends(get_db),authorization:str|None=Header(None)):
    return await _finish_interview(req.session_id,principal,db,authorization)

@app.post("/v1/behavioural/interview/{session_id}/end")
async def end_interview(session_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db),authorization:str|None=Header(None)):
    return await _finish_interview(session_id,principal,db,authorization)
@app.post("/v1/assessments",status_code=201)
def create_assessment(req:AssessmentCreate,_:Principal=Depends(require_admin),db:Session=Depends(get_db)):
    obj=Assessment(id=req.id,course_id=req.course_id,title=req.title,description=req.description,engine=req.engine,time_limit_minutes=req.time_limit_minutes,pass_threshold_percent=req.pass_threshold_percent); obj.questions=[Question(**q.model_dump()) for q in req.questions]; db.add(obj); db.commit(); db.refresh(obj); return {"id":obj.id}
async def course_metadata(course_id:str)->dict:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response=await client.get(f"{get_settings().learning_url}/v1/courses/{course_id}"); return response.json() if response.is_success else {}
    except httpx.HTTPError: return {}
@app.get("/v1/assessments/{assessment_id}")
async def get_assessment(assessment_id:int,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    obj=db.get(Assessment,assessment_id)
    if not obj: raise HTTPException(404,"Assessment not found")
    meta=await course_metadata(obj.course_id); questions=list(obj.questions); random.shuffle(questions); attempts=db.scalars(select(Attempt).where(Attempt.user_id==principal.user_id,Attempt.assessment_id==assessment_id).order_by(Attempt.submitted_at.desc())).all(); last=attempts[0] if attempts else None
    safe_options=lambda values:[str(option.get("text",option.get("label",option.get("id","")))) if isinstance(option,dict) else str(option) for option in values]
    return {"id":obj.id,"course_id":obj.course_id,"course_title":meta.get("title",""),"organization":meta.get("organization",""),"title":obj.title,"description":obj.description,"time_limit_minutes":obj.time_limit_minutes,"pass_threshold_percent":obj.pass_threshold_percent,"total_questions":len(questions),"questions":[{"id":q.id,"text":q.text,"options":safe_options(q.options),"order":q.order} for q in questions],"last_attempt":({"id":last.id,"score_percent":last.score_percent,"passed":last.passed,"submitted_at":last.submitted_at.strftime("%d %b %Y, %I:%M %p")} if last else None),"total_attempts_count":len(attempts)}
@app.post("/v1/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id:int,req:SubmitAssessmentRequest,principal:Principal=Depends(current_principal),db:Session=Depends(get_db),idempotency_key:str|None=Header(None,alias="Idempotency-Key")):
    if idempotency_key:
        old=db.scalar(select(Attempt).where(Attempt.user_id==principal.user_id,Attempt.idempotency_key==idempotency_key))
        if old:return old.result
    obj=db.get(Assessment,assessment_id)
    if not obj:raise HTTPException(404,"Assessment not found")
    if not obj.questions:raise HTTPException(400,"No questions configured for this assessment")
    breakdown=[];correct=0;evidence={}
    for q in obj.questions:
        selected=req.answers.get(str(q.id));ok=selected==q.correct_option_index;correct+=int(ok);breakdown.append({"question_id":q.id,"question_text":q.text,"options":q.options,"selected_option":selected,"correct_option":q.correct_option_index,"is_correct":ok,"explanation":q.explanation})
        if q.competency_code:evidence.setdefault(q.competency_code,[]).append(ok)
    score=round(correct*100/len(obj.questions),1);passed=score>=obj.pass_threshold_percent;attempt_id=str(uuid4());meta=await course_metadata(obj.course_id);result={"attempt_id":attempt_id,"score_percent":score,"pass_threshold_percent":obj.pass_threshold_percent,"passed":passed,"correct_answers":correct,"total_questions":len(obj.questions),"course_id":obj.course_id,"course_title":meta.get("title",""),"organization":meta.get("organization",""),"duration_hours":meta.get("duration_hours",0),"certificate_id":f"KARM-CERT-{obj.course_id}-{int(principal.user_id):04d}","recipient_name":principal.full_name,"breakdown":breakdown}
    db.add(Attempt(id=attempt_id,user_id=principal.user_id,assessment_id=obj.id,engine=obj.engine,score_percent=score,passed=passed,answers=req.answers,result=result,idempotency_key=idempotency_key));event={"event_id":str(uuid4()),"occurred_at":datetime.now(timezone.utc).isoformat(),"user_id":principal.user_id,"assessment_id":obj.id,"attempt_id":attempt_id,"course_id":obj.course_id,"engine":obj.engine,"score_percent":score,"passed":passed,"evidence":[{"competency_code":c,"domain_code":obj.engine,"level":round(sum(v)*5/len(v),2),"source_type":"assessment","source_id":attempt_id} for c,v in evidence.items()]};db.add(OutboxEvent(topic="assessment.completed.v1",payload=event));db.commit();return result
@app.post("/v1/sessions",status_code=201)
def start_session(req:SessionStart,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    impl=REGISTRY.get(req.engine)
    if not impl:raise HTTPException(422,"unknown assessment engine")
    assessment=db.get(Assessment,req.assessment_id)
    if not assessment:raise HTTPException(404,"Assessment not found")
    if assessment.engine!=req.engine:raise HTTPException(409,"assessment engine does not match requested engine")
    definition={"items":[{"id":q.id,"text":q.text,"options":q.options,"correct_option_index":q.correct_option_index,"competency_code":q.competency_code} for q in assessment.questions],"competency_codes":sorted({q.competency_code for q in assessment.questions if q.competency_code}),"pass_threshold_percent":assessment.pass_threshold_percent}
    try:state=impl.start(definition)
    except ValueError as exc:raise HTTPException(409,str(exc))
    record=SessionRecord(user_id=principal.user_id,assessment_id=req.assessment_id,engine=req.engine,state=state);db.add(record);db.commit();return {"session_id":record.id,"status":record.status,"state":public_state(record.state)}
@app.get("/v1/sessions/{session_id}")
def get_session(session_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record=db.get(SessionRecord,session_id)
    if not record or record.user_id!=principal.user_id:raise HTTPException(404,"Session not found")
    return {"session_id":record.id,"engine":record.engine,"status":record.status,"state":public_state(record.state),**({"result":record.state.get("final_result")} if record.status=="completed" else {})}
@app.post("/v1/sessions/{session_id}/submit")
def session_submit(session_id:str,req:SessionAnswer,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record=db.get(SessionRecord,session_id)
    if not record or record.user_id!=principal.user_id:raise HTTPException(404,"Session not found")
    if record.status!="active":raise HTTPException(409,"session is not active")
    try:record.state=REGISTRY[record.engine].submit(dict(record.state),req.answer)
    except ValueError as exc:raise HTTPException(409,str(exc))
    db.commit();return {"session_id":record.id,"state":public_state(record.state)}
@app.post("/v1/sessions/{session_id}/finalize")
def finalize(session_id:str,principal:Principal=Depends(current_principal),db:Session=Depends(get_db)):
    record=db.get(SessionRecord,session_id)
    if not record or record.user_id!=principal.user_id:raise HTTPException(404,"Session not found")
    if record.status=="completed":return record.state["final_result"]
    try:result=REGISTRY[record.engine].finalize(record.state)
    except ValueError as exc:raise HTTPException(409,str(exc))
    state=dict(record.state);state["final_result"]=result;record.state=state;record.status="completed";payload={"event_id":str(uuid4()),"occurred_at":datetime.now(timezone.utc).isoformat(),"user_id":principal.user_id,"assessment_id":record.assessment_id,"attempt_id":record.id,"course_id":None,"engine":record.engine,**result};db.add(OutboxEvent(topic="assessment.completed.v1",payload=payload));db.commit();return result
