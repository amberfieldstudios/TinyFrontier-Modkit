# PropHunt Steam Workshop - Custom Maps Setup Guide

This is the step-by-step guide for shipping community custom maps via the Steam Workshop.
The in-game code is already implemented (see "What the game already does" below); this
document covers the parts that live **outside the game build**: the Steamworks partner
configuration, generating a base-game release version, the Mod Kit creators use, the
cook-as-DLC step, and how to upload + test.

> App ID: **4133940** (from `prophunt/Config/DefaultEngine.ini`)
> Engine: **Unreal Engine 5.7.4**
> Networking: Steam listen-server P2P (SteamSockets)

---

## 0. What the game already does (implemented)

| Area | Where |
|------|-------|
| Runtime Workshop subsystem (enumerate / download / mount subscribed items) | `prophunt/Source/prophunt/Workshop/WorkshopSubsystem.{h,cpp}` |
| Combined map catalog (built-in + mounted Workshop maps) | `UPropHuntGameInstance::RebuildMapCatalog` |
| Lobby picker shows Workshop maps | `ULobbyWidget::NativeOnInitialized` -> `GI->RefreshWorkshopMaps()` |
| Selected map id replicated to clients | `FMatchSettings::MapPublishedFileId` / `MapPackagePath` |
| Client auto-download + progress overlay | `APropHuntPlayerController::ClientPrepareWorkshopMap` + `UWorkshopDownloadWidget` |
| Host waits for all clients before travel (with timeout) | `ALobbyGameMode::BeginWorkshopReadyGate` / `NotifyWorkshopReady` |
| Steam UGC compile guard | `WITH_PROPHUNT_STEAM_UGC` in `prophunt.Build.cs` (Win64 only) |

The runtime expects each Workshop item to contain:
- a cooked **`.pak`** with the map, and
- a loose **`meta.json`** descriptor (schema in section 4).

Nothing here works in PIE/editor without the Steam client running; Workshop is **Win64
packaged build + Steam** only. In the editor the catalog simply shows the built-in maps.

---

## 1. Steamworks partner site configuration

1. Sign in to <https://partner.steamgames.com> and open app **4133940**.
2. **Enable the Workshop**: `Edit Store Page / Workshop` -> `Workshop Settings` ->
   enable "Ready-to-use items" (so subscribing auto-installs items; this is the model the
   game relies on - subscribed items are downloaded by Steam and mounted at runtime).
3. **Set up Workshop legal agreement**: enable the Steam Workshop Legal Agreement so
   uploaders must accept terms (this complements the in-game Terms of Service).
4. **Define tags** under Workshop settings so players can filter (e.g. a `Type` tag with a
   `Map` value). Recommended baseline tags: `Map`, plus theme tags if you want them.
5. **Publish** the configuration changes (Steam requires publishing partner-site changes).
6. Make sure the **App ID** in `prophunt/Config/DefaultEngine.ini`
   (`[OnlineSubsystemSteam] SteamAppId` / `SteamDevAppId`) matches, and that a
   `steam_appid.txt` containing `4133940` sits next to the packaged executable for local
   testing.

---

## 2. Generate a base-game "release version" (required for DLC cooking)

Workshop maps are cooked as **DLC against a release version** of the base game. The
release version is a snapshot of what content the shipped game already contains, so the
DLC cook only packages the creator's new assets (the map) and references - not the whole
game. The package paths and asset IDs then line up at runtime.

From the engine directory (`F:\Unreal\UE_5.7`), run UAT to cook + create a release
version named e.g. `1.0`:

```bat
"F:\Unreal\UE_5.7\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun ^
  -project="F:\PropHunt\prophunt\prophunt.uproject" ^
  -noP4 -platform=Win64 -clientconfig=Shipping ^
  -cook -stage -pak ^
  -createreleaseversion=1.0
```

This writes the release manifest/asset registry under:

```
F:\PropHunt\prophunt\Releases\1.0\Win64\
```

