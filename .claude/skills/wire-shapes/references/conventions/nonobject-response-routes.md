# Nonobject response routes

> The 145 routes whose response T is a List or scalar — i.e. every endpoint that hard-fails with `Malformed Response: '{}'`. Generated table at il2cpp-2025/nonobject-responses.txt, plus the scan that rebuilds it.

Built **2026-08-24** for build `20250718.01` while diagnosing a `Malformed Response: '{}'`
([ioncmjiacfi-malformed-response](ioncmjiacfi-malformed-response.md)).

**Why the list exists:** a `{}` body deserializes *fine* into any object DTO (every member just takes
its default). It only throws when the expected `T` is a **`List<…>`, an array, or a scalar**
(`int` / `bool` / `string`), because Utf8Json hits `{` where it expects `[` or a literal. So
`Malformed Response: '{}'` narrows the culprit to exactly this set — and the stack trace never names
the endpoint, because everything goes through the shared FIFO queue `CBACIMLIBPF`
([serialized-request-queue-stall](../../../rr-client-bringup/references/serialized-request-queue-stall.md)).

**Table: `C:\Games\recnet-patcher\il2cpp-2025\nonobject-responses.txt`** — `route | T | owner method`,
145 rows. Highlights of the scalar ones (the least obvious):
`api/influencerpartnerprogram/myinfluencer` + `/influencer` → **int**
([influencerpartnerprogram-wire-shape](../endpoints/influencerpartnerprogram-wire-shape.md)); `api/sanitize/v1`, `circuits/instructions`,
`platformid/{0}`, `account/me/createlogintoken`, `upload/roomReportScreenshot` → **string**;
`api/customAvatarItems/v1/itemOwnershipLimit`, `api/customAvatarItems/v1/minPriceForPublicItem`,
`api/players/v1/progression/xpEarnedToday`, `subscription/subscriberCount/{0}` → **int**;
a large family of `bool` routes (`api/roomkeys/v1/owns`, `player/avoidjuniors`,
`voice/requiresModeration`, `ghostProtocol/enabledForPlayer`,
`api/playeritems/v1/isavataritemowned/{0}/{1}`, `club/{0}/hasDisabledClubChat`, …).

**Rebuilding it** (three scripts, all in `il2cpp-2025/`):
1. `py sendscan.py` — walks every `.data` metadata-usage slot, keeps kind-6 MethodRefs whose
   methodDef is `MGPBDIAGCFD::HPBKMCLEANE` or `::CJBFDPLCIEJ`, resolves the generic instantiation and
   keeps the ones whose `T` is list/array/scalar → `_sendtargets.pkl`.
2. `py mxref.py $(slots) > _mx.txt` — the *proven* xref pass. A hand-rolled numpy rip-relative scan
   was tried first and mis-attributed owners (it guessed instruction lengths); use `mxref.py`.
3. `py sendreport.py` — disassembles each owning method with capstone and resolves rip-relative
   operands against `out/stringliteral.json` to recover the route literal. **A raw byte-scan of the
   method's own RVAs finds nothing** — the literals are reached through `.data` slots, so you must
   disassemble.

**How to apply:** when `Malformed Response: '{}'` appears, don't read the stack — grep this table
against the server's access log around that timestamp. A route in it must return `[]` or a bare
scalar; `{}` is never valid for any of them.
