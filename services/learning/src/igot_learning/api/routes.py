import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from igot_learning.adapters.database import get_db
from igot_learning.application.auth import Principal, admin, internal_secret, optional_principal, principal
from igot_learning.domain.models import AssessmentProjection, Certificate, Course, CourseSkill, Enrollment, LearnerProjection, LearningHistory, Lesson, Module, PlannedCourse, ProcessedEvent, Progress, SearchHistory

router=APIRouter(prefix="/v1")
class ActivityAnswer(BaseModel): selected_option:int
class Assignment(BaseModel): user_id:int; course_id:int; planned_for:str|None=None
class AssessmentCompleted(BaseModel):
    event_id:str; user_id:int; course_id:int; attempt_id:str; score_percent:float; passed:bool; occurred_at:datetime
class CourseCreate(BaseModel):
    title:str=Field(min_length=1,max_length=255); overview:str=Field(min_length=1); instructor:str=Field(min_length=1,max_length=255); organization:str=Field(min_length=1,max_length=255); duration_hours:float=Field(default=4,gt=0); difficulty:str="intermediate"; category:str="General"; source:str="internal"
class LearnerProjectionIn(BaseModel):
    user_id:int; email:str; full_name:str; role:str="learner"; designation:str|None=None; department:str|None=None; onboarding_completed:bool=False; daily_goal_minutes:int=30; current_streak_days:int=1; last_active_date:datetime|None=None

def course_summary(c:Course):
    return {"id":c.id,"title":c.title,"overview":c.overview,"instructor":c.instructor,"organization":c.organization,"duration_hours":c.duration_hours,"difficulty":c.difficulty,"source":c.source,"category":c.category,"thumbnail_url":c.thumbnail_url,"rating":c.rating,"enrolled_count":c.enrolled_count,"is_popular":c.is_popular,"is_new":c.is_new}

@router.get("/discover/courses")
def discover_courses(q:str|None=None,category:str|None=None,difficulty:str|None=None,source:str|None=None,sort:str="popular",limit:int=Query(200,ge=1,le=200),p:Principal|None=Depends(optional_principal),db:Session=Depends(get_db)):
    stmt=select(Course)
    if q and q.strip():
        term=f"%{q.strip()}%"; stmt=stmt.where(or_(Course.title.ilike(term),Course.overview.ilike(term),Course.instructor.ilike(term),Course.organization.ilike(term),Course.category.ilike(term)))
        if p: db.add(SearchHistory(user_id=p.user_id,query=q.strip()))
    if category and category.lower()!="all":
        stmt=stmt.where(Course.is_popular.is_(True)) if category.lower()=="popular" else stmt.where(Course.is_new.is_(True)) if category.lower()=="new" else stmt.where(Course.category.ilike(f"%{category}%"))
    if difficulty and difficulty.lower()!="all": stmt=stmt.where(Course.difficulty==difficulty.lower())
    if source and source.lower()!="all": stmt=stmt.where(Course.source==source.lower())
    ordering={"new":Course.created_at.desc(),"rating":Course.rating.desc(),"duration":Course.duration_hours.asc()}.get(sort,Course.enrolled_count.desc())
    rows=db.scalars(stmt.order_by(ordering).limit(limit)).all()
    modules=dict(db.execute(select(Module.course_id,func.count(Module.id)).group_by(Module.course_id)).all())
    categories=list(db.scalars(select(Course.category).distinct().order_by(Course.category)))
    recent=[]
    if p:
        for value in db.scalars(select(SearchHistory.query).where(SearchHistory.user_id==p.user_id).order_by(SearchHistory.searched_at.desc()).limit(50)):
            if value not in recent: recent.append(value)
            if len(recent)==5: break
    db.commit()
    return {"total_results":len(rows),"courses":[{**course_summary(c),"modules_count":modules.get(c.id,0),"has_assessment":c.assessment_id is not None} for c in rows],"categories":categories,"trending_searches":["National Sample Survey","Consumer Price Index","CAPI Field Validation","UN-NQAF Data Quality","Treasury Single Account PFMS","Python Microdata Analysis"],"user_recent_searches":recent}

