//
// metadump.exe -- external live-memory capture for recflare-2025 (build 20250718.01).
//
// Stage 1 of the DUMPING.md carve. This build ships a decoy `global-metadata.dat` (52 MB of 0x52)
// and an encrypted `GameAssembly.dll` `.text`/`il2cpp`, so nothing on disk is analysable. Both are
// decrypted/loaded during il2cpp_init, so the only source is a running process.
//
// It is a pure READER: OpenProcess + ReadProcessMemory only, no injection, no writes, no calls into
// the game. Run it BEFORE launching (it polls), or any time while the game is at the title screen.
//
// Outputs, next to the exe in .\out\ :
//   ga_image.bin     GameAssembly.dll flattened by RVA (file offset == RVA, gaps zero-filled)
//   metadata.bin     the whole private allocation holding the il2cpp metadata (permuted header)
//   manifest.txt     bases, sizes, region table, and the decryption sanity check
//
// Sanity check: RVA 0x77E0950 is BestHTTP.HTTPManager.SendRequest in this build (the address the
// working hook uses). If the bytes there are a plausible prologue, .text really is decrypted.
//
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define TARGET_EXE      "Recroom_Release.exe"
#define TARGET_MODULE   "GameAssembly.dll"
#define SENDREQUEST_RVA 0x77E0950ull

// The metadata string table always contains the assembly names; mscorlib is the reliable anchor.
static const char kAnchor[] = "mscorlib.dll";

static FILE *g_man;

static void mlog(const char *fmt, ...)
{
    char line[1024];
    SYSTEMTIME st; GetLocalTime(&st);
    int n = sprintf(line, "[%02d:%02d:%02d.%03d] ", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
    va_list ap; va_start(ap, fmt);
    n += vsprintf(line + n, fmt, ap);
    va_end(ap);
    fputs(line, stdout); fputc('\n', stdout); fflush(stdout);
    if (g_man) { fputs(line, g_man); fputc('\n', g_man); fflush(g_man); }
}

static DWORD FindPid(const char *exe)
{
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;
    PROCESSENTRY32 pe = { sizeof(pe) };
    DWORD pid = 0;
    if (Process32First(snap, &pe)) {
        do { if (_stricmp(pe.szExeFile, exe) == 0) { pid = pe.th32ProcessID; break; } }
        while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    return pid;
}

static int FindModule(HANDLE p, const char *want, BYTE **base, SIZE_T *size)
{
    HMODULE mods[2048]; DWORD needed = 0;
    if (!EnumProcessModulesEx(p, mods, sizeof(mods), &needed, LIST_MODULES_ALL)) return 0;
    DWORD count = needed / sizeof(HMODULE);
    if (count > 2048) count = 2048;
    for (DWORD i = 0; i < count; i++) {
        char name[MAX_PATH];
        if (!GetModuleBaseNameA(p, mods[i], name, sizeof(name))) continue;
        if (_stricmp(name, want) != 0) continue;
        MODULEINFO mi;
        if (!GetModuleInformation(p, mods[i], &mi, sizeof(mi))) continue;
        *base = (BYTE *)mi.lpBaseOfDll;
        *size = mi.SizeOfImage;
        return 1;
    }
    return 0;
}

// Flatten [base, base+size) into buf so that buf[rva] is the byte at base+rva. Uncommitted or
// unreadable pages stay zero. Returns bytes actually copied.
static uint64_t FlattenRange(HANDLE p, BYTE *base, SIZE_T size, BYTE *buf, int logRegions)
{
    uint64_t got = 0;
    BYTE *q = base, *end = base + size;
    while (q < end) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQueryEx(p, q, &mbi, sizeof(mbi))) break;
        BYTE *rb = (BYTE *)mbi.BaseAddress;
        SIZE_T rs = mbi.RegionSize;
        if (rb + rs > end) rs = (SIZE_T)(end - rb);
        int readable = mbi.State == MEM_COMMIT &&
                       !(mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) && mbi.Protect != 0;
        if (readable && rb >= base) {
            SIZE_T off = (SIZE_T)(rb - base), done = 0;
            while (done < rs) {
                SIZE_T chunk = rs - done; if (chunk > (4u << 20)) chunk = 4u << 20;
                SIZE_T rd = 0;
                if (ReadProcessMemory(p, rb + done, buf + off + done, chunk, &rd) && rd) got += rd;
                else break;
                done += chunk;
            }
            if (logRegions)
                mlog("  region %p len=%llx prot=%08x", rb, (unsigned long long)rs, mbi.Protect);
        }
        q = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    return got;
}

// Search every committed private region for the metadata string-table anchor. On a hit, return the
// AllocationBase and the total length of that allocation (walking forward while it stays the same).
static int FindMetadata(HANDLE p, BYTE **allocBase, SIZE_T *allocLen, BYTE **hitAt)
{
    BYTE *q = NULL;
    BYTE *scratch = (BYTE *)VirtualAlloc(NULL, (4u << 20) + 64, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!scratch) return 0;
    const SIZE_T alen = sizeof(kAnchor) - 1;
    int found = 0;

    while (!found) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQueryEx(p, q, &mbi, sizeof(mbi))) break;
        BYTE *rb = (BYTE *)mbi.BaseAddress;
        SIZE_T rs = mbi.RegionSize;
        int candidate = mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE &&
                        !(mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) && mbi.Protect != 0 &&
                        rs >= (4u << 20);
        if (candidate) {
            SIZE_T off = 0;
            while (off < rs && !found) {
                SIZE_T chunk = rs - off; if (chunk > (4u << 20)) chunk = 4u << 20;
                SIZE_T rd = 0;
                if (ReadProcessMemory(p, rb + off, scratch, chunk, &rd) && rd >= alen) {
                    for (SIZE_T i = 0; i + alen < rd; i++) {
                        if (scratch[i] == 'm' && memcmp(scratch + i, kAnchor, alen) == 0 &&
                            scratch[i + alen] == 0) {
                            *hitAt = rb + off + i;
                            *allocBase = (BYTE *)mbi.AllocationBase;
                            found = 1;
                            break;
                        }
                    }
                }
                off += chunk;
            }
        }
        q = rb + rs;
        if (q < rb) break; // wrapped
    }
    VirtualFree(scratch, 0, MEM_RELEASE);
    if (!found) return 0;

    // Measure the allocation: walk forward from AllocationBase while it stays the same.
    BYTE *w = *allocBase;
    for (;;) {
        MEMORY_BASIC_INFORMATION mbi;
        if (!VirtualQueryEx(p, w, &mbi, sizeof(mbi))) break;
        if ((BYTE *)mbi.AllocationBase != *allocBase) break;
        w = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    *allocLen = (SIZE_T)(w - *allocBase);
    return 1;
}

