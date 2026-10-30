"""VeriScholar prototype backend. Run: uvicorn app:app --reload"""
import csv, io, json, hashlib, secrets, sqlite3, time, base64, random, os, threading, re
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from nacl.signing import SigningKey
from rapidfuzz import fuzz
import qrcode

DB, KEYF = "verischolar.db", "signing.key"
# Rules live here (edit without touching logic). demo_checkdigit is a DEMO rule, NOT the official APAAR spec.
RULES = {"supernumerary_cap_pct": 5, "nri_cap_pct": 15, "fuzzy_threshold": 88, "demo_checkdigit": True}
SK = SigningKey(open(KEYF, "rb").read()) if os.path.exists(KEYF) else SigningKey.generate()
if not os.path.exists(KEYF): open(KEYF, "wb").write(bytes(SK))

USERS = {"aicte": ("aicte123", "aicte", None), "reviewer": ("rev123", "reviewer", None), "verifier": ("ver123", "verifier", None)}
USERS.update({f"inst{i}": ("inst123", "institution", f"I{i}") for i in range(1, 6)})
TOKENS = {}
C = sqlite3.connect(DB, check_same_thread=False); LOCK = threading.Lock()

def q(sql, *a, one=False):
    with LOCK:
        cur = C.execute(sql, a); cols = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(zip(cols, r)) for r in cur.fetchall()] if cols else []; C.commit()
    return (rows[0] if rows else None) if one else rows

def init():
    for s in ["CREATE TABLE IF NOT EXISTS inst(id TEXT PRIMARY KEY,name,state)",
              "CREATE TABLE IF NOT EXISTS intake(inst,programme,intake INT,PRIMARY KEY(inst,programme))",
              "CREATE TABLE IF NOT EXISTS students(apaar,inst,name,dob,gender,programme,category,nri INT,oci INT,fn INT,sn INT,adm,consent INT,version INT,status,PRIMARY KEY(apaar,inst))",
              "CREATE TABLE IF NOT EXISTS flags(id INTEGER PRIMARY KEY AUTOINCREMENT,apaar,inst,kind,sev,reason,status DEFAULT 'open',note)",
              "CREATE TABLE IF NOT EXISTS hist(apaar,inst,version,data,ts)",
              "CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,ts,actor,action,detail,prev,h)",
              "CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,email,full_name,pw,salt,role,inst,created)",
              "CREATE TABLE IF NOT EXISTS revoked(jti PRIMARY KEY)", "CREATE TABLE IF NOT EXISTS issued(jti PRIMARY KEY,apaar,inst,rh)"]: q(s)

def sha(*p): return hashlib.sha256("|".join(map(str, p)).encode()).hexdigest()
def log(actor, action, detail=""):
    last = q("SELECT h FROM audit ORDER BY id DESC LIMIT 1", one=True); prev = last["h"] if last else "GENESIS"
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    q("INSERT INTO audit(ts,actor,action,detail,prev,h) VALUES(?,?,?,?,?,?)", ts, actor, action, detail, prev, sha(prev, ts, actor, action, detail))

# ---------- validation ----------
def luhn(s):
    t = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2: d = d * 2 - 9 if d > 4 else d * 2
        t += d
    return t % 10 == 0
def registry_lookup(a): return not a.startswith("0000")  # MOCK of ABC/APAAR registry
REQ = ["apaar_id", "name", "dob", "gender", "programme", "category", "admission_date", "consent"]
def validate(r):
    e = [f"missing {k}" for k in REQ if not (r.get(k) or "").strip()]
    a = (r.get("apaar_id") or "").strip()
    if a:
        if not (a.isdigit() and len(a) == 12): e.append("APAAR ID must be exactly 12 digits")
        elif RULES["demo_checkdigit"] and not luhn(a): e.append("check digit invalid (demo rule)")
        elif not registry_lookup(a): e.append("not found in ABC registry (MOCK)")
    for k in ("dob", "admission_date"):
        v = (r.get(k) or "").strip()
        if v and not (len(v) == 10 and v[4] == "-" and v[7] == "-"): e.append(f"{k} must be YYYY-MM-DD")
    return e

