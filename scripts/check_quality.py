"""
Altiora 质量断言（5 条）
    python3 scripts/check_quality.py

只读本地文件、只跑本地 node，不联网、不调模型、不消耗额度。
退出码：0 全部通过；1 有 FAIL。

断言范围：
  1. 排程——「下午3点到5点」「下午3点半」能不能算出正确的起止时间
  2. 冲突——两件重叠的事能否被识别，重叠分钟与 A/B/C 选项是否齐全
  3. 日期兜底——原话有相对日期时，模型给错的日期会被本地推算覆盖，且前后端口径一致
  4. Key 泄漏——仓库里不允许出现真实 API Key 字面量
  5. 单一成品——全仓只允许 1 份成品 HTML
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HTML = BASE / "Altiora-未来的我.html"

results = []  # (level, name, detail)


def ok(name, detail=""):
    results.append(("PASS", name, detail))


def fail(name, detail=""):
    results.append(("FAIL", name, detail))


def grab_func(text: str, name: str) -> str:
    """按本仓风格取顶层函数：行首 function name( 开始，到行首单独的 } 结束。"""
    m = re.search(rf"^function {re.escape(name)}\([\s\S]*?^\}}", text, re.M)
    if not m:
        raise AssertionError(f"HTML 里找不到 function {name}()")
    return m.group(0)


def grab_const(text: str, name: str) -> str:
    m = re.search(rf"^const {re.escape(name)}=.*?;$", text, re.M)
    if not m:
        raise AssertionError(f"HTML 里找不到 const {name}")
    return m.group(0)


def build_harness(text: str) -> str:
    parts = [
        grab_const(text, "CN_NUM"),
        grab_const(text, "T0"),
        grab_func(text, "todayStr"),
        grab_func(text, "addDays"),
        grab_func(text, "resolveDate"),
        grab_func(text, "normDate"),
        grab_func(text, "pickDate"),
        grab_const(text, "pad2"),
        grab_func(text, "cnHour"),
        grab_func(text, "parseTimeRange"),
        grab_const(text, "toMin"),
        grab_func(text, "makeConflict"),
        grab_func(text, "detectConflicts"),
    ]
    # toMin 依赖 T0/T1/SPAN；T0 那行同时定义了三个，取一行即可
    body = "\n".join(parts)
    stub = """
const DATA={events:[
  {id:"e1",name:"跟导师聊",start:"14:00",end:"16:00",date:"2026-11-16",priority:2,type:"meeting"},
  {id:"e2",name:"家教",start:"15:30",end:"17:30",date:"2026-11-16",priority:1,type:"work",wage:80},
  {id:"e3",name:"另一天",start:"15:30",end:"17:30",date:"2026-11-17",priority:1,type:"work",wage:80}
],profile:{buffer_min:10,known_weakness:[],hard_sleep_deadline:null}};
function goalMatch(){return null;}
const out=[];
function eq(n,g,w){out.push({n:n,p:JSON.stringify(g)===JSON.stringify(w),d:JSON.stringify(g)});}

eq("排程-区间",parseTimeRange("明天下午3点到5点去家教"),{start:"15:00",end:"17:00"});
eq("排程-单点补1小时",parseTimeRange("下午3点半开会"),{start:"15:30",end:"16:30",guess:true});

const cs=detectConflicts("2026-11-16");
eq("冲突-只算同一天",cs.length,1);
eq("冲突-重叠分钟",cs[0]&&cs[0].overlap_min,30);
eq("冲突-ABC选项",cs[0]?cs[0].options.map(o=>o.k):null,["A","B","C"]);

const txt="周五下午3点到5点去家教";
const want=resolveDate(txt), wrong=want===addDays(todayStr(),5)?addDays(todayStr(),6):addDays(todayStr(),5);
const got=pickDate(txt,wrong);
eq("日期兜底-按原话推算",got,want);
eq("日期兜底-不听模型",got!==wrong,true);

