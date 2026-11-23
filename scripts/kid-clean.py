#!/usr/bin/env python3
"""孩子自用版清理：幂等，可在每次同步上游后重复运行。
- 去掉各页顶部跳外部测评站 test.pansgo.com 的横幅
- 去掉首页智商测试卡片、诊断结果页的测评链接段
- 关闭统计上报（endpoint 清空，不向原作者的统计端发数据）
- 分享图二维码指向本站
- 去掉首页导航跳 pansgo.com 的「资源搜索」外链（网盘搜索）
- 去掉各页「学习好物」购物入口并删除 goods/ 商品页（京东推广）
- 兜底修复：结果页 renderResult 若丢了 show(page) 调用则补回（丢了会卡在最后一题、点「下一题」无反应）
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

ALL_PAGES = ['index.html','explore/index.html','diagnose/index.html','children/index.html','children/history.html','english/index.html','finals/index.html','wrongbook/index.html','vocab/index.html']
for rel in ALL_PAGES:
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
# 「学习好物」购物入口（各页导航 + 首页大按钮）与商品页本体
for rel in ALL_PAGES:
    edit(rel, lambda t: re.sub(r'\s*<a[^>]*href="(?:\.\./)?goods/"[^>]*>.*?</a>', '', t, flags=re.S))
goods_dir = root / 'goods'
if goods_dir.is_dir():
    import shutil
    shutil.rmtree(goods_dir)
    print('removed goods/')

# 结果页兜底：renderResult 结尾必须有 show(page) + mountPathGraph(sum)
def fix_result(t):
    i = t.find('function renderResult()')
    if i < 0: return t
    j = t.find('page.append(logCard());', i)
    if j < 0: return t
    tail = t[j:j+300]
    if 'show(page)' in tail: return t
    k = t.find('\n', j)
    return t[:k+1] + '    show(page);\n    mountPathGraph(sum);\n' + t[k+1:]
edit('diagnose/app.js', fix_result)

# 每日一句（english/app.js）可用性修复：上游原版里「猜出意思」只能靠展开第 2 步翻译层打勾，
# 打卡条本身点不动、「完成今日一句」未集齐三项时是禁用态、点了毫无提示，孩子会以为坏了。
# 孩子版改为：打卡条可点（未完成项点击后滚动到对应步骤；「猜出意思」还会顺手打开第一层翻译），
# 完成按钮不再禁用，未集齐时点击会写明还差哪项、怎么做。
def fix_daily(t):
    if 'finishHint' in t: return t
    a1 = "      checkEls[c[0]] = { node: s, label: c[1] };\n      checkBox.appendChild(s);"
    b1 = ("      checkEls[c[0]] = { node: s, label: c[1] };\n"
          "      s.addEventListener('click', function () {\n"
          "        if (checks[c[0]]) return;\n"
          "        var target = c[0] === 'guess' ? trans : (c[0] === 'order' ? sortBox.node : opts);\n"
          "        if (target && target.scrollIntoView) target.scrollIntoView({ behavior: 'smooth', block: 'center' });\n"
          "        if (c[0] === 'guess') { var sm = trans.querySelector('details:not([open]) summary'); if (sm) setTimeout(function () { sm.click(); }, 350); }\n"
          "      });\n"
          "      checkBox.appendChild(s);")
    if a1 not in t: return t
    t = t.replace(a1, b1, 1)
    a2 = "    var finishBtn = btn('完成今日一句', 'primary finish', function () { if (EN.checksComplete(checks)) onDone(checks); });\n    finishBtn.disabled = true;\n    if (mode !== 'revisit') card.appendChild(finishBtn);"
    b2 = ("    var finishHint = el('p', 'finish-hint muted', '');\n"
          "    var finishBtn = btn('完成今日一句', 'primary finish', function () {\n"
          "      if (EN.checksComplete(checks)) { onDone(checks); return; }\n"
          "      var miss = [];\n"
          "      if (!checks.guess) miss.push('「猜出意思」：点上面的○猜出意思，或打开第 2 步任意一层翻译');\n"
          "      if (!checks.order) miss.push('「排序正确」：完成第 5 步词卡排序');\n"
          "      if (!checks.build) miss.push('「完成造句」：完成第 6 步换词造句');\n"
          "      finishHint.textContent = '还差 ' + miss.join('；');\n"
          "    });\n"
          "    if (mode !== 'revisit') { card.appendChild(finishBtn); card.appendChild(finishHint); }")
    if a2 not in t: return t
    t = t.replace(a2, b2, 1)
    t = t.replace("      finishBtn.disabled = !EN.checksComplete(checks);",
                  "      if (EN.checksComplete(checks)) finishHint.textContent = '三项都完成了，点「完成今日一句」打卡。';", 1)
    return t
edit('english/app.js', fix_daily)
# 课外工具箱入口（PhET / GeoGebra / Qwerty Learner）：同步后若被上游覆盖则补回，幂等
TOOLS_BLOCK = """
  <!-- kid-tools -->
  <h2 class="section-title">课外工具箱</h2>
  <div class="stat-grid">
    <a class="stat-card" href="https://phet.colorado.edu/zh_CN/" target="_blank" rel="noopener noreferrer"><div class="stat-num">🧪 PhET</div><div class="stat-label">互动仿真实验：物理 · 化学 · 生物 · 数学，拖一拖就懂（中文）</div></a>
    <a class="stat-card" href="https://www.geogebra.org/classic" target="_blank" rel="noopener noreferrer"><div class="stat-num">📐 GeoGebra</div><div class="stat-label">几何与函数动态绘图：初中几何 · 高中函数</div></a>
    <a class="stat-card" href="https://qwerty.kaiyi.cool/" target="_blank" rel="noopener noreferrer"><div class="stat-num">⌨️ Qwerty Learner</div><div class="stat-label">打字背单词：选中考 / 高考词库，接键盘练</div></a>
    <a class="stat-card" href="english/"><div class="stat-num">🇬🇧 英语精选</div><div class="stat-label">Awesome English 精选版：听力 · 视频 · 阅读 · 语法 · 词汇，中文导航、已过滤成人与社交类</div></a>
    <a class="stat-card" href="https://xckevin.github.io/magic-english-buddy/" target="_blank" rel="noopener noreferrer"><div class="stat-num">🧙 Magic English Buddy</div><div class="stat-label">分级阅读跟读：L1–L7 共 90 篇故事，逐词高亮朗读、点词查词，在设置里下载音频后可离线</div></a>
  </div>
  <p class="stat-note">PhET / GeoGebra / Qwerty Learner / Magic English Buddy 是站外工具，点开会在新页面打开；英语精选是本站内页。Qwerty Learner 需要键盘，平板接上键盘后使用。</p>
