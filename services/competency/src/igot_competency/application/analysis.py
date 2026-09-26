from sqlalchemy import select
from sqlalchemy.orm import Session
from igot_competency.domain.models import Competency,Domain,Gap,Profile,UserScore
DOMAIN_COLUMNS={"statistical":"statistical_score","technical":"technical_score","digital_governance":"digital_governance_score","behavioural":"behavioural_score"}
def analyze(db:Session,user_id:int,target_levels:dict[str,float]|None=None):
    targets=target_levels or {}; scores=db.scalars(select(UserScore).where(UserScore.user_id==user_id)).all(); by={s.competency_id:s.level for s in scores}; gaps=[]; percentages={}
    for d in db.scalars(select(Domain).order_by(Domain.id)):
        ids=[c.id for c in d.competencies]; values=[by[x] for x in ids if x in by]; current=sum(values)/len(values) if values else 0.0; target=float(targets.get(d.code,2.5)); row=Gap(user_id=user_id,domain_id=d.id,target_level=target,current_level=current,gap=max(0,target-current)); db.add(row); gaps.append(row); percentages[d.code]=round(current/5*100,1)
    profile=db.scalar(select(Profile).where(Profile.user_id==user_id)) or Profile(user_id=user_id); db.add(profile)
    for code,column in DOMAIN_COLUMNS.items(): setattr(profile,column,percentages.get(code,0))
    db.commit()
    for row in gaps: db.refresh(row)
    return profile,gaps
