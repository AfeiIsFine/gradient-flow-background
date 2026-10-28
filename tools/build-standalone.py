#!/usr/bin/env python3
"""把 index.html + styles.css + app.js 打包成单文件 HTML。

用法：
    python3 tools/build-standalone.py

产物：
    gradient-flow.html —— 与 index.html 完全等价，但零外部文件依赖，
    双击即可打开，也可以直接发给别人。

为什么用脚本而不是手改：三份源文件将来还会改，手拼的单文件必然与主版本不同步。
每次改完 app.js / styles.css 后重跑一次即可。
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "gradient-flow.html"

LINK = '<link rel="stylesheet" href="styles.css">'
SCRIPT = '<script src="app.js"></script>'


def main() -> int:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    js = (ROOT / "app.js").read_text(encoding="utf-8")

    # 结构自检：源文件必须只有一个样式表、一个脚本，否则说明 index.html 改过了
    for label, needle, text, count in (
        ("css link", LINK, html, 1),
        ("script tag", SCRIPT, html, 1),
    ):
        got = text.count(needle)
        if got != count:
            print(f"[FAIL] index.html 里 {label} 出现 {got} 次，预期 {count} 次", file=sys.stderr)
            return 1

    # 内联安全：CSS 里出现 </style>、JS 里出现 </script> 会提前闭合标签。
    # app.js 里的导出模板已经写成 <\/script>，所以这里应当为 0。
    if "</style" in css.lower():
        print("[FAIL] styles.css 含 </style>，无法安全内联", file=sys.stderr)
        return 1
    if "</script" in js.lower():
        print("[FAIL] app.js 含 </script>，无法安全内联", file=sys.stderr)
        return 1
    if "<!--" in css or "<!--" in js:
        print("[FAIL] 源文件含 <!--（会触发 HTML 脚本转义状态）", file=sys.stderr)
        return 1

    out = html.replace(LINK, "<style>\n" + css + "\n</style>")
    out = out.replace(SCRIPT, "<script>\n" + js + "\n</script>")

    # 产物自检：不能残留任何外部文件引用
    for leftover in ('href="styles.css"', 'src="app.js"', '<link rel="stylesheet"'):
        if leftover in out:
            print(f"[FAIL] 产物仍含外部引用：{leftover}", file=sys.stderr)
            return 1
    if not out.rstrip().endswith("</html>"):
        print("[FAIL] 产物结尾不是 </html>", file=sys.stderr)
        return 1

    OUT.write_text(out, encoding="utf-8")
    print(f"[OK] {OUT.name}  {len(out.encode('utf-8')) / 1024:.1f} KB"
          f"（index.html {len(html.encode('utf-8')) / 1024:.1f} KB"
          f" + css {len(css.encode('utf-8')) / 1024:.1f} KB"
          f" + js {len(js.encode('utf-8')) / 1024:.1f} KB）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
