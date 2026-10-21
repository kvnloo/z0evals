import sqlite3,json,os
db=sqlite3.connect(f"file:{os.path.expanduser('~/.local/state/workspace-copilot/workspace.db')}?mode=ro",uri=True)
mru=[]; n=t1=t3=e1=e3=0
for st,fam,tgt,ranked in db.execute("select state_json,actual_family,actual_target,ranked from shadow_predictions order by ts"):
    app=json.loads(st).get("app","")
    if app:
        if app in mru: mru.remove(app)
        mru.insert(0,app)
    if fam=="switch_app" and tgt:
        cand=[a for a in mru if a!=app][:3]
        n+=1; t1+= bool(cand) and cand[0]==tgt; t3+= tgt in cand
        e1+= ranked==1; e3+= ranked is not None and 1<=ranked<=3
print(json.dumps({"subset":"actual_family=switch_app","n":n,"mru_top1":round(t1/n,3),"mru_top3":round(t3/n,3),"engine_top1":round(e1/n,3),"engine_top3":round(e3/n,3)}))
