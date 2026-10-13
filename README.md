# Výdaje Brna na tisícikoruně

Grafy se načítají z `data.json`, který se při každém nasazení sestaví z exportů v `data/`.

## Jednorázové nastavení
1. Zkopírujte všech 17 exportů (`Odvětvový_rozklikávací_rozpočet_pro_výdaje_RRRR-MM.xlsx`) do složky `data/`.
2. GitHub → Settings → Pages → Build and deployment → Source: **GitHub Actions**.
3. Pokud v repozitáři už je jiný workflow pro Pages, smažte ho (jinak se budou nasazení přebíjet).
4. Commit a push do větve `main`.

## Každý rok
1. V Monitoru stáhněte export „Odvětvový rozklikávací rozpočet pro výdaje“ pro Statutární město Brno, období prosinec.
2. Soubor pojmenujte `Odvětvový_rozklikávací_rozpočet_pro_výdaje_2026-12.xlsx` (rok a měsíc na konci názvu) a dejte do `data/`.
3. Commit a push. Workflow sám sestaví data a nasadí web (cca 1 minuta).

Pro každý rok se použije soubor s nejvyšším měsícem, takže starší neúplný export (např. `2026-08`) nemusíte mazat.
Když se něco nesrovná (jiný formát, nesedí součty), workflow skončí chybou a na webu zůstanou původní data.

## Místní náhled
`python scripts/build_data.py` a pak `python -m http.server` (stránky načítají `data.json`, přes `file://` nefungují).