def upsert(inst, r):
    b = lambda k: 1 if (r.get(k) or "").strip().lower() in ("1", "yes", "y", "true") else 0
    a = r["apaar_id"].strip()
    v = (q("SELECT version FROM students WHERE apaar=? AND inst=?", a, inst, one=True) or {"version": 0})["version"] + 1
    d = (a, inst, r["name"].strip(), r["dob"].strip(), r["gender"].strip(), r["programme"].strip(), r["category"].strip(),
         b("nri"), b("oci"), b("fn"), b("supernumerary"), r["admission_date"].strip(), b("consent"), v, "active")
    q("INSERT OR REPLACE INTO students VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", *d)
    q("INSERT INTO hist VALUES(?,?,?,?,?)", a, inst, v, json.dumps(d), time.strftime("%F %T"))

# ---------- detection engine: every flag carries a reason ----------
def detect(inst):
    q("DELETE FROM flags WHERE inst=? AND status='open'", inst)
    done = {(f["apaar"], f["kind"]) for f in q("SELECT apaar,kind FROM flags WHERE inst=?", inst)}
    def add(a, k, s, r):
        if (a, k) not in done: q("INSERT INTO flags(apaar,inst,kind,sev,reason) VALUES(?,?,?,?,?)", a, inst, k, s, r); done.add((a, k))
    S = q("SELECT * FROM students WHERE inst=? AND status='active'", inst)
    for s in S:
        for o in q("SELECT * FROM students WHERE apaar=? AND inst<>? AND status='active'", s["apaar"], inst):
            add(s["apaar"], "CROSS_DUP", "high", f"Same APAAR ID also enrolled at {o['inst']} ({o['programme']})")
        if s["fn"] and (s["oci"] or s["nri"]):
            add(s["apaar"], "INCONSISTENT", "medium", "Foreign National cannot also be flagged NRI/OCI")
        for o in q("SELECT * FROM students WHERE dob=? AND apaar<>?", s["dob"], s["apaar"]):
            sc = fuzz.token_sort_ratio(s["name"].lower(), o["name"].lower())
            if sc >= RULES["fuzzy_threshold"]:
                add(s["apaar"], "FUZZY_DUP", "medium", f"Name+DOB {sc:.0f}% match with '{o['name']}' ({o['apaar']}) at {o['inst']}: needs human review")
    for it in q("SELECT * FROM intake WHERE inst=?", inst):
        p, n = it["programme"], it["intake"]; P = [s for s in S if s["programme"] == p]; key = "PROGRAMME:" + p
        reg, sn, nri = sum(not s["sn"] for s in P), sum(s["sn"] for s in P), sum(s["nri"] for s in P)
        scap, ncap = int(n * RULES["supernumerary_cap_pct"] / 100), int(n * RULES["nri_cap_pct"] / 100)
        if reg > n: add(key, "OVER_INTAKE", "high", f"{p}: enrolled {reg} vs approved intake {n} (+{(reg-n)*100/n:.1f}%); {reg-n} excess seats not explained by supernumerary")
        if sn > scap: add(key, "SUPERNUMERARY", "medium", f"{p}: {sn} supernumerary seats exceed cap of {scap} ({RULES['supernumerary_cap_pct']}% of intake)")
        if nri > ncap: add(key, "NRI_CAP", "medium", f"{p}: {nri} NRI admissions exceed cap of {ncap} ({RULES['nri_cap_pct']}% of intake)")

def risk(inst):
    pen, c = {"high": 15, "medium": 8, "low": 3}, {}
    for f in q("SELECT kind,sev FROM flags WHERE inst=? AND status IN ('open','flagged')", inst): c[f["kind"]] = c.get(f["kind"], 0) + pen[f["sev"]]
    return max(0, 100 - sum(c.values())), c

