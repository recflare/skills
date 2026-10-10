# The Account DTO (`.PHCHGFEEEMG`) — 13 keys, and there is NO verified badge

> The 2025 Account DTO has **exactly 13 wire keys**: `AccountId`, `UserName`, `DisplayName`,
> `DisplayEmoji`, `ProfileImage`, `BannerImage`, `TreatAsJunior`, `HasBirthday`, `PersonalPronouns`,
> `IdentityFlags`, **`createdAt`** (lowercase), `IsMetaPlatformBlocked`, `IsJunior`.
> **There is no `IsVerified`, no `VerifiedAt`, no badge flag of any kind on the account.** Every
> "Verified" string in the build belongs to the **incentivized-referral** feature; phone and email
> verification are separate account-security flows with no public marker.

Derived **2026-10-08** from build `20250718.01`, answering "is there a verified badge on the
account". `.PHCHGFEEEMG` (typedef #21674) is the payload of the **`AccountUpdate`** and
`SelfAccountUpdate` pushes ([notification-types-2025](notification-types-2025.md)) and the shape every account-bearing
route returns.

Formatter **`DJIBEJJCLBG` `.ctor 0x762F0B0`** (+0x11E0), `____stringByteKeys` run
`0x762FDA3`..`0x7630133`:

| # | key | CLR | off |
|---|---|---|---|
| 1 | `AccountId` | `ObscuredInt` | 0x18 |
| 2 | `UserName` | `ObscuredString` | 0x30 |
| 3 | `DisplayName` | `ObscuredString` | 0x38 |
| 4 | `DisplayEmoji` | `ObscuredString` | 0x40 |
| 5 | `ProfileImage` | `ObscuredString` | 0x48 |
| 6 | `BannerImage` | `ObscuredString` | 0x50 |
| 7 | `TreatAsJunior` | `ObscuredBool` | 0x60 |
| 8 | `HasBirthday` | `ObscuredBool` | 0x6c |
| 9 | `PersonalPronouns` | enum `.OOCDMFJLNGG` | 0x78 |
| 10 | `IdentityFlags` | enum `.EFFHBNIFNBE` | 0x7c |
| 11 | **`createdAt`** | DateTime | 0x80 |
| 12 | `IsMetaPlatformBlocked` | bool | 0x88 |
| 13 | `IsJunior` | **`bool?`** | 0x89 |

⚠️ **`createdAt` is lowercase in the byte-keys run** — a `[DataMember]` rename, the same pattern as
`error_id`. Everything else is PascalCase. The deserialize automata still accepts
`CreatedAt`/`createdAt`/`createdat`, but lowercase is what the client *emits*, so match it.

All the `Obscured*` types are plain JSON numbers / strings / bools on the wire — the obfuscation is
in-memory only ([inventions-v2-search](inventions-v2-search-wire-shape.md) records the same).

The type declares **17** fields: three (`0x00`/`0x08`/`0x10`) are plain non-property fields and never
serialize, and of the six `ObscuredString` auto-properties only **five** have keys — one at `0x58` is
`[IgnoreDataMember]`. 14 auto-properties, 13 keys.

## The two flags enums are identity, not verification

`PersonalPronouns` — `.OOCDMFJLNGG : int` (bit flags):
`None 0`, `SheHer 1`, `HeHim 2`, `TheyThem 4`, `ZeHir 8`, `ZeZir 16`, `XeXem 32`.

`IdentityFlags` — `.EFFHBNIFNBE : int` (bit flags):
`None 0`, `LGBTQIA 1`, `Transgender 2`, `Bisexual 4`, `Lesbian 8`, `Pansexual 16`, `Asexual 32`,
`Intersex 64`, `Genderqueer 128`, `Nonbinary 256`, `Aromantic 512`.

`IdentityFlags` is the obvious place a "verified" bit might hide. It is not there — it is the
pride/identity display feature. Both are **bitmasks**, so send a summed integer, not an array.

## The hook is a normalizer, not a validator

`PHCHGFEEEMG.CPOBHIECLEN` is **`0x7C97400`** (+0x100) — a real body, not the shared `0xA60520` stub.
It opens:

```asm
movzx eax, word ptr [rbx + 0x89]   ; Nullable<bool> IsJunior: al = hasValue, ah = value
test  al, al
jne   0x7C97484                    ; has a value -> skip
                                   ; otherwise derive it
```

So it **back-fills `IsJunior` when the key is absent** rather than rejecting the payload. Omitting
`IsJunior` is safe; so is omitting any other key. Another case of the standing rule: a non-stub
`CPOBHIECLEN` RVA does not mean validation ([subroom-save-by-id](subroom-save-by-id-wire-shape.md) has the same trap).

## What "Verified" actually is in this build

Searching the metadata for `Verifi*` turns up a lot, and **none of it is an account badge**:

| thing | what it really is |
|---|---|
| `'VerifiedAt'` (literal `0xD052730`) | a key on **`.AEGIJHINBFD`**, the **referral** DTO — formatter `KJJPHMIOGJB` `.ctor 0x7889A80`, 3 keys: `InviteeAccountId` (int), `CreatedAt` (DateTime), `VerifiedAt` (`DateTime?`). Payload of the `IncentivizedReferralUpdate` push. |
| `VerifiedTextImpl` `0x27C5BC0`, `VerifiedDateImpl` `0x27C5970`, `HideIfNotVerifiedImpl` `0x27AF580` | all three bind `RRUI.Data.ControllerImplementation<T>` with **inst #11551 = `RRUI.Data.PlayerReferralModel`** and test a `Nullable<DateTime>` (inst #3312). `VerifiedDateImpl` formats it `'MMMM dd, yyyy'`. Pure referral UI. |
| `VerifiedFriendCountTextImpl`, `HideIfNoVerifiedReferralsImpl`, `HideIfHasVerifiedReferralsImpl`, `get_ReferralsVerifiedCount` | same feature, the "how many invited friends got verified" counters |
| `VerifiedPhone`, `PhoneVerificationIcon`, `VerificationCodeSent`, `EnterCodeForVerification` | **phone** verification — an account-security flow |
| `PendingEmailVerification`, `EmailVerificationTextImpl`, `'Waiting for email verification'` | **email** verification — likewise |
| `IVerifier`, `TlsSrpGroupVerifier`, `VerifierFactory`, … | BouncyCastle TLS. Noise. |
| `'Images.VerifySignature'`, `'Image signature verification failed'` | the image content-signature check, unrelated |

So "verified" in Rec Room 2025 means *a referred friend completed signup*, or *a phone/email was
confirmed*. **Neither surfaces as a flag on the account object**, and nothing renders a badge from
one.

## The closest thing to a public badge

The nametag label system, which is a **client-side opt-in driven by a JWT role**, not an account
field: `Developer` / `Community Team` / `Volunteer Mod`. See
[jwt-role-privilege-claims](../conventions/jwt-role-privilege-claims.md). If a self-hosted server wants to mark an account
as special and have it visible to other players, that is the only mechanism this build has.
