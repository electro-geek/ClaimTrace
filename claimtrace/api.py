from datetime import datetime
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from .db import connect
from .validation import validate
from .evaluation import evaluate
from .settings import CORS_ORIGINS
app=FastAPI(title="ClaimTrace API",version="0.1.0")
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_methods=["*"],allow_headers=["*"])
class Update(BaseModel): status:str; note:str=""
@app.get("/api/metrics")
def metrics():
    c=connect(); return {"claims":c.execute("SELECT COUNT(*) FROM claims").fetchone()[0],"claimants":c.execute("SELECT COUNT(*) FROM claimants").fetchone()[0],"providers":c.execute("SELECT COUNT(*) FROM providers").fetchone()[0],"investigations":c.execute("SELECT COUNT(*) FROM investigations").fetchone()[0],"critical":c.execute("SELECT COUNT(*) FROM investigations WHERE severity='critical'").fetchone()[0],"open":c.execute("SELECT COUNT(*) FROM investigations WHERE status NOT IN ('CLEARED','CONFIRMED')").fetchone()[0]}
@app.get("/api/validation")
def validation(): return validate()
@app.get("/api/evaluation")
def evaluation(): return evaluate()
@app.get("/api/investigations")
def investigations(status:str|None=None):
    c=connect(); q="SELECT * FROM investigations"; args=()
    if status: q+=" WHERE status=?"; args=(status,)
    return [dict(r) for r in c.execute(q+" ORDER BY risk_score DESC, updated_at DESC",args)]
@app.get("/api/investigations/{iid}")
def investigation(iid:str):
    c=connect(); row=c.execute("SELECT * FROM investigations WHERE id=?",(iid,)).fetchone()
    if not row: raise HTTPException(404,"Investigation not found")
    result=dict(row); result["indicators"]=[dict(r) for r in c.execute("SELECT * FROM fraud_indicators WHERE claim_id=? ORDER BY score DESC",(row["claim_id"],))]; result["claim"]=dict(c.execute("SELECT * FROM claims WHERE id=?",(row["claim_id"],)).fetchone()); result["events"]=[dict(r) for r in c.execute("SELECT * FROM investigation_events WHERE investigation_id=? ORDER BY created_at",(iid,))]; return result
@app.get("/api/investigations/{iid}/events")
def investigation_events(iid:str):
    c=connect(); return [dict(r) for r in c.execute("SELECT * FROM investigation_events WHERE investigation_id=? ORDER BY created_at",(iid,))]
@app.get("/api/entities/{entity_type}/{entity_id}")
def entity(entity_type:str,entity_id:str):
    tables={"claimant":"claimants","policy":"policies","claim":"claims","incident":"incidents","provider":"providers","invoice":"invoices","payment":"payments"}; table=tables.get(entity_type)
    if not table: raise HTTPException(400,"Unsupported entity type")
    c=connect(); row=c.execute(f"SELECT * FROM {table} WHERE id=?",(entity_id,)).fetchone()
    if not row: raise HTTPException(404,"Entity not found")
    return dict(row)
@app.get("/api/entities/{entity_type}/{entity_id}/network")
def entity_network(entity_type:str,entity_id:str):
    c=connect(); edges=[dict(r) for r in c.execute("SELECT * FROM relationship_edges WHERE (source_id=? AND source_type=?) OR (target_id=? AND target_type=?)",(entity_id,entity_type,entity_id,entity_type))]
    claims=[]
    if entity_type=="claimant": claims=[dict(r) for r in c.execute("SELECT * FROM claims WHERE claimant_id=?",(entity_id,))]
    if entity_type=="provider": claims=[dict(r) for r in c.execute("SELECT c.* FROM claims c JOIN claim_providers cp ON cp.claim_id=c.id WHERE cp.provider_id=?",(entity_id,))]
    return {"entity_id":entity_id,"entity_type":entity_type,"edges":edges,"claims":claims}
@app.patch("/api/investigations/{iid}")
def update(iid:str,payload:Update):
    c=connect(); row=c.execute("SELECT * FROM investigations WHERE id=?",(iid,)).fetchone()
    if not row: raise HTTPException(404,"Investigation not found")
    allowed={"NEW":{"REVIEWING"},"REVIEWING":{"ESCALATED","CLEARED"},"ESCALATED":{"CONFIRMED","CLEARED"},"CLEARED":set(),"CONFIRMED":set()}
    if payload.status!=row["status"] and payload.status not in allowed[row["status"]]: raise HTTPException(400,"Invalid lifecycle transition")
    now=datetime.utcnow().isoformat(); c.execute("UPDATE investigations SET status=?,updated_at=? WHERE id=?",(payload.status,now,iid)); c.execute("INSERT INTO investigation_events VALUES (?,?,?,?,?,?)",(f"EV-{iid}-{now}",iid,row["status"],payload.status,payload.note,now)); c.commit(); return dict(c.execute("SELECT * FROM investigations WHERE id=?",(iid,)).fetchone())