# ---------- api ----------
app = FastAPI(title="VeriScholar API", version="1")
def user(authorization: str = Header("")):
    u = TOKENS.get(authorization)
    if not u: raise HTTPException(401, "Please log in")
    return u
def need(u, *r):
    if u["role"] not in r: raise HTTPException(403, "Not allowed for your role")

class Login(BaseModel): username: str; password: str
class Rev(BaseModel): outcome: str; note: str = ""
class Tok(BaseModel): token: str
class Jti(BaseModel): jti: str

def hpw(p, salt): return hashlib.pbkdf2_hmac("sha256", p.encode(), bytes.fromhex(salt), 200_000).hex()
def session(name, role, inst):
    t = secrets.token_hex(16); TOKENS[t] = {"name": name, "role": role, "inst": inst}; log(name, "LOGIN")
    return {"token": t, **TOKENS[t]}

@app.post("/api/v1/login")
def login(b: Login):
    name = b.username.strip().lower(); r = q("SELECT * FROM users WHERE username=?", name, one=True)
    if r:
        if not secrets.compare_digest(hpw(b.password, r["salt"]), r["pw"]): raise HTTPException(401, "Wrong username or password")
        return session(r["username"], r["role"], r["inst"])
    u = USERS.get(name)
    if not u or u[0] != b.password: raise HTTPException(401, "Wrong username or password")
    return session(name, u[1], u[2])

class Reg(BaseModel): full_name: str; username: str; email: str; password: str; role: str = "institution"; inst: str = ""

@app.get("/api/v1/institutions")
def institutions(): return q("SELECT id,name,state FROM inst ORDER BY name")

@app.post("/api/v1/register")
def register(b: Reg):
    name, mail, full = b.username.strip().lower(), b.email.strip().lower(), " ".join(b.full_name.split())
    if len(full) < 2: raise HTTPException(400, "Please enter your full name")
    if not re.fullmatch(r"[a-z0-9_]{3,30}", name): raise HTTPException(400, "Username must be 3 to 30 letters, numbers or underscores")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", mail): raise HTTPException(400, "Please enter a valid email address")
    if len(b.password) < 8 or not re.search(r"[A-Za-z]", b.password) or not re.search(r"\d", b.password): raise HTTPException(400, "Password needs at least 8 characters with a letter and a number")
    if b.role not in ("institution", "verifier"): raise HTTPException(400, "You can register as an institution or a verifier. AICTE and reviewer accounts are created by an administrator")
    inst = None
    if b.role == "institution":
        if not q("SELECT 1 FROM inst WHERE id=?", b.inst, one=True): raise HTTPException(400, "Please choose your institution")
        inst = b.inst
    if name in USERS or q("SELECT 1 FROM users WHERE username=?", name, one=True): raise HTTPException(409, "That username is already taken")
    if q("SELECT 1 FROM users WHERE email=?", mail, one=True): raise HTTPException(409, "An account with that email already exists")
    salt = secrets.token_hex(16)
    q("INSERT INTO users VALUES(?,?,?,?,?,?,?,?)", name, mail, full, hpw(b.password, salt), salt, b.role, inst, time.strftime("%F %T"))
    log(name, "REGISTER", f"{b.role}" + (f" at {inst}" if inst else ""))
    return session(name, b.role, inst)

HEAD = "apaar_id,name,dob,gender,programme,category,nri,oci,fn,supernumerary,admission_date,consent"
@app.get("/api/v1/template")
def template(): return Response(HEAD + "\n123456789012,Asha Rao,2006-04-12,F,CSE,General,no,no,no,no,2025-08-10,yes\n", media_type="text/csv")

