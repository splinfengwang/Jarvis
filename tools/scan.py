import os, re, ast

errors = []

# 1. Core routing covers all skills (works for both brief and full)
with open('jarvis/core/JARVIS_CORE.md') as f: core = f.read()
s0 = core.split('## 入口路由')[1] if '## 入口路由' in core else core.split('## 0. 入口路由')[1]
s0 = s0.split('\n##')[0]  # stop at next ## heading
skills_in_core = set(re.findall(r'jarvis-[\w-]+', s0))
actual_skills = {d for d in os.listdir('jarvis/skills') if os.path.isdir(os.path.join('jarvis/skills', d))}
excluded = {'jarvis-knowledge-model'}  # no user trigger, referenced on-demand
for s in actual_skills - skills_in_core - excluded:
    errors.append(f'Core§0 缺 skill: {s}')
for s in skills_in_core - actual_skills:
    errors.append(f'Core§0 引用不存在: {s}')

# 2. Core § refs ≤ 14
for m in re.finditer(r'§(\d+)', core):
    if int(m.group(1)) > 14:
        errors.append(f'Core §{m.group(1)} >14 (旧编号)')

# 3. Skill next_skills all exist
for d in sorted(actual_skills):
    with open(os.path.join('jarvis/skills', d, 'SKILL.md')) as f: sc = f.read()
    ns = sc.split('next_skills:')[1].split('---')[0] if 'next_skills:' in sc else ''
    for t in re.findall(r'-\s*(jarvis-[\w-]+)', ns):
        if t not in actual_skills:
            errors.append(f'{d}: next_skills → 不存在 {t}')

# 4. Skill refs all resolve
for d in sorted(actual_skills):
    with open(os.path.join('jarvis/skills', d, 'SKILL.md')) as f: sc = f.read()
    refs = re.findall(r'`(jarvis/[^`]+\.(?:md|py))`', sc)
    refs += re.findall(r'`(plugins/[^`]+\.md)`', sc)
    refs += re.findall(r'`(jarvis-knowledge-model)`', sc)
    for ref in refs:
        if ref == 'jarvis-knowledge-model':
            if not os.path.exists('jarvis/skills/jarvis-knowledge-model/SKILL.md'):
                errors.append(f'{d}: ref jarvis-knowledge-model not found')
        elif not os.path.exists(ref):
            errors.append(f'{d}: broken ref {ref}')

# 5. Version consistency
with open('jarvis/__init__.py') as f:
    m = re.search(r'__version__\s*=\s*"([^"]*)"', f.read())
    ver = m.group(1) if m else None
for check, label in [('jarvis/core/JARVIS_CORE.md', 'Core'), ('install.sh', 'install.sh')]:
    with open(check) as f: c = f.read()
    if ver and ver not in c:
        errors.append(f'{label}: version {ver} not found')

# 6. AGENT_v3.4 historical check
with open('jarvis/AGENT_v3.4.md') as f: v34 = f.read()
if '历史参考' not in v34[:500]:
    errors.append('AGENT_v3.4: 缺历史参考声明')

# 7. Bootstrap consistency
with open('jarvis/core/JARVIS_BOOTSTRAP.md') as f: bs = f.read()
if '回退' in bs and 'AGENT_v3' in bs and '历史参考' not in bs:
    errors.append('Bootstrap: 仍将 AGENT_v3.4 当回退')

# 8. Template variable check — CLI templates (CLAUDE.md.tmpl) handled by cli.py
# install.sh has its own inline templates for wiki/术语/仪表盘/log
for tmpl in ['jarvis/templates/settings.json.tmpl']:
    if not os.path.exists(tmpl): continue
    with open(tmpl) as f: tc = f.read()
    with open('install.sh') as f: inst = f.read()
    for v in re.findall(r'\{\{(\w+)\}\}', tc):
        if v not in inst:
            errors.append(f'{tmpl}: var {{{{{v}}}}} not in install.sh')

# 9. Jarvis.yaml template keys
with open('install.sh') as f: inst = f.read()
# Find the YAML heredoc — skip past "<< YAML_EOF" line
yaml_start = inst.find('<< YAML_EOF')
if yaml_start > 0:
    yaml_block = inst[yaml_start+11:].split('YAML_EOF')[0]
else:
    yaml_block = ''
for key in ['jarvis_version', 'jarvis_home', 'paths', 'knowledge_base', 'wiki_index',
            'terms_dir', 'terms_index', 'business_dir', 'ops_dir', 'dashboard', 'log', 'topics',
            'plugins', 'backend']:
    if key not in yaml_block:
        errors.append(f'install.sh jarvis.yaml: 缺 {key}')

# 10. §3.x section refs
for ref in ['§3 事实口径', '§9 知识引用标注', '§11 知识捕获', '§8 会话模式', '§6 写入裁决']:
    if ref not in core:
        errors.append(f'Core §3.x: 缺引用 {ref}')

print(f"Dimensions: 10, Errors: {len(errors)}")
for e in errors: print(f"  FAIL {e}")
if not errors: print("  ALL CLEAN")