Distribute the `Releases\1.0\Win64\` folder (specifically `DevelopmentAssetRegistry.bin`
and the manifest) **inside the Mod Kit** so creators can cook against it.

> Re-generate the release version (bump to `1.1`, `2.0`, ...) and re-ship the Mod Kit
> whenever the base game's cooked content changes materially. Maps cooked against an old
> release version may fail to load against a newer base game.

---

## 3. The Mod Kit (what creators use)

The Mod Kit is a trimmed copy of this UE project that lets creators build a map and
publish it. See `prophunt/Plugins/PropHuntModKit/README.md` for the editor upload tool.

> **Players download the Mod Kit here:**
> <https://github.com/AmberfieldStudios/TinyFrontier-Modkit/releases/latest>
> (grab `PropHunt-ModKit-<ver>.zip`, unzip to a path with no spaces, open with UE 5.7.4).
> The kit version must match the `-basedonreleaseversion` used when cooking (section 4).

> **Automated packaging:** `tools/package_modkit.ps1` builds the Mod Kit zip for you -
> it copies the project, excludes transient/dev folders, drops the throwaway `PipelineTest`
> plugin, keeps `PropHuntModKit`, bundles `Releases/<ver>/Win64`, and emits
> `dist/PropHunt-ModKit-<ver>.zip`. **Review the `$ExcludeContentDirs` list at the top of
> the script** (pre-filled with paid packs to exclude) before sharing. Generate the release
> version in the same step with `-GenerateRelease`:
>
> ```powershell
> pwsh -File tools\package_modkit.ps1 -ReleaseVersion 1.0 -GenerateRelease
> ```

To assemble the Mod Kit manually instead:

1. Copy the project, then **remove** content you do not want to ship to creators:
   - gameplay source you don't want exposed can stay (it's needed to open the project),
     but remove proprietary/marketplace asset packs you are not licensed to redistribute
     (e.g. paid Fab packs under `Content/`). Creators only need:
     - the engine + project so the editor opens,
     - the `Releases/1.0/Win64/` release version from section 2,
     - the `PropHuntModKit` plugin (the Publish tool),
     - a map template and any **freely redistributable** props/materials you want them to
       build with.
2. Provide a **map template** (a `.umap` with the spawn points / volumes the game mode
   needs). Document required actors (player starts, nav mesh, kill/boundary volumes).
3. Tell creators to author their map **inside a content plugin named after the map**, NOT
   under `/Game`. Unreal's DLC cook (section 4) only packages content that lives inside the
   named plugin, so a `/Game/...` map cooks to an **empty pak**. The flow is:
   1. In the editor: **Edit -> Plugins -> + Add -> "Content Only"**, name it e.g.
      `MyAwesomeMap`. Restart if prompted so the plugin mounts at `/MyAwesomeMap/`.
   2. Author (or move) the map to **`/<PluginName>/<MapName>`**, e.g.
      `/MyAwesomeMap/MyAwesomeMap`. `Plugins/PropHuntModKit/Scripts/create_map_template.py`
      creates the template level inside the plugin for you (it refuses if the plugin
      isn't created yet).
   3. The shipping game resolves this plugin path at runtime: when it mounts a subscribed
      Workshop pak, `UWorkshopSubsystem::MountWorkshopPak` registers the plugin's content
      mount point (`/<PluginName>/` -> `Plugins/<PluginName>/Content`) so the level loads by
      its `meta.json` path. This is why the map does **not** need to live under `/Game`.

---

## 3a. Make props disguiseable (prop tag + CPU access)

A hider can only disguise as a prop whose **static mesh** is set up for it. This is per-mesh
**asset** data (set once, works everywhere the mesh is placed), so map creators must do it
for each prop they want hiders to hide as. Re-cook (section 4) after changing either.

1. **Prop tag.** Open the Static Mesh asset -> Details -> **Asset User Data** -> **+** ->
   **Prop Tag (PropHunt)**; leave **Can Disguise As** ticked. This adds a
   `UPropTagAssetUserData` (shipped in the `PropHuntModKitRuntime` module, so the same class
   is present in both the Mod Kit and the game). `UDisguiseComponent::CanDisguiseAsMesh()`
   reads it at runtime; untagged meshes are not disguiseable (`bRequirePropTag` defaults on).
2. **Allow CPUAccess.** Tick **Allow CPUAccess** on the same mesh. The disguise copies the
   prop geometry from the cooked render buffers at runtime, which only survive cooking when
   this is enabled; without it the disguise falls back to a non-paintable render of the raw
   mesh. The bundled `Plugins/PropHuntModKit/Scripts/fix_prop_cpu_access.py` enables it in
   bulk on every tagged prop:

```python
exec(open(r"<ModKit>\Plugins\PropHuntModKit\Scripts\fix_prop_cpu_access.py").read())
```

> The tag class lives in the Mod Kit's runtime plugin module specifically so a prop tagged
> by a creator carries the exact `UClass` the shipping game checks. A `CoreRedirect` in
> `DefaultEngine.ini` remaps the old `/Script/prophunt.PropTagAssetUserData` path to it.

---

## 4. Cook a map as DLC + the `meta.json` schema

A creator cooks **only their plugin/map** as DLC against the release version. The map must
live inside a content plugin (section 3); the `-DLCName` you pass **must be that plugin's
name** — UE resolves it to `Plugins/<DLCName>/<DLCName>.uplugin` and packages only that
plugin's content. For a plugin named `MyAwesomeMap`:

```bat
"F:\Unreal\UE_5.7\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun ^
  -project="<ModKitProject>\prophunt.uproject" ^
  -noP4 -platform=Win64 -clientconfig=Shipping ^
  -cook -stage -pak ^
  -basedonreleaseversion=1.0 ^
  -DLCName=MyAwesomeMap -DLCIncludeEngineContent ^
  -unrealexe="F:\Unreal\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
