# Chat cansenddm wire shape

> Wire shape of GET thread/checkCanSendDirectMessageWithPrivacySetting on the Chat service (svc 9) for recflare-2025 — the body is a BARE integer enum, not an object.

Derived **2026-08-17** from `C:\Games\recflare-2025` (build `20250718.01`) via
[recflare-2025-metadata-carve](../../../il2cpp-analysis/references/recflare-2025-metadata-carve.md).

`GET https://chat.<host>/thread/checkCanSendDirectMessageWithPrivacySetting?receivingPlayerId={int}`
— **GET** (`HttpMethod` statics `+0x08`), service **9 = Chat** (`mov r8d, 9` before
`AKJEAMCCEOH..ctor`). Whole method is `PNAHAINBHAH.IGGKHOJNJMB(int receivingPlayerId)` at
`0x7CB9190` — non-async, one query param added via `MGPBDIAGCFD.ELHKHFJEHLM` as an I4.

**The response body is a bare JSON integer**, e.g. `0`. Not an object, not an envelope, not an
array. `MGPBDIAGCFD.HPBKMCLEANE<TResponse>` is instantiated with `TResponse = OOGFKCNGLBF`
(confirmed by resolving methodSpec inst 16749's generic inst, not inferred), which is a plain int
enum — and no by-name enum formatter exists on this build (the distinctive member names are absent
from the literal table), so it goes over the wire numerically.

`OOGFKCNGLBF` (implicit 0-based): Success 0, InvalidArguments 1, ThreadNotFound 2,
MembershipNotFound 3, PlayerAlreadyOnThread 4, CannotMessagePlayer 5, InvalidCharacters 6,
RecentlyLeftThread 7, ThreadTooLarge 8, InsufficientPermission 9, TooManyAffiliationThreads 10,
UnderModeration 11, MessageNotFound 12, InvalidThreadJoinType 13, PlayerBanned 14,
CannotMessagePlayerDueToLocalPrivacySetting 15, CannotMessagePlayerDueToRemotePrivacySetting 16,
SuccessWithPartialPlayersAddedToThreadDueToPrivacySetting 17,
CannotAddPlayersToThreadDueToPrivacySetting 18,
CannotConvertDirectMessageChatToGroupChatDueToPrivacySetting 19.

The promise is wrapped in the catch-and-log extension `BBHOKCAHEAD<T>` with the message
"Unable to check if DM is allowed with privacy settings", so a transport/parse failure is logged
rather than thrown at the caller.

**Why:** every other RecNet endpoint examined so far returns an object or array, so the instinct is
to wrap this in `{...}` — that fails. The whole body is the number.

**How to apply:** the same enum `OOGFKCNGLBF` is the result type for other `thread/*` chat calls
(`EBODDIHJMLO` etc.), so those are likely bare integers too — check each one's `HPBKMCLEANE`
instantiation before assuming.
