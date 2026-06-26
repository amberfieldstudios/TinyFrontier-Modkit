# PropHunt Mod Kit

Editor-only plugin that lets map creators publish PropHunt custom maps to the Steam
Workshop. It is **disabled by default** and is intended to be shipped inside the Mod Kit
project given to creators - it is NOT enabled in the shipping game.

See the full creator workflow in [`docs/workshop/README.md`](../../docs/workshop/README.md).
Players download the packaged Mod Kit from the
[Releases page](https://github.com/AmberfieldStudios/TinyFrontier-Modkit/releases/latest).

## Enabling

In the Mod Kit copy of the project, enable the plugin (Edit -> Plugins -> "PropHunt Mod
Kit", or set `"Enabled": true` for `PropHuntModKit` in the `.uproject`'s plugin list) and
restart the editor. The Steam client must be running and logged in, and a
`steam_appid.txt` containing `4133940` must sit next to the editor executable.

## What it provides

`UWorkshopUploadTool` (`Source/PropHuntModKit/Public/WorkshopUploadTool.h`) - a
`BlueprintType` / `CallInEditor` object wrapping the Steamworks `ISteamUGC` flow:

| Function | Purpose |
|----------|---------|
| `IsSteamReady()` | Check Steam + UGC are available. |
| `PublishNewItem(ContentFolder, Title, Description, PreviewImagePath)` | Create a new Workshop item and upload the content folder. Returns the new `PublishedFileId`. |
| `UpdateExistingItem(PublishedFileId, ContentFolder, Title, Description, PreviewImagePath, ChangeNote)` | Re-upload content/metadata to an existing item. |

`ContentFolder` must contain the cooked **`.pak`**, a **`meta.json`** (schema in the docs),
and a **preview image**. The call blocks the editor (pumping Steam callbacks) until the
upload completes or times out - this is acceptable for a manual editor tool.

### Driving it

A ready-made driver ships in `Scripts/publish_test_item.py`. Edit the settings block at the
top (content folder, preview, title/description; leave `PUBLISHED_FILE_ID` empty to create a
new item) and run it from the editor's Python console (Output Log -> Cmd: Python):

```python
exec(open(r"<ModKit>\Plugins\PropHuntModKit\Scripts\publish_test_item.py").read())
```

It spawns a `UWorkshopUploadTool`, calls `PublishNewItem` (or `UpdateExistingItem`), and
logs the returned `FWorkshopPublishResult.Message` and `PublishedFileId`. If
`bNeedsLegalAgreement` is true, open the item's Steam page to accept the Workshop Legal
Agreement. (You can also wrap the same object in an Editor Utility Widget if you prefer a UI.)

### Scripts

| Script | Purpose |
|--------|---------|
| `Scripts/create_map_template.py` | Generates a starting map (`/Game/WorkshopMaps/<MapName>/<MapName>`) with a floor, player starts, nav-mesh bounds, and a boundary volume. Set `MAP_NAME` then run in the Python console. |
| `Scripts/publish_test_item.py` | Publishes/updates a Workshop item via `UWorkshopUploadTool` (see "Driving it"). |

## Notes

- Steam UGC calls are Win64-only (`WITH_PROPHUNT_MODKIT_STEAM`); on other platforms the
  tool compiles but reports unavailable.
- The Steamworks SDK comes from the engine's `OnlineSubsystemSteam` third-party module, so
  no separate SDK download is needed.
