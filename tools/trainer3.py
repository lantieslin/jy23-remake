#!/usr/bin/env python3
"""jy3 存檔修改器 (CLI)。讀寫 JY1.sol(JY2/JY3 同格式),stdlib only。
用量:
  trainer3.py list [--slot 1|2|3] [--file PATH] [路徑]
  trainer3.py get <路徑> [...]            # 如 m.4 / Hp / x.139 / v.37
  trainer3.py set <路徑> <值> [...]       # 數字鍵給數字,文字鍵給文字
  trainer3.py setname <姓> <名> [自創武學名] [...]
  trainer3.py jingmai [...]               # 經脈全通(n.*=1)
  trainer3.py additem <物品id> <數量> [...] # 背包加一格(f)+數量(g)
  trainer3.py addskill <系o/p/q/r/s/t/u/v_1/w> <武功id> [...]
  trainer3.py teammate <槽位52-55> <NPC代號> [...]
  trainer3.py ref [m|items|skills|npc]
路徑用點分隔(m.4, x.139, f.0, g.29, n.12, Hp)。改前自動備份,寫完回讀驗證。
重要:改檔前先關遊戲,改完進遊戲讀檔驗收。
"""
import sys
import os
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from amf import Sol, fmt, pkg_root  # noqa: E402
import jy3ref as R  # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

DEF_SAVE = os.path.join(pkg_root(), 'save', 'localhost')
ROOTS = {1: 'JY1.sol', 2: 'JY2.sol', 3: 'JY3.sol'}


def resolve(args):
    if args.file:
        return args.file
    if not os.path.isdir(DEF_SAVE):
        sys.exit('找不到存檔目錄,請用 --file 指定')
    if args.slot:
        p = os.path.join(DEF_SAVE, ROOTS[args.slot])
        if not os.path.isfile(p):
            sys.exit('slot%s 無存檔' % args.slot)
        return p
    p = os.path.join(DEF_SAVE, 'JY1.sol')
    if os.path.isfile(p):
        return p
    sys.exit('請用 --slot 1|2|3 或 --file 指定')


def split(path):
    return path.split('.')


def shownode(sol, node, name=''):
    if node.kind in ('O', 'A', 'L'):
        print('%s<%s len=%d>' % (name, node.kind, len(node.kids)))
        return
    print('%s=%s' % (name, fmt(node.val)))


def cmd_list(sol, path=None):
    if not path:
        print('%s : %d keys' % (os.path.basename(sol.path), len(sol.entries)))
        for k, nd in sol.entries:
            extra = ' len=%d' % len(nd.kids) if nd.kind in ('O', 'A', 'L') else '=%s' % fmt(nd.val)
            print('%-6s %s%s' % (k, nd.kind, extra))
        return
    parts = split(path)
    top = None
    for k, nd in sol.entries:
        if k == parts[0]:
            top = nd
            break
    if top is None:
        sys.exit('無此鍵')
    if top.kind not in ('O', 'A', 'L'):
        shownode(sol, top, path)
        return
    kids = top.kids if top.kind == 'L' else top.kids
    for kk, nd in (enumerate(kids) if top.kind == 'L' else kids):
        key = str(kk)
        disp = ''
        if parts[0] == 'm' and key.isdigit() and int(key) in R.M_TABLE:
            disp = R.M_TABLE[int(key)]
        elif parts[0] in R.SKILLS and key.isdigit() and int(key) in R.SKILLS[parts[0]]:
            disp = R.SKILLS[parts[0]][int(key)]
        elif parts[0] == 'f' and nd.kind == 'N' and int(nd.val) in R.ITEMS:
            disp = R.ITEMS[int(nd.val)]
        if nd.kind == 'N' and nd.val == 0 and parts[0] in ('v', 'x', 'g', 'n'):
            continue  # 0 太多,只看非零
        print('%-8s %-12s %s' % (key, disp, fmt(nd.val) if nd.kind in ('N', 'B', 'S') else '<%s>' % nd.kind))


def backup(path):
    bak = '%s.bak.%d' % (path, int(time.time()))
    shutil.copyfile(path, bak)
    return bak


def cmd_set(sol, path, text):
    parts = split(path)
    nd = sol.get(parts)
    bak = backup(sol.path)
    if nd.kind == 'N':
        try:
            nv = float(text)
            sol.set_number(nd, nv)
            show = fmt(nv)
        except ValueError:
            sol.replace(nd, 'S', text)  # 如 m.3 經驗封頂字串
            show = text
    elif nd.kind == 'B':
        if text not in ('0', '1'):
            sys.exit('請給 0/1')
        sol.raw[nd.vpos] = int(text)
        show = text
    elif nd.kind == 'S':
        sol.set_string(nd, text)
        show = text
    sol.save()
    print('OK %s=%s  備份:%s' % (path, show, bak))
    print('進遊戲讀檔驗收。')


def cmd_setname(sol, xing, ming, zc=None):
    bak = backup(sol.path)
    for key, val in (('1', xing), ('2', ming)):
        nd = sol.get(['m', key])
        if nd.kind != 'S':
            sys.exit('m.%s 不是文字' % key)
        sol.set_string(nd, val)
    nd50 = sol.get(['m', '50'])
    if zc is not None:
        if nd50.kind == 'S':
            sol.set_string(nd50, zc)
        else:
            sol.replace(nd50, 'S', zc)  # 新開局 m.50 是數字 0，直接換型別
    sol.save()
    print('OK 姓=%s 名=%s%s  備份:%s' % (xing, ming, ' 自創=%s' % zc if zc else '', bak))
    print('進遊戲讀檔驗收。')


