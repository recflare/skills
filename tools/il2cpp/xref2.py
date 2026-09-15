import struct, bisect, ijson

DLL = __import__("os").environ.get("GAMEASSEMBLY", r"C:\Games\recflare-client\GameAssembly.dll")
SCRIPT = "out/script.json"
TARGET_RVA = 0x9369C80  # "eac challenge failed"

# ---- Parse PE section headers to map RVA <-> file offset ----
with open(DLL, "rb") as f:
    data = f.read()

pe = struct.unpack_from("<I", data, 0x3C)[0]
assert data[pe:pe+4] == b"PE\x00\x00"
num_sections = struct.unpack_from("<H", data, pe+6)[0]
size_opt = struct.unpack_from("<H", data, pe+20)[0]
sect_off = pe + 24 + size_opt

sections = []
for i in range(num_sections):
    o = sect_off + i*40
    name = data[o:o+8].rstrip(b"\x00").decode("latin1")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o+8)
    chars = struct.unpack_from("<I", data, o+36)[0]
    sections.append((name, vaddr, vsize, rawptr, rawsize, chars))
    print(f"  section {name:8} rva=0x{vaddr:08x} vsize=0x{vsize:08x} raw=0x{rawptr:08x} rawsize=0x{rawsize:08x} exec={bool(chars & 0x20000000)}")

# executable sections to scan
exec_sections = [s for s in sections if s[5] & 0x20000000]

# ---- Scan exec sections for RIP-relative refs to TARGET_RVA ----
# A rip-relative operand: ModRM byte with (modrm & 0xC7)==0x05, followed by disp32.
# target = rva_of_next_instruction + disp32. For lea/mov reg,[rip+d] with no trailing
# immediate, next_instruction == disp_end, so target = (disp_rva + 4) + disp32.
hits = []
for name, vaddr, vsize, rawptr, rawsize, chars in exec_sections:
    blob = data[rawptr:rawptr+rawsize]
    print(f"scanning {name} ({len(blob)} bytes)...")
    # iterate every position where a disp32 could sit (need modrm at pos-1)
    for i in range(1, len(blob)-4):
        d = struct.unpack_from("<i", blob, i)[0]
        disp_rva = vaddr + i
        target = disp_rva + 4 + d
        if target != TARGET_RVA:
            continue
        modrm = blob[i-1]
        if (modrm & 0xC7) != 0x05:
            continue
        # instruction start heuristically a few bytes before modrm
        code_rva = vaddr + (i - 1)  # at least the modrm; opcode/prefix precede it
        hits.append(code_rva)

print(f"\n{len(hits)} rip-relative reference(s) to 0x{TARGET_RVA:08x}: " +
      ", ".join(hex(h) for h in hits))

# ---- Load ScriptMethod (Address,Name), sorted, then bisect each hit ----
print("loading ScriptMethod (streaming)...")
addrs = []
names = []
with open(SCRIPT, "rb") as f:
    cur = {}
    for prefix, event, value in ijson.parse(f):
        if prefix == "ScriptMethod.item.Address":
            cur_addr = value
        elif prefix == "ScriptMethod.item.Name":
            addrs.append(cur_addr)
            names.append(value)
        elif prefix.startswith("ScriptString"):
            break  # ScriptMethod section done
print(f"  {len(addrs)} methods")

order = sorted(range(len(addrs)), key=lambda k: addrs[k])
sorted_addrs = [addrs[k] for k in order]

print("\n=== RESULTS ===")
for h in hits:
    j = bisect.bisect_right(sorted_addrs, h) - 1
    if j < 0:
        print(f"  ref 0x{h:08x}: (no method below)")
        continue
    start = sorted_addrs[j]
    nend = sorted_addrs[j+1] if j+1 < len(sorted_addrs) else None
    name = names[order[j]]
    ends = f"0x{nend:08x}" if nend else "?"
    print(f"  ref 0x{h:08x} -> method start 0x{start:08x} (next {ends})")
    print(f"       {name}")
