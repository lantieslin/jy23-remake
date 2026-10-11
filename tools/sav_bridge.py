#!/usr/bin/env python3
"""jy2→jy3 繼承轉換橋。原版在線才有繼承邏輯,離線包無此代碼,故自實現。
規則(用戶核定的原版邏輯):
  基礎: 力道m16/根骨m17/悟性m18/福緣m19/靈敏m20 +10; 修為m5 +10;
        拳掌m22/彈指m23/御劍m24/耍刀m25/舞棍m26/內功m27 +5; 金錢m110 +1000
  武功: 已擁有武功經驗 v[id] +35(只加已存在的,不憑空建)
  內功: 龜息功134 入u表; x.134=max(,1)
  武器: 背包+f(2木劍/30菜刀/56木棍/63飛鏢); g.2/30/56=max(,1), g.63=max(,100)
  防具: 背包+f(73皮甲); g.73=max(,1)
用法:
  sav_bridge.py inherit [--jy2slot 1|2|3] [--jy2file P] [--jy3slot 1|2|3]
    [--skip-skills] [--skip-neigong] [--skip-weapons] [--skip-armor] [--yes]
  預設只預覽;加 --yes 才寫入。jy2 存檔僅作存在性見證(加成數固定)。
  目標須是新開局存過一次的 JY 槽,且只用一次(重複用會疊加)。
"""
import sys
import os
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from amf import Sol, fmt, pkg_root  # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PKG_SAVE = os.path.join(pkg_root(), 'save', 'localhost')
OLD_BASE = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'ruffle', 'SharedObjects')
JY2ROOTS = {1: 'gamezly.sol', 2: 'gamelzy.sol', 3: 'gameylz.sol'}
SKILL_CATS = ('o', 'p', 'q', 'r', 's', 't', 'u', 'v_1', 'w')


def find_jy2(slot):
    cands = []
    for base in (PKG_SAVE, OLD_BASE):
        for dp, dn, fn in os.walk(base):
            if JY2ROOTS[slot] in fn:
                cands.append(os.path.join(dp, JY2ROOTS[slot]))
    if not cands:
        sys.exit('找不到 jy2 slot%s 存檔' % slot)
    cands.sort(key=os.path.getmtime, reverse=True)
    return cands[0]


def getnum(sol, path, default=None):
    try:
        nd = sol.get(path)
    except KeyError:
        return default
    return nd.val if nd.kind == 'N' else default


def addnum(sol, path, delta, create=0):
    try:
        nd = sol.get(path)
    except KeyError:
        return None
    if nd.kind != 'N':
        return None
    nv = nd.val + delta
    sol.set_number(nd, nv)
    return nv


def next_key(node):
    mx = -1
    for k, nd in node.kids:
        if str(k).isdigit():
            mx = max(mx, int(k))
    return str(mx + 1)


