# DELETE curatedlists/{listId}/items/{itemId}: remove an item from a curated list

> DELETE curatedlists/{listId}/items/{itemId} (svc 13 Lists) has no params and no body, and returns a BARE `RecNet.Lists.CuratedListDTO`, the same 8-key object as the add. Return the list AFTER the removal: the Saved-for-Later caller caches the returned DTO and reads `ItemIds.Contains(itemId)` on the next toggle. Unlike the add, a `null` body does not NRE, but it drops the client's cached list.

Derived **2026-10-16** from build `20260323.14`, answering "what's the wire shape of
`DELETE https://lists.recflare.net/curatedlists/3437/items/2576`". The add half is
[curatedlists-items-createlistifneeded](curatedlists-items-createlistifneeded-wire-shape.md); read it
for the DTO formatter and the rest of the Saved-for-Later flow.

## The route

```
RecNet.Lists.PZONXXKUWMN.PFKOTQAEFBZ(long listId, string itemId, CancellationToken)
        -> Task<RecNet.Lists.CuratedListDTO>                          0x95E90A0
state machine  <RemoveItemFromCuratedList>d__21$$MoveNext             0x962D470
```

- **Path**: `String.Format("curatedlists/{0}/items/{1}", listId, itemId)` (literal shared with the
  plain add). `{0}` is the **numeric list id**, not the list name. The add-if-needed route uses the
  name; the remove does not.
- **Verb DELETE**: `HttpMethod` statics `[+0x00]` (`mov rsi, [rcx]` at `0x962D58B`).
- **Send** `MSBYXMTYOOH<T>` with generic inst **#3137 = `RecNet.Lists.CuratedListDTO`**, so the body is
  a bare `T` ([2026-send-helper-tiers](../conventions/2026-send-helper-tiers.md)). The description
  literal is `'remove item from list'`.
- **No params, no body**: the `Action<RGBOOBRDHEB>` argument is `null` (`mov qword [rsp+0x28], 0`
  at `0x962D5DD`).

## Response: bare `CuratedListDTO`, 8 keys

Same DTO and formatter (`Utf8Json.Formatters.RecNet.Lists.YOMLWJVCRKH`) as the add:
`ListId` long, `CreatorAccountId` int, `Name` string, `Description` string?, `ImageName` string?,
`Type` EntityType (numeric byte), `ItemIds` `IReadOnlyList<string>`, `CreatedAt` DateTime. There is
no post-deserialize hook.

```json
{
  "ListId": 3437,
  "CreatorAccountId": 12345,
  "Name": "__SavedForLater_Rooms",
  "Description": null,
  "ImageName": null,
  "Type": 1,
  "ItemIds": [],
  "CreatedAt": "2026-10-16T18:04:11.482Z"
}
```

`ItemIds` is the list's remaining items as decimal strings, **without `"2576"`**.

## Client-side behaviour

### The `Client` wrapper is null-safe here

`RecNet.Lists.Client.PFKOTQAEFBZ(long, string, ct)` `0x95E1B70` →
`<RemoveItemFromCuratedList>d__25$$MoveNext` `0x95F3E70`:

```
dto = await facade
if (dto != null) Client.VUNVZAUYLFI(dto.ListId, dto)     // cache update, 0x95F40F4..0x95F411B
return dto                                               // no further dereference
```

This differs from the add's wrapper (`<AddItemToCuratedList>d__24`), which re-dereferences the DTO
outside its null guard and NREs.

### The Saved-for-Later caller caches whatever comes back

`<SetRoomSavedForLaterStateAsync>d__142$$MoveNext` (`0x196B7B0`). On the unsave branch
(`desiredState == false`, `0x196BA79`) it:

1. reads the list id from the manager (`[r14+0xB8]`, populated by the earlier
   `GET curatedlists?name=` lookup),
2. calls `Client.PFKOTQAEFBZ(listId, roomId.ToString())` at `0x196BAB6`,
3. jumps to `0x196BBE3`, the **same store the add path uses**:
   `this.<cachedList> (+0xC8) = result`,
4. broadcasts the state change via `OFYRLOBOYPO.YQYHGCYHPMP` `0x196BC2F`.

The next toggle decides saved-vs-not with `cachedList?.ItemIds.Contains(roomId.ToString())`
(`0x196BA49..0x196BA6C`). So:

| answer | what the client does |
|---|---|
| **the list after removal, `ItemIds` without the id** ✅ | cache updated, room reads as unsaved |
| the list with the id **still in** `ItemIds` ❌ | silent: the room still reads as saved, and the next tap sends another DELETE instead of the add |
| `200 null` / `204` ⚠️ | **no NRE**. The cache is set to `null`, so the room reads as unsaved and the next save re-adds by name. It works, but the client has lost its cached copy of the list |
| `{}` ❌ | `ListId 0`, `ItemIds null`. The next toggle calls `Contains` on a null list |
| non-2xx | `RecNetWebException: HTTP Error {0}`, nothing cached |

Whether the generic send helper itself rejects a `null` body first could not be read
(`MSBYXMTYOOH<T>` is generic-shared and absent from `methods.pkl`, as noted for the add). Return
the object either way.

**How to apply:** treat it as read-modify-write. Remove the item from the list named by `{listId}`
(scoped to the caller), then return the updated list. Make it idempotent: removing an item that is
not in the list should still return `200` with the list, because the client retries the DELETE
whenever its cached `ItemIds` still contains the id.