const dates={};
["周五下午3点到5点去家教","明天上午十点面试","下周三晚上八点开会","今天上午交作业"].forEach(t=>{
  dates[t]=resolveDate(t);
});
process.stdout.write(JSON.stringify({items:out,dates:dates,today:todayStr()}));
"""
    return body + stub


def run_js() -> dict:
    node = shutil.which("node")
    if not node:
        raise AssertionError("本机没有 node，无法执行前端断言")
    if not HTML.exists():
        raise AssertionError("找不到 Altiora-未来的我.html")
    harness = build_harness(HTML.read_text(encoding="utf-8"))
    r = subprocess.run([node, "-e", harness], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError((r.stderr or "node 执行失败")[-500:])
    return json.loads(r.stdout)


def check_schedule(data: dict):
    names = {"排程-区间", "排程-单点补1小时"}
    bad = [x for x in data["items"] if x["n"] in names and not x["p"]]
    if bad:
        fail("排程", "；".join(f"{x['n']} 得到 {x['d']}" for x in bad))
    else:
        detail = "，".join(f"{x['n']} {x['d']}" for x in data["items"] if x["n"] in names)
        ok("排程", detail)


def check_conflict(data: dict):
    names = {"冲突-只算同一天", "冲突-重叠分钟", "冲突-ABC选项"}
    bad = [x for x in data["items"] if x["n"] in names and not x["p"]]
    if bad:
        fail("冲突", "；".join(f"{x['n']} 得到 {x['d']}" for x in bad))
    else:
        ok("冲突", "重叠 30 分钟、A/B/C 三个选项齐全，跨天不误判")


def check_date(data: dict):
    names = {"日期兜底-按原话推算", "日期兜底-不听模型"}
    bad = [x for x in data["items"] if x["n"] in names and not x["p"]]
    if bad:
        fail("日期兜底", "；".join(f"{x['n']} 得到 {x['d']}" for x in bad))
        return
    # 前后端同一套规则：Python 的 _date_from_text 必须与前端 resolveDate 给出同一天
    try:
        sys.path.insert(0, str(BASE / "Altiora" / "backend"))
        import llm  # noqa: E402
    except Exception as e:
        fail("日期兜底", f"后端 llm.py 导入失败：{type(e).__name__}: {e}")
        return
    diff = []
    for text, js_date in data["dates"].items():
        py_date = llm._date_from_text(text)
        py_iso = py_date.isoformat() if py_date else None
        if py_iso != js_date:
            diff.append(f"「{text}」前端 {js_date} / 后端 {py_iso}")
    if diff:
        fail("日期兜底", "前后端口径不一致：" + "；".join(diff))
    else:
        ok("日期兜底", f"模型给错日期会被覆盖；前后端对 {len(data['dates'])} 句推算一致")


def check_key_leak():
    pat = re.compile(r"sk-[A-Za-z0-9]{20,}")
    hits = []
    for p in list(BASE.rglob("*.html")) + list(BASE.rglob("*.py")) + list(BASE.rglob("*.md")):
        if any(part in {".git", "node_modules", ".uploads"} for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if pat.search(text):
            hits.append(str(p.relative_to(BASE)))
    if hits:
        fail("Key 泄漏", "疑似真实 Key：" + "、".join(hits[:5]))
    else:
        ok("Key 泄漏", "仓库里没有真实 API Key 字面量")


def check_single_copy():
    banned = ["index.html", "app.html",
              "Altiora/index.html", "Altiora/Altiora-未来的我.html"]
    found = [f for f in banned if (BASE / f).exists()]
    if found:
        fail("单一成品", "多余副本：" + "、".join(found))
    elif not HTML.exists():
        fail("单一成品", "根目录成品缺失")
    else:
        ok("单一成品", "只有 Altiora-未来的我.html")


def main():
    print("Altiora 质量断言\n" + "=" * 52)
    try:
        data = run_js()
    except Exception as e:
        fail("前端断言", f"{type(e).__name__}: {e}")
        data = None

    for fn in (lambda: check_schedule(data) if data else None,
               lambda: check_conflict(data) if data else None,
               lambda: check_date(data) if data else None,
               check_key_leak,
               check_single_copy):
        try:
            fn()
        except Exception as e:
            fail("断言本身出错", f"{type(e).__name__}: {e}")

    print()
    for i, (level, name, detail) in enumerate(results, 1):
        mark = {"PASS": "[ OK ]", "FAIL": "[FAIL]"}[level]
        print(f"{mark} {i}. {name:<10} {detail}")

    n_fail = sum(1 for r in results if r[0] == "FAIL")
    print("=" * 52)
    if n_fail:
        print(f"{n_fail} 条断言失败。")
    else:
        print("5 条断言全部通过。")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