def cmd_inherit(a):
    sys.path.insert(0, HERE)
    import trainer as T
    jy2p = a.jy2file or find_jy2(a.jy2slot)
    j2 = T.Sol(jy2p)  # 存在性＋可解析見證
    lv = j2.entries.get('LV', {}).get('val', '?')
    print('jy2 見證: %s LV=%s' % (jy2p, T.Sol.fmt(j2, lv) if not isinstance(lv, str) else lv))
    tp = a.jy3file or os.path.join(PKG_SAVE, 'JY%s.sol' % a.jy3slot)
    if not os.path.isfile(tp):
        sys.exit('jy3 目標無存檔:請先新開局並存檔一次 (%s)' % tp)
    s = Sol(tp)
    plan = []
    m = s.get(['m'])
    for i in (16, 17, 18, 19, 20):
        plan.append(('m.%d +10' % i, lambda i=i: addnum(s, ['m', str(i)], 10)))
    plan.append(('m.5 +10', lambda: addnum(s, ['m', '5'], 10)))
    for i in (22, 23, 24, 25, 26, 27):
        plan.append(('m.%d +5' % i, lambda i=i: addnum(s, ['m', str(i)], 5)))
    plan.append(('m.110 +1000', lambda: addnum(s, ['m', '110'], 1000)))
    if not a.skip_skills:
        owned = set()
        for c in SKILL_CATS:
            try:
                lst = s.get([c])
            except KeyError:
                continue
            if lst.kind not in ('O', 'A'):
                continue
            for k, nd in lst.kids:
                if nd.kind == 'N':
                    owned.add(int(nd.val))
        v = s.get(['v'])
        n = 0
        for sid in sorted(owned):
            try:
                nd = s.get(['v', str(sid)])
            except KeyError:
                continue
            if nd.kind == 'N':
                plan.append(('v.%d +35' % sid, lambda nd=nd: (s.set_number(nd, nd.val + 35), nd.val + 35)[1]))
                n += 1
        print('武功經驗: %d 個已擁有武功 v.+35' % n)
    if not a.skip_neigong:
        def _ng():
            u = s.get(['u'])
            has = any(nd.kind == 'N' and nd.val == 134 for k, nd in u.kids)
            if not has:
                s.object_set(u, next_key(u), 'N', 134)
            try:
                x = s.get(['x', '134'])
                if x.kind == 'N' and x.val < 1:
                    s.set_number(x, 1)
            except KeyError:
                s.object_set(s.get(['x']), '134', 'N', 1)
            return 'ok'
        plan.append(('龜息功134入u, x.134=1', _ng))
    def fin(item):
        lst = s.get(['f'])
        return any(nd.kind == 'N' and nd.val == item for k, nd in lst.kids)

    if not a.skip_weapons:
        def _wp():
            for iid, cnt in ((2, 1), (30, 1), (56, 1), (63, 100)):
                if not fin(iid):
                    s.object_set(s.get(['f']), next_key(s.get(['f'])), 'N', iid)
                try:
                    old = s.get(['g', str(iid)])
                    if old.kind == 'N' and old.val < cnt:
                        s.set_number(old, cnt)
                except KeyError:
                    s.object_set(s.get(['g']), str(iid), 'N', cnt)
            return 'ok'
        plan.append(('武器2/30/56/63入f, g計數', _wp))
    if not a.skip_armor:
        def _ar():
            if not fin(73):
                s.object_set(s.get(['f']), next_key(s.get(['f'])), 'N', 73)
            try:
                old = s.get(['g', '73'])
                if old.kind == 'N' and old.val < 1:
                    s.set_number(old, 1)
            except KeyError:
                s.object_set(s.get(['g']), '73', 'N', 1)
            return 'ok'
        plan.append(('皮甲73入f, g.73=1', _ar))
    print('目標: %s,共 %d 項' % (tp, len(plan)))
    if not a.yes:
        print('預覽模式(加 --yes 才寫入)。前5項:')
        for name, fn in plan[:5]:
            print('  ', name)
        print('  ...')
        return
    bak = '%s.bak.%d' % (tp, int(time.time()))
    shutil.copyfile(tp, bak)
    for name, fn in plan:
        try:
            r = fn()
            print('OK %-18s -> %s' % (name, r if r != 'ok' else 'ok'))
        except Exception as e:
            print('FAIL %s: %r (檔已備份,中斷)' % (name, e))
            print('備份:%s' % bak)
            return
    s.save()
    print('寫入完成 備份:%s' % bak)
    print('進遊戲讀檔驗收(只對新開局用一次,重複會疊加)。')


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description='jy2→jy3 繼承轉換橋')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('inherit')
    p.add_argument('--jy2slot', type=int, default=1, choices=(1, 2, 3))
    p.add_argument('--jy2file')
    p.add_argument('--jy3slot', type=int, default=1, choices=(1, 2, 3))
    p.add_argument('--jy3file')
    p.add_argument('--skip-skills', action='store_true')
    p.add_argument('--skip-neigong', action='store_true')
    p.add_argument('--skip-weapons', action='store_true')
    p.add_argument('--skip-armor', action='store_true')
    p.add_argument('--yes', action='store_true')
    a = ap.parse_args(argv)
    if a.cmd == 'inherit':
        cmd_inherit(a)


if __name__ == '__main__':
    main(sys.argv[1:])
