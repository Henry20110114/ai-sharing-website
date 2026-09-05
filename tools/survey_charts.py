#!/usr/bin/env python3
"""Render the survey charts into the report page.

    python3 tools/survey_charts.py

Reads reports/data/ai-usage-survey-2026-07.json and fills every region of the form

    <!-- chart KEY zh -->  ...  <!-- /chart -->
    <!-- chart KEY en -->  ...  <!-- /chart -->

in reports/*.html with an HTML bar chart (one row per option, width = share of
respondents) plus a collapsible data table. Optional attributes on the opening
marker: `top=8` (chart only the first 8 options; the table keeps all).
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "reports" / "data" / "ai-usage-survey-2026-07.json"
T = {
    "zh": {"n": "n = {n}", "multi": "可多选，百分比为选择该项的人数占比", "table": "查看数据表",
           "option": "选项", "count": "人数", "share": "占比", "rest": "其余各项："},
    "en": {"n": "n = {n}", "multi": "multiple choice; percentages are the share of respondents who picked each option",
           "table": "Show data table", "option": "Option", "count": "Count", "share": "Share", "rest": "Remaining options: "},
}


def esc(s):
    return html.escape(s, quote=True)


def render(q, lang, n, top=None):
    t = T[lang]
    opts = q["options"]
    shown = opts[:top] if top else opts
    note = t["n"].format(n=n) + ("，" if lang == "zh" else "; ") + t["multi"] if q["multi"] else t["n"].format(n=n)
    rows = []
    for o in shown:
        pct = round(100 * o["count"] / n)
        label = o[lang]
        rows.append(
            f'      <li class="bar-row" title="{esc(label)}: {o["count"]} ({pct}%)">'
            f'<span class="bar-label">{esc(label)}</span>'
            f'<span class="bar-track"><span class="bar-fill" style="width:{pct}%"></span></span>'
            f'<span class="bar-value">{o["count"]} · {pct}%</span></li>'
        )
    rest = ""
    if top and len(opts) > top:
        tail = "、".join(f'{o[lang]}（{o["count"]}）' for o in opts[top:]) if lang == "zh" else \
               ", ".join(f'{o[lang]} ({o["count"]})' for o in opts[top:])
        rest = f'    <p class="chart-rest">{t["rest"]}{esc(tail)}</p>\n'
    table = "\n".join(
        f'        <tr><td>{esc(o[lang])}</td><td>{o["count"]}</td><td>{round(100 * o["count"] / n)}%</td></tr>'
        for o in opts
    )
    return (
        f'<figure class="chart">\n'
        f'    <figcaption><span class="chart-title">{esc(q[lang])}</span><span class="chart-note">{esc(note)}</span></figcaption>\n'
        f'    <ol class="bars">\n' + "\n".join(rows) + "\n    </ol>\n" + rest +
        f'    <details class="chart-data"><summary>{t["table"]}</summary>\n'
        f'      <table><thead><tr><th>{t["option"]}</th><th>{t["count"]}</th><th>{t["share"]}</th></tr></thead>\n'
        f'      <tbody>\n{table}\n      </tbody></table>\n'
        f'    </details>\n'
        f'</figure>'
    )


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    questions = {q["key"]: q for q in data["questions"]}
    pattern = re.compile(r"(<!-- chart (\w+) (zh|en)((?: [^>]*?)?) -->)(.*?)(<!-- /chart -->)", re.S)
    for page in sorted((ROOT / "reports").glob("*.html")):
        text = page.read_text(encoding="utf-8")
        count = 0

        def repl(m):
            nonlocal count
            key, lang, attrs = m.group(2), m.group(3), m.group(4)
            if key not in questions:
                sys.exit(f"{page.name}: unknown chart key {key!r}")
            top = re.search(r"top=(\d+)", attrs)
            count += 1
            body = render(questions[key], lang, data["n"], int(top.group(1)) if top else None)
            return m.group(1) + "\n" + body + "\n" + m.group(6)

        new = pattern.sub(repl, text)
        if new != text:
            page.write_text(new, encoding="utf-8")
        print(f"{page.relative_to(ROOT)}: {count} charts")


if __name__ == "__main__":
    main()
