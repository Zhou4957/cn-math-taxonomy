#!/usr/bin/env python3
"""孩子自用版清理：幂等，可在每次同步上游后重复运行。
- 去掉各页顶部跳外部测评站 test.pansgo.com 的横幅
- 去掉首页智商测试卡片、诊断结果页的测评链接段
- 关闭统计上报（endpoint 清空，不向原作者的统计端发数据）
- 分享图二维码指向本站
- 去掉首页导航跳 pansgo.com 的「资源搜索」外链（网盘搜索）
原作者署名与许可证不动。文件不存在或内容已变时跳过对应项，不报错。
"""
import re, pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent

def edit(rel, fn):
    fp = root / rel
    if not fp.exists(): return
    t = fp.read_text(encoding='utf-8')
    t2 = fn(t)
    if t2 != t:
        fp.write_text(t2, encoding='utf-8')
        print('cleaned', rel)

for rel in ['index.html','explore/index.html','diagnose/index.html','children/index.html','children/history.html']:
    edit(rel, lambda t: re.sub(r'\s*<a class="top-banner"[^>]*>.*?</a>', '', t, count=1))
    edit(rel, lambda t: re.sub(r'\s*<a[^>]*href="https://pansgo\.com"[^>]*>.*?</a>', '', t, count=1, flags=re.S))
edit('index.html', lambda t: re.sub(r'\s*<a class="iq-card"[^>]*>.*?</a>', '', t, count=1, flags=re.S))
edit('diagnose/app.js', lambda t: re.sub(r"\n\s*page\.append\(h\('p', \{ class: 'iq-line'.*?\}\)\);\n", "\n", t, count=1, flags=re.S))
edit('diagnose/share.js', lambda t: t.replace("https://math.pansgo.com/?from=share", "https://zhou4957.github.io/cn-math-taxonomy/?from=share"))
def stats_off(t):
    t = re.sub(r"endpoint:\s*'[^']*'", "endpoint: ''", t)
    t = re.sub(r'endpoint:\s*"[^"]*"', 'endpoint: ""', t)
    return t
edit('assets/stats-config.js', stats_off)
print('kid-clean done')
