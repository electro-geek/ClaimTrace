import csv, json
from pathlib import Path
from .db import TABLES

def export_tables(conn, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    manifest={"format":"synthetic","tables":{}}
    sql_lines=["PRAGMA foreign_keys = ON;",""]
    def sql_value(value):
        if value is None: return "NULL"
        if isinstance(value,(int,float)): return str(value)
        return "'"+str(value).replace("'","''")+"'"
    for table in TABLES:
        rows=[dict(row) for row in conn.execute(f"SELECT * FROM {table}")]
        fields=[d["name"] for d in conn.execute(f"PRAGMA table_info({table})")]
        csv_path=output/f"{table}.csv"; json_path=output/f"{table}.json"
        with csv_path.open("w",newline="") as fh:
            writer=csv.DictWriter(fh,fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        json_path.write_text(json.dumps(rows,indent=2,default=str))
        for row in rows:
            values=", ".join(sql_value(row[field]) for field in fields)
            sql_lines.append(f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({values});")
        manifest["tables"][table]={"rows":len(rows),"csv":csv_path.name,"json":json_path.name}
    (output/"seed.sql").write_text("\n".join(sql_lines)+"\n")
    manifest["sql_seed"]="seed.sql"
    (output/"source_manifest.json").write_text(json.dumps(manifest,indent=2))
    return manifest