@app.post("/api/v1/upload")
async def upload(f: UploadFile = File(...), u=Depends(user)):
    need(u, "institution"); inst = u["inst"]
    rows = list(csv.DictReader(io.StringIO((await f.read()).decode("utf-8-sig"))))
    errs, seen, ok = [], {}, 0
    for n, r in enumerate(rows, start=2):
        e = validate(r); a = (r.get("apaar_id") or "").strip()
        if a and a in seen: e.append(f"duplicate of row {seen[a]} in this file")
        elif a: seen[a] = n
        if e: errs.append({"row": n, "apaar": a, "errors": e}); continue
        upsert(inst, r); ok += 1
    detect(inst); log(u["name"], "UPLOAD", f"{inst}: {ok} accepted, {len(errs)} rejected")
    return {"accepted": ok, "rejected": len(errs), "errors": errs}

@app.get("/api/v1/dashboard")
def dash(u=Depends(user)):
    need(u, "institution", "aicte", "reviewer"); out = []
    for i in q("SELECT * FROM inst"):
        if u["inst"] and i["id"] != u["inst"]: continue
        progs = [{"programme": t["programme"], "intake": t["intake"], "enrolled": q("SELECT COUNT(*) n FROM students WHERE inst=? AND programme=? AND status='active'", i["id"], t["programme"], one=True)["n"]} for t in q("SELECT * FROM intake WHERE inst=?", i["id"])]
        sc, c = risk(i["id"])
        out.append({**i, "progs": progs, "score": sc, "contrib": c, "open": len(q("SELECT id FROM flags WHERE inst=? AND status IN ('open','flagged')", i["id"]))})
    return out

@app.get("/api/v1/flags")
def flags(u=Depends(user)):
    need(u, "institution", "aicte", "reviewer"); sql, a = "SELECT * FROM flags", []
    if u["inst"]: sql += " WHERE inst=?"; a = [u["inst"]]
    return q(sql + " ORDER BY CASE sev WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,id", *a)

@app.post("/api/v1/flags/{fid}/review")
def review(fid: int, b: Rev, u=Depends(user)):
    need(u, "reviewer", "aicte")
    if b.outcome not in ("verified", "flagged", "rejected"): raise HTTPException(400, "Outcome must be verified, flagged or rejected")
    q("UPDATE flags SET status=?,note=? WHERE id=?", b.outcome, b.note, fid); log(u["name"], "REVIEW", f"flag {fid} -> {b.outcome}")
    return {"ok": True}

@app.get("/api/v1/students")
def students(search: str = "", u=Depends(user)):
    need(u, "institution", "aicte", "reviewer")
    sql, a = "SELECT apaar,inst,name,programme,category,status,version,consent FROM students WHERE (name LIKE ? OR apaar LIKE ? OR inst LIKE ? OR programme LIKE ?)", [f"%{search.strip()}%"] * 4
    if u["inst"]: sql += " AND inst=?"; a.append(u["inst"])
    return q(sql + " LIMIT 100", *a)

@app.get("/api/v1/uploads")
def uploads(u=Depends(user)):
    need(u, "institution", "aicte"); sql, a = "SELECT ts,actor,detail FROM audit WHERE action='UPLOAD'", []
    if u["inst"]: sql += " AND detail LIKE ?"; a = [u["inst"] + ":%"]
    return q(sql + " ORDER BY id DESC LIMIT 100", *a)

@app.get("/api/v1/verifications")
def verifications(u=Depends(user)):
    need(u, "verifier", "aicte"); sql, a = "SELECT ts,actor,action,detail FROM audit WHERE action IN ('VERIFY_OK','VERIFY_FAIL')", []
    if u["role"] == "verifier": sql += " AND actor=?"; a = [u["name"]]
    return q(sql + " ORDER BY id DESC LIMIT 100", *a)

# ---------- signed records + verification ----------
def b64(b): return base64.urlsafe_b64encode(b).decode().rstrip("=")
def unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def rec_hash(s): return sha(s["apaar"], s["inst"], s["name"], s["dob"], s["programme"], s["status"])

