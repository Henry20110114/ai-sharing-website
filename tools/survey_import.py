#!/usr/bin/env python3
"""Turn the Microsoft Forms export (xlsx) of the AI usage survey into an aggregated,
anonymous dataset for the report page.

    python3 tools/survey_import.py "/path/to/AI 使用情况调研.xlsx"

Writes reports/data/ai-usage-survey-2026-07.json with per-question counts only.
Names, emails, timestamps and individual rows are never written. Needs only Python 3.
"""
import collections, datetime, json, re, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "data" / "ai-usage-survey-2026-07.json"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))

    def col(ref):
        n = 0
        for ch in re.match(r"[A-Z]+", ref).group(0):
            n = n * 26 + ord(ch) - 64
        return n - 1

    rows = []
    for r in sheet.find("m:sheetData", NS):
        vals = {}
        for c in r:
            v = c.find("m:v", NS)
            if v is None:
                isel = c.find("m:is", NS)
                val = "".join(x.text or "" for x in isel.iter("{%s}t" % NS["m"])) if isel is not None else ""
            elif c.get("t") == "s":
                val = shared[int(v.text)]
            else:
                val = v.text
            vals[col(c.get("r"))] = val
        width = max(vals) + 1 if vals else 0
        rows.append([vals.get(i, "") for i in range(width)])
    return rows


def excel_date(serial):
    return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(serial))).date().isoformat()


def grade_band(raw):
    s = raw.strip().lower()
    if s in ("高一", "10", "g1", "a1", "准a1"):
        return "高一（10 年级）"
    if s in ("高二", "11", "g2"):
        return "高二（11 年级）"
    if s in ("高三", "12", "a2"):
        return "高三（12 年级）"
    if s in ("8", "8.5", "九年级", "七年级", "八年级", "7", "9", "初一", "初二", "初三"):
        return "初中（7–9 年级）"
    return "未注明"


# key, column index, ordered (keep option order instead of sorting by count), english title
QUESTIONS = [
    ("gender", 5, False, "Gender"),
    ("grade", 6, True, "Grade"),
    ("curriculum", 7, False, "Curriculum"),
    ("frequency", 8, True, "How often did you use AI to help you learn in the past month?"),
    ("ai_types", 9, False, "What types of AI do you usually use?"),
    ("services", 10, False, "Which AI services did you actually use in the past month?"),
    ("stages", 11, False, "In which parts of learning did you use AI in the past month?"),
    ("delegated", 12, False, "Which tasks have you ever handed almost entirely to AI?"),
    ("crunch", 13, True, "Lots of holiday homework, school starts tomorrow, and you can't finish tonight. Would you have AI generate the answers?"),
    ("group", 14, False, "For a school field study or group project, how would you use AI?"),
    ("writing", 15, True, "For essay or writing assignments, how do you use AI?"),
    ("concept", 16, False, "When you suddenly need to understand an unfamiliar concept, you usually…"),
    ("manual_skills", 17, True, "Do you still need the old “manual” skills of searching and organizing information?"),
    ("verify", 18, True, "Do you check the answers AI gives you?"),
    ("impact", 19, True, "How much has AI changed the way you learn?"),
    ("impact_aspects", 20, False, "Where has AI changed your learning the most?"),
    ("motivation", 21, True, "Has AI affected your motivation to learn?"),
    ("without_ai", 22, False, "If you couldn't use AI for a while, what would change?"),
    ("pure_ai", 23, True, "Are you optimistic about a future pure-AI teaching model?"),
    ("ip", 24, True, "Does AI threaten intellectual property and patents?"),
    ("creativity", 25, False, "If a student feels short on imagination or creativity, what does heavy AI use do to them?"),
    ("detail", 26, True, "How detailed do you want AI answers to be?"),
    ("too_long", 27, False, "When an AI answer is much longer than you need, you usually…"),
    ("rules", 28, True, "Do you know your school's or teachers' rules on AI use?"),
    ("guidance", 29, False, "What AI guidance would you like your school to provide?"),
]

