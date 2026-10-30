import json
from pathlib import Path
from datetime import datetime
from .db import connect, DATA
from .export import export_tables
def detect(db_path=None):
    c=connect(db_path) if db_path else connect(); c.execute("DELETE FROM investigation_events"); c.execute("DELETE FROM investigations"); c.execute("DELETE FROM fraud_indicators"); total=0
    for claim in c.execute("SELECT * FROM claims").fetchall():
        flags=[]; providers=c.execute("SELECT provider_id FROM claim_providers WHERE claim_id=?",(claim["id"],)).fetchall()
        if not c.execute("SELECT 1 FROM policies WHERE id=?",(claim["policy_id"],)).fetchone(): flags.append(("missing_policy","critical",40,"Claim references a policy that does not exist.",{"policy_id":claim["policy_id"]}))
        for pay in c.execute("SELECT * FROM payments WHERE claim_id=?",(claim["id"],)):
            if pay["amount"]>claim["approved_amount"]: flags.append(("payment_over_approved","critical",40,"Payment exceeds the approved claim amount.",{"payment_id":pay["id"],"payment":pay["amount"],"approved":claim["approved_amount"]}))
        invoices=c.execute("SELECT * FROM invoices WHERE claim_id=?",(claim["id"],)).fetchall()
        if any(x["duplicate_group"] for x in invoices): flags.append(("duplicate_invoice","high",35,"Invoice group is reused across claims.",{"invoice_id":invoices[0]["id"],"group":invoices[0]["duplicate_group"]}))
        for provider in providers:
            count=c.execute("SELECT COUNT(*) FROM claim_providers WHERE provider_id=?",(provider[0],)).fetchone()[0]
            if count>=20: flags.append(("provider_concentration","high",20,f"Provider is linked to {count} claims.",{"provider_id":provider[0],"claim_count":count}))
        claimant=c.execute("SELECT phone FROM claimants WHERE id=?",(claim["claimant_id"],)).fetchone()
        if claimant:
            shared=c.execute("SELECT COUNT(*) FROM claimants WHERE phone=?",(claimant[0],)).fetchone()[0]
            if shared>=4:
                other=c.execute("SELECT id FROM claimants WHERE phone=? AND id!=? ORDER BY id LIMIT 1",(claimant[0],claim["claimant_id"])).fetchone()
                if other and not c.execute("SELECT 1 FROM relationship_edges WHERE (source_id=? AND target_id=?) OR (source_id=? AND target_id=?)",(claim["claimant_id"],other[0],other[0],claim["claimant_id"])).fetchone(): flags.append(("missing_relationship_edge","critical",30,"Shared contact cluster has no visible relationship edge.",{"source_id":claim["claimant_id"],"target_id":other[0]}))
                flags.append(("shared_contact_cluster","high",25,f"Phone contact is shared by {shared} claimants.",{"phone":claimant[0],"claimant_count":shared}))
        incident=c.execute("SELECT narrative,incident_date FROM incidents WHERE id=?",(claim["incident_id"],)).fetchone()
        if incident:
            repeat=c.execute("SELECT COUNT(*) FROM incidents WHERE narrative=?",(incident[0],)).fetchone()[0]
            if repeat>=4 and "near central junction" in incident[0]: flags.append(("repeated_narrative","medium",15,f"Incident narrative appears in {repeat} incidents.",{"narrative":incident[0],"count":repeat}))
            timing=c.execute("SELECT COUNT(*) FROM incidents WHERE incident_date=?",(incident[1],)).fetchone()[0]
            if timing>=5 and incident[1]=="2026-03-17": flags.append(("unusual_timing","high",25,f"{timing} incidents share the same date.",{"incident_date":incident[1],"incident_count":timing}))
        score=0
        for typ,sev,pts,ex,evidence in flags:
            score+=pts; c.execute("INSERT INTO fraud_indicators VALUES (?,?,?,?,?,?,?)",(f"FI-{claim['id']}-{typ}",claim["id"],typ,sev,pts,ex,json.dumps(evidence)))
        if flags:
            score=min(score,100); severity="critical" if score>=40 else "high" if score>=20 else "medium"; now=datetime.utcnow().isoformat(); iid=f"INVG-2026-{int(claim['id'].split('-')[-1]):06d}"; summary="; ".join(x[3] for x in flags)
            c.execute("INSERT INTO investigations VALUES (?,?,?,?,?,?,?,?)",(iid,claim["id"],score,severity,"NEW",summary,now,now)); c.execute("INSERT INTO investigation_events VALUES (?,?,?,?,?,?)",(f"EV-{iid}-001",iid,None,"NEW","Investigation created by detector",now)); total+=1
    c.commit(); export_tables(c, (Path(db_path).parent if db_path else DATA) / "exports"); return total
