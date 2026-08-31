# -*- coding: utf-8 -*-
import io
import json

d = json.load(io.open("etat/presence.json", encoding="utf-8"))
r = d["resolu"]
meta = dict((k, v) for k, v in r.items() if k != "gens")
print("meta ::", json.dumps(meta, ensure_ascii=False)[:600])
print("nesse ::", json.dumps(r["gens"].get("nesse"), ensure_ascii=False))
print("tobb  ::", json.dumps(r["gens"].get("tobb"), ensure_ascii=False))
p = d.get("presence")
print("presence keys ::", json.dumps(p, ensure_ascii=False)[:600])