static int WriteAll(const char *path, const void *data, uint64_t len)
{
    FILE *f = fopen(path, "wb");
    if (!f) return 0;
    const BYTE *b = (const BYTE *)data;
    uint64_t left = len;
    while (left) {
        size_t chunk = left > (16u << 20) ? (16u << 20) : (size_t)left;
        if (fwrite(b, 1, chunk, f) != chunk) { fclose(f); return 0; }
        b += chunk; left -= chunk;
    }
    fclose(f);
    return 1;
}

int main(int argc, char **argv)
{
    char dir[MAX_PATH], outdir[MAX_PATH], path[MAX_PATH];
    GetModuleFileNameA(NULL, dir, MAX_PATH);
    for (int i = (int)strlen(dir); i > 0; i--) if (dir[i-1] == '\\') { dir[i-1] = 0; break; }
    sprintf(outdir, "%s\\out", dir);
    CreateDirectoryA(outdir, NULL);
    sprintf(path, "%s\\manifest.txt", outdir);
    g_man = fopen(path, "w");

    int settleSec = (argc > 1) ? atoi(argv[1]) : 8;

    mlog("==== metadump: waiting for %s (poll 500ms, Ctrl-C to abort) ====", TARGET_EXE);
    DWORD pid = 0;
    while (!(pid = FindPid(TARGET_EXE))) Sleep(500);
    mlog("pid=%lu", pid);

    HANDLE p = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (!p) { mlog("OpenProcess failed err=%lu (try running elevated)", GetLastError()); return 1; }

    BYTE *gaBase = NULL; SIZE_T gaSize = 0;
    for (int i = 0; i < 1200 && !FindModule(p, TARGET_MODULE, &gaBase, &gaSize); i++) Sleep(500);
    if (!gaBase) { mlog("%s never mapped -- aborting", TARGET_MODULE); return 1; }
    mlog("%s base=%p SizeOfImage=%llx", TARGET_MODULE, gaBase, (unsigned long long)gaSize);

    // Wait for il2cpp_init: the metadata allocation only appears once it has been loaded/decrypted.
    BYTE *mdBase = NULL, *mdHit = NULL; SIZE_T mdLen = 0;
    mlog("scanning for metadata anchor \"%s\" ...", kAnchor);
    int ok = 0;
    for (int i = 0; i < 360 && !ok; i++) {           // up to ~6 min of polling
        ok = FindMetadata(p, &mdBase, &mdLen, &mdHit);
        if (!ok) Sleep(1000);
    }
    if (!ok) { mlog("metadata anchor never found -- aborting"); CloseHandle(p); return 1; }
    mlog("metadata anchor hit at %p; allocation base=%p len=%llx (%llu MB)",
         mdHit, mdBase, (unsigned long long)mdLen, (unsigned long long)(mdLen >> 20));

    mlog("settling %d s to let il2cpp_init finish ...", settleSec);
    Sleep(settleSec * 1000);

    // ---- GameAssembly.dll flattened by RVA ----
    BYTE *img = (BYTE *)VirtualAlloc(NULL, gaSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!img) { mlog("VirtualAlloc %llx failed", (unsigned long long)gaSize); CloseHandle(p); return 1; }
    mlog("flattening %s ...", TARGET_MODULE);
    uint64_t gaGot = FlattenRange(p, gaBase, gaSize, img, 1);
    mlog("  copied %llu bytes of %llu", (unsigned long long)gaGot, (unsigned long long)gaSize);

    if (SENDREQUEST_RVA + 16 < gaSize) {
        BYTE *s = img + SENDREQUEST_RVA;
        char hex[64] = { 0 };
        for (int i = 0; i < 16; i++) sprintf(hex + i * 3, "%02X ", s[i]);
        int looksCode = !(s[0] == 0 && s[1] == 0 && s[2] == 0 && s[3] == 0);
        mlog("sanity: bytes @RVA 0x%llX (SendRequest) = %s -> %s",
             SENDREQUEST_RVA, hex, looksCode ? "non-zero (decrypted .text captured)" : "ZERO -- NOT captured");
    }

    sprintf(path, "%s\\ga_image.bin", outdir);
    mlog("writing %s ...", path);
    if (!WriteAll(path, img, gaSize)) mlog("  WRITE FAILED (disk full?)");
    VirtualFree(img, 0, MEM_RELEASE);

    // ---- metadata allocation ----
    BYTE *md = (BYTE *)VirtualAlloc(NULL, mdLen, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!md) { mlog("VirtualAlloc %llx failed for metadata", (unsigned long long)mdLen); CloseHandle(p); return 1; }
    mlog("flattening metadata allocation ...");
    uint64_t mdGot = FlattenRange(p, mdBase, mdLen, md, 1);
    mlog("  copied %llu bytes of %llu", (unsigned long long)mdGot, (unsigned long long)mdLen);
    mlog("  anchor offset within allocation = 0x%llx", (unsigned long long)(mdHit - mdBase));
    {
        char hex[64] = { 0 };
        for (int i = 0; i < 16; i++) sprintf(hex + i * 3, "%02X ", md[i]);
        mlog("  first 16 bytes of allocation: %s", hex);
    }
    sprintf(path, "%s\\metadata.bin", outdir);
    mlog("writing %s ...", path);
    if (!WriteAll(path, md, mdLen)) mlog("  WRITE FAILED (disk full?)");
    VirtualFree(md, 0, MEM_RELEASE);

    mlog("gaBase=%p gaSize=%llx mdBase=%p mdLen=%llx",
         gaBase, (unsigned long long)gaSize, mdBase, (unsigned long long)mdLen);
    mlog("==== done. The game can be closed now. ====");
    CloseHandle(p);
    if (g_man) fclose(g_man);
    return 0;
}
