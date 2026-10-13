#!/usr/bin/env python3
"""Sestaví data.json z exportů Monitoru Státní pokladny (Odvětvový rozklikávací rozpočet pro výdaje).

Vstup:  data/*-RRRR-MM.xlsx   (např. ..._výdaje_2025-12.xlsx; pro každý rok se použije soubor s nejvyšším měsícem)
Výstup: data.json  (částky v tis. Kč; z = Kč z každých 1000 Kč výdajů; sch/sk = schválený rozpočet / skutečnost)
Při jakékoli nesrovnalosti skončí chybou, takže se nikdy nezveřejní poškozená data.
"""
import glob, json, re, sys, datetime, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAP = {"Tělovýchova a zájmová činnost": "Sport a zájmová činnost",
       "Ostatní činnosti související se službami pro obyvatelstvo": "Ostatní činnosti související se službami pro fyzické osoby"}
DAV_SRC = "Dávky a podpory v sociálním zabezpečení"
DAV = "Dávky a podpory v sociálním zabezpečení (jen 2010–2012)"
REM = "Ostatní oddíly mimo výběr"
ROWS = ["Doprava", "Státní moc, státní správa, územní samospráva a politické strany", "Kultura, církve a sdělovací prostředky", "Bydlení, komunální služby a územní rozvoj", "Vzdělávání a školské služby", "Sport a zájmová činnost", "Sociální služby a společné činnosti v sociálním zabezpečení a politice zaměstnanosti", "Ochrana životního prostředí", "Vodní hospodářství", "Bezpečnost a veřejný pořádek", "Finanční operace", "Zdravotnictví", "Ostatní činnosti", "Požární ochrana a integrovaný záchranný systém", "Průmysl, stavebnictví, obchod a služby", "Ostatní činnosti související se službami pro fyzické osoby", "Ostatní výzkum a vývoj", "Zemědělství, lesní hospodářství a rybářství", "Jiné veřejné služby a činnosti", DAV, REM]
KNOWN_REM = {"Spoje", "Civilní připravenost na krizové stavy", "Obrana", "Politika zaměstnanosti"}  # záměrně mimo výběr
SHORT = ["Doprava", "Státní správa a samospráva", "Kultura a církve", "Bydlení a komunální služby", "Školství", "Sport a volný čas", "Sociální služby", "Životní prostředí", "Vodní hospodářství", "Bezpečnost a pořádek", "Finanční operace", "Zdravotnictví", "Ostatní činnosti", "Požární ochrana", "Průmysl a obchod", "Služby pro fyzické osoby", "Výzkum a vývoj", "Zemědělství a lesnictví", "Jiné veřejné služby", "Dávky (jen 2010–2012)", "Mimo výběr (ostatní oddíly)"]

def clean(s):
    return s.replace("\xa0", " ").strip() if isinstance(s, str) else s

def read(path):
    h = pd.read_excel(path, header=None, nrows=11)
    if not ("Schválený" in str(h.iloc[10, 5]) and "Po změnách" in str(h.iloc[10, 6]) and "Skutečnost" in str(h.iloc[9, 7])):
        sys.exit(f"{path}: sloupce nejsou Schválený / Po změnách / Skutečnost (hlavičky: {h.iloc[9, 5:8].tolist()} {h.iloc[10, 5:8].tolist()}); změnil se formát exportu?")
    raw = pd.read_excel(path, header=None, skiprows=11).iloc[:, :8]
    raw.columns = ["obec", "skupina", "oddil", "pododdil", "paragraf", "sch", "zm", "sk"]
    for c in ("skupina", "oddil", "pododdil"):
        raw[c] = raw[c].map(clean)
    for c in ("sch", "zm", "sk"):
        raw[c] = pd.to_numeric(raw[c], errors="coerce").fillna(0)
    total = raw.iloc[0]
    if not (1e6 < total.sch < 1e12):
        sys.exit(f"{path}: celkový řádek vypadá divně (sch={total.sch}); změnil se formát exportu?")
    od = raw[(raw.oddil != "-") & (raw.pododdil == "-")].copy()
    if od.empty:
        sys.exit(f"{path}: nenalezeny řádky oddílů; změnil se formát exportu?")
    return total, od

files = {}
for f in glob.glob(str(ROOT / "data" / "*.xlsx")):
    m = re.search(r"(20\d\d)-(\d\d)\.xlsx$", f)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if y not in files or mo > files[y][0]:
            files[y] = (mo, f)
if not files:
    sys.exit("Ve složce data/ nejsou žádné soubory *-RRRR-MM.xlsx")

out = {"ob": [{"s": s, "n": n} for s, n in zip(SHORT, ROWS)], "yrs": [], "mes": {}, "z": {}, "sch": {}, "sk": {}}
for y in sorted(files):
    mo, f = files[y]
    total, od = read(f)
    sums = {k: {r: 0.0 for r in ROWS} for k in ("sch", "sk")}
    for r in od.itertuples():
        name = MAP.get(r.oddil, r.oddil)
        if name == DAV_SRC: name = DAV
        if name not in ROWS:
            if name not in KNOWN_REM: print(f"UPOZORNĚNÍ {y}: neznámý oddíl '{r.oddil}' zařazen do '{REM}'")
            name = REM
        sums["sch"][name] += r.sch / 1000; sums["sk"][name] += r.sk / 1000
    for k, col in (("sch", total.sch), ("sk", total.sk)):
        if abs(sum(sums[k].values()) - col / 1000) > 0.5:
            sys.exit(f"{y} ({k}): součet oddílů {sum(sums[k].values()):.1f} != celkem {col/1000:.1f} tis. Kč")
    tot = sum(sums["sk"].values())
    if tot <= 0:
        sys.exit(f"{y}: nulová skutečnost")
    out["yrs"].append(y); out["mes"][str(y)] = mo
    out["z"][str(y)] = [round(sums["sk"][r] / tot * 1000, 1) for r in ROWS]
    out["sch"][str(y)] = [round(sums["sch"][r], 1) for r in ROWS]
    out["sk"][str(y)] = [round(sums["sk"][r], 1) for r in ROWS]
    print(f"{y}-{mo:02d}: výdaje skutečnost {tot:,.0f} tis. Kč  ({pathlib.Path(f).name})")
out["generovano"] = datetime.date.today().isoformat()
(ROOT / "data.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("data.json OK:", len(out["yrs"]), "let")
