import os, re, secrets, tempfile, shutil
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
import docker
app=FastAPI(title="Aether Isolated Sandbox")
TOKEN=os.environ.get("SANDBOX_API_TOKEN","")
IMAGE=os.environ.get("SANDBOX_IMAGE","aether-sandbox:latest")
WORK_ROOT=Path(os.environ.get("SANDBOX_WORK_ROOT","/tmp/aether-workspaces")); WORK_ROOT.mkdir(parents=True,exist_ok=True)
client=docker.from_env()
class ExecIn(BaseModel): workspace_id:str=Field(min_length=1,max_length=80); command:str=Field(min_length=1,max_length=4000)
@app.post('/execute')
def execute(data:ExecIn, authorization:str=Header(default="")):
    if not TOKEN or authorization != f"Bearer {TOKEN}": raise HTTPException(401,"Unauthorized")
    if not re.fullmatch(r'[A-Za-z0-9_-]+',data.workspace_id): raise HTTPException(400,"Invalid workspace id")
    path=(WORK_ROOT/data.workspace_id).resolve(); path.mkdir(parents=True,exist_ok=True)
    container=None
    try:
        os.chmod(path,0o777)
        container=client.containers.run(IMAGE,["sh","-lc",data.command],detach=True,working_dir="/workspace",volumes={str(path):{"bind":"/workspace","mode":"rw"}},network_disabled=False,mem_limit="1g",nano_cpus=1_000_000_000,pids_limit=128,read_only=True,tmpfs={"/tmp":"rw,nosuid,size=128m","/var/tmp":"rw,nosuid,size=64m"},cap_drop=["ALL"],security_opt=["no-new-privileges:true"],user="65534:65534",auto_remove=False)
        result=container.wait(timeout=60); logs=container.logs(stdout=True,stderr=True).decode(errors="replace")[-20000:]
        container.remove(force=True)
        return {"exit_code":result.get("StatusCode"),"output":logs}
    except Exception as exc:
        if container is not None:
            try: container.remove(force=True)
            except Exception: pass
        raise HTTPException(500,f"Sandbox execution failed: {type(exc).__name__}")
