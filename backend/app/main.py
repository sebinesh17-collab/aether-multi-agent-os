import os, secrets
from pathlib import Path
import zipfile
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from .config import settings
from .db import Base, engine, get_db, SessionLocal
from .models import User, Project, ProjectFile, Task, Secret, Activity, Decision
from .schemas import LoginIn, ProjectIn, SecretIn, DecisionIn, DebateIn, TerminalIn
from .security import hash_password, verify_password, create_token, current_user
from .vault import encrypt
from .providers import get_secret
from .services.files import extract_text
from .services.storage import upload_to_firebase
from .services.terminal import execute_remote
from .orchestrator.decomposer import build_task_plan
from .orchestrator.decisions import resolve_dispute
from .agents.catalog import roster_counts
from .tools.catalog import TOOL_CATALOG

app=FastAPI(title=settings.app_name, version="1.0.0")
origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET","POST","PUT","DELETE"], allow_headers=["Authorization","Content-Type"])
redis_conn=Redis.from_url(settings.redis_url)
queue=Queue("aether", connection=redis_conn, default_timeout=60*60*24)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True); Path(settings.artifact_dir).mkdir(parents=True, exist_ok=True)
    if settings.owner_email and settings.owner_password:
        with SessionLocal() as db:
            if not db.query(User).filter_by(email=settings.owner_email.lower()).first():
                db.add(User(email=settings.owner_email.lower(), password_hash=hash_password(settings.owner_password), is_admin=True)); db.commit()

@app.get("/api/health")
def health():
    from sqlalchemy import text
    checks={"database":"ok","redis":"ok"}
    try:
        with engine.connect() as conn: conn.execute(text("SELECT 1"))
    except Exception: checks["database"]="error"
    try: redis_conn.ping()
    except Exception: checks["redis"]="error"
    ok=all(v=="ok" for v in checks.values())
    return {"status":"ok" if ok else "degraded", "checks":checks, "service":settings.app_name, "agent_roster":roster_counts()}

@app.post("/api/auth/login")
def login(data: LoginIn, db: Session=Depends(get_db)):
    user=db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, "Invalid email or password")
    return {"access_token":create_token(user),"token_type":"bearer","email":user.email}

@app.get("/api/me")
def me(user: User=Depends(current_user)): return {"email":user.email,"is_admin":user.is_admin}

@app.post("/api/auth/change-password")
def change_password(payload:dict, db:Session=Depends(get_db), user:User=Depends(current_user)):
    current=str(payload.get("current_password", "")); new=str(payload.get("new_password", ""))
    if len(new)<12 or len(new)>200: raise HTTPException(400,"New password must be 12–200 characters")
    from .security import verify_password
    if not verify_password(current,user.password_hash): raise HTTPException(400,"Current password is incorrect")
    user.password_hash=hash_password(new); db.commit(); return {"changed":True}

@app.post("/api/projects")
def create_project(data: ProjectIn, db: Session=Depends(get_db), user: User=Depends(current_user)):
    p=Project(owner_id=user.id,name=data.name,brief=data.brief,completion_email=data.completion_email,status="draft")
    db.add(p); db.commit(); db.refresh(p)
    db.add(Activity(project_id=p.id,message="Project workspace created",metadata_json={})); db.commit()
    return {"id":p.id,"name":p.name,"status":p.status}

@app.get("/api/projects")
def list_projects(db: Session=Depends(get_db), user: User=Depends(current_user)):
    rows=db.query(Project).filter_by(owner_id=user.id).order_by(Project.created_at.desc()).all()
    return [{"id":p.id,"name":p.name,"status":p.status,"task_count":p.task_count,"completed_count":p.completed_count,"failed_count":p.failed_count,"completion_email":p.completion_email,"created_at":p.created_at.isoformat() if p.created_at else None} for p in rows]

