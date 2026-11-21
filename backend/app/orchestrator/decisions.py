from ..agents.catalog import load_agent
from ..providers import chat
from ..models import Decision

TIER_PANELS={
    "leaders": [f"leader-{i:05d}" for i in range(1,6)],
    "hod": [f"hod-{i:03d}" for i in range(1,4)],
    "principals": [f"principal-{i:02d}" for i in range(1,4)],
}

def _panel_review(db, owner_id, subject, evidence, tier, agent_ids):
    reviews=[]
    for agent_id in agent_ids:
        profile=load_agent(agent_id)
        msg=[{"role":"system","content":profile["system_prompt"]},{"role":"user","content":f"Review this dispute independently at the {tier} tier. State your recommended option, evidence, risks, and whether it is safe to resolve at this tier. Start with ESCALATE only when your authority or evidence is insufficient.\nSubject: {subject}\n{evidence}"}]
        reviews.append({"agent":agent_id,"review":chat(db,owner_id,msg,temperature=0.1)})
    chair=load_agent(agent_ids[0])
    synthesis=[{"role":"system","content":chair["system_prompt"]},{"role":"user","content":f"You are chairing the {tier} council. Reconcile the panel reviews. Resolve only if there is a defensible evidence-based decision. If material disagreement remains or higher authority is required, begin with ESCALATE. Return one actionable decision and explain dissent.\nSubject: {subject}\nProposals and evidence:\n{evidence}\nPanel reviews:\n"+"\n\n".join(f"{x['agent']}: {x['review']}" for x in reviews)}]
    return reviews, chat(db,owner_id,synthesis,temperature=0.1)

def resolve_dispute(db: Session, owner_id: int, project_id: int, subject: str, proposals: list[dict], critical: bool=False) -> Decision:
    record=Decision(project_id=project_id, subject=subject, proposals={"items":proposals}, critical=critical, audit_log=[])
    db.add(record); db.commit(); db.refresh(record)
    evidence="\n".join(f"{p.get('agent','Agent')}: {p.get('proposal','')}\nEvidence: {p.get('evidence','')}" for p in proposals)
    for tier, ids in TIER_PANELS.items():
        try:
            reviews, result=_panel_review(db,owner_id,subject,evidence,tier,ids)
            record.audit_log.append({"tier":tier,"panel":reviews,"chair_decision":result})
        except Exception as exc:
            result=f"ESCALATE: {type(exc).__name__}: {exc}"
            record.audit_log.append({"tier":tier,"error":result})
        if not result.strip().upper().startswith("ESCALATE"):
            record.resolution=result; record.escalated_to=tier; record.status="resolved"; db.commit(); return record
    if critical:
        profile=load_agent("master-001")
        msg=[{"role":"system","content":profile["system_prompt"]},{"role":"user","content":f"Critical unresolved decision. Review the complete prior audit, select one safe, implementable decision, and state risks and verification. If evidence is insufficient, begin with OWNER_REVIEW.\nSubject: {subject}\nProposals:\n{evidence}\nAudit:\n{record.audit_log}"}]
        try: result=chat(db,owner_id,msg,temperature=0.0)
        except Exception as exc: result=f"OWNER_REVIEW: Master decision unavailable: {exc}"
        record.audit_log.append({"tier":"master","agent":"master-001","response":result})
        if result.strip().upper().startswith("OWNER_REVIEW"):
            record.resolution=result; record.escalated_to="owner"; record.status="owner_review"
        else:
            record.resolution=result; record.escalated_to="master"; record.status="resolved"
    else:
        record.resolution="Unresolved at Principal tier. Marked for owner review; Master Leader was not contacted because this case was not marked critical."; record.escalated_to="owner"; record.status="owner_review"
    db.commit(); return record