"""
def add_tools(t):
    if 'kid-tools' in t: return t
    anchor = '  <div class="grade-grid" id="grades" aria-busy="true"></div>\n'
    if anchor not in t: return t
    return t.replace(anchor, anchor + TOOLS_BLOCK, 1)
edit('index.html', add_tools)
print('kid-clean done')

# 英语精选入口：工具箱已存在但缺英语卡时补卡（幂等）；english/ 精选页为本站新增目录，上游没有、不受同步影响
ENG_CARD = '    <a class="stat-card" href="english/"><div class="stat-num">🇬🇧 英语精选</div><div class="stat-label">Awesome English 精选版：听力 · 视频 · 阅读 · 语法 · 词汇，中文导航、已过滤成人与社交类</div></a>\n'
def add_eng_card(t):
    if 'href="english/"' in t: return t
    anchor = '打字背单词：选中考 / 高考词库，接键盘练</div></a>\n'
    if anchor not in t: return t
    return t.replace(anchor, anchor + ENG_CARD, 1)
edit('index.html', add_eng_card)
edit('index.html', lambda t: t.replace('以上是站外工具，点开会在新页面打开；Qwerty Learner 需要键盘，平板接上键盘后使用。', 'PhET / GeoGebra / Qwerty Learner 是站外工具，点开会在新页面打开；英语精选是本站内页。Qwerty Learner 需要键盘，平板接上键盘后使用。'))

# Magic English Buddy 入口：工具箱已有英语精选卡但缺 Buddy 卡时补卡（幂等）
BUDDY_CARD = '    <a class="stat-card" href="https://xckevin.github.io/magic-english-buddy/" target="_blank" rel="noopener noreferrer"><div class="stat-num">🧙 Magic English Buddy</div><div class="stat-label">分级阅读跟读：L1–L7 共 90 篇故事，逐词高亮朗读、点词查词，在设置里下载音频后可离线</div></a>\n'
def add_buddy_card(t):
    if 'magic-english-buddy' in t: return t
    anchor = '中文导航、已过滤成人与社交类</div></a>\n'
    if anchor not in t: return t
    return t.replace(anchor, anchor + BUDDY_CARD, 1)
edit('index.html', add_buddy_card)
edit('index.html', lambda t: t.replace('PhET / GeoGebra / Qwerty Learner 是站外工具，点开会在新页面打开；英语精选是本站内页。Qwerty Learner 需要键盘，平板接上键盘后使用。', 'PhET / GeoGebra / Qwerty Learner / Magic English Buddy 是站外工具，点开会在新页面打开；英语精选是本站内页。Qwerty Learner 需要键盘，平板接上键盘后使用。'))