# Display order for ordered questions, and English labels for every option.
ORDER = {
    "grade": ["初中（7–9 年级）", "高一（10 年级）", "高二（11 年级）", "高三（12 年级）", "未注明"],
    "frequency": ["每天", "每周几次", "很少"],
    "crunch": ["会，经常这样做", "可能会，但只作为临时应急", "不太会，最多让 AI 提供思路", "不会，我会尽量自己完成"],
    "writing": ["直接让 AI 生成全文，自己稍作修改", "让 AI 提供大纲和素材方向，自己写正文", "只让 AI 检查语法或润色表达", "完全不用 AI", "视作业要求而定"],
    "manual_skills": ["非常需要", "仍然需要，但重要性降低", "只在严肃学习或研究中需要", "基本不需要"],
    "verify": ["总是会", "经常会", "偶尔会", "很少会", "从不会"],
    "impact": ["影响很大", "影响较大", "影响一般", "影响较小"],
    "motivation": ["明显增强", "有些增强", "基本无影响", "明显削弱", "因任务而异"],
    "pure_ai": ["很看好，可以替代部分课堂", "比较看好，但需要教师监督", "不太看好，AI 只能辅助教学"],
    "ip": ["会，威胁很大", "会，但可以通过规则管理", "影响有限", "不会，反而可能促进创新"],
    "detail": ["一两句话结论", "简短结论加关键理由", "先简略回答，需要时再展开", "分步骤详细解释", "视任务而定"],
    "rules": ["非常清楚", "大致了解", "听说过但不清楚", "完全不了解", "学校目前没有明确要求"],
}
EN = {
    "男": "Male", "女": "Female", "不方便透露": "Prefer not to say",
    "初中（7–9 年级）": "Grades 7–9", "高一（10 年级）": "Grade 10", "高二（11 年级）": "Grade 11",
    "高三（12 年级）": "Grade 12", "未注明": "Not specified",
    "体制内课程": "Chinese national curriculum", "A-Level": "A-Level", "不确定": "Not sure", "AP": "AP", "IB": "IB",
    "每周几次": "A few times a week", "每天": "Every day", "很少": "Rarely",
    "通用问答类 AI": "General chat assistants", "翻译或语言学习类 AI": "Translation / language learning",
    "搜索或资料整理类 AI": "Search / research assistants", "写作润色类 AI": "Writing and editing",
    "图片、音乐、视频生成类 AI": "Image, music, video generation", "编程类 AI": "Coding assistants",
    "豆包": "Doubao", "通义千问 Qwen": "Qwen", "manus": "Manus", "智谱清言 GLM": "GLM (Zhipu)",
    "MiniMax 或海螺 AI": "MiniMax / Hailuo",
    "理解概念": "Understanding concepts", "查找资料": "Finding information", "解题思路": "Working out how to solve problems",
    "翻译": "Translation", "整理资料": "Organizing notes and materials", "写作大纲": "Outlining writing",
    "语法检查或润色": "Grammar checking / polishing", "复习总结": "Review and summaries",
    "编程或数据处理": "Coding / data processing", "小组项目": "Group projects", "提出建议": "Getting suggestions",
    "查资料整理": "Researching and organizing information", "从未这样做": "Never done this",
    "解答完整题目": "Solving entire problems", "制作 PPT 或项目文案": "Making slides or project write-ups",
    "完成整篇作文或作业": "Writing a whole essay or assignment", "写代码": "Writing code", "实验报告": "Lab reports",
    "会，经常这样做": "Yes, I often do", "可能会，但只作为临时应急": "Maybe, but only as a last resort",
    "不太会，最多让 AI 提供思路": "Probably not — at most ask AI for hints", "不会，我会尽量自己完成": "No, I'd try to finish it myself",
    "查找和整理资料": "Finding and organizing information", "帮助构思项目方向": "Brainstorming the project direction",
    "润色文字": "Polishing text", "帮助细化任务框架": "Breaking down the task structure", "分析数据": "Analyzing data",
    "制作展示材料": "Making presentation materials", "直接完成自己负责的部分": "Doing my whole part for me",
    "让 AI 提供大纲和素材方向，自己写正文": "AI gives an outline and ideas, I write the text",
    "只让 AI 检查语法或润色表达": "AI only checks grammar or polishes wording",
    "直接让 AI 生成全文，自己稍作修改": "AI writes the whole thing, I lightly edit",
    "视作业要求而定": "Depends on the assignment rules", "完全不用 AI": "Don't use AI at all",
    "先用搜索引擎查资料，再视情况问 AI": "Search engine first, then AI if needed", "直接问 AI": "Ask AI directly",
    "先看课本或课堂资料": "Textbook or class materials first", "暂时不处理": "Leave it for later",
    "先问老师或同学": "Ask a teacher or classmate first",
    "非常需要": "Still essential", "仍然需要，但重要性降低": "Still needed, but less important",
    "只在严肃学习或研究中需要": "Only for serious study or research", "基本不需要": "Basically not needed",
    "总是会": "Always", "经常会": "Often", "偶尔会": "Sometimes", "很少会": "Rarely", "从不会": "Never",
    "影响很大": "Very large", "影响较大": "Fairly large", "影响一般": "Moderate", "影响较小": "Small",
    "获取资料更快": "Faster access to information", "复习效率提高": "More efficient revision",
    "解题方式变化": "Changed how I solve problems", "时间管理变化": "Changed my time management",
    "写作方式变化": "Changed how I write", "更依赖 AI": "More dependent on AI", "独立思考减少": "Less independent thinking",
    "学习兴趣变化": "Changed my interest in learning", "没有明显影响": "No clear effect",
    "明显增强": "Clearly stronger", "有些增强": "Somewhat stronger", "基本无影响": "No real effect",
    "明显削弱": "Clearly weaker", "因任务而异": "Depends on the task",
    "查资料更费时间": "Research would take longer", "独立思考变多": "More independent thinking",
    "学习效率下降": "Lower efficiency", "影响不大": "Not much change", "完成作业变慢": "Slower on homework",
    "更依赖老师或同学": "Rely more on teachers or classmates", "可能更认真掌握基础技能": "Might master basic skills more seriously",
    "学习动力下降": "Lower motivation",
    "很看好，可以替代部分课堂": "Optimistic — could replace some classes",
    "比较看好，但需要教师监督": "Fairly optimistic, with teacher supervision",
    "不太看好，AI 只能辅助教学": "Skeptical — AI can only assist teaching",
    "会，威胁很大": "Yes, a serious threat", "会，但可以通过规则管理": "Yes, but manageable with rules",
    "影响有限": "Limited effect", "不会，反而可能促进创新": "No — it may even encourage innovation",
    "会提供更多灵感": "Gives more inspiration", "短期有帮助，但可能形成依赖": "Helps short-term, but may create dependence",
    "会进一步限制原创能力": "Further limits originality", "主要取决于使用方式": "Depends mainly on how it's used",
    "一两句话结论": "A one- or two-sentence conclusion", "简短结论加关键理由": "Short conclusion plus key reasons",
    "先简略回答，需要时再展开": "Brief answer first, expand on request", "分步骤详细解释": "Detailed step-by-step explanation",
    "视任务而定": "Depends on the task",
    "仔细看完": "Read it all carefully", "让 AI 重新概括": "Ask AI to summarize", "只看开头或结论": "Read only the start or the conclusion",
    "直接跳过": "Skip it", "视重要程度而定": "Depends how important it is",
    "非常清楚": "Very clear", "大致了解": "Roughly aware", "听说过但不清楚": "Heard of them, unclear",
    "完全不了解": "Not aware at all", "学校目前没有明确要求": "School has no clear rules yet",
    "如何判断 AI 答案是否可靠": "How to judge whether AI answers are reliable",
    "不同学科中的 AI 使用方法": "How to use AI in different subjects", "如何向 AI 提问": "How to ask AI good questions",
    "哪些行为属于学术不诚信": "What counts as academic dishonesty", "AI 写作和引用规范": "Rules for AI-assisted writing and citation",
    "如何保护隐私和数据安全": "How to protect privacy and data", "不需要相关指导": "No guidance needed", "其他": "Other",
}


