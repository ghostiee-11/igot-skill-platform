from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from sqlalchemy import delete,or_,select
from sqlalchemy.orm import Session,selectinload
from igot_competency.adapters.database import get_db
from igot_competency.application.analysis import analyze
from igot_competency.application.auth import Principal,admin,internal,principal
from igot_competency.domain.models import Competency,CourseCandidate,Domain,Evidence,Gap,Profile,Recommendation,UserScore,UserSkill
router=APIRouter(prefix="/v1")
class AnalyzeRequest(BaseModel): target_levels:dict[str,float]=Field(default_factory=dict)
class EvidenceIn(BaseModel):
    event_id:str; user_id:int; competency_code:str; domain_code:str; level:float=Field(ge=0,le=5); source_type:str; source_id:str; observed_at:datetime; metadata:dict=Field(default_factory=dict)
class EvidenceBatch(BaseModel): evidence:list[EvidenceIn]
class StatusUpdate(BaseModel): status:str
class CourseProjection(BaseModel): course_id:int;title:str;category:str;difficulty:str;overview:str
def profile_dict(p): return {"statistical_score":p.statistical_score,"technical_score":p.technical_score,"digital_governance_score":p.digital_governance_score,"behavioural_score":p.behavioural_score,"last_computed_at":p.last_computed_at.isoformat() if p.last_computed_at else None,"is_default_framework":True}
def gap_dict(g): return {"domain_code":g.domain.code,"domain_name":g.domain.name,"target_level":g.target_level,"current_level":g.current_level,"gap":g.gap,"generated_at":g.generated_at.isoformat()}
def rec_dict(r): return {"id":r.id,"course_id":r.course_id,"course_title":r.course_title,"reason":r.reason,"score":r.score,"status":r.status,"generated_at":r.generated_at.isoformat()}
@router.get("/competency/profile")
def profile(p:Principal=Depends(principal),db:Session=Depends(get_db)):
    row=db.scalar(select(Profile).where(Profile.user_id==p.user_id))
    if not row: raise HTTPException(404,"No competency profile yet. Call POST /competency/analyze first.")
    return profile_dict(row)
@router.get("/competency/gaps")
def gaps(p:Principal=Depends(principal),db:Session=Depends(get_db)):
    rows=db.scalars(select(Gap).options(selectinload(Gap.domain)).where(Gap.user_id==p.user_id).order_by(Gap.generated_at.desc())).all(); latest={}
    for row in rows: latest.setdefault(row.domain_id,row)
    if not latest: raise HTTPException(404,"No gap analysis yet. Call POST /competency/analyze first.")
    return [gap_dict(x) for x in latest.values()]
