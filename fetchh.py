import pandas as pd
import re

EXCEL_FILE = r"C:\Users\T.Vimal Raj\Documents\sbi_extraction.xlsx"

EXTRACT_RULES = [
    {"name": "between_data", "mode": "between", "start": "BULK POSTING-", "end": "EPAO"},
    {"name": "before_keyword", "mode": "before", "keyword": " 2026 to 2030 "},
    {"name": "after_keyword", "mode": "after", "keyword": " 2026 to 2030 "},
    {"name": "rows_end", "mode": "filter", "endswith": "TRANSFER TO"},
    {"name": "rows_contains_end", "mode": "filter", "endswith": "TRANSFE", "contains": "BKH4"},
    {"name": "rows_contains_start", "mode": "filter", "startswith": "BULK", "contains": "44"},
    {"name": "rows_has_end_slash_or_dash", "mode": "filter", "endswith": "Nov 2025", "contains_any": ["-"]},
    {"name": "rows_has_start_slash_or_dash", "mode": "filter", "startswith": "HOF", "contains_any": ["-"]},
    {"name": "row_contain", "mode": "filter", "contains": "12"},
    {"name": "row_not_contain", "mode": "filter", "not_contains": " "},
]

df = pd.read_excel(EXCEL_FILE, dtype=str)
df = df.fillna("")

def build_row_text(row):
    parts = []
    for cell in row:
        s = str(cell).strip()
        if s:
            parts.append(s)
    return " ".join(parts)


def extract_between_all(text, start, end):
    pattern = re.escape(start) + r"(.*?)" + re.escape(end)
    return [m.strip() for m in re.findall(pattern, text, flags=re.DOTALL) if m.strip()]


def extract_before(text, keyword, occurrence="first", include_keyword=False):
    if occurrence == "last":
        idx = text.rfind(keyword)
    else:
        idx = text.find(keyword)
    if idx == -1:
        return None
    end_idx = idx + (len(keyword) if include_keyword else 0)
    result = text[:end_idx].strip()
    return result if result else None


def extract_after(text, keyword, occurrence="first", include_keyword=False):
    if occurrence == "last":
        idx = text.rfind(keyword)
    else:
        idx = text.find(keyword)
    if idx == -1:
        return None
    start_idx = idx + (0 if include_keyword else len(keyword))
    result = text[start_idx:].strip()
    return result if result else None


def extract_regex_all(text, pattern, group=1, flags=0):
    compiled = re.compile(pattern, flags)
    results = []
    for m in compiled.finditer(text):
        try:
            val = m.group(group)
        except IndexError:
            val = m.group(0)
        if val is None:
            continue
        val = str(val).strip()
        if val:
            results.append(val)
    return results


def normalize_for_match(text, normalize_spaces=True, case_insensitive=True):
    s = text
    if normalize_spaces:
        s = re.sub(r"\s+", " ", s).strip()
    if case_insensitive:
        s = s.upper()
    return s


def row_matches(text, rule):
    normalize_spaces = rule.get("normalize_spaces", True)
    case_insensitive = rule.get("case_insensitive", True)
    t = normalize_for_match(text, normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)

    if "contains" in rule:
        contains = rule.get("contains")
        if isinstance(contains, (list, tuple)):
            for c in contains:
                if c is None:
                    continue
                c_norm = normalize_for_match(str(c), normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)
                if c_norm and c_norm not in t:
                    return False
        else:
            c_norm = normalize_for_match(str(contains), normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)
            if c_norm and c_norm not in t:
                return False

    if "contains_any" in rule:
        any_list = rule.get("contains_any") or []
        ok = False
        for c in any_list:
            if c is None:
                continue
            c_norm = normalize_for_match(str(c), normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)
            if c_norm and c_norm in t:
                ok = True
                break
        if not ok:
            return False

    if "startswith" in rule:
        s_norm = normalize_for_match(str(rule.get("startswith", "")), normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)
        if s_norm and not t.startswith(s_norm):
            return False

    if "endswith" in rule:
        e_norm = normalize_for_match(str(rule.get("endswith", "")), normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)
        if e_norm and not t.endswith(e_norm):
            return False

    if "regex" in rule:
        pattern = rule.get("regex")
        if pattern:
            flags = rule.get("regex_flags", 0)
            if case_insensitive:
                flags |= re.IGNORECASE
            if not re.search(pattern, text, flags=flags):
                return False

    if "not_contains" in rule:
        not_contains = rule.get("not_contains")
        if isinstance(not_contains, (list, tuple)):
            for c in not_contains:
                if c is None:
                    continue
                c_norm = normalize_for_match(str(c), normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)
                if c_norm and c_norm in t:
                    return False
        else:
            c_norm = normalize_for_match(str(not_contains), normalize_spaces=normalize_spaces, case_insensitive=case_insensitive)
            if c_norm and c_norm in t:
                return False

    return True


def apply_rule(text, rule):
    mode = rule.get("mode")
    if mode == "between":
        start = rule.get("start", "")
        end = rule.get("end", "")
        if not start or not end:
            return []
        return extract_between_all(text, start, end)

    if mode == "before":
        keyword = rule.get("keyword", "")
        if not keyword:
            return []
        occurrence = rule.get("occurrence", "first")
        include_keyword = bool(rule.get("include_keyword", False))
        r = extract_before(text, keyword, occurrence=occurrence, include_keyword=include_keyword)
        return [r] if r else []

    if mode == "after":
        keyword = rule.get("keyword", "")
        if not keyword:
            return []
        occurrence = rule.get("occurrence", "first")
        include_keyword = bool(rule.get("include_keyword", False))
        r = extract_after(text, keyword, occurrence=occurrence, include_keyword=include_keyword)
        return [r] if r else []

    if mode == "regex":
        pattern = rule.get("pattern", "")
        if not pattern:
            return []
        group = rule.get("group", 1)
        flags = rule.get("flags", 0)
        return extract_regex_all(text, pattern, group=group, flags=flags)

    if mode == "filter":
        return [text] if row_matches(text, rule) else []

    return []

results_by_rule = {r["name"]: [] for r in EXTRACT_RULES}

for row_idx, row in df.iterrows():
    row_text = build_row_text(row)
    if not row_text:
        continue

    for rule in EXTRACT_RULES:
        extracted = apply_rule(row_text, rule)
        if extracted:
            results_by_rule[rule["name"]].append({"row": int(row_idx) + 1, "text": row_text, "values": extracted})


for rule in EXTRACT_RULES:
    name = rule["name"]
    print(f"\n---- {name} ----")
    hits = results_by_rule.get(name, [])
    if not hits:
        print("No matches")
        continue
    for i, hit in enumerate(hits, 1):
        values = " | ".join(hit["values"])
        print(f"{i}. Row {hit['row']}: {values}")