def main(path):
    rows = read_xlsx(path)
    header, data = rows[0], rows[1:]
    n = len(data)
    dates = sorted(excel_date(r[1]) for r in data if r[1])
    out = {"n": n, "period": [dates[0], dates[-1]], "questions": []}
    missing = set()
    for key, col, ordered, title_en in QUESTIONS:
        counts = collections.Counter()
        multi = any(";" in (r[col] if col < len(r) else "") for r in data)
        for r in data:
            raw = r[col] if col < len(r) else ""
            if not raw:
                continue
            parts = raw.split(";") if multi else [raw]
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                if key == "grade":
                    p = grade_band(p)
                counts[p] += 1
        if ordered and key in ORDER:
            items = [(o, counts[o]) for o in ORDER[key] if counts[o]]
            leftovers = [(o, c) for o, c in counts.items() if o not in ORDER[key]]
            items += sorted(leftovers, key=lambda x: -x[1])
        else:
            items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        options = []
        for zh, c in items:
            en = EN.get(zh, zh)
            if zh not in EN and not re.match(r"^[A-Za-z0-9 ./-]+$", zh):
                missing.add(zh)
            options.append({"zh": zh, "en": en, "count": c})
        out["questions"].append({
            "key": key, "zh": header[col], "en": title_en, "multi": multi, "ordered": ordered, "options": options,
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: n={n}, period {out['period'][0]} to {out['period'][1]}, {len(out['questions'])} questions")
    if missing:
        print("options without an English label:", sorted(missing))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
