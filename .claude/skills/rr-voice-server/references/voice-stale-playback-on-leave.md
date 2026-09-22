# Voice stale playback on leave

> "RecRoomVoicePlayback: Failed to find player for voice playback: {id} after {n} updates." repeating forever after a player leaves means the VOICE SERVER never removed them from the Dissonance session — the game dropped them from the room, the voice roster still lists them, and the client cannot clean up a playback object on its own.

Diagnosed **2026-09-21** on build `20250718.01` from a live client log.
Extends [voice-roster-account-id](voice-roster-account-id.md) (the binding chain) and
[dissonance-named-message-framing](dissonance-named-message-framing.md) (the frame the fix goes in).

## Symptom

```
[Warning] RecRoomVoicePlayback: Failed to find player for voice playback: 205 after 72600 updates.
[Warning] RecRoomVoicePlayback: Failed to find player for voice playback: 205 after 73200 updates.
[Warning] RecRoomVoicePlayback: Failed to find player for voice playback: 205 after 73800 updates.
```

One line roughly every 19 s, counter climbing by exactly 600, **never recovering**. The room UI
correctly shows the player as gone.

## It is emitted every 600 updates, forever

`RecRoomVoicePlayback.GBJLCHBJMEK` `0xC34130` holds the retry counter at **`this+0x78`** and logs the
literal (`0xD1DDC50`) from **two** sites: `0xC341E6` (first failure) and `0xC34652` (the periodic
re-warn). The periodic one is gated on a modulo:

```
0xC345ED  mov  eax, 0x1B4E81B5      ; reciprocal for /600
0xC345F2  imul dword ptr [rdi+0x78]
0xC345FF  imul eax, edx, 0x258      ; 0x258 = 600
0xC34605  cmp  dword ptr [rdi+0x78], eax
```

So **`n / 600` is the number of warnings, and `n` is frames since the playback object appeared.**
72,600 updates at ~31.6 Hz ≈ **38 minutes** of retrying — proof the condition is permanent, not a
join/leave race that later resolves.

## Mechanism

Per [voice-roster-account-id](voice-roster-account-id.md), the bind is:

```
BaseVoicePlayback.get_PlayerName()   // the account id as a decimal string, e.g. "205"
  -> Int32.TryParse
  -> Player.GetFromAccountId(205)    // null once the player left the room
  -> warn
```

**Two independent memberships are disagreeing:**

| membership | owned by | state after leave |
|---|---|---|
| room / game (Photon or NGO GameServer) | game server | removed ✅ |
| **Dissonance voice session** | **voice server** | still present ❌ |

Dissonance instantiates exactly one `RecRoomVoicePlayback` prefab **per remote session player** and
destroys it on `OnPlayerLeftSession` — a **server-driven** event. The client will never tear the
object down just because the avatar disappeared, so it ticks and retries indefinitely.

## Fix: broadcast Dissonance `RemoveClient` on disconnect

On player disconnect the voice server must tell the remaining clients, as a stock Dissonance
**`RemoveClient` (MessageType `0`)** packet inside the fork's frame
([dissonance-named-message-framing](dissonance-named-message-framing.md)):

```
u16 NamedMessageType = 2   (DissonanceToClient)
i32 length
<stock Dissonance packet, magic 0x8bc7, type 0 = RemoveClient>
```

⚠️ `NamedMessage.Hash` is a **ushort**, not stock NGO's ulong — writing 8 bytes there eats six bytes
of the payload. The Dissonance packet itself is stock, so the Placeholder Software source is the
reference for the `RemoveClient` body.

`RemoveClient` does **not** appear in the immediate-scan list of message-type bytes in
[dissonance-named-message-framing](dissonance-named-message-framing.md) (1,2,3,4,6,9,0x0A,0x0B). That is expected twice over: those are
the bytes the *client's writers* emit, and `RemoveClient` is server→client; and a literal `0` is
compiled as `xor reg,reg`, which an immediate scan cannot see. Its absence there is not evidence it
is unused.

## Two sub-cases — check which one you are in

1. **The voice server knows the player left but never announces it.** Missing broadcast on the
   disconnect path. The common case.
2. **The voice server still believes they are connected** — leaving the room is not tearing down the
   voice transport, so the session genuinely still holds them. Check whether the departed account's
   voice connection is still open server-side; if so, fix the room-leave → voice-disconnect path and
   add an idle timeout as a backstop.

## Consequences if left unfixed

Each departed player leaks one `RecRoomVoicePlayback` GameObject plus its AudioSource, accumulating
for the lifetime of the client session, and a rejoin by the same account can produce a duplicate
playback for one account id.

## Not the "empty roster" symptom

This is the **inverse** of a roster that never populates — here the roster is *too full*. Do not work
the empty-roster entry: voice is connected, the handshake succeeded, and audio for present players
is fine.
