#!/usr/bin/env python3
"""金庸群俠傳2 修改器 GUI (tkinter, stdlib only)。引擎: trainer.Sol。"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trainer as T  # noqa: E402
from amf import pkg_root  # noqa: E402

ATTR_CN = {'LV': '等級', 'JYZ': '經驗', 'S_M': '生命', 'S_M0': '當前生命',
 'N_L': '內力', 'N_L0': '當前內力', 'F_Y': '福緣', 'S_W': '聲望', 'W_X': '悟性',
 'L_D': '力道', 'L_D0': '力道(當)', 'H_T': '護體', 'H_T0': '護體(當)',
 'S_F': '身法', 'Q_Z': '拳掌', 'Y_J': '御劍', 'A_Q': '暗器', 'Y_L': '醫療',
 'Y_D': '用毒', 'J_D': '解毒', 'X_Y': '俠義', 'Y_Z': '銀兩', 'XXD': '學習點'}

SKILLS = [
 ('taijiquan', '太極拳'), ('qishang', '七傷拳'), ('xingyi', '形意拳'),
 ('anran', '黯然銷魂掌'), ('tianshan', '天山六陽掌'), ('tiezhang', '鐵掌'),
 ('liumai', '六脈神劍'), ('nianhua', '拈花指'), ('taijijian', '太極劍'),
 ('wuyue', '五嶽劍法'), ('xuantie', '玄鐵劍法'), ('jiuyang', '九陽神功'),
 ('beiming', '北冥'), ('hanbing', '寒冰真氣'), ('kongming', '空明拳'),
 ('luohan', '羅漢拳'), ('xianglong', '降龍十八掌'), ('mianzhang', '綿掌'),
 ('hunyuan', '混元掌'), ('yiyang', '一陽指'), ('tanzhi', '彈指神通'),
 ('canhe', '參合指'), ('jinshe', '金蛇劍法'), ('dugu', '獨孤九劍'),
 ('pixie', '辟邪劍法'), ('taixuan', '太玄經神功'), ('longxiang', '龍象般若功'),
 ('jinzhong', '吐納術'), ('jichujian', '基礎劍'), ('jichuquan', '基礎拳'),
 ('kkk', '自創等級'), ('hhh', '九陰神爪'),
]
ATTRS = ['LV', 'JYZ', 'S_M', 'S_M0', 'N_L', 'N_L0', 'F_Y', 'S_W', 'W_X',
         'L_D', 'L_D0', 'H_T', 'H_T0', 'S_F', 'Q_Z', 'Y_J', 'A_Q',
         'Y_L', 'Y_D', 'J_D', 'X_Y', 'Y_Z', 'XXD']


def inner_text(markup):
    """name_1/name_2 存的是整段 TEXTFORMAT，只取第一段明文；沒有就原樣回傳。"""
    import re
    runs = [r for r in re.findall(r'>([^<>]*)</FONT>', markup) if r.strip()]
    if runs:
        return runs[0]
    i = markup.find('">')
    j = markup.find('</FONT>')
    if i >= 0 and j > i:
        return markup[i + 2:j]
    return markup


def set_inner(raw_bytes, new_text):
    """等長替換第一段明文區(補空格)，回傳新整段 bytes。"""
    import re
    s = raw_bytes.decode('utf-8', 'replace')
    nb = new_text.encode('utf-8')
    m = None
    for mm in re.finditer(r'>([^<>]*)</FONT>', s):
        if mm.group(1).strip():
            m = mm
            break
    if m is None:
        if len(nb) > len(raw_bytes):
            raise ValueError('太長(上限%d bytes)' % len(raw_bytes))
        return nb + b' ' * (len(raw_bytes) - len(nb))
    a = len(s[:m.start(1)].encode('utf-8'))
    b = len(s[:m.end(1)].encode('utf-8'))
    cap = b - a
    if len(nb) > cap:
        raise ValueError('太長(上限%d bytes)' % cap)
    return raw_bytes[:a] + nb + b' ' * (cap - len(nb)) + raw_bytes[b:]


class App:
    def __init__(self, root):
        self.root = root
        root.title('金庸群俠傳2 修改器')
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
        self.vars = {}
        p1 = ttk.Frame(nb)
        nb.add(p1, text='基本')
        for i, (k, name) in enumerate([('name_1', '姓'), ('name_2', '名'),
                                       ('jjj', '自創武學名'), ('Menpai', '門派'),
                                       ('Chenhao', '稱號')]):
            ttk.Label(p1, text='%s %s' % (name, k)).grid(row=i, column=0, sticky='e', padx=4, pady=3)
            v = tk.StringVar()
            ttk.Entry(p1, textvariable=v, width=30).grid(row=i, column=1, sticky='w')
            self.vars[k] = v
        ttk.Button(p1, text='套用基本', command=self.apply_basic).grid(row=5, column=1, sticky='w', pady=6)
        p2 = ttk.Frame(nb)
        nb.add(p2, text='屬性')
        for i, k in enumerate(ATTRS):
            ttk.Label(p2, text='%s %s' % (ATTR_CN.get(k, k), k)).grid(row=i // 4, column=(i % 4) * 2, sticky='e', padx=2, pady=2)
            v = tk.StringVar()
            ttk.Entry(p2, textvariable=v, width=10).grid(row=i // 4, column=(i % 4) * 2 + 1, sticky='w')
            self.vars[k] = v
        ttk.Button(p2, text='套用屬性', command=self.apply_attrs).grid(row=7, column=1, sticky='w', pady=6)
        p3 = ttk.Frame(nb)
        nb.add(p3, text='武功')
        ttk.Label(p3, text='武功').grid(row=0, column=0, sticky='e')
        self.skill = tk.StringVar(value=self.slabel(SKILLS[0][0]))
        ttk.OptionMenu(p3, self.skill, self.slabel(SKILLS[0][0]),
                       *[self.slabel(s[0]) for s in SKILLS]).grid(row=0, column=1, sticky='w')
        self.skill_lv = tk.StringVar()
        self.skill_exp = tk.StringVar()
        ttk.Label(p3, text='等級 lv_').grid(row=1, column=0, sticky='e')
        ttk.Entry(p3, textvariable=self.skill_lv, width=10).grid(row=1, column=1, sticky='w')
        ttk.Label(p3, text='經驗 exp_').grid(row=2, column=0, sticky='e')
        ttk.Entry(p3, textvariable=self.skill_exp, width=10).grid(row=2, column=1, sticky='w')
        ttk.Button(p3, text='讀取', command=self.skill_load).grid(row=0, column=2, padx=6)
        ttk.Button(p3, text='套用武功', command=self.apply_skill).grid(row=3, column=1, sticky='w', pady=6)
        self.rrr = tk.StringVar()
        ttk.Label(p3, text='半瓶醋次數 rrr').grid(row=4, column=0, sticky='e')
        ttk.Entry(p3, textvariable=self.rrr, width=10).grid(row=4, column=1, sticky='w')
        ttk.Button(p3, text='套用 rrr', command=self.apply_rrr).grid(row=4, column=2, padx=6)
        p4 = ttk.Frame(nb)
        nb.add(p4, text='開關')
        self.aaa = tk.BooleanVar()
        ttk.Checkbutton(p4, text='左右互搏 aaa（遊戲內驗證中）', variable=self.aaa).pack(anchor='w', padx=8, pady=8)
        ttk.Button(p4, text='套用開關', command=self.apply_aaa).pack(anchor='w', padx=8)
        ttk.Label(root, textvariable=self.status).pack(anchor='w', padx=8, pady=4)
        self.refresh()

    def sol(self):
        try:
            p = T.find_slot(self.slot.get())
        except FileNotFoundError:
            raise FileNotFoundError('slot%s 包內無存檔(先進遊戲存檔)' % self.slot.get())
        return T.Sol(p)

    def refresh(self):
        try:
            s = self.sol()
        except Exception as e:
            self.status.set(str(e))
            return
        e = s.entries
        for k, v in self.vars.items():
            if k in e:
                val = e[k]['val']
                if isinstance(val, str) and k in ('name_1', 'name_2'):
                    v.set(inner_text(val))
                else:
                    v.set('' if val is None else str(int(val)) if isinstance(val, float) and val.is_integer() else str(val))
        lv = e.get('LV', {}).get('val', '?')
        mp = e.get('Menpai', {}).get('val', '')
        self.info.set('LV %s · %s' % (lv if lv == '?' else int(lv), mp))
        self.skill_load()
        if 'aaa' in e and e['aaa']['type'] == 0x00:
            self.aaa.set(bool(e['aaa']['val']))
        if 'rrr' in e:
            self.rrr.set(str(int(e['rrr']['val'])))
        self.status.set('已讀取 %s' % os.path.basename(s.path))

    def done(self, msg, bak=None):
        self.status.set(msg + ((' 備份:%s' % bak) if bak else ''))
        self.refresh()

    def apply_basic(self):
        try:
            s = self.sol()
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            for k in ('name_1', 'name_2', 'jjj', 'Menpai', 'Chenhao'):
                if k not in s.entries:
                    continue
                en = s.entries[k]
                if en['type'] != 0x02:
                    continue
                old = bytes(s.raw[en['vpos'] + 2:en['vpos'] + en['vlen']])
                new = set_inner(old, self.vars[k].get())
                s.raw[en['vpos'] + 2:en['vpos'] + en['vlen']] = new
            s.save()
            self.done('基本已寫入', bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_attrs(self):
        try:
            s = self.sol()
            import time
            import shutil
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            import struct
            for k in ATTRS:
                t = self.vars[k].get().strip()
                if t == '' or k not in s.entries:
                    continue
                en = s.entries[k]
                if en['type'] != 0x00:
                    continue
                struct.pack_into('>d', s.raw, en['vpos'], float(t))
            s.save()
            self.done('屬性已寫入', bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    @staticmethod
    def slabel(sid):
        for i, n in SKILLS:
            if i == sid:
                return '%s (%s)' % (n, i)
        return sid

    @staticmethod
    def sid_of(label):
        if '(' in label and label.endswith(')'):
            return label.rsplit('(', 1)[1][:-1]
        return label

    def skill_load(self):
        try:
            s = self.sol()
            sid = self.sid_of(self.skill.get())
            lvk, exk = ('kkk', 'lll') if sid == 'kkk' else (('hhh', 'iii') if sid == 'hhh' else ('lv_' + sid, 'exp_' + sid))
            self.skill_lv.set('' if lvk not in s.entries else str(int(s.entries[lvk]['val'])))
            self.skill_exp.set('' if exk not in s.entries else str(int(s.entries[exk]['val'])))
        except Exception:
            pass

    def apply_skill(self):
        try:
            s = self.sol()
            import time
            import shutil
            import struct
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            sid = self.sid_of(self.skill.get())
            lvk, exk = ('kkk', 'lll') if sid == 'kkk' else (('hhh', 'iii') if sid == 'hhh' else ('lv_' + sid, 'exp_' + sid))
            for k, v in ((lvk, self.skill_lv.get()), (exk, self.skill_exp.get())):
                if v.strip() == '' or k not in s.entries:
                    continue
                struct.pack_into('>d', s.raw, s.entries[k]['vpos'], float(v))
            s.save()
            self.done('武功已寫入', bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_rrr(self):
        try:
            s = self.sol()
            import time
            import shutil
            import struct
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            struct.pack_into('>d', s.raw, s.entries['rrr']['vpos'], float(self.rrr.get()))
            s.save()
            self.done('rrr 已寫入', bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def apply_aaa(self):
        try:
            s = self.sol()
            import time
            import shutil
            import struct
            bak = '%s.bak.%d' % (s.path, int(time.time()))
            shutil.copyfile(s.path, bak)
            struct.pack_into('>d', s.raw, s.entries['aaa']['vpos'], 1.0 if self.aaa.get() else 0.0)
            s.save()
            self.done('aaa 已寫入', bak)
        except Exception as e:
            messagebox.showerror('失敗', str(e))

    def launch(self):
        pkg = pkg_root()
        subprocess.Popen([os.path.join(pkg, 'resource', 'engine', 'ruffle.exe'),
                          os.path.join(pkg, 'resource', 'assets', 'jy2', 'jy2.swf'),
                          '--save-directory', os.path.join(pkg, 'save')])


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
