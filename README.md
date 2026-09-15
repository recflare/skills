# Rec Room reverse-engineering skills

Claude Code skills covering the obfuscated Rec Room IL2CPP client, written while building a
compatible self-hosted server (**recflare**). Everything here is derived from the client binary —
the formatters, the disassembly and the metadata — not from any server implementation.

Drop the repo somewhere Claude Code can see it, or copy `.claude/skills/` into a project. Each skill
loads on demand from its description; the bulk sits in `references/` and is only read when needed.

## The skills

| Skill | Use it when |
|---|---|
| [`wire-shapes`](.claude/skills/wire-shapes/SKILL.md) | "What JSON should my server send for `<route>`?" / "Why does the client NRE on this response?" — plus a catalog of **75 routes already derived**. |
| [`rr-voice-server`](.claude/skills/rr-voice-server/SKILL.md) | Writing or debugging the voice server: Tachyon handshake, RSA/AES key exchange, encrypt layer, forked NGO, Dissonance relay. |
| [`rr-room-networking`](.claude/skills/rr-room-networking/SKILL.md) | Room/session traffic: Photon vs the dedicated NGO backend, event codes, the join handshake, RPC dispatch, timeouts. |
| [`rr-client-bringup`](.claude/skills/rr-client-bringup/SKILL.md) | The client crashes, quits silently, or never finishes loading a room; choosing an injection vector for a new build. |
| [`il2cpp-analysis`](.claude/skills/il2cpp-analysis/SKILL.md) | Before trusting any obfuscated name, RVA or enum value: carving metadata, driving the toolkit, telling builds apart. |

`il2cpp-tools.zip` holds the scripts the skills invoke. `SCENES.md` is the scene-location GUID
table; `INVENTIONS.md` covers the invention pipeline.

## Two things to know before using any of this

**Obfuscated names and RVAs are per-build and re-roll on every client update.** Enum member names and
values, compiler-generated names, Utf8Json key literals and `[DataMember]` renames survive; nothing
else does. Every note states the build it was derived from — `20250718.01` unless it says otherwise.
Identify your build first (`il2cpp-analysis`), because a name resolved against the wrong one comes
back plausible and wrong rather than empty.

**Wire shapes transfer between builds; names and offsets do not.** That is what makes the
`wire-shapes` catalog worth keeping. Where a shape genuinely differs between builds, the note says so
— see `playerevent-tags-build-difference`.

## Corrections are kept, not overwritten

Several notes record a conclusion that was wrong first time and what the evidence actually showed —
`elhkhfjehlm-verb-dependent-params` (parameters are verb-dependent, not always query-string),
`rooms-showcase-wire-shape` (envelope status is per-helper, not per-facade),
`platformnotifications-wire-shapes` (paged object, not a bare array). They are kept in that form on
purpose: the wrong reading is usually the *plausible* one, so knowing it was tried is worth as much
as the answer.
