from datetime import date,timedelta
import json,random
from .db import connect,init_db,DATA
from .settings import DEFAULT_SEED, DEFAULT_SCALE
from .export import export_tables
SEED=DEFAULT_SEED; BASE=date(2026,1,1)
NARRATIVES=["rear-ended at intersection","water damage from burst pipe","theft from locked vehicle","slip and fall at premises","hail damage to roof"]
def ident(prefix,n): return f"{prefix}-2026-{n:06d}"
def build(seed=SEED,scale=DEFAULT_SCALE,output=DATA):
    rng=random.Random(seed); nclt,nclaim,nprv,nedge={"full":(2000,5000,500,8000),"starter":(120,250,45,400)}[scale]; output.mkdir(exist_ok=True)
    db_file=output/"claimtrace.db"
    if db_file.exists(): db_file.unlink()
    conn=connect(db_file); init_db(conn); cur=conn.cursor()
    for i in range(1,nclt+1):
        household=f"HH-{(i-1)//3+1:05d}" if i%11 in (0,1) else f"HH-{i:05d}"
        phone="+1-555-010-0101" if i in (101,102,103,104,105) else f"+1-555-{i%1000:03d}-{(i*17)%10000:04d}"
        cur.execute("INSERT INTO claimants VALUES (?,?,?,?,?,?,?)",(f"CLT-2026-{i:06d}",f"Claimant {i:04d}",f"claimant{i}@example.test",phone,f"{100+i%700} Market Street, Metro",household,"2026-01-01T00:00:00"))
    providers=[]
    for i in range(1,nprv+1):
        pid=f"PRV-{i:06d}"; providers.append(pid); cur.execute("INSERT INTO providers VALUES (?,?,?,?,?)",(pid,f"Provider {i:04d}",rng.choice(["repairer","medical","assessor"]),f"{i%400+1} Service Road, Metro",f"+1-555-8{i%100:02d}-{i:04d}"))
    policies=[]
    for i in range(1,nclt+1):
        pid=f"POL-2026-{i:06d}"; policies.append(pid); start=BASE-timedelta(days=rng.randint(30,500)); cur.execute("INSERT INTO policies VALUES (?,?,?,?,?,?,?)",(pid,f"CLT-2026-{i:06d}",rng.choice(["AUTO","HOME","HEALTH"]),start.isoformat(),(start+timedelta(days=365)).isoformat(),"ACTIVE",round(rng.uniform(15000,100000),2)))
    ground=[]; meta=[]
    for i in range(1,nclaim+1):
        num=(i-1)%nclt+1; cid=f"CLT-2026-{num:06d}"; clid=ident("CLM",i); inc=ident("INC",i); day=BASE+timedelta(days=rng.randint(0,330)); day=BASE+timedelta(days=75) if i in (41,42,43,44,45) else day; narrative=NARRATIVES[(i+num)%len(NARRATIVES)]
        if i in (31,32,33,34,35): narrative="rear-ended at intersection near central junction"
        cur.execute("INSERT INTO incidents VALUES (?,?,?,?,?,?)",(inc,cid,day.isoformat(),rng.choice(["collision","water","theft","injury"]),narrative,rng.choice(["Metro North","Metro Central","Metro West"])))
        policy="POL-2026-999999" if i==12 else policies[num-1]; issue="missing_policy" if i==12 else ("payment_exceeds_approved" if i==8 else None); filed=day+timedelta(days=rng.randint(2,20)); approved=round(rng.uniform(150,18000),2)
        provider=providers[(i*7)%nprv] if i not in (31,32,33,34,35) else providers[3]; inv=f"INV-PRV-{provider}-{i:06d}"; group="DUP-GROUP-001" if i in (71,72) else None; amount=round(approved*rng.uniform(.35,.95),2); paid=approved+1250 if i==8 else amount
        status="REVIEW" if issue or group else "PAID"
        cur.execute("INSERT INTO claims VALUES (?,?,?,?,?,?,?,?)",(clid,cid,policy,inc,filed.isoformat(),approved,status,issue)); cur.execute("INSERT INTO claim_providers VALUES (?,?,?)",(clid,provider,"primary")); cur.execute("INSERT INTO invoices VALUES (?,?,?,?,?,?)",(inv,clid,provider,amount,(filed+timedelta(days=1)).isoformat(),group)); cur.execute("INSERT INTO payments VALUES (?,?,?,?,?,?)",(f"PAY-2026-{i:06d}",clid,inv,paid,(filed+timedelta(days=10)).isoformat(),"settled"))
        for issue_name in (["payment_exceeds_approved"] if i==8 else [])+(["duplicate_invoice"] if i in (71,72) else [])+(["missing_policy"] if i==12 else [])+(["repeated_narrative_provider_cluster"] if i in (31,32,33,34,35) else [])+(["unusual_timing"] if i in (41,42,43,44,45) else [])+(["shared_contact_cluster"] if i in (101,102,103,104,105) else []): ground.append(("claim",clid,issue_name,"suspicious"))
        meta.append((clid,cid,day,provider))
    for i in range(1,nedge+1):
        src=meta[(i*13)%len(meta)][1]; tgt=meta[(i*29+3)%len(meta)][1]
        cur.execute("INSERT INTO relationship_edges VALUES (?,?,?,?,?,?,?,?)",(f"RE-2026-{i:06d}",src,"claimant",tgt,"claimant",rng.choice(["shared_contact","household","prior_claim"]),"2026-01-01",0))
    ground.extend([("relationship","CLT-2026-000101|CLT-2026-000102","missing_relationship_edge","suspicious"),("claimant","CLT-2026-000001","benign_common_address","benign"),("claimant","CLT-2026-000701","benign_common_address","benign")])
    conn.commit(); export_tables(conn,output/"exports"); (output/"ground_truth.csv").write_text("truth_id,entity_type,entity_id,issue_type,expected_label\n"+"\n".join(f"GT-{i:06d},{a},{b},{c},{d}" for i,(a,b,c,d) in enumerate(ground,1))+"\n"); (output/"manifest.json").write_text(json.dumps({"seed":seed,"scale":scale,"counts":{"claimants":nclt,"claims":nclaim,"providers":nprv,"relationship_edges":nedge},"provenance":{"source":"synthetic","external_data":False},"exports":"exports/"},indent=2)); return {"claimants":nclt,"claims":nclaim,"providers":nprv,"relationship_edges":nedge}