@app.post("/api/v1/records/{apaar}/{inst}/issue")
def issue(apaar: str, inst: str, u=Depends(user)):
    need(u, "institution", "aicte")
    if u["inst"] and u["inst"] != inst: raise HTTPException(403, "Other institution's student")
    s = q("SELECT * FROM students WHERE apaar=? AND inst=?", apaar, inst, one=True)
    if not s: raise HTTPException(404, "Student not found")
    p = {"jti": secrets.token_hex(6), "apaar": apaar, "inst": inst, "exp": int(time.time()) + 365 * 86400, "rh": rec_hash(s)}
    body = b64(json.dumps(p).encode()); tok = body + "." + b64(SK.sign(body.encode()).signature)
    q("INSERT INTO issued VALUES(?,?,?,?)", p["jti"], apaar, inst, p["rh"]); log(u["name"], "ISSUE", p["jti"])
    buf = io.BytesIO(); qrcode.make(tok).save(buf, format="PNG")
    return {"token": tok, "jti": p["jti"], "qr": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()}

@app.post("/api/v1/records/revoke")
def revoke(b: Jti, u=Depends(user)):
    need(u, "institution", "aicte"); q("INSERT OR IGNORE INTO revoked VALUES(?)", b.jti); log(u["name"], "REVOKE", b.jti); return {"ok": True}

@app.post("/api/v1/verify")
def verify(b: Tok, u=Depends(user)):
    def bad(m): log(u["name"], "VERIFY_FAIL", m); return {"valid": False, "reason": m}
    try:
        body, sig = b.token.strip().split("."); SK.verify_key.verify(body.encode(), unb64(sig)); p = json.loads(unb64(body))
    except Exception: return bad("Signature invalid or token malformed")
    if p["exp"] < time.time(): return bad("Record expired")
    if q("SELECT 1 FROM revoked WHERE jti=?", p["jti"]): return bad("Record has been revoked")
    s = q("SELECT * FROM students WHERE apaar=? AND inst=?", p["apaar"], p["inst"], one=True)
    if not s: return bad("Record not found")
    if not s["consent"]: return bad("Student has not consented to sharing")
    if rec_hash(s) != p["rh"]: return bad("Record changed after it was issued (tamper check failed)")
    res = {"valid": True, "institution": q("SELECT name FROM inst WHERE id=?", p["inst"], one=True)["name"], "programme": s["programme"], "admission_year": s["adm"][:4], "status": s["status"]}
    log(u["name"], "VERIFY_OK", p["jti"])
    return {**res, "signature": b64(SK.sign(json.dumps(res, sort_keys=True).encode()).signature)}  # minimal disclosure: no name, DOB or APAAR returned

# ---------- audit + demo tamper ----------
@app.get("/api/v1/audit")
def audit(u=Depends(user)): need(u, "aicte"); return q("SELECT * FROM audit ORDER BY id DESC LIMIT 100")
@app.get("/api/v1/audit/verify")
def audit_verify(u=Depends(user)):
    need(u, "aicte"); prev, rows = "GENESIS", q("SELECT * FROM audit ORDER BY id")
    for r in rows:
        if r["prev"] != prev or r["h"] != sha(prev, r["ts"], r["actor"], r["action"], r["detail"]): return {"ok": False, "broken_at": r["id"]}
        prev = r["h"]
    return {"ok": True, "entries": len(rows)}
@app.post("/api/v1/demo/tamper-audit")
def tamper_audit(u=Depends(user)): need(u, "aicte"); q("UPDATE audit SET detail='EDITED' WHERE id=2"); return {"ok": True}
@app.post("/api/v1/demo/tamper-student/{apaar}/{inst}")
def tamper_student(apaar: str, inst: str, u=Depends(user)): need(u, "aicte"); q("UPDATE students SET name=name||' X' WHERE apaar=? AND inst=?", apaar, inst); return {"ok": True}

@app.get("/api/v1/report.csv")
def report(u=Depends(user)):
    need(u, "aicte"); o = io.StringIO(); w = csv.writer(o); w.writerow(["institution", "state", "programme", "intake", "enrolled", "open_flags", "compliance_score"])
    for d in dash(u):
        for p in d["progs"]: w.writerow([d["name"], d["state"], p["programme"], p["intake"], p["enrolled"], d["open"], d["score"]])
    return Response(o.getvalue(), media_type="text/csv")

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def home(): return FileResponse("index.html")

