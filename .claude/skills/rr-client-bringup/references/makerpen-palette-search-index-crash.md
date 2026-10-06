# MakerPen palette search ArgumentOutOfRangeException

> `ArgumentOutOfRangeException: Parameter name: index` from `InternalArray__IReadOnlyList_get_Item` under a LINQ `Where(...).Select(...).ToList()` is the MakerPen palette search desyncing its item list from its parallel match list. It is a CLIENT bug in an `async void` callback — no server response shape can cause or fix it.

Diagnosed **2026-10-01** on build `20250718.01` from a live client stack.

## The stack, decoded

```
ArgumentOutOfRangeException: ... Parameter name: index
  System.Array.InternalArray__IReadOnlyList_get_Item[T] (int index)   <- throws
  System.Predicate`1[T].Invoke
  Enumerable+WhereSelectListIterator`2.MoveNext
  Enumerable+WhereSelectEnumerableIterator`2.MoveNext
  List`1.AddEnumerable / List`1..ctor(IEnumerable) / Enumerable.ToList
  GPMLMCMPOLB.NFPDJKOMJHD (IEnumerable items, IReadOnlyList matches, string category)
  GPMLMCMPOLB+ONKCPIMHEGG.ELBLNBEAGBF (IEnumerable items, IReadOnlyList matches)
  ECPBNBCLLDF.OLILHPMOAKI (IReadOnlyList matches)
  HMGPEDOLBIG.INALMJLIPMO (string query, HMGPEDOLBIG+IMAEDBDBGMO callback)
  ExecutionContext.RunInternal
```

| frame | RVA | what it is |
|---|---|---|
| `HMGPEDOLBIG.INALMJLIPMO` | `0x81A34C0` | the **search driver** — `async void` (`AsyncVoidMethodBuilder.Create` at `0x81A351D`); the class also holds a `CancellationTokenSource`, so searches are cancellable/debounced |
| `ECPBNBCLLDF.OLILHPMOAKI` | `0x81A17D0` | delivers results; called from `ECPBNBCLLDF.KGNEFHFNNHF` `0x81A1410`. The class holds **two parallel lists**: `IReadOnlyList<MEHLEKHCIAA>` and `IReadOnlyList<bool>` |
| `GPMLMCMPOLB+ONKCPIMHEGG.ELBLNBEAGBF` | `0x16488B0` | a 0x30-byte closure forwarder; captures `<>4__this` and an **unobfuscated `category` string**, passes it as the third arg |
| `GPMLMCMPOLB.NFPDJKOMJHD` | `0x1612040` | does the `Where(pred).Select(lambda).ToList()`; Select lambda is `<>c.GCOEJGNMEDD` `0x165BE90` |

**`GPMLMCMPOLB` is the MakerPen palette controller** — its 53 fields include
`RecRoom.Tools.MakerPen`, `RRUI.Dialogs.DialogListModel` and the **unobfuscated**
`showAllShapesByDefault`. `MakerPenPaletteSearchScreen` carries methods with the same obfuscated
names (`INALMJLIPMO` `0xE9D820`, `OLILHPMOAKI` `0xE9EDA0`), which is what ties the stack to palette
search rather than some other list UI.

`MEHLEKHCIAA` (typedef #57628) is **3 ints** at `0x10`/`0x14`/`0x18` — a match range/score record, one
per searched entry.

## The mechanism

`NFPDJKOMJHD(items, matches, category)` filters `items` with a predicate that indexes `matches` by a
position derived from `items`. The thrower is `InternalArray__IReadOnlyList_get_Item`, which is the
`IReadOnlyList<T>` implementation **used when the list is actually a `T[]` array** — so `matches` is
array-backed and gets indexed past its end.

That only happens if **`items` is longer than `matches`**: the two were computed against different
snapshots of the palette.

## It is not a server problem

Nothing about a response shape can produce this:

- The palette's item list is **local content**, not an HTTP payload.
- The nearest server-driven list in this area is `api/CircuitChipLists/{name}`
  ([circuitchiplists](../../wire-shapes/references/endpoints/circuitchiplists-wire-shape.md)) — but that is a `List<Guid>` used as a
  **membership check** (`whiteglove1`/`whiteglove2` on `NOEKPCJEAHJ`), not a parallel array feeding
  these predicates. Serving `[]` there is still correct, and unrelated to this crash.

So: do not go looking for a wire shape to fix. The useful conclusion is that this one is out of the
server's hands.

## Likely trigger (inferred, not pinned)

The driver is **`async void`** with a `CancellationTokenSource` — a debounced search. The closure
captures a specific `category`, so a result delivered after the palette's items for that category
changed (new query typed, category switched, palette repopulated) would pair a fresh `items` with a
stale `matches`. Being `async void` is also why it surfaces as a logged `LogException` on the sync
context rather than a handled error.

**I did not pin the desync trigger** — the predicate and the `items`/`matches` producers sit in
generic-shared LINQ code whose call targets fold onto unrelated symbols, so the producer side was not
readable. Treat the race as a hypothesis.

## Impact and what to tell a user

The exception escapes mid-`ToList()`, so the filtered result list is never built: **palette search
returns nothing for that category** while other categories keep working. It is cosmetic-ish and
recoverable — re-running the search usually succeeds, because the second pass sees consistent lists.

If it needs chasing further, instrument `GPMLMCMPOLB.NFPDJKOMJHD` `0x1612040` and log
`items.Count` / `matches.Count` / `category` on entry; one reproduction would confirm the length
mismatch and name the category involved.
