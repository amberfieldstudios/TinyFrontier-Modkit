# TinyFrontier Mod Kit (PropHunt)

Build and publish **custom maps** for PropHunt and ship them to the Steam Workshop. No
gameplay coding required - if you can open Unreal Engine and place actors in a level, you
can make a map.

## Download the Mod Kit

Grab the latest **`PropHunt-ModKit-<version>.zip`** from the Releases page:

**https://github.com/AmberfieldStudios/TinyFrontier-Modkit/releases/latest**

Unzip it to a path with **no spaces** (e.g. `C:\PropHuntModKit`) and open
`prophunt.uproject` with **Unreal Engine 5.7.4**.

## What's in this repo

| Path | What it is |
|------|------------|
| `docs/workshop/STEAM_GUIDE.txt` | Steam-formatted, step-by-step guide for players making maps. |
| `docs/workshop/README.md` | The same creator guide in Markdown (shipped inside the kit as `CREATOR_GUIDE.md`). |
| `tools/package_modkit.ps1` | The script the studio uses to assemble the downloadable Mod Kit zip. |
| `Plugins/PropHuntModKit/` | Source for the in-editor **Publish** tool + the map-template / publish Python scripts. |

> The downloadable Release zip additionally bundles the prebuilt editor plugin binaries and
> the base-game **release version** so your map cooks compatibly. Those large/binary pieces
> are intentionally not stored in this repo.

## Quick start

1. Download + unzip the kit (above) and open it in UE 5.7.4.
2. Follow `docs/workshop/STEAM_GUIDE.txt` to generate a map template, cook it as DLC, and
   publish it to the Workshop from the editor's Python console.

---

(c) Amberfield Studios. Workshop maps are third-party content - only publish assets you have
the right to redistribute.