# ---------- seed data with planted problems ----------
def mk():
    b = str(random.randint(10**10, 10**11 - 1))
    return next(b + str(d) for d in range(10) if luhn(b + str(d)))
def seed():
    random.seed(7); F = "Arjun Priya Rahul Sneha Karthik Divya Vikram Anjali Rohan Meera Suresh Kavya".split(); L = "Sharma Iyer Reddy Nair Patel Singh Kumar Menon Das Gupta Rao Khan".split()
    for i, n, s in [("I1", "Chennai Institute of Technology", "TN"), ("I2", "Pune College of Engineering", "MH"), ("I3", "Bengaluru Technical College", "KA"), ("I4", "Hyderabad School of Engineering", "TS"), ("I5", "Jaipur Institute of Engineering", "RJ")]:
        q("INSERT INTO inst VALUES(?,?,?)", i, n, s)
        for prog in ("CSE", "ECE"):
            n_in = 40 if (i, prog) == ("I3", "CSE") else 60; q("INSERT INTO intake VALUES(?,?,?)", i, prog, n_in)
            for _ in range(52 if (i, prog) == ("I3", "CSE") else n_in - random.randint(2, 8)):
                q("INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mk(), i, f"{random.choice(F)} {random.choice(L)}", f"{random.randint(2004,2007)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}", random.choice("MF"), prog, random.choice(["General", "OBC", "SC", "ST", "EWS"]), 0, 0, 0, 0, f"2025-08-{random.randint(1,25):02d}", 1, 1, "active")
    q("UPDATE students SET sn=1 WHERE rowid IN (SELECT rowid FROM students WHERE inst='I2' AND programme='ECE' LIMIT 8)")   # supernumerary breach
    q("UPDATE students SET nri=1 WHERE rowid IN (SELECT rowid FROM students WHERE inst='I5' AND programme='ECE' LIMIT 12)")  # NRI cap breach
    q("UPDATE students SET oci=1,fn=1 WHERE rowid IN (SELECT rowid FROM students WHERE inst='I4' AND programme='CSE' LIMIT 2)")  # inconsistent flags
    x = q("SELECT * FROM students WHERE inst='I1' AND programme='CSE' LIMIT 1", one=True)  # same student in two colleges
    q("INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", x["apaar"], "I2", x["name"], x["dob"], x["gender"], "CSE", "General", 0, 0, 0, 0, "2025-08-20", 1, 1, "active")
    y = q("SELECT * FROM students WHERE inst='I4' AND programme='ECE' LIMIT 1", one=True)  # fuzzy name+DOB twin with a different ID
    q("INSERT INTO students VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mk(), "I5", y["name"] + "h", y["dob"], y["gender"], "ECE", "General", 0, 0, 0, 0, "2025-08-21", 1, 1, "active")
    for i in range(1, 6): detect(f"I{i}")
    log("system", "SEED", "demo data loaded")
    ok = lambda a, nm="Demo Student", dob="2006-05-05", ad="2025-08-12": [a, nm, dob, "F", "CSE", "General", "no", "no", "no", "no", ad, "yes"]
    v1, v2, bad = mk(), mk(), mk(); bad = bad[:-1] + str((int(bad[-1]) + 1) % 10)
    with open("sample_upload.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(HEAD.split(","))
        w.writerows([ok(v1, "Nisha Verma"), ok(v2, "Aman Joshi"), ok(bad, "Bad Checkdigit"), ok("12345678901", "Short Id"), ok(mk(), ""), ok(v1, "Nisha Verma"), ok(mk(), "Bad Date", ad="12-08-2025"),
                     ok(q("SELECT apaar FROM students WHERE inst='I3' LIMIT 1", one=True)["apaar"], "Cross College Dup")])

init()
if not q("SELECT 1 FROM inst", one=True): seed()
