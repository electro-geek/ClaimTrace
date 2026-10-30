import csv,os
from collections import defaultdict
from .db import connect
from .settings import GROUND_TRUTH_PATH

def evaluate(db_path=None,truth_path=GROUND_TRUTH_PATH):
    c=connect(db_path) if db_path else connect(); truths=list(csv.DictReader(open(truth_path))) if os.path.exists(truth_path) else []
    claim_truth=[x for x in truths if x["entity_type"]=="claim"]; expected={x["entity_id"] for x in claim_truth}; predicted={x["claim_id"] for x in c.execute("SELECT claim_id FROM investigations")}; tp=len(expected&predicted)
    by_issue=defaultdict(set)
    for row in claim_truth: by_issue[row["issue_type"]].add(row["entity_id"])
    per_issue={}
    for issue,ids in by_issue.items():
        aliases={"repeated_narrative_provider_cluster":"repeated_narrative","payment_exceeds_approved":"payment_over_approved"}; indicator=aliases.get(issue,issue)
        found={r["claim_id"] for r in c.execute("SELECT DISTINCT claim_id FROM fraud_indicators WHERE indicator_type=?",(indicator,))}
        per_issue[issue]={"truth":len(ids),"detected":len(ids&found),"recall":round(len(ids&found)/len(ids),3) if ids else 0}
    ranked=[r["claim_id"] for r in c.execute("SELECT claim_id FROM investigations ORDER BY risk_score DESC, claim_id")]; precision=tp/len(predicted) if predicted else 0; recall=tp/len(expected) if expected else 0
    top_k={}
    for k in (10,100):
        top=set(ranked[:k]); top_k[f"precision_at_{k}"]=round(len(top&expected)/len(top),3) if top else 0; top_k[f"recall_at_{k}"]=round(len(top&expected)/len(expected),3) if expected else 0
    network_truth=sum(1 for x in truths if x["entity_type"]=="relationship"); network_evidence=c.execute("SELECT COUNT(*) FROM fraud_indicators WHERE indicator_type='missing_relationship_edge'").fetchone()[0]
    return {"truth_count":len(expected),"predicted_count":len(predicted),"true_positives":tp,"precision":round(precision,3),"recall":round(recall,3),"false_negative_rate":round(1-recall,3),"false_positive_rate":round(1-precision,3),"top_k":top_k,"per_issue":per_issue,"relationship_truth_count":network_truth,"relationship_evidence_claims":network_evidence}