@router.get("/courses")
def courses(limit:int=Query(50,ge=1,le=200),db:Session=Depends(get_db)):
    return [course_summary(c) for c in db.scalars(select(Course).order_by(Course.is_popular.desc(),Course.created_at.desc()).limit(limit))]

def load_course(db,id):
    return db.scalar(select(Course).options(selectinload(Course.modules).selectinload(Module.lessons),selectinload(Course.course_skills).selectinload(CourseSkill.skill)).where(Course.id==id))

@router.get("/courses/{course_id}")
def course_detail(course_id:int,p:Principal|None=Depends(optional_principal),db:Session=Depends(get_db)):
    c=load_course(db,course_id)
    if not c: raise HTTPException(404,"Course not found")
    if p:
        history=db.scalar(select(LearningHistory).where(LearningHistory.user_id==p.user_id,LearningHistory.course_id==c.id))
        if history: history.viewed_at=datetime.now(timezone.utc)
        else: db.add(LearningHistory(user_id=p.user_id,course_id=c.id))
    counts={"videos":0,"readings":0,"labs":0,"assessments":1 if c.assessment_id else 0,"modules":len(c.modules)}; modules=[]
    for m in c.modules:
        lessons=[]
        for l in m.lessons:
            key="videos" if l.content_type=="video" else "labs" if l.content_type=="lab" else "readings"; counts[key]+=1
            lessons.append({"id":l.id,"title":l.title,"content_type":l.content_type,"duration_minutes":l.duration_minutes,"has_activity":bool(l.activity_question),"order":l.position})
        modules.append({"id":m.id,"title":m.title,"description":m.description,"order":m.position,"lessons_count":len(lessons),"lessons":lessons})
    enrollment=None
    if p:
        e=db.scalar(select(Enrollment).where(Enrollment.user_id==p.user_id,Enrollment.course_id==c.id))
        if e: enrollment={"enrollment_id":e.id,"status":e.status,"progress_percent":e.progress_percent,"last_lesson_id":e.last_lesson_id}
    db.commit(); return {**course_summary(c),"counts":counts,"skills_gained":[x.skill.name for x in c.course_skills],"modules":modules,"assessment_id":c.assessment_id,"enrollment":enrollment}

