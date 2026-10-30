import argparse,json
from pathlib import Path
from .generator import build
from .validation import validate
from .detection import detect
from .evaluation import evaluate
from .settings import DEFAULT_SEED, DEFAULT_SCALE, DATA_DIR
def main():
    p=argparse.ArgumentParser(prog="claimtrace"); s=p.add_subparsers(dest="cmd",required=True); g=s.add_parser("generate"); g.add_argument("--seed",type=int,default=DEFAULT_SEED); g.add_argument("--scale",choices=["starter","full"],default=DEFAULT_SCALE); s.add_parser("validate"); s.add_parser("detect"); s.add_parser("evaluate"); a=p.parse_args()
    if a.cmd=="generate": result=build(a.seed,a.scale)
    elif a.cmd=="validate":
        result=validate(); Path(DATA_DIR/"validation_summary.json").write_text(json.dumps(result,indent=2))
    elif a.cmd=="detect": result={"investigations":detect()}
    else: result=evaluate()
    print(json.dumps(result,indent=2))
