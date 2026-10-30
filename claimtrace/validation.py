from .db import connect

def _check(name, passed, detail): return {"name":name,"passed":bool(passed),"detail":detail}

def validate(db_path=None):
    c=connect(db_path) if db_path else connect(); out=[]
    for table in ["claimants","policies","claims","incidents","providers","claim_providers","invoices","payments","relationship_edges"]:
        n=c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]; out.append(_check(f"{table}_nonempty",n>0,f"{n} rows"))
    for table in ["claimants","policies","claims","incidents","providers","invoices","payments","relationship_edges"]:
        dup=c.execute(f"SELECT COUNT(*) FROM (SELECT id FROM {table} GROUP BY id HAVING COUNT(*)>1)").fetchone()[0]; out.append(_check(f"{table}_primary_keys",dup==0,f"{dup} duplicate IDs"))
    out.append(_check("primary_key_uniqueness",all((x["passed"] for x in out if x["name"].endswith("_primary_keys"))),"all entity primary keys are unique"))
    fk_queries={
      "policy_claimant":("SELECT COUNT(*) FROM policies x LEFT JOIN claimants p ON p.id=x.claimant_id WHERE p.id IS NULL",),
      "claim_claimant":("SELECT COUNT(*) FROM claims x LEFT JOIN claimants p ON p.id=x.claimant_id WHERE p.id IS NULL",),
      "claim_incident":("SELECT COUNT(*) FROM claims x LEFT JOIN incidents p ON p.id=x.incident_id WHERE p.id IS NULL",),
      "provider_claim":("SELECT COUNT(*) FROM claim_providers x LEFT JOIN claims p ON p.id=x.claim_id WHERE p.id IS NULL",),
      "provider_reference":("SELECT COUNT(*) FROM claim_providers x LEFT JOIN providers p ON p.id=x.provider_id WHERE p.id IS NULL",),
      "invoice_claim":("SELECT COUNT(*) FROM invoices x LEFT JOIN claims p ON p.id=x.claim_id WHERE p.id IS NULL",),
      "invoice_provider":("SELECT COUNT(*) FROM invoices x LEFT JOIN providers p ON p.id=x.provider_id WHERE p.id IS NULL",),
      "payment_invoice":("SELECT COUNT(*) FROM payments x LEFT JOIN invoices p ON p.id=x.invoice_id WHERE p.id IS NULL",),
      "payment_claim":("SELECT COUNT(*) FROM payments x LEFT JOIN claims p ON p.id=x.claim_id WHERE p.id IS NULL",),
    }
    for name,(sql,) in fk_queries.items():
        n=c.execute(sql).fetchone()[0]; out.append(_check(f"foreign_key_{name}",n==0,f"{n} orphan rows"))
    missing=c.execute("SELECT COUNT(*) FROM claims x LEFT JOIN policies p ON p.id=x.policy_id WHERE p.id IS NULL").fetchone()[0]; out.append(_check("expected_missing_policy_exception",missing==1,f"{missing} labelled missing-policy claim"))
    enums=[("policy_type", "policies", "policy_type", "('AUTO','HOME','HEALTH')"),("claim_status","claims","status","('PAID','REVIEW')"),("provider_type","providers","provider_type","('repairer','medical','assessor')"),("payment_status","payments","status","('settled')")]
    for name,table,col,allowed in enums:
        n=c.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} NOT IN {allowed}").fetchone()[0]; out.append(_check(f"enum_{name}",n==0,f"{n} invalid values"))
    date_bad=c.execute("SELECT COUNT(*) FROM claims x JOIN incidents i ON i.id=x.incident_id WHERE x.filed_date<i.incident_date").fetchone()[0]; out.append(_check("date_ordering",date_bad==0,f"{date_bad} claims filed before incident"))
    amounts=c.execute("SELECT COUNT(*) FROM invoices WHERE amount<0 UNION ALL SELECT COUNT(*) FROM payments WHERE amount<0").fetchall(); bad=sum(x[0] for x in amounts); out.append(_check("non_negative_amounts",bad==0,f"{bad} invalid amounts"))
    reconcile=c.execute("SELECT COUNT(*) FROM payments p JOIN invoices i ON i.id=p.invoice_id WHERE p.amount!=i.amount AND p.amount<=(SELECT approved_amount FROM claims WHERE id=p.claim_id)").fetchone()[0]; out.append(_check("payment_invoice_reconciliation",reconcile==0,f"{reconcile} unexplained payment differences"))
    dup_groups=c.execute("SELECT COUNT(*) FROM (SELECT duplicate_group FROM invoices WHERE duplicate_group IS NOT NULL GROUP BY duplicate_group HAVING COUNT(*)>1)").fetchone()[0]; out.append(_check("duplicate_invoice_groups_labelled",dup_groups>=1,f"{dup_groups} duplicate groups"))
    valid_states={"NEW":{"REVIEWING"},"REVIEWING":{"ESCALATED","CLEARED"},"ESCALATED":{"CONFIRMED","CLEARED"},"CLEARED":set(),"CONFIRMED":set()}; invalid=0
    for row in c.execute("SELECT investigation_id,from_status,to_status FROM investigation_events WHERE from_status IS NOT NULL"):
        if row["to_status"] not in valid_states.get(row["from_status"],set()): invalid+=1
    out.append(_check("lifecycle_transitions",invalid==0,f"{invalid} invalid transitions"))
    return out