```

> **Why `-unrealexe`?** The Mod Kit is a *content-only* project (no `Source/`, no compiled
> `Binaries/`), but the enabled engine plugins (GeometryScripting, etc.) make UAT treat it as
> code-based and generate a temporary `prophuntEditor` target. UAT then looks for a build
> receipt at `<ModKitProject>\Binaries\Win64\prophuntEditor.target` — which the kit does not
> ship — and cooking fails with `DirectoryNotFoundException: … prophuntEditor.target`.
> Passing `-unrealexe=` points cooking at your **installed engine** editor instead (which
> already has those plugins and loads the bundled `PropHuntModKit` plugin), skipping the
> receipt lookup. **Adjust the path to wherever you installed UE 5.7.4** — it is not always
> `F:\Unreal\UE_5.7`.

The resulting `.pak` (under the DLC staged folder) is the file that goes into the Workshop
item. Alongside it, the creator adds a **`meta.json`** describing the map.

### `meta.json` schema (read by `UWorkshopSubsystem::ParseItemMeta`)

```json
{
  "displayName": "My Awesome Map",
  "mapPackagePath": "/MyAwesomeMap/MyAwesomeMap",
  "pakFile": "MyAwesomeMap.pak",
  "previewImage": "preview.png"
}
```

| Field | Required | Meaning |
|-------|----------|---------|
| `displayName` | recommended | Name shown in the lobby map picker. Falls back to the map filename. |
| `mapPackagePath` | **yes** | Level package path the game travels to. Must be the **plugin** path where the map was authored/cooked, e.g. `/MyAwesomeMap/MyAwesomeMap` (or `/MyAwesomeMap/<Sub>/MyAwesomeMap` if the map sits in a subfolder). NOT a `/Game/...` path. |
| `pakFile` | optional | The `.pak` filename in the item folder. If omitted, the first `*.pak` found is mounted. |
| `previewImage` | optional | Image file in the item folder (also use it as the Workshop preview). |

The final Workshop item folder contains: `MyAwesomeMap.pak`, `meta.json`, `preview.png`.

---

## 5. Upload to the Workshop

Use the in-editor Publish driver shipped with the Mod Kit:
`Plugins/PropHuntModKit/Scripts/publish_test_item.py`. Edit the settings block at the top
(`CONTENT_FOLDER`, `PREVIEW_IMAGE`, `TITLE`, `DESCRIPTION`; leave `PUBLISHED_FILE_ID` empty
to create a new item) then run it from the editor's Python console (Output Log -> Cmd:
Python):

```python
exec(open(r"<ModKit>\Plugins\PropHuntModKit\Scripts\publish_test_item.py").read())
```

It calls `UWorkshopUploadTool`, which wraps `ISteamUGC`: `CreateItem` -> `StartItemUpdate`
-> `SetItemTitle` / `SetItemDescription` / `SetItemPreview` / `SetItemContent` (the folder
containing the pak + meta.json + preview) -> `SubmitItemUpdate`.

Requirements:
- The Steam client must be running and logged in.
- `steam_appid.txt` with `4133940` must sit next to the editor executable used to upload
  (or run the editor through Steam).
- The content folder must contain the cooked `.pak`, `meta.json`, and a preview image.

After submitting, set the item **Visibility** (start with `Hidden` or `Friends only` for
testing) and accept the Workshop Legal Agreement on the item's page.

---

## 6. Testing checklist

Do all of this from a **packaged Win64 Shipping build under Steam** (not PIE):

1. Subscribe to the test Workshop item in the Steam client.
2. Launch the game; let Steam install the item.
3. In the lobby, open the map picker - the Workshop map should appear after the built-in
   maps (check the log channel `LogPropHuntWorkshop` if it does not - "missing/invalid
   meta.json or pak" means the item layout is wrong; "failed to mount" means the pak path
   is wrong).
4. Solo: pick the Workshop map and start a match - it should travel and load.
5. Two-player (a friend who has **not** subscribed):
   - host picks the Workshop map and presses Create Match,
   - the client should show the **download overlay** with a progress bar
     (`UWorkshopDownloadWidget`), auto-subscribe + download, then travel with the host,
   - confirm the host waits for the client and only travels once they report ready
     (log: `workshop ready gate - waiting on N client(s)` then `all clients ready`).
6. Failure path: have a client decline/block the download and confirm the host times out
   after `WorkshopReadyTimeoutSeconds` (default 180s) and stays in the lobby instead of
   stranding everyone.

---

## 7. Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| Workshop maps never appear in the picker | Not a packaged Steam build; or `meta.json` missing/invalid; check `LogPropHuntWorkshop`. |
| Map appears but travel fails on clients | Map cooked against the wrong release version; re-cook DLC with the correct `-basedonreleaseversion`. |
| Host travels before clients are ready | Map was treated as built-in (empty `MapPublishedFileId`) - confirm the entry's `Source` is `Workshop` in the catalog. |
| `failed to mount` in logs | `pakFile` path wrong, or the pak is corrupt / not a valid UE pak. |
| Editor compile error about Steamworks headers | `WITH_PROPHUNT_STEAM_UGC` is Win64-only by design; building another platform disables UGC (expected). |

---

## 8. Legal note

The first-launch Terms of Service (implemented in `ULegalConsentWidget`) already discloses
that Workshop content is third-party content used at the player's own risk, and that this
is a multiplayer game. That text is a **template, not legal advice** - have a lawyer review
it (and your Privacy Policy) before release, and fill in the bracketed placeholders. Bump
`UPropHuntLegalSave::CurrentTOSVersion` when the terms change so players re-accept.
