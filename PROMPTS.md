# Starting prompts

Copy-paste openers for a Claude Code session rooted at this repo. Each one names its skill outright —
the descriptions should make Claude load the right one unprompted, but saying it removes the doubt.

Fill in the two paths marked `<...>` once and keep your edited copy; everything else is reusable.

- `<INDEX>` — the directory holding your carved `methods.pkl` and `out/stringliteral.json`
- `<CARVE_OUT>` — the directory holding `GameAssembly.dll`, `ga_image.bin`, `global-metadata.dat`

Neither is in this repo: both are build-specific and large. See `tools/il2cpp/README.md`.

---

## Look up a wire shape

The common case. Answers from the catalog without touching the binary.

```
Use the wire-shapes skill.

What does the Rec Room client expect back from
GET https://rooms.recflare.net/rooms/1162/roles ?

Check .claude/skills/wire-shapes/references/CATALOG.md first — grep it for a
path fragment, then read only the file it names. If it's already there, give me
the shape and stop; don't re-derive it.

Answer with: verb + service, the request (params/body), the response JSON with
every key, and any field the client hard-requires (NREs / silently drops the
item without).
```

## Derive one that isn't in the catalog

75 routes are catalogued, so a miss is normal. Append this to the prompt above:

```
If CATALOG.md has no row for it, derive it from the client binary per the skill:
build 20250718.01, toolkit at tools/il2cpp in this repo. Run index-reading
scripts from <INDEX>, with
  GAMEASSEMBLY=<CARVE_OUT>/GameAssembly.dll
  GA_IMAGE=<CARVE_OUT>/ga_image.bin
  GA_METADATA=<CARVE_OUT>/global-metadata.dat
set explicitly — the in-script defaults point at another machine's paths.

Read T from the HPBKMCLEANE<T> generic instantiation, never from the client
method's return type. Then write the new note into
.claude/skills/wire-shapes/references/endpoints/ and add a row to CATALOG.md.
```

## Check a capture against the client

Use this whenever live traffic and the notes disagree. It caught two wrong notes the week these were
written, so treat a contradiction as a real finding rather than assuming the capture is odd.

```
Use the wire-shapes skill.

I'm seeing this in mitmproxy:

<paste request + response>

Confirm against the client binary whether the client actually accepts that.
If the catalog note is wrong, correct the note and say what the evidence was.
```

## Diagnose a client-side failure

```
Use the rr-client-bringup skill.

The client <crashes / quits silently after ~35s / hangs on "Downloading" /
never finishes loading a room>. Here is the log:

<paste>

Work the symptom table first. Tell me which of the known causes this matches,
or say plainly that it matches none of them.
```

Worth knowing before you start: **blocking a dead host makes load worse, not better** — all client
HTTP shares one FIFO queue, so dead hosts must return an instant 200/204. That single fact explains
most "it worked yesterday" reports.

## Work on the voice server

```
Use the rr-voice-server skill.

<Nobody can hear anybody / the roster is empty / the client never connects /
I'm implementing the connect handshake>.

Start by telling me which of the four layers this is (gate / transport /
session / voice), because they fail identically from the client's UI.
```

## Work on the room server

```
Use the rr-room-networking skill.

<Clients won't join / they drop after ~10s / I'm implementing the join
handshake>.

First confirm which backend I'm on — Photon or the dedicated NGO GameServer —
and how the client decides.
```

## Resolve an obfuscated name or RVA

```
Use the il2cpp-analysis skill.

What is <OBFUSCATED_NAME / 0xRVA>?

Identify the build before resolving it, and verify the index isn't stale —
a wrong index answers confidently rather than failing.
```

---

## What to expect

**A name is only valid for one build.** Obfuscated types, methods and RVAs re-roll on every client
update. Wire shapes transfer; names and offsets do not. If Claude quotes a name at you, the build it
came from should be stated — `20250718.01` unless said otherwise.

**Absence is not evidence.** Several traps here return a clean negative for the wrong reason: raw
byte scans of LZ4-compressed bundles, jump-table dispatch invisible to an immediate scan, shared
generic bodies missing from `methods.pkl`. Ask for a positive control before believing a "not found".
