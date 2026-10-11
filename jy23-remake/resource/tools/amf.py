#!/usr/bin/env python3
"""嵌套 AMF0 .sol 讀寫引擎(stdlib only)。給 trainer3 / sav_bridge 共用。
.sol 版式: 00 BF len TCSO(6 pad) u16 root + root + entries。
entry = [klen u16][key][marker u8][value]; object/ecma 以 00 00 09 結尾。
只做: 讀(全巢)、數字原地寫、字串重建(可變長)、strict array  append、
object 成員改/增。寫完一律回讀驗證。
"""
import os
import struct


def _looks_root(d):
    import os
    return os.path.isdir(os.path.join(d, 'save')) and os.path.isdir(os.path.join(d, 'resource'))


def pkg_root():
    """重製包根目錄。
    .py 開發: tools/../jy23-remake；包內 .py: 上溯找含 save/＋resource/ 者；
    exe: 同上（根目錄或 tools/ 皆認，最多上溯兩層）。"""
    import sys
    import os
    if getattr(sys, 'frozen', False):
        d = os.path.dirname(sys.executable)
    else:
        d = os.path.dirname(os.path.abspath(__file__))
    dev = os.path.normpath(os.path.join(d, '..', 'jy23-remake'))
    if os.path.isdir(dev):
        return dev
    cur = d
    for _ in range(3):
        if _looks_root(cur):
            return cur
        cur = os.path.normpath(os.path.join(cur, '..'))
    return cur


class Node:
    def __init__(self, kind, mpos, vpos, vend, val=None, kids=None):
        self.kind = kind      # N B S O A L
        self.mpos = mpos      # marker offset
        self.vpos = vpos      # value 區起點(marker 之後)
        self.vend = vend      # value 區終點
        self.val = val        # N/B/S 的值
        self.kids = kids or []  # O/A: [(key,node)]  L: [node]


class R:
    def __init__(self, b):
        self.b = b
        self.p = 0

    def u8(self):
        v = self.b[self.p]
        self.p += 1
        return v

    def u16(self):
        v = struct.unpack('>H', self.b[self.p:self.p + 2])[0]
        self.p += 2
        return v

    def u32(self):
        v = struct.unpack('>I', self.b[self.p:self.p + 4])[0]
        self.p += 4
        return v

    def f64(self):
        v = struct.unpack('>d', self.b[self.p:self.p + 8])[0]
        self.p += 8
        return v

    def raw(self, n):
        v = self.b[self.p:self.p + n]
        self.p += n
        return v

    def s(self):
        n = self.u16()
        return self.raw(n).decode('utf-8', 'replace')

    def node(self, depth=0):
        mpos = self.p
        t = self.u8()
        if t == 0x00:
            v = self.f64()
            return Node('N', mpos, mpos + 1, self.p, v)
        if t == 0x01:
            v = bool(self.u8())
            return Node('B', mpos, mpos + 1, self.p, v)
        if t == 0x02:
            n = self.u16()
            v = self.raw(n).decode('utf-8', 'replace')
            return Node('S', mpos, mpos + 1, self.p, v)
        if t in (0x03, 0x08):
            if t == 0x08:
                self.u32()
            kids = []
            while True:
                k = self.s()
                if k == '':
                    self.u8()
                    break
                kids.append((k, self.node(depth + 1)))
                if depth > 8 or len(kids) > 5000:
                    raise ValueError('too deep/wide')
            return Node('O' if t == 0x03 else 'A', mpos, mpos + 1, self.p, None, kids)
        if t == 0x0A:
            n = self.u32()
            if n > 5000:
                raise ValueError('array too long')
            kids = [self.node(depth + 1) for _ in range(n)]
            return Node('L', mpos, mpos + 1, self.p, None, kids)
        if t in (0x05, 0x06):
            return Node('B', mpos, mpos + 1, self.p, None)
        raise ValueError('type %02x at %d' % (t, mpos))


def is_key(b):
    import string as _s
    ok = _s.ascii_letters + _s.digits + '_.'
    return bool(b) and len(b) <= 64 and all(chr(c) in ok for c in b)


def entry_starts(b, p):
    import struct as _st
    for z in range(9):
        q = p + z
        if q >= len(b):
            return True
        if q + 3 > len(b):
            continue
        klen = _st.unpack('>H', b[q:q + 2])[0]
        if not 1 <= klen <= 64 or q + 2 + klen >= len(b):
            continue
        if is_key(bytes(b[q + 2:q + 2 + klen])):
            return True
    return False