@router.post("/competency/analyze")
def run(req:AnalyzeRequest|None=None,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    prof,rows=analyze(db,p.user_id,req.target_levels if req else None); return {"profile":profile_dict(prof),"gaps":[gap_dict(x) for x in rows]}
@router.get("/competency/domains/{code}")
def domain_detail(code:str,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    d=db.scalar(select(Domain).options(selectinload(Domain.competencies)).where(Domain.code==code))
    if not d: raise HTTPException(404,"Competency domain not found")
    rows=db.scalars(select(UserScore).where(UserScore.user_id==p.user_id)).all(); levels={x.competency_id:x for x in rows}; latest=db.scalar(select(Gap).where(Gap.user_id==p.user_id,Gap.domain_id==d.id).order_by(Gap.generated_at.desc()))
    return {"domain":{"code":d.code,"name":d.name,"description":d.description},"target_level":latest.target_level if latest else None,"current_level":latest.current_level if latest else None,"gap":latest.gap if latest else None,"analyzed_at":latest.generated_at.isoformat() if latest else None,"competencies":[{"code":c.code,"name":c.name,"level":levels[c.id].level if c.id in levels else 0,"evidence_source":levels[c.id].evidence_source if c.id in levels else None} for c in d.competencies],"courses":[],"is_default_framework":True}

@router.get("/competency/skills")
def skills(p:Principal=Depends(principal),db:Session=Depends(get_db)):
    rows=db.scalars(select(UserSkill).options(selectinload(UserSkill.skill)).where(UserSkill.user_id==p.user_id).order_by(UserSkill.acquired_at.desc())).all()
    return [{"id":row.skill.id,"name":row.skill.name,"category":row.skill.category,"source_course_id":row.source_course_id,"competency_id":row.competency_id,"acquired_at":row.acquired_at.isoformat()} for row in rows]
def accept(e:EvidenceIn,db:Session):
    comp=db.scalar(select(Competency).join(Domain).where(Competency.code==e.competency_code,Domain.code==e.domain_code))
    if not comp: raise HTTPException(422,f"Unknown competency {e.domain_code}/{e.competency_code}")
    if db.scalar(select(Evidence).where(Evidence.event_id==e.event_id,Evidence.competency_id==comp.id)): return "duplicate"
    db.add(Evidence(event_id=e.event_id,user_id=e.user_id,competency_id=comp.id,level=e.level,source_type=e.source_type,source_id=e.source_id,observed_at=e.observed_at,metadata_json=e.metadata))
    score=db.scalar(select(UserScore).where(UserScore.user_id==e.user_id,UserScore.competency_id==comp.id))
    if not score: db.add(UserScore(user_id=e.user_id,competency_id=comp.id,level=e.level,evidence_source=e.source_type))
    elif e.level>=score.level: score.level=e.level; score.evidence_source=e.source_type
    return "accepted"
@router.post("/evidence",dependencies=[Depends(internal)])
def evidence(e:EvidenceIn,db:Session=Depends(get_db)):
    status=accept(e,db); db.commit(); return {"status":status,"event_id":e.event_id,"competency_code":e.competency_code}
@router.post("/evidence/batch",dependencies=[Depends(internal)])
def evidence_batch(batch:EvidenceBatch,db:Session=Depends(get_db)):
    result=[{"event_id":e.event_id,"competency_code":e.competency_code,"status":accept(e,db)} for e in batch.evidence]; db.commit(); return result
@router.get("/recommendations")
def recommendations(status:str|None=Query(None),p:Principal=Depends(principal),db:Session=Depends(get_db)):
    stmt=select(Recommendation).where(Recommendation.user_id==p.user_id)
    if status: stmt=stmt.where(Recommendation.status==status)
    return [rec_dict(x) for x in db.scalars(stmt.order_by(Recommendation.generated_at.desc()))]
@router.post("/recommendations/generate")
def generate(p:Principal=Depends(principal),db:Session=Depends(get_db)):
    latest={}
    for g in db.scalars(select(Gap).options(selectinload(Gap.domain)).where(Gap.user_id==p.user_id).order_by(Gap.generated_at.desc())): latest.setdefault(g.domain_id,g)
    db.execute(delete(Recommendation).where(Recommendation.user_id==p.user_id,Recommendation.status=="pending")); rows=[]
    for g in sorted(latest.values(),key=lambda x:x.gap,reverse=True):
        terms={g.domain.code,g.domain.name.split()[0]}; candidates=db.scalars(select(CourseCandidate).where(or_(*[CourseCandidate.category.ilike(f"%{term}%") for term in terms])).limit(3)).all()
        for c in candidates:
            r=Recommendation(user_id=p.user_id,course_id=c.course_id,course_title=c.title,reason=f"Builds {g.domain.name} toward target level {g.target_level:.1f}.",score=round(g.gap/5,3)); db.add(r); rows.append(r)
    db.commit(); return [rec_dict(x) for x in rows]
@router.patch("/recommendations/{recommendation_id}")
def update(recommendation_id:int,req:StatusUpdate,p:Principal=Depends(principal),db:Session=Depends(get_db)):
    if req.status not in {"pending","enrolled","dismissed"}: raise HTTPException(400,"status must be pending, enrolled, or dismissed")
    row=db.scalar(select(Recommendation).where(Recommendation.id==recommendation_id,Recommendation.user_id==p.user_id))
    if not row: raise HTTPException(404,"Recommendation not found")
    row.status=req.status; db.commit(); return rec_dict(row)
@router.put("/internal/course-candidates/{course_id}",dependencies=[Depends(internal)])
def project_course(course_id:int,req:CourseProjection,db:Session=Depends(get_db)):
    if course_id!=req.course_id: raise HTTPException(400,"course id mismatch")
    row=db.get(CourseCandidate,course_id) or CourseCandidate(course_id=course_id); db.add(row)
    for k,v in req.model_dump().items(): setattr(row,k,v)
    db.commit(); return {"status":"accepted","course_id":course_id}

@router.post("/admin/courses/{course_id}/reindex")
def reindex_course(course_id:int,_:Principal=Depends(admin),db:Session=Depends(get_db)):
    candidate=db.get(CourseCandidate,course_id)
    if not candidate: raise HTTPException(404,"Course projection not found")
    raise HTTPException(503,"Semantic vector indexing is not configured for the competency service")

@router.get("/admin/competency-analytics")
def competency_analytics(_:Principal=Depends(admin),db:Session=Depends(get_db)):
    domains=db.scalars(select(Domain).order_by(Domain.id)).all(); profiles=db.scalars(select(Profile)).all()
    columns={"statistical":"statistical_score","technical":"technical_score","digital_governance":"digital_governance_score","behavioural":"behavioural_score"}
    averages=[]
    for domain in domains:
        values=[getattr(row,columns[domain.code]) or 0 for row in profiles] if domain.code in columns else []
        averages.append({"domain_code":domain.code,"domain_name":domain.name,"average_score":round(sum(values)/len(values),1) if values else 0})
    latest={}
    for row in db.scalars(select(Gap).order_by(Gap.generated_at.desc())):
        latest.setdefault((row.user_id,row.domain_id),row)
    distribution=[]
    for domain in domains:
        rows=[row for (_,domain_id),row in latest.items() if domain_id==domain.id]
        distribution.append({"domain_code":domain.code,"domain_name":domain.name,"on_target":sum(row.gap<=0 for row in rows),"minor_gap":sum(0<row.gap<=1 for row in rows),"major_gap":sum(row.gap>1 for row in rows)})
    demand={}
    for row in db.scalars(select(Recommendation).where(Recommendation.course_id.is_not(None))):
        demand[row.course_id]=demand.get(row.course_id,0)+1
    courses={row.course_id:row for row in db.scalars(select(CourseCandidate).where(CourseCandidate.course_id.in_(demand.keys()))) } if demand else {}
    top=sorted(demand.items(),key=lambda item:item[1],reverse=True)[:5]
    return {"profiled_learners":len(profiles),"average_scores":averages,"gap_distribution":distribution,"gap_trend":[],"projections":[],"training_effectiveness":{},"top_recommended_courses":[{"course_id":course_id,"title":courses[course_id].title if course_id in courses else "","recommended_to":count} for course_id,count in top]}
