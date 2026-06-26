"""
fix_prop_cpu_access.py  -  PropHunt Mod Kit: enable Allow CPUAccess on tagged props.

WHY THIS EXISTS
    Hiders paint on a runtime auto-unwrapped copy of the prop they disguise as. At
    disguise time the game copies the prop's geometry into a dynamic mesh and gives every
    face its own packed UV island. That copy reads CPU-side mesh data, which Unreal STRIPS
    from cooked static meshes unless the asset has "Allow CPUAccess" enabled. In a packaged
    build the copy then yields 0 triangles and the painter drops to a static fallback that
    paints on the prop's authored (often overlapping) UVs - the "wrong layout / shared UVs"
    bug.

WHAT THIS DOES
    Finds every StaticMesh under /Game that is tagged as a disguiseable prop
    (Prop Tag (PropHunt) / UPropTagAssetUserData with bCanDisguiseAs == True - the same tag
    the game reads at runtime), enables Allow CPUAccess on it, and saves it. Scoping to
    tagged props keeps the extra CPU-side memory limited to the meshes that actually need
    it. Re-run whenever new props are tagged, then re-cook your map.

HOW TO RUN (from the Mod Kit project)
    Requires the Python Editor Script Plugin (enabled in prophunt.uproject).
      - Editor:  Tools > Execute Python Script... and pick this file, or
      - Console: exec(open(r"<ModKit>\\Plugins\\PropHuntModKit\\Scripts\\fix_prop_cpu_access.py").read())
    Pass --dry-run to list matches without modifying assets.
"""

import sys
import unreal

DRY_RUN = "--dry-run" in sys.argv


def _read_prop_tag(static_mesh):
    """Return the UPropTagAssetUserData on the mesh, or None.

    Tries the AssetUserData interface accessor first, then a manual scan of the
    asset_user_data array, so it survives differences in Python API exposure.
    """
    tag_class = getattr(unreal, "PropTagAssetUserData", None)
    if tag_class is None:
        # The Mod Kit runtime module isn't loaded / the class isn't reflected to Python.
        return None

    # Preferred: the IInterface_AssetUserData accessor.
    try:
        tag = static_mesh.get_asset_user_data_of_class(tag_class)
        if tag is not None:
            return tag
    except Exception:
        pass

    # Fallback: scan the asset_user_data array directly.
    try:
        for entry in static_mesh.get_editor_property("asset_user_data") or []:
            if isinstance(entry, tag_class):
                return entry
    except Exception:
        pass

    return None


def _can_disguise_as(tag):
    """Read bCanDisguiseAs across possible Python property-name spellings."""
    for name in ("can_disguise_as", "b_can_disguise_as"):
        try:
            return bool(tag.get_editor_property(name))
        except Exception:
            continue
    # If the tag exists but we can't read the flag, treat the mesh as a prop (the tag's
    # presence already marks intent); default for the property is True anyway.
    return True


def main():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()

    # Asset paths only (don't force-load everything up front); load lazily per asset.
    static_mesh_class = unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")
    asset_datas = registry.get_assets_by_class(static_mesh_class, search_sub_classes=True)

    changed, already_ok, skipped_errors = [], [], []
    examined = 0

    with unreal.ScopedSlowTask(len(asset_datas), "Scanning static meshes for prop tags") as task:
        task.make_dialog(True)
        for asset_data in asset_datas:
            if task.should_cancel():
                break
            task.enter_progress_frame(1)

            package_name = str(asset_data.package_name)
            if not package_name.startswith("/Game"):
                continue  # ignore engine/plugin content

            examined += 1
            try:
                mesh = asset_data.get_asset()
            except Exception as exc:
                skipped_errors.append((package_name, "load failed: %s" % exc))
                continue
            if mesh is None:
                continue

            tag = _read_prop_tag(mesh)
            if tag is None or not _can_disguise_as(tag):
                continue  # not a disguiseable prop

            if bool(mesh.get_editor_property("allow_cpu_access")):
                already_ok.append(package_name)
                continue

            if DRY_RUN:
                changed.append(package_name + "  (dry-run, not saved)")
                continue

            try:
                mesh.set_editor_property("allow_cpu_access", True)
                unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
                changed.append(package_name)
            except Exception as exc:
                skipped_errors.append((package_name, "save failed: %s" % exc))

    # ---- Report -------------------------------------------------------------
    unreal.log("=" * 72)
    unreal.log("[fix_prop_cpu_access] %sexamined %d /Game static meshes"
               % ("DRY-RUN: " if DRY_RUN else "", examined))
    unreal.log("[fix_prop_cpu_access] enabled Allow CPUAccess on %d prop mesh(es):" % len(changed))
    for p in changed:
        unreal.log("    + %s" % p)
    if already_ok:
        unreal.log("[fix_prop_cpu_access] %d prop mesh(es) already had CPUAccess:" % len(already_ok))
        for p in already_ok:
            unreal.log("    = %s" % p)
    if skipped_errors:
        unreal.log_warning("[fix_prop_cpu_access] %d asset(s) skipped due to errors:" % len(skipped_errors))
        for p, why in skipped_errors:
            unreal.log_warning("    ! %s  (%s)" % (p, why))
    if not changed and not already_ok:
        unreal.log_warning("[fix_prop_cpu_access] No Prop Tag (PropHunt) meshes found. "
                           "Confirm props are tagged and the Mod Kit plugin is enabled.")
    unreal.log("=" * 72)


if __name__ == "__main__":
    main()
