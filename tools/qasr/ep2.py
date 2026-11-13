import json,sys
words=[w for s in json.load(open("ep2/words.json")) for w in s["words"]]
SEG=[(7.20,12.55),(15.25,17.10),(17.15,21.95),(22.90,29.95),(43.10,46.30),(53.00,54.90),(61.10,67.75),(68.28,69.30),(69.40,74.70),
(105.45,108.10),(84.85,86.95),(87.85,90.25),(92.65,95.25),(95.90,97.10),(98.60,100.85),(101.25,103.50),(109.50,116.25),
(127.35,131.85),(134.05,136.75),(139.60,141.25),(141.55,144.90),(145.35,146.95),(148.15,153.80),(160.25,163.50),(163.85,165.75),
(169.80,172.80),(172.78,174.45),(175.20,178.00)]
FIX={"אורחות":"לוחות","הערימו":"הרימו","נער":"נהר","רגל.":"רגיל.","מכינו":"הקימו","מצאו":"עשו","בי":"בים","ים":"","-12":"12","מ":"מ־","ה":"ה־","תנ״ך.":"תנ״ך."}
HL=["מעברות הירדן","ארון הברית","לוחות הברית","יהושע","מעברות","הירדן","הירדן,","לירדן,","לשתיים","ארון","הברית","לוחות","לשניים","12","אבנים","אבנים.","אבן.","סלעים","גלגל","מזבח","הנס","סוף","נהר","רגיל","הכוהנים","כשהכוהנים","תנ״ך","מהנהר"]
Y="{\\c&H0000E5FF&}"; W="{\\c&H00FFFFFF&}"
t=0; items=[]
for a,b in SEG:
    seg=[]
    for w in words:
        if w["s"]>=a-0.05 and w["e"]<=b+0.15:
            txt=w["w"].strip().lstrip("‫-")
            if not txt: continue
            if txt in FIX: txt=FIX[txt]
            if not txt: continue
            seg.append([txt,w["s"]-a+t,min(w["e"],b)-a+t])
    # merge prefix tokens like מ־ / ה־ with next
    m=[]
    for x in seg:
        if m and (m[-1][0].endswith("־") or m[-1][0] in ("מעברות","ארון","לוחות")): m[-1]=[m[-1][0]+("" if m[-1][0].endswith("־") else " ")+x[0],m[-1][1],x[2]]
        else: m.append(x)
    items.append(m); t+=b-a
TOTAL=t
caps=[]
for m in items:
    cur=[]
    for i,x in enumerate(m):
        cur.append(x)
        txt=" ".join(c[0] for c in cur)
        nxt=m[i+1] if i+1<len(m) else None
        brk = nxt is None or x[0][-1] in ",.?!" or len(txt)>=13 or len(cur)>=3 or (nxt and nxt[1]-x[2]>0.35)
        if brk:
            caps.append([cur[0][1],x[2],cur]); cur=[]
# extend ends to next start (max +0.5)
for i,c in enumerate(caps):
    nx=caps[i+1][0] if i+1<len(caps) else TOTAL
    c[1]=min(max(c[1],c[0]+0.35),nx,c[1]+0.5) if nx>c[0] else c[1]
def fmt(cur):
    out=[]
    for c in cur:
        core=c[0].strip(",.?!…")
        out.append(Y+c[0]+W if core in [h.strip(",.") for h in HL] else c[0])
    return " ".join(out)
json.dump({"segs":SEG,"total":TOTAL,"caps":[[c[0],c[1],fmt(c[2])] for c in caps]},open("ep2/edit.json","w"),ensure_ascii=False,indent=0)
print("total",round(TOTAL,2),"caps",len(caps))
for c in caps: print(f"{c[0]:6.2f}-{c[1]:6.2f} "+" ".join(x[0] for x in c[2]))