@router.post("/courses/{course_id}/enroll")
def enroll(course_id:int,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    c=load_course(db,course_id)
    if not c: raise HTTPException(404,"Course not found")
    e=db.scalar(select(Enrollment).where(Enrollment.user_id==p.user_id,Enrollment.course_id==course_id)); first=next((l.id for m in c.modules for l in m.lessons),None)
    if not e:
        e=Enrollment(user_id=p.user_id,course_id=course_id,last_lesson_id=first); c.enrolled_count+=1; db.add(e); db.commit(); db.refresh(e)
    return {"success":True,"message":f"Enrolled successfully in {c.title}","enrollment_id":e.id,"status":e.status,"first_lesson_id":e.last_lesson_id or first}

@router.get("/learning/course/{course_id}/player")
def player(course_id:int,lesson_id:int|None=None,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    c=load_course(db,course_id)
    if not c: raise HTTPException(404,"Course not found")
    e=db.scalar(select(Enrollment).where(Enrollment.user_id==p.user_id,Enrollment.course_id==course_id))
    if not e: e=Enrollment(user_id=p.user_id,course_id=course_id); db.add(e); db.flush()
    progress={x.lesson_id:x for x in db.scalars(select(Progress).where(Progress.enrollment_id==e.id))}; flat=[]; tree=[]; objects={}
    for m in c.modules:
        ml=[]
        for l in m.lessons:
            objects[l.id]=l; item={"id":l.id,"module_id":m.id,"title":l.title,"content_type":l.content_type,"duration_minutes":l.duration_minutes,"completed":bool(progress.get(l.id) and progress[l.id].completed),"order":l.position}; ml.append(item); flat.append(item)
        tree.append({"id":m.id,"title":m.title,"description":m.description,"order":m.position,"lessons":ml,"completed_lessons":sum(x["completed"] for x in ml),"total_lessons":len(ml)})
    target=objects.get(lesson_id) or objects.get(e.last_lesson_id) or (objects[flat[0]["id"]] if flat else None)
    if not target: raise HTTPException(404,"No lesson content available in this course")
    e.last_lesson_id=target.id; idx=next(i for i,x in enumerate(flat) if x["id"]==target.id); pr=progress.get(target.id)
    result={"course":{"id":c.id,"title":c.title,"organization":c.organization,"progress_percent":round(sum(x["completed"] for x in flat)/max(len(flat),1)*100,1),"assessment_id":c.assessment_id},"modules_tree":tree,"current_lesson":{"id":target.id,"module_id":target.module_id,"module_title":target.module.title,"title":target.title,"content_type":target.content_type,"duration_minutes":target.duration_minutes,"content":target.content,"video_url":target.video_url,"completed":bool(pr and pr.completed),"activity":{"question":target.activity_question,"options":json.loads(target.activity_options_json or "[]"),"has_activity":True,"is_completed":bool(pr and pr.activity_completed)} if target.activity_question else None,"prev_lesson_id":flat[idx-1]["id"] if idx else None,"next_lesson_id":flat[idx+1]["id"] if idx+1<len(flat) else None,"is_last_lesson":idx+1==len(flat)}}
    db.commit(); return result

@router.post("/learning/lesson/{lesson_id}/complete")
def complete_lesson(lesson_id:int,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    lesson=db.get(Lesson,lesson_id)
    if not lesson: raise HTTPException(404,"Lesson not found")
    e=db.scalar(select(Enrollment).where(Enrollment.user_id==p.user_id,Enrollment.course_id==lesson.module.course_id))
    if not e: e=Enrollment(user_id=p.user_id,course_id=lesson.module.course_id); db.add(e); db.flush()
    row=db.scalar(select(Progress).where(Progress.enrollment_id==e.id,Progress.lesson_id==lesson.id))
    if row: row.completed=True
    else: db.add(Progress(enrollment_id=e.id,module_id=lesson.module_id,lesson_id=lesson.id,completed=True))
    db.flush(); total=db.scalar(select(func.count(Lesson.id)).join(Module).where(Module.course_id==lesson.module.course_id)); done=db.scalar(select(func.count(Progress.id)).where(Progress.enrollment_id==e.id,Progress.completed.is_(True))); e.progress_percent=min(100,round(done/max(total,1)*100,1)); db.commit()
    return {"success":True,"lesson_id":lesson.id,"progress_percent":e.progress_percent,"is_course_finished":e.progress_percent>=100}

@router.post("/learning/lesson/{lesson_id}/activity")
def activity(lesson_id:int,req:ActivityAnswer,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    lesson=db.get(Lesson,lesson_id)
    if not lesson or not lesson.activity_question: raise HTTPException(404,"Activity not found for this lesson")
    correct=req.selected_option==lesson.activity_correct_option
    if correct:
        e=db.scalar(select(Enrollment).where(Enrollment.user_id==p.user_id,Enrollment.course_id==lesson.module.course_id))
        if e:
            row=db.scalar(select(Progress).where(Progress.enrollment_id==e.id,Progress.lesson_id==lesson.id))
            if not row: row=Progress(enrollment_id=e.id,module_id=lesson.module_id,lesson_id=lesson.id,completed=False); db.add(row)
            row.activity_completed=True; db.commit()
    return {"is_correct":correct,"correct_option_index":lesson.activity_correct_option,"explanation":lesson.activity_explanation or "Correct concept understanding verified."}

@router.post("/internal/events/assessment-completed",dependencies=[Depends(internal_secret)])
def assessment_completed(event:AssessmentCompleted,db:Session=Depends(get_db)):
    if db.get(ProcessedEvent,event.event_id): return {"status":"duplicate","event_id":event.event_id}
    if event.passed:
        e=db.scalar(select(Enrollment).where(Enrollment.user_id==event.user_id,Enrollment.course_id==event.course_id))
        if not e: e=Enrollment(user_id=event.user_id,course_id=event.course_id); db.add(e); db.flush()
        e.status="completed"; e.completed_at=event.occurred_at; e.progress_percent=100
        cert=db.scalar(select(Certificate).where(Certificate.user_id==event.user_id,Certificate.course_id==event.course_id))
        if not cert: db.add(Certificate(user_id=event.user_id,course_id=event.course_id,attempt_id=event.attempt_id,score_percent=event.score_percent,issued_at=event.occurred_at))
    db.add(ProcessedEvent(event_id=event.event_id,event_type="assessment.completed.v1")); db.commit(); return {"status":"accepted","event_id":event.event_id}

@router.get("/dashboard/summary")
def dashboard(p:Principal=Depends(principal),db:Session=Depends(get_db)):
    enrollments=db.scalars(select(Enrollment).options(selectinload(Enrollment.course)).where(Enrollment.user_id==p.user_id)).all()
    learner=db.get(LearnerProjection,p.user_id); active=next((e for e in sorted(enrollments,key=lambda x:x.started_at,reverse=True) if e.status=="in_progress"),None); last=db.get(Lesson,active.last_lesson_id) if active and active.last_lesson_id else None
    enrolled_ids={e.course_id for e in enrollments}; recommended=db.scalars(select(Course).where(Course.id.not_in(enrolled_ids) if enrolled_ids else True).order_by(Course.rating.desc()).limit(4)).all(); trending=db.scalars(select(Course).order_by(Course.enrolled_count.desc()).limit(4)).all(); histories=db.scalars(select(LearningHistory).options(selectinload(LearningHistory.course)).where(LearningHistory.user_id==p.user_id).order_by(LearningHistory.viewed_at.desc()).limit(3)).all(); planned=db.scalars(select(PlannedCourse).options(selectinload(PlannedCourse.course)).where(PlannedCourse.user_id==p.user_id)).all()
    completed=sum(e.status=="completed" for e in enrollments); in_progress=sum(e.status=="in_progress" for e in enrollments); target=learner.daily_goal_minutes if learner else 30
    return {"authenticated":True,"learner":{"id":p.user_id,"full_name":learner.full_name if learner else "Learner","email":learner.email if learner else "","designation":learner.designation if learner and learner.designation else "Civil Servant","department":learner.department if learner and learner.department else "Official Statistical System","role":p.role},"continue_learning":{"enrollment_id":active.id,"course_id":active.course_id,"course_title":active.course.title,"organization":active.course.organization,"progress_percent":active.progress_percent,"current_module":last.module.title if last else "Orientation","current_lesson":last.title if last else "Introduction","last_lesson_id":active.last_lesson_id} if active else None,"todays_goals":{"target_minutes":target,"achieved_minutes":20 if active else 0,"percent":min(100,int(20/max(target,1)*100)) if active else 0},"learning_streak":{"streak_days":learner.current_streak_days if learner else 1,"last_active":learner.last_active_date.isoformat() if learner and learner.last_active_date else None},"my_learning_progress":{"in_progress_count":in_progress,"completed_count":completed,"overall_progress_percent":round(sum(e.progress_percent for e in enrollments)/max(len(enrollments),1),1),"hours_learned":round(sum(e.course.duration_hours for e in enrollments if e.status=="completed"),1)},"competencies":{"skills_count":0,"top_skills":[]},"recently_explored":[{**course_summary(h.course),"viewed_at":h.viewed_at.isoformat()} for h in histories if h.course],"trending_courses":[course_summary(c) for c in trending],"recommended_courses":[course_summary(c) for c in recommended],"future_planned":[{"id":x.id,"course_id":x.course_id,"course_title":x.course.title,"organization":x.course.organization,"duration_hours":x.course.duration_hours,"planned_for":x.planned_for or "Upcoming Quarter","source":x.source} for x in planned if x.course]}

@router.get("/certificates")
def certificates(p:Principal=Depends(principal),db:Session=Depends(get_db)):
    rows=db.scalars(select(Certificate).options(selectinload(Certificate.course)).where(Certificate.user_id==p.user_id)).all()
    return [{"certificate_id":f"KARM-CERT-{x.course_id}-{x.user_id:04d}","course_id":x.course_id,"course_title":x.course.title,"organization":x.course.organization,"instructor":x.course.instructor,"issued_date":x.issued_at.strftime("%B %d, %Y"),"score_percent":x.score_percent,"verification_status":"Verified Official Credential","duration_hours":x.course.duration_hours} for x in rows]

@router.get("/admin/courses")
def admin_courses(_:Principal=Depends(admin),db:Session=Depends(get_db)): return [course_summary(c) for c in db.scalars(select(Course).order_by(Course.title))]
@router.post("/admin/courses",status_code=201)
def create_course(req:CourseCreate,_:Principal=Depends(admin),db:Session=Depends(get_db)):
    row=Course(**req.model_dump(),is_new=True); db.add(row); db.commit(); db.refresh(row); return {"success":True,"message":"Course created successfully","course_id":row.id}
@router.post("/admin/assign-course")
def assign(req:Assignment,_:Principal=Depends(admin),db:Session=Depends(get_db)):
    if not db.get(Course,req.course_id): raise HTTPException(404,"Course not found")
    e=db.scalar(select(Enrollment).where(Enrollment.user_id==req.user_id,Enrollment.course_id==req.course_id))
    if not e: db.add(Enrollment(user_id=req.user_id,course_id=req.course_id)); db.commit()
    return {"success":True,"message":"Course officially assigned to learner.","user_id":req.user_id,"course_id":req.course_id}

@router.get("/admin/overview")
def admin_overview(_:Principal=Depends(admin),db:Session=Depends(get_db)):
    users=db.scalars(select(LearnerProjection)).all(); courses=db.scalars(select(Course)).all(); enrollments=db.scalars(select(Enrollment)).all(); by_course={c.id:c for c in courses}
    user_rows=[]
    for u in users:
        owned=[e for e in enrollments if e.user_id==u.user_id]; user_rows.append({"id":u.user_id,"email":u.email,"full_name":u.full_name,"role":u.role,"designation":u.designation or "Not onboarded","department":u.department or "N/A","onboarding_completed":u.onboarding_completed,"enrolled_courses_count":len(owned),"completed_courses_count":sum(e.status=="completed" for e in owned),"courses":[{"course_id":e.course_id,"title":by_course[e.course_id].title,"status":e.status,"progress_percent":e.progress_percent} for e in owned if e.course_id in by_course]})
    projections=db.scalars(select(AssessmentProjection)).all(); attempts=sum(x.attempts for x in projections); passed=sum(x.passed_attempts for x in projections); completed=sum(e.status=="completed" for e in enrollments)
    analytics=[]
    for c in courses:
        owned=[e for e in enrollments if e.course_id==c.id]; ap=next((x for x in projections if x.course_id==c.id),None); analytics.append({"id":c.id,"title":c.title,"organization":c.organization,"enrolled_count":len(owned),"completed_count":sum(e.status=="completed" for e in owned),"completion_rate_percent":round(100*sum(e.status=="completed" for e in owned)/max(len(owned),1),1),"assessment_pass_rate":round(100*ap.passed_attempts/max(ap.attempts,1),1) if ap else 0,"source":c.source})
    struggling=[]
    for ap in projections:
        try: struggling.extend(json.loads(ap.struggling_questions_json))
        except (TypeError,json.JSONDecodeError): pass
    return {"summary":{"total_users":len(users),"total_courses":len(courses),"total_enrollments":len(enrollments),"completed_enrollments":completed,"completion_rate_percent":round(100*completed/max(len(enrollments),1),1),"total_assessment_attempts":attempts,"overall_pass_rate_percent":round(100*passed/max(attempts,1),1)},"users":user_rows,"course_analytics":analytics,"struggling_questions":sorted(struggling,key=lambda x:x.get("accuracy_percent",100))}

@router.put("/internal/learners/{user_id}",dependencies=[Depends(internal_secret)])
def project_learner(user_id:int,req:LearnerProjectionIn,db:Session=Depends(get_db)):
    if user_id!=req.user_id: raise HTTPException(400,"user id mismatch")
    row=db.get(LearnerProjection,user_id) or LearnerProjection(user_id=user_id); db.add(row)
    for key,value in req.model_dump().items(): setattr(row,key,value)
    db.commit(); return {"status":"accepted","user_id":user_id}
