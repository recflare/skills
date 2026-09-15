"""Stage 2c: pin the remaining tables using counts cross-referenced out of typeDefinitions/methods.

typeDefinitions (region 19, 88-byte stride) carries start+count for fields, methods, events,
properties, nestedTypes, interfaces, vtable and interfaceOffsets; methods (region 8, 36-byte stride)
carries parameterStart/parameterCount. Those maxima give each dependent table's exact entry count,
which pins it to exactly one region once divided by the struct stride.
"""
import struct

data = open("out/metadata.bin", "rb").read()

LAYOUT = [
    (0x100, 0x5E3908), (0x5E3A08, 0x3F48), (0x5E7950, 0x30E08), (0x618758, 0xA950),
    (0x6230A8, 0x0), (0x6230A8, 0x407CE8), (0xA2AD90, 0x7D9B8), (0xAA8748, 0x0),
    (0xAA8748, 0xD3E324), (0x17E6A6C, 0x89940), (0x18703AC, 0x98880), (0x1908C2C, 0x2EE220),
    (0x1BF6E4C, 0x173888), (0x1D6A6D4, 0x1647E0), (0x1ECEEB4, 0x21DD0), (0x1EF0C84, 0x4418),
    (0x1EF509C, 0x1B5D0), (0x1F1066C, 0x31D7F8), (0x222DE64, 0x3B2F4), (0x2269158, 0x503380),
    (0x276C4D8, 0x1A984), (0x2786E5C, 0x2C0424), (0x2A47280, 0x4C64), (0x2A4BEE4, 0x3FD50),
    (0x2A8BC34, 0x21990), (0x2AAD5C4, 0x3E24), (0x2AB13E8, 0x69BAC), (0x2B1AF94, 0x26CA90),
    (0x2D87A24, 0x6540), (0x2D8DF64, 0x2150), (0x2D900B4, 0x2D7E0),
]

TYPEDEFS, METHODS = 19, 8
TD_OFF, TD_SIZE = LAYOUT[TYPEDEFS]
M_OFF, M_SIZE = LAYOUT[METHODS]
ntd = TD_SIZE // 88
nm = M_SIZE // 36
print(f"typeDefinitions: {ntd} entries   methods: {nm} entries")

# Il2CppTypeDefinition (v27+): 16 u32, then 8 u16 counts, then bitfield+token.
maxima = {k: 0 for k in ("field", "method", "event", "property", "nested", "iface", "vtable", "ifaceoff")}
gc_max = -1
for i in range(ntd):
    b = TD_OFF + i * 88
    u = struct.unpack_from("<16i", data, b)
    c = struct.unpack_from("<8H", data, b + 64)
    gc_max = max(gc_max, u[6])
    fieldStart, methodStart, eventStart, propStart = u[8], u[9], u[10], u[11]
    nestStart, ifaceStart, vtStart, ifoStart = u[12], u[13], u[14], u[15]
    method_c, prop_c, field_c, event_c, nest_c, vt_c, iface_c, ifo_c = c
    if fieldStart >= 0:  maxima["field"]    = max(maxima["field"], fieldStart + field_c)
    if methodStart >= 0: maxima["method"]   = max(maxima["method"], methodStart + method_c)
    if eventStart >= 0:  maxima["event"]    = max(maxima["event"], eventStart + event_c)
    if propStart >= 0:   maxima["property"] = max(maxima["property"], propStart + prop_c)
    if nestStart >= 0:   maxima["nested"]   = max(maxima["nested"], nestStart + nest_c)
    if ifaceStart >= 0:  maxima["iface"]    = max(maxima["iface"], ifaceStart + iface_c)
    if vtStart >= 0:     maxima["vtable"]   = max(maxima["vtable"], vtStart + vt_c)
    if ifoStart >= 0:    maxima["ifaceoff"] = max(maxima["ifaceoff"], ifoStart + ifo_c)

# Il2CppMethodDefinition (v31, 36 bytes): nameIndex, declaringType, returnType,
# returnParameterToken, parameterStart, genericContainerIndex, token, flags/iflags/slot/paramCount.
param_max = 0
mgc_max = -1
for i in range(nm):
    b = M_OFF + i * 36
    u = struct.unpack_from("<7i", data, b)
    pc = struct.unpack_from("<4H", data, b + 28)[3]
    mgc_max = max(mgc_max, u[5])
    if u[4] >= 0:
        param_max = max(param_max, u[4] + pc)

maxima["parameter"] = param_max
maxima["genericContainer"] = max(gc_max, mgc_max) + 1
print("derived counts:")
for k, v in maxima.items():
    print(f"  {k:17} {v}")

STRIDE = {
    "field": 12, "event": 24, "property": 20, "nested": 4, "iface": 4,
    "vtable": 4, "ifaceoff": 8, "parameter": 12, "genericContainer": 16,
}
print("\nmatching regions (count * stride == region size):")
for name, n in maxima.items():
    if name == "method":
        continue
    st = STRIDE.get(name)
    if not st:
        continue
    want = n * st
    hit = [i for i, (o, s) in enumerate(LAYOUT) if s == want]
    print(f"  {name:17} n={n:7} stride={st:2} -> want {want:#9x}  regions {hit}")
