# Privileges me restrictions wire shape

> Wire shape of GET privileges/me/restrictions — it is on the AUTH service (svc 1), not Accounts, and returns a bare array of 8-key restriction records.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://auth.<host>/privileges/me/restrictions` — **GET**, no query params, no body,
auth-scoped. Service is **1 = Auth** (`mov r8d, 1` before `AKJEAMCCEOH..ctor`) — *not* Accounts (11)
or API (2), which is the guess the path invites. Whole call is `PHAEJFAEGAF.NKHGCMDLKAF()` at
`0x7C967E0`, non-async, wrapped in the catch-and-log helper with "Error retrieving account
restrictions".

Response is a **bare array**, `List<NIFFCIOCJAI>` — no envelope. Element formatter `PCFDIIJBGLB`
ctor `0x76BC910`, 8 keys in `____stringByteKeys` order: `AccountId` int 0x10, `Name` string 0x18,
`Description` string 0x20, `EndDate` DateTime? 0x28, `AssociatedAccountId` int? 0x38,
`AssociatedAccountUsername` string? 0x40, `ReportCategory` enum? 0x48, `DisplayReason` string? 0x50.
`CPOBHIECLEN` is the `0xA60520` no-op — no validation, and an empty array is the normal
unrestricted response.

`ReportCategory` `NDIGFGBCINJ.DGJGKHDFDCN`: Moderator -1, Unknown 0, DEPRECATED_MicrophoneAbuse 1,
Harassment 2, Cheating 3, DEPRECATED_ImmatureBehavior 4, AFK 5, Misc 6, Underage 7, VoteKick 10,
MisleadingPurchases 11, CoC_Underage 100, CoC_Sexual 101, CoC_Discrimination 102, CoC_Trolling 103,
CoC_NameOrProfile 104, InappropriateClothing 200, IssuingInaccurateReports 1000,
RoomInventoryItems 1100, InappropriateRooms 1101, InappropriateInventions 1102, RoomOffers 1103,
Spam 1200.

The only caller is `MKMKKJMJNIN.OGLLJECKMIK` (`0x1009630`), which just clears and refills a list —
it references **no string literals**, so `Name` is never matched against hardcoded values. `Name` /
`Description` / `DisplayReason` are display text only; gating is driven by the presence of a record
and its `EndDate`.

**Why:** the `privileges/*` prefix sits on Auth, so pointing it at an accounts/api host is the easy
mistake.

**How to apply:** `il2cpp-2025/callxref.py <rva>` (added 2026-08-17) finds direct `E8`/`E9` callers
over the decrypted image — `callers.py` cannot run here because it needs Il2CppDumper's
`script.json`. See [recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).