@app.get("/api/projects/{project_id}")
def project_detail(project_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    return {"id":p.id,"name":p.name,"brief":p.brief,"status":p.status,"task_count":p.task_count,"completed_count":p.completed_count,"failed_count":p.failed_count}

@app.post("/api/projects/{project_id}/files")
def upload_file(project_id:int, file:UploadFile=File(...), db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    safe_name=Path(file.filename or "upload.bin").name
    if len(safe_name)>250: raise HTTPException(400,"Filename too long")
    dest=Path(settings.upload_dir)/f"{project_id}_{secrets.token_hex(8)}_{safe_name}"
    size=0
    with dest.open("wb") as out:
        while chunk:=file.file.read(1024*1024):
            size+=len(chunk)
            if size>settings.max_upload_mb*1024*1024: dest.unlink(missing_ok=True); raise HTTPException(413,"Upload exceeds configured limit")
            out.write(chunk)
    extracted=extract_text(str(dest))
    pf=ProjectFile(project_id=project_id,filename=safe_name,local_path=str(dest),extracted_text=extracted,content_type=file.content_type or "application/octet-stream",size_bytes=size)
    db.add(pf); db.commit(); db.refresh(pf)
    try: pf.storage_uri=upload_to_firebase(db,user.id,str(dest),f"projects/{project_id}/{dest.name}"); db.commit()
    except Exception as exc: db.add(Activity(project_id=project_id,level="warning",message=f"Firebase upload failed; local file retained: {exc}",metadata_json={})); db.commit()
    return {"id":pf.id,"filename":pf.filename,"size_bytes":size,"storage_uri":pf.storage_uri,"extracted_chars":len(extracted)}

@app.post("/api/projects/{project_id}/start")
def start_project(project_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    if p.status in ("queued","running"): raise HTTPException(409,"Project is already running")
    if not get_secret(db,user.id,"provider:api_key"): raise HTTPException(400,"Add an AI provider API key in Settings before starting this project")
    source=[f.extracted_text for f in db.query(ProjectFile).filter_by(project_id=project_id).all()]
    plan=build_task_plan(p.name,p.brief,source)
    db.query(Task).filter_by(project_id=project_id).delete()
    for item in plan: db.add(Task(project_id=project_id,**item))
    p.task_count=len(plan); p.completed_count=0; p.failed_count=0; p.status="queued"
    db.add(Activity(project_id=project_id,message=f"Generated {len(plan)} tasks; queued for execution",metadata_json={"tasks":len(plan)})); db.commit()
    queue.enqueue("app.orchestrator.runner.run_project", project_id, job_timeout=60*60*24, result_ttl=86400, failure_ttl=86400)
    return {"project_id":project_id,"tasks_created":len(plan),"status":"queued"}

@app.get("/api/projects/{project_id}/tasks")
def list_tasks(project_id:int, offset:int=0, limit:int=100, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    rows=db.query(Task).filter_by(project_id=project_id).order_by(Task.sequence).offset(max(0,offset)).limit(min(max(1,limit),500)).all()
    return [{"id":t.id,"sequence":t.sequence,"title":t.title,"phase":t.phase,"department":t.department,"agent_id":t.agent_id,"status":t.status,"result":t.result,"error":t.error} for t in rows]

@app.get("/api/projects/{project_id}/export")
def export_results(project_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    out=Path(settings.artifact_dir)/f"project_{project_id}_results.md"
    rows=db.query(Task).filter_by(project_id=project_id).order_by(Task.sequence).all()
    with out.open("w",encoding="utf-8") as f:
        f.write(f"# {p.name}\n\nStatus: {p.status}\n\n")
        for t in rows: f.write(f"## Task {t.sequence}: {t.title}\n\nStatus: {t.status}\n\n{t.result or t.error}\n\n---\n\n")
    return FileResponse(out,filename=out.name,media_type="text/markdown")

@app.get("/api/projects/{project_id}/download")
def download_artifacts(project_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    root=Path(settings.artifact_dir)/f"project_{project_id}"
    if not root.exists(): raise HTTPException(404,"No generated artifacts yet")
    archive=Path(settings.artifact_dir)/f"project_{project_id}_artifacts.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for item in root.rglob("*"):
            if item.is_file() and item.resolve().is_relative_to(root.resolve()): z.write(item,item.relative_to(root))
    return FileResponse(archive,filename=f"{p.name.replace(' ','_')}_artifacts.zip",media_type="application/zip")

@app.get("/api/projects/{project_id}/activity")
def activity(project_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    rows=db.query(Activity).filter_by(project_id=project_id).order_by(Activity.created_at.desc()).limit(200).all()
    return [{"level":x.level,"message":x.message,"created_at":x.created_at.isoformat() if x.created_at else None} for x in rows]

@app.post("/api/settings/secrets")
def save_secret(data:SecretIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    allowed={"provider:api_key","provider:base_url","provider:model","firebase:service_account_json","firebase:storage_bucket"}
    if data.name not in allowed: raise HTTPException(400,"Unsupported secret name")
    row=db.query(Secret).filter_by(owner_id=user.id,name=data.name).first()
    if not row: row=Secret(owner_id=user.id,name=data.name,ciphertext=encrypt(data.value)); db.add(row)
    else: row.ciphertext=encrypt(data.value)
    db.commit(); return {"saved":True,"name":data.name,"value":"[redacted]"}

@app.get("/api/settings/secrets")
def secret_status(db:Session=Depends(get_db),user:User=Depends(current_user)):
    rows=db.query(Secret).filter_by(owner_id=user.id).all()
    return {x.name:True for x in rows}

@app.get("/api/agents/roster")
def agents(user:User=Depends(current_user)): return roster_counts()

@app.get("/api/tools/catalog")
def tools_catalog(user:User=Depends(current_user)): return TOOL_CATALOG

@app.post("/api/decisions/debate")
def debate(data:DebateIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=data.project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    from .agents.catalog import load_agent
    from .providers import chat
    positions=[("specialist-00003","Frontend Engineering"),("specialist-00004","Backend Engineering")]
    proposals=[]
    for agent_id, domain in positions:
        profile=load_agent(agent_id)
        prompt=f"Analyze the issue from your domain perspective. Make a concrete proposal, explain trade-offs, identify risks, and critique the alternative without straw-manning it. Provide evidence and a verification test.\nIssue: {data.subject}\nContext: {data.context}"
        response=chat(db,user.id,[{"role":"system","content":profile["system_prompt"]},{"role":"user","content":prompt}],temperature=0.2)
        proposals.append({"agent":domain,"proposal":response,"evidence":f"Agent profile {agent_id}; project context supplied by owner"})
    row=resolve_dispute(db,user.id,p.id,data.subject,proposals,data.critical)
    return {"id":row.id,"status":row.status,"escalated_to":row.escalated_to,"proposals":proposals,"resolution":row.resolution,"audit_log":row.audit_log}

@app.post("/api/decisions/resolve")
def decision(data:DecisionIn, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.query(Project).filter_by(id=data.project_id,owner_id=user.id).first()
    if not p: raise HTTPException(404,"Project not found")
    row=resolve_dispute(db,user.id,p.id,data.subject,data.proposals,data.critical)
    return {"id":row.id,"status":row.status,"escalated_to":row.escalated_to,"resolution":row.resolution,"audit_log":row.audit_log}

@app.post("/api/terminal/execute")
def terminal(data:TerminalIn,user:User=Depends(current_user)):
    try: return execute_remote(data.command,data.workspace_id)
    except Exception as exc: raise HTTPException(503,str(exc))

@app.get("/")
def frontend(): return FileResponse("/app/frontend/index.html")
@app.get("/{asset_path:path}")
def assets(asset_path:str):
    candidate=Path("/app/frontend")/asset_path
    if candidate.is_file() and candidate.resolve().is_relative_to(Path("/app/frontend").resolve()): return FileResponse(candidate)
    raise HTTPException(404,"Not found")
