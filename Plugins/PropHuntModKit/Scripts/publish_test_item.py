# Drives UWorkshopUploadTool to publish (or update) a PropHunt Workshop item from the
# Unreal Editor's Python console - no Editor Utility Widget needed.
#
# Requirements (see docs/workshop/README.md):
#   - Win64 editor build of the project with the PropHuntModKit plugin enabled.
#   - Steam client running + logged in, and steam_appid.txt (4133940) next to the editor exe.
#
# Usage in the editor Python console (Window -> Output Log -> Cmd: "Python"):
#   exec(open(r"F:\PropHunt\prophunt\Plugins\PropHuntModKit\Scripts\publish_test_item.py").read())
#
# To UPDATE an existing item instead of creating a new one, set PUBLISHED_FILE_ID below.

import unreal

# ---------------------------------------------------------------------------
# Config - edit these for your test item.
# ---------------------------------------------------------------------------
CONTENT_FOLDER = r"F:\PropHunt\docs\workshop\test-item"          # folder with pak + meta.json + preview
PREVIEW_IMAGE  = r"F:\PropHunt\docs\workshop\test-item\preview.png"
TITLE          = "PropHunt Pipeline Test"
DESCRIPTION    = "Internal test item to validate the PropHunt Workshop pipeline. Hidden."
CHANGE_NOTE    = "Pipeline test upload."
PUBLISHED_FILE_ID = ""   # leave "" to create a new item; set the decimal id to update.
# ---------------------------------------------------------------------------


def _read(result, name):
    """Read a struct field robustly regardless of Python naming conversion."""
    try:
        return result.get_editor_property(name)
    except Exception:
        return None


def main():
    tool = unreal.WorkshopUploadTool()

    ready = tool.is_steam_ready()
    if not ready:
        unreal.log_error(
            "[Workshop] Steam UGC is NOT available. Check: Steam client running + logged in, "
            "steam_appid.txt (4133940) next to the editor exe, and this is a Win64 build."
        )
        return

    unreal.log("[Workshop] Steam is ready. Submitting item (the editor will freeze until done)...")

    if PUBLISHED_FILE_ID.strip():
        result = tool.update_existing_item(
            PUBLISHED_FILE_ID.strip(), CONTENT_FOLDER, TITLE, DESCRIPTION, PREVIEW_IMAGE, CHANGE_NOTE
        )
    else:
        result = tool.publish_new_item(CONTENT_FOLDER, TITLE, DESCRIPTION, PREVIEW_IMAGE)

    success = _read(result, "bSuccess")
    file_id = _read(result, "PublishedFileId")
    message = _read(result, "Message")
    needs_agreement = _read(result, "bNeedsLegalAgreement")

    if success:
        unreal.log("[Workshop] SUCCESS: %s" % message)
        unreal.log("[Workshop] PublishedFileId: %s" % file_id)
        unreal.log("[Workshop] Item page: https://steamcommunity.com/sharedfiles/filedetails/?id=%s" % file_id)
    else:
        unreal.log_error("[Workshop] FAILED: %s" % message)
        if file_id:
            unreal.log_error("[Workshop] (item id created: %s)" % file_id)

    if needs_agreement:
        unreal.log_warning(
            "[Workshop] You must accept the Steam Workshop Legal Agreement on the item's page "
            "before it can be made visible: "
            "https://steamcommunity.com/sharedfiles/filedetails/?id=%s" % (file_id or "")
        )


main()