def cmd_jingmai(sol):
    n = None
    for k, nd in sol.entries:
        if k == 'n':
            n = nd
            break
    if n is None or n.kind not in ('O', 'A'):
        sys.exit('無 n 表')
    bak = backup(sol.path)
    c = 0
    for k, nd in n.kids:
        if nd.kind == 'N' and nd.val == 0:
            sol.set_number(nd, 1)
            c += 1
    sol.save()
    print('OK 經脈 %d 處 0→1  備份:%s' % (c, bak))
    print('進遊戲讀檔驗收。')


def next_key(node):
    mx = -1
    for k, nd in node.kids:
        if str(k).isdigit():
            mx = max(mx, int(k))
    return str(mx + 1)


def cmd_additem(sol, iid, cnt):
    iid, cnt = int(iid), int(cnt)
    bak = backup(sol.path)
    f = sol.get(['f'])
    g = sol.get(['g'])
    sol.object_set(f, next_key(f), 'N', iid)
    try:
        old = sol.get(['g', str(iid)])
        if old.kind == 'N':
            sol.set_number(old, max(old.val, cnt))
        else:
            sol.object_set(g, str(iid), 'N', cnt)
    except KeyError:
        g = sol.get(['g'])
        sol.object_set(g, str(iid), 'N', cnt)
    sol.save()
    print('OK 背包+%s x%s  備份:%s' % (R.ITEMS.get(iid, iid), cnt, bak))
    print('進遊戲讀檔驗收。')


def cmd_addskill(sol, cat, sid):
    if cat not in R.SKILLS:
        sys.exit('系須為 o/p/q/r/s/t/u/v_1/w')
    sid = int(sid)
    name = R.SKILLS[cat].get(sid, sid)
    bak = backup(sol.path)
    lst = sol.get([cat])
    for k, nd in lst.kids:
        if nd.kind == 'N' and nd.val == sid:
            print('已擁有 %s,不重複加  備份:%s' % (name, bak))
            return
    sol.object_set(lst, next_key(lst), 'N', sid)
    sol.save()
    print('OK %s系+%s  記得再設等級(x.%s)與經驗(v.%s)  備份:%s'
          % (cat, name, sid, sid, bak))
    print('進遊戲讀檔驗收。')


def cmd_teammate(sol, slot, npc):
    if slot not in ('52', '53', '54', '55'):
        sys.exit('槽位須為 52/53/54/55')
    npc = int(npc)
    bak = backup(sol.path)
    sol.set_number(sol.get(['m', slot]), npc)
    sol.save()
    print('OK 隊友%s=%s  備份:%s' % (slot, R.NPC.get(npc, npc), bak))
    print('進遊戲讀檔驗收。')


def cmd_ref(what):
    if what in ('m', None) and what != 'items' and what != 'skills' and what != 'npc':
        for k in sorted(R.M_TABLE):
            print('m.%-4d %s' % (k, R.M_TABLE[k]))
    if what in ('items', None):
        for k in sorted(R.ITEMS):
            print('%-4d %s' % (k, R.ITEMS[k]))
    if what in ('skills', None):
        for c, tbl in R.SKILLS.items():
            for k in sorted(tbl):
                print('%-4s %-4d %s' % (c, k, tbl[k]))
    if what in ('npc', None):
        for k in sorted(R.NPC):
            print('%-4d %s' % (k, R.NPC[k]))


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description='jy3 存檔修改器')
    c = argparse.ArgumentParser(add_help=False)
    c.add_argument('--slot', type=int, choices=(1, 2, 3))
    c.add_argument('--file')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('list', parents=[c]); p.add_argument('path', nargs='?')
    p = sub.add_parser('get', parents=[c]); p.add_argument('path')
    p = sub.add_parser('set', parents=[c]); p.add_argument('path'); p.add_argument('value')
    p = sub.add_parser('setname', parents=[c]); p.add_argument('xing'); p.add_argument('ming'); p.add_argument('zc', nargs='?')
    p = sub.add_parser('jingmai', parents=[c])
    p = sub.add_parser('additem', parents=[c]); p.add_argument('iid'); p.add_argument('cnt')
    p = sub.add_parser('addskill', parents=[c]); p.add_argument('cat'); p.add_argument('sid')
    p = sub.add_parser('teammate', parents=[c]); p.add_argument('slot'); p.add_argument('npc')
    p = sub.add_parser('ref'); p.add_argument('what', nargs='?', choices=('m', 'items', 'skills', 'npc'))
    a = ap.parse_args(argv)
    if a.cmd == 'ref':
        return cmd_ref(a.what)
    from amf import Sol as _S
    s = _S(resolve(a))
    if a.cmd == 'list':
        cmd_list(s, a.path)
    elif a.cmd == 'get':
        nd = s.get(split(a.path))
        shownode(s, nd, a.path)
    elif a.cmd == 'set':
        cmd_set(s, a.path, a.value)
    elif a.cmd == 'setname':
        cmd_setname(s, a.xing, a.ming, a.zc)
    elif a.cmd == 'jingmai':
        cmd_jingmai(s)
    elif a.cmd == 'additem':
        cmd_additem(s, a.iid, a.cnt)
    elif a.cmd == 'addskill':
        cmd_addskill(s, a.cat, a.sid)
    elif a.cmd == 'teammate':
        cmd_teammate(s, a.slot, a.npc)


if __name__ == '__main__':
    main(sys.argv[1:])