def scan_entry(b, p):
    import struct as _st
    for z in range(9):
        q = p + z
        if q + 3 > len(b):
            continue
        klen = _st.unpack('>H', b[q:q + 2])[0]
        if not 1 <= klen <= 64 or q + 2 + klen >= len(b):
            continue
        kb = bytes(b[q + 2:q + 2 + klen])
        if not is_key(kb):
            continue
        r = R(b)
        r.p = q + 2 + klen
        try:
            nd = r.node()
        except ValueError:
            continue
        if entry_starts(b, r.p):
            return kb.decode(), nd, r.p
    return None


class Sol:
    def __init__(self, path):
        self.path = path
        self.raw = bytearray(open(path, 'rb').read())
        self.root = None
        self.entries = []
        self.parse()

    def parse(self):
        b = self.raw
        i = bytes(b).find(b'TCSO')
        if i < 0:
            raise ValueError('not a .sol file')
        r = R(b)
        r.p = i + 4 + 6
        rlen = r.u16()
        self.root = r.raw(rlen).decode()
        r.p += 4
        self.entries = []
        while r.p < len(b):
            s = scan_entry(bytes(b), r.p)
            if s is None:
                break
            key, nd, npos = s
            self.entries.append((key, nd))
            r.p = npos

    def find(self, key):
        for k, nd in self.entries:
            if k == key:
                return nd
        return None

    def get(self, path):
        cur = None
        for k, nd in self.entries:
            if k == path[0]:
                cur = nd
                break
        if cur is None:
            raise KeyError(path[0])
        for part in path[1:]:
            if cur.kind == 'L':
                cur = cur.kids[int(part)]
            elif cur.kind in ('O', 'A'):
                for k, nd in cur.kids:
                    if k == str(part):
                        cur = nd
                        break
                else:
                    raise KeyError(part)
            else:
                raise KeyError(part)
        return cur

    def set_number(self, node, nv):
        assert node.kind == 'N', 'not a number'
        struct.pack_into('>d', self.raw, node.vpos, float(nv))

    def set_string(self, node, text):
        assert node.kind == 'S', 'not a string'
        nb = text.encode('utf-8')
        self.raw[node.mpos:node.vend] = b'\x02' + struct.pack('>H', len(nb)) + nb
        self.parse()

    def replace(self, node, kind, val):
        """整顆值換型別(Numbers<->Strings)，重建位元組後重 parse。"""
        self.raw[node.mpos:node.vend] = self._enc(kind, val)
        self.parse()

    def _enc(self, kind, val):
        if kind == 'N':
            return b'\x00' + struct.pack('>d', float(val))
        if kind == 'B':
            return b'\x01' + bytes([1 if val else 0])
        if kind == 'S':
            nb = str(val).encode('utf-8')
            return b'\x02' + struct.pack('>H', len(nb)) + nb
        raise ValueError('kind')

    def array_append(self, node, kind, val):
        assert node.kind == 'L', 'not an array'
        cnt = struct.unpack('>I', self.raw[node.vpos:node.vpos + 4])[0]
        self.raw[node.vpos:node.vpos + 4] = struct.pack('>I', cnt + 1)
        self.raw[node.vend:node.vend] = self._enc(kind, val)
        self.parse()

    def object_set(self, node, key, kind, val):
        assert node.kind in ('O', 'A'), 'not an object'
        for k, nd in node.kids:
            if k == key:
                self.raw[nd.mpos:nd.vend] = self._enc(kind, val)
                self.parse()
                return
        payload = struct.pack('>H', len(key)) + key.encode() + self._enc(kind, val)
        if node.kind == 'A':
            cnt = struct.unpack('>I', self.raw[node.vpos:node.vpos + 4])[0]
            self.raw[node.vpos:node.vpos + 4] = struct.pack('>I', cnt + 1)
        self.raw[node.vend - 3:node.vend - 3] = payload
        self.parse()

    def save(self):
        open(self.path, 'wb').write(self.raw)
        chk = Sol(self.path)
        if len(chk.entries) < len(self.entries):
            raise ValueError('write verify failed')


def fmt(v):
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return repr(v)
