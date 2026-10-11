#!/usr/bin/env python3
"""金庸群俠傳3 修改器＋繼承 GUI (tkinter, stdlib only)。引擎: amf。"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from amf import Sol, fmt, pkg_root  # noqa: E402
import jy3ref as R  # noqa: E402

DEF_SAVE = os.path.join(pkg_root(), 'save', 'localhost')
ROOTS = {1: 'JY1.sol', 2: 'JY2.sol', 3: 'JY3.sol'}
CAT_CN = {'o': '掌拳', 'p': '指法', 'q': '劍法', 'r': '刀法', 's': '棍法',
          't': '暗器', 'u': '內功', 'v_1': '輕功', 'w': '其他'}
CATS = ['o', 'p', 'q', 'r', 's', 't', 'u', 'v_1', 'w']


def catlabel(c):
    return '%s (%s)' % (CAT_CN[c], c)


def cat_of(label):
    if '(' in label and label.endswith(')'):
        return label.rsplit('(', 1)[1][:-1]
    return label
MATTRS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
          30, 31, 32, 33, 34, 35, 36, 37]


def next_key(node):
    mx = -1
    for k, nd in node.kids:
        if str(k).isdigit():
            mx = max(mx, int(k))
    return str(mx + 1)


class App:
    def __init__(self, root):
        self.root = root
        root.title('金庸群俠傳3 修改器＋繼承')
        self.slot = tk.IntVar(value=1)
        self.status = tk.StringVar(value='就緒')
        bar = ttk.Frame(root)
        bar.pack(fill='x', padx=8, pady=6)
        ttk.Label(bar, text='存檔').pack(side='left')
        ttk.OptionMenu(bar, self.slot, 1, 1, 2, 3,
                       command=lambda *_: self.refresh()).pack(side='left', padx=4)
        ttk.Button(bar, text='重新讀取', command=self.refresh).pack(side='left')
        ttk.Button(bar, text='啟動遊戲', command=self.launch).pack(side='right')
        self.info = tk.StringVar()
        ttk.Label(bar, textvariable=self.info).pack(side='right', padx=8)
        nb = ttk.Notebook(root)
        nb.pack(fill='both', expand=True, padx=8)
        # 基本
        p1 = ttk.Frame(nb)
        nb.add(p1, text='基本')
        self.v_basic = {}
        for i, (k, name) in enumerate([('1', '姓 m.1'), ('2', '名 m.2'),
                                       ('50', '自創武學名 m.50'), ('4', '等級 m.4'),
                                       ('3', '經驗 m.3'), ('5', '修為點 m.5'),
                                       ('110', '金錢 m.110')]):
            ttk.Label(p1, text=name).grid(row=i // 2, column=(i % 2) * 2, sticky='e', padx=4, pady=3)
            v = tk.StringVar()
            ttk.Entry(p1, textvariable=v, width=22).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky='w')
            self.v_basic[k] = v
        self.v_hp = tk.StringVar()
        self.v_mp = tk.StringVar()
        ttk.Label(p1, text='生命 Hp').grid(row=4, column=0, sticky='e', padx=4, pady=3)
        ttk.Entry(p1, textvariable=self.v_hp, width=22).grid(row=4, column=1, sticky='w')
        ttk.Label(p1, text='內力 Mp').grid(row=4, column=2, sticky='e', padx=4, pady=3)
        ttk.Entry(p1, textvariable=self.v_mp, width=22).grid(row=4, column=3, sticky='w')
        ttk.Button(p1, text='套用基本', command=self.apply_basic).grid(row=5, column=1, sticky='w', pady=6)
        # 屬性
        p2 = ttk.Frame(nb)
        nb.add(p2, text='屬性')
        self.v_attr = {}
        for i, idx in enumerate(MATTRS):
            name = R.M_TABLE.get(idx, str(idx))
            ttk.Label(p2, text='m.%d %s' % (idx, name)).grid(row=i // 4, column=(i % 4) * 2, sticky='e', padx=2, pady=2)
            v = tk.StringVar()
            ttk.Entry(p2, textvariable=v, width=10).grid(row=i // 4, column=(i % 4) * 2 + 1, sticky='w')
            self.v_attr[idx] = v
        ttk.Button(p2, text='套用屬性', command=self.apply_attr).grid(row=5, column=1, sticky='w', pady=6)
        # 武功
        p3 = ttk.Frame(nb)
        nb.add(p3, text='武功')
        ttk.Label(p3, text='系').grid(row=0, column=0, sticky='e')
        self.cat = tk.StringVar(value=catlabel('q'))
        ttk.OptionMenu(p3, self.cat, catlabel('q'),
                       *[catlabel(c) for c in CATS],
                       command=lambda *_: self.skill_names()).grid(row=0, column=1, sticky='w')
        ttk.Label(p3, text='武功').grid(row=0, column=2, sticky='e')
        self.sid = tk.StringVar()
        self.skill_menu = ttk.OptionMenu(p3, self.sid, '')
        self.skill_menu.grid(row=0, column=3, sticky='w')
        self.owned = tk.BooleanVar(value=True)
        ttk.Checkbutton(p3, text='已擁有', variable=self.owned).grid(row=0, column=4, padx=6)
        self.s_lv = tk.StringVar()
        self.s_exp = tk.StringVar()
        ttk.Label(p3, text='等級 x').grid(row=1, column=0, sticky='e')
        ttk.Entry(p3, textvariable=self.s_lv, width=10).grid(row=1, column=1, sticky='w')
        ttk.Label(p3, text='經驗 v').grid(row=1, column=2, sticky='e')
        ttk.Entry(p3, textvariable=self.s_exp, width=10).grid(row=1, column=3, sticky='w')
        ttk.Button(p3, text='讀取', command=self.skill_load).grid(row=1, column=4, padx=6)
        ttk.Button(p3, text='套用武功', command=self.apply_skill).grid(row=2, column=1, sticky='w', pady=6)
        ttk.Label(p3, text='w 系 190 = 左右互搏（jy3 的互搏是武功）；u 139 = 自創').grid(row=3, column=0, columnspan=5, sticky='w', padx=4)
        # 物品
        p4 = ttk.Frame(nb)
        nb.add(p4, text='物品')
        ttk.Label(p4, text='物品').grid(row=0, column=0, sticky='e')
        self.iid = tk.StringVar(value='29')
        names = ['%d %s' % (k, R.ITEMS[k]) for k in sorted(R.ITEMS)]
        ttk.OptionMenu(p4, self.iid, '29 倚天劍', *names).grid(row=0, column=1, sticky='w')
        self.icnt = tk.StringVar(value='1')
        ttk.Label(p4, text='數量').grid(row=0, column=2, sticky='e')
        ttk.Entry(p4, textvariable=self.icnt, width=10).grid(row=0, column=3, sticky='w')
        ttk.Button(p4, text='加入背包', command=self.apply_item).grid(row=0, column=4, padx=6)
        self.baginfo = tk.StringVar()
        ttk.Label(p4, textvariable=self.baginfo).grid(row=1, column=0, columnspan=5, sticky='w', padx=4)
        # 經脈
        p5 = ttk.Frame(nb)
        nb.add(p5, text='經脈')
        self.jm_info = tk.StringVar()
        ttk.Label(p5, textvariable=self.jm_info).pack(anchor='w', padx=8, pady=4)
        ttk.Button(p5, text='一鍵全通', command=self.apply_jm_all).pack(anchor='w', padx=8)
        fr = ttk.Frame(p5)
        fr.pack(anchor='w', padx=8, pady=8)
        ttk.Label(fr, text='逐條').pack(side='left')
        self.jm_idx = tk.StringVar(value='0')
        ttk.OptionMenu(fr, self.jm_idx, '0', *[str(i) for i in range(200)]).pack(side='left', padx=4)
        self.jm_val = tk.BooleanVar()
        ttk.Checkbutton(fr, text='通', variable=self.jm_val).pack(side='left')
        ttk.Button(fr, text='讀取', command=self.jm_load).pack(side='left', padx=4)
        ttk.Button(fr, text='套用', command=self.apply_jm_one).pack(side='left')
        ttk.Label(p5, text='編號 0-199 無官方名稱對照，只能逐號試（全通最省事）').pack(anchor='w', padx=8)
        # 隊友
        p6 = ttk.Frame(nb)
        nb.add(p6, text='隊友')
        self.tm = {}
        npcs = ['%d %s' % (k, R.NPC[k]) for k in sorted(R.NPC)]
        for i, slot in enumerate(('52', '53', '54', '55')):
            ttk.Label(p6, text='隊友 m.%s' % slot).grid(row=i, column=0, sticky='e', padx=4, pady=3)
            v = tk.StringVar()
            ttk.OptionMenu(p6, v, '', '', *npcs).grid(row=i, column=1, sticky='w')
            self.tm[slot] = v
        ttk.Button(p6, text='套用隊友', command=self.apply_tm).grid(row=4, column=1, sticky='w', pady=6)
        ttk.Label(p6, text='非隊友 NPC 改入戰鬥無圖，後果自負').grid(row=5, column=0, columnspan=2, sticky='w', padx=4)
        # 繼承
        p7 = ttk.Frame(nb)
        nb.add(p7, text='繼承')
        ttk.Label(p7, text='jy2 見證檔').grid(row=0, column=0, sticky='e', padx=4, pady=3)
        self.jy2slot = tk.IntVar(value=1)
        ttk.OptionMenu(p7, self.jy2slot, 1, 1, 2, 3).grid(row=0, column=1, sticky='w')
        self.f_base = tk.BooleanVar(value=True)
        self.f_skill = tk.BooleanVar(value=True)
        self.f_ng = tk.BooleanVar(value=True)
        self.f_eq = tk.BooleanVar(value=True)
        for i, (v, t) in enumerate([(self.f_base, '基礎(+10/+5/+1000)'), (self.f_skill, '武功經驗+35'),
                                    (self.f_ng, '龜息功'), (self.f_eq, '武器防具')]):
            ttk.Checkbutton(p7, text=t, variable=v).grid(row=1 + i // 2, column=i % 2, sticky='w', padx=8)
        ttk.Button(p7, text='執行繼承', command=self.apply_inherit).grid(row=3, column=0, pady=8)
        ttk.Label(p7, text='只對新開局用一次（重複會疊加）；執行前自動備份').grid(row=3, column=1, sticky='w')
        ttk.Label(root, textvariable=self.status).pack(anchor='w', padx=8, pady=4)
        self.refresh()

    def path(self):
        p = os.path.join(DEF_SAVE, ROOTS[self.slot.get()])
        if not os.path.isfile(p):
            raise FileNotFoundError('slot%s 無存檔' % self.slot.get())
        return p

    def refresh(self):
        try:
            s = Sol(self.path())
        except Exception as e:
            self.status.set(str(e))
            return
        m = s.get(['m'])
        for k, v in self.v_basic.items():
            try:
                nd = s.get(['m', k])
                v.set(fmt(nd.val) if nd.kind in ('N', 'S') else '')
            except KeyError:
                v.set('')
        for idx, v in self.v_attr.items():
            try:
                nd = s.get(['m', str(idx)])
                v.set(fmt(nd.val) if nd.kind == 'N' else '')
            except KeyError:
                v.set('')
        for var, key in ((self.v_hp, 'Hp'), (self.v_mp, 'Mp')):
            try:
                var.set(fmt(s.get([key]).val))
            except KeyError:
                var.set('')
        try:
            self.info.set('等級 %s · %s%s' % (fmt(s.get(['m', '4']).val), s.get(['m', '1']).val, s.get(['m', '2']).val))
        except KeyError:
            self.info.set('')
        self.skill_names()
        self.skill_load()
        try:
            f = s.get(['f'])
            self.baginfo.set('背包 %d 格' % len(f.kids))
        except KeyError:
            pass
        self.jm_refresh()
        for slot, v in self.tm.items():
            try:
                nd = s.get(['m', slot])
                cur = int(nd.val) if nd.kind == 'N' else 0
                v.set('%d %s' % (cur, R.NPC.get(cur, '（空）')) if cur else '')
            except KeyError:
                v.set('')
        self.status.set('已讀取 %s' % os.path.basename(s.path))

    def done(self, msg):
        self.status.set(msg)
        self.refresh()

    def apply_basic(self):
        try:
            s = Sol(self.path())
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            for k in ('1', '2', '50'):
                t = self.v_basic[k].get()
                if t == '':
                    continue
                nd = s.get(['m', k])
                if nd.kind != 'S':
                    if k == '50':
                        s.replace(nd, 'S', t)
                    continue
                s.set_string(nd, t)
            for k, var in (('4', None), ('3', None), ('5', None), ('110', None)):
                t = self.v_basic[k].get().strip()
                if t == '':
                    continue
                nd = s.get(['m', k])
                if nd.kind == 'N':
                    try:
                        s.set_number(nd, float(t))
                    except ValueError:
                        s.replace(nd, 'S', t)
                elif nd.kind == 'S':
                    s.set_string(nd, t)
            for var, key in ((self.v_hp, 'Hp'), (self.v_mp, 'Mp')):
                t = var.get().strip()
                if t == '':
                    continue
                s.set_number(s.get([key]), float(t))
            s.save()
            self.done('基本已寫入 備份:%s' % bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_attr(self):
        try:
            s = Sol(self.path())
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            for idx, var in self.v_attr.items():
                t = var.get().strip()
                if t == '':
                    continue
                try:
                    nd = s.get(['m', str(idx)])
                except KeyError:
                    continue
                if nd.kind == 'N':
                    s.set_number(nd, float(t))
            s.save()
            self.done('屬性已寫入 備份:%s' % bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def skill_names(self):
        menu = self.skill_menu['menu']
        menu.delete(0, 'end')
        tbl = R.SKILLS.get(cat_of(self.cat.get()), {})
        ids = sorted(tbl)
        if ids:
            self.sid.set(str(ids[0]))
        for i in ids:
            menu.add_command(label='%d %s' % (i, tbl[i]),
                             command=lambda v=str(i): self.sid.set(v))

    def skill_load(self):
        try:
            s = Sol(self.path())
            sid = self.sid.get().split()[0] if self.sid.get() else ''
            if not sid:
                return
            try:
                self.s_lv.set(fmt(s.get(['x', sid]).val))
            except KeyError:
                self.s_lv.set('')
            try:
                self.s_exp.set(fmt(s.get(['v', sid]).val))
            except KeyError:
                self.s_exp.set('')
            cat = cat_of(self.cat.get())
            try:
                lst = s.get([cat])
                self.owned.set(any(nd.kind == 'N' and int(nd.val) == int(sid) for k, nd in lst.kids))
            except KeyError:
                self.owned.set(False)
        except Exception:
            pass

    def apply_skill(self):
        try:
            s = Sol(self.path())
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            sid = self.sid.get().split()[0]
            cat = cat_of(self.cat.get())
            if self.owned.get():
                lst = s.get([cat])
                if not any(nd.kind == 'N' and int(nd.val) == int(sid) for k, nd in lst.kids):
                    mx = -1
                    for k, nd in lst.kids:
                        if str(k).isdigit():
                            mx = max(mx, int(k))
                    s.object_set(lst, str(mx + 1), 'N', int(sid))
            if self.s_lv.get().strip():
                try:
                    s.set_number(s.get(['x', sid]), float(self.s_lv.get()))
                except KeyError:
                    s.object_set(s.get(['x']), sid, 'N', float(self.s_lv.get()))
            if self.s_exp.get().strip():
                try:
                    s.set_number(s.get(['v', sid]), float(self.s_exp.get()))
                except KeyError:
                    pass
            s.save()
            self.done('武功已寫入 備份:%s' % bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_item(self):
        try:
            s = Sol(self.path())
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            iid = int(self.iid.get().split()[0])
            cnt = int(self.icnt.get())
            f = s.get(['f'])
            mx = -1
            for k, nd in f.kids:
                if str(k).isdigit():
                    mx = max(mx, int(k))
            s.object_set(f, str(mx + 1), 'N', iid)
            try:
                old = s.get(['g', str(iid)])
                if old.kind == 'N' and old.val < cnt:
                    s.set_number(old, cnt)
            except KeyError:
                s.object_set(s.get(['g']), str(iid), 'N', cnt)
            s.save()
            self.done('已加入 %s x%d  備份:%s' % (R.ITEMS.get(iid, iid), cnt, bak))
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def jm_refresh(self):
        try:
            s = Sol(self.path())
            n = s.get(['n'])
            c = sum(1 for k, nd in n.kids if nd.kind == 'N' and nd.val == 1)
            self.jm_info.set('已通 %d / %d' % (c, len(n.kids)))
        except KeyError:
            self.jm_info.set('無 n 表')

    def jm_load(self):
        try:
            s = Sol(self.path())
            nd = s.get(['n', self.jm_idx.get()])
            self.jm_val.set(bool(nd.val))
        except (KeyError, ValueError):
            pass

    def apply_jm_all(self):
        try:
            s = Sol(self.path())
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            n = s.get(['n'])
            c = 0
            for k, nd in n.kids:
                if nd.kind == 'N' and nd.val == 0:
                    s.set_number(nd, 1)
                    c += 1
            s.save()
            self.done('經脈 %d 處全通 備份:%s' % (c, bak))
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_jm_one(self):
        try:
            s = Sol(self.path())
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            s.set_number(s.get(['n', self.jm_idx.get()]), 1 if self.jm_val.get() else 0)
            s.save()
            self.done('經脈 %s 已設 備份:%s' % (self.jm_idx.get(), bak))
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_tm(self):
        try:
            s = Sol(self.path())
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            for slot, var in self.tm.items():
                t = var.get().strip()
                if t == '':
                    continue
                s.set_number(s.get(['m', slot]), int(t.split()[0]))
            s.save()
            self.done('隊友已寫入 備份:%s' % bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_inherit(self):
        try:
            import sav_bridge as B
            import argparse
            ns = argparse.Namespace(jy2slot=self.jy2slot.get(), jy2file=None,
                                    jy3slot=self.slot.get(), jy3file=None,
                                    skip_skills=not self.f_skill.get(),
                                    skip_neigong=not self.f_ng.get(),
                                    skip_weapons=not self.f_eq.get(),
                                    skip_armor=not self.f_eq.get(), yes=True)
            B.cmd_inherit(ns)
            self.done('繼承已寫入（只用一次，重複會疊加）')
        except SystemExit as e:
            messagebox.showerror('失敗', str(e))
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def launch(self):
        pkg = pkg_root()
        subprocess.Popen([os.path.join(pkg, 'resource', 'engine', 'ruffle.exe'),
                          os.path.join(pkg, 'resource', 'assets', 'jy3', 'play.swf'),
                          '--save-directory', os.path.join(pkg, 'save')])


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
