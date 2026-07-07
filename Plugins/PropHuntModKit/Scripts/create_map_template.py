# Creates a starting PropHunt map template with the actors the game mode needs.
#
# Workshop maps ship as DLC, and Unreal only packages DLC content that lives INSIDE a
# plugin, so your map must live in a content plugin (mounted at "/<PluginName>/..."),
# NOT under "/Game". The shipping game registers that plugin mount at runtime when it
# mounts your Workshop pak, so the map loads by its "/<PluginName>/<MapName>" path.
#
# ONE-TIME SETUP before running this script:
#   1. Edit -> Plugins -> "+ Add" (New Plugin) -> choose "Content Only".
#   2. Name it exactly the same as MAP_NAME below (e.g. "MyAwesomeMap"). Create + restart
#      if prompted so the plugin mounts.
#
# Then run this from the editor Python console (Window -> Output Log -> Cmd: "Python"):
#   exec(open(r"<ModKit>\Plugins\PropHuntModKit\Scripts\create_map_template.py").read())
#
# Then save, build your geometry on top, and continue with the cook + publish steps in the
# creator guide. Edit MAP_NAME below to name your map (keep it short and alphanumeric).

import unreal

# ---------------------------------------------------------------------------
MAP_NAME       = "MyAwesomeMap"   # your map's name. Must match the content plugin you made
                                  # above; also used as the DLC name (-DLCName) + meta path.
PLAYER_STARTS  = 12               # number of spawn points to place in a ring
RING_RADIUS_CM = 1200.0           # spacing of the spawn ring (cm)
FLOOR_SIZE     = 40.0             # floor scale (each engine cube is 100cm; 40 -> 40m)
NAV_SCALE      = 50.0             # nav-mesh bounds volume scale (resize to cover your map)
# ---------------------------------------------------------------------------

# The map lives inside the "<MAP_NAME>" content plugin: mount "/<MAP_NAME>/".
PLUGIN_ROOT  = "/%s" % MAP_NAME
PACKAGE_PATH = "%s/%s" % (PLUGIN_ROOT, MAP_NAME)


def _level_subsystem():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def _actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _spawn(cls, location, rotation=None):
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    return _actor_subsystem().spawn_actor_from_class(cls, unreal.Vector(*location), rot)


def _plugin_is_mounted():
    # The plugin's content mount only exists once the Content-Only plugin has been created.
    return unreal.EditorAssetLibrary.does_directory_exist(PLUGIN_ROOT)


def main():
    import math

    if not _plugin_is_mounted():
        unreal.log_error(
            "[Template] Content plugin '%s' is not mounted. Create it first: "
            "Edit -> Plugins -> + Add -> 'Content Only', name it exactly '%s', then re-run "
            "this script. (Workshop maps must live in a plugin, not under /Game.)"
            % (MAP_NAME, MAP_NAME))
        return

    les = _level_subsystem()

    # New empty level inside the map's content plugin (the mount the game resolves at runtime).
    les.new_level(PACKAGE_PATH)
    unreal.log("[Template] Created new level: %s" % PACKAGE_PATH)

    # Floor: an engine cube scaled flat so creators have something to stand on.
    floor = _spawn(unreal.StaticMeshActor, (0.0, 0.0, -50.0))
    if floor:
        comp = floor.static_mesh_component
        mesh = unreal.load_object(None, "/Engine/BasicShapes/Cube.Cube")
        if mesh:
            comp.set_static_mesh(mesh)
        floor.set_actor_scale3d(unreal.Vector(FLOOR_SIZE, FLOOR_SIZE, 1.0))
        floor.set_actor_label("Floor")

    # Player starts arranged in a ring above the floor.
    for i in range(PLAYER_STARTS):
        ang = (2.0 * math.pi) * (i / float(PLAYER_STARTS))
        x = math.cos(ang) * RING_RADIUS_CM
        y = math.sin(ang) * RING_RADIUS_CM
        yaw = math.degrees(ang) + 180.0  # face the center
        ps = _spawn(unreal.PlayerStart, (x, y, 100.0), unreal.Rotator(0.0, 0.0, yaw))
        if ps:
            ps.set_actor_label("PlayerStart_%02d" % i)

    # Nav-mesh bounds volume so AI/hunters can path. Resize to cover your final playspace.
    nav = _spawn(unreal.NavMeshBoundsVolume, (0.0, 0.0, 0.0))
    if nav:
        nav.set_actor_scale3d(unreal.Vector(NAV_SCALE, NAV_SCALE, 10.0))
        nav.set_actor_label("NavMeshBounds")

    # A blocking volume ceiling/boundary hint (creators should box in their map edges).
    boundary = _spawn(unreal.BlockingVolume, (0.0, 0.0, 1500.0))
    if boundary:
        boundary.set_actor_scale3d(unreal.Vector(NAV_SCALE, NAV_SCALE, 1.0))
        boundary.set_actor_label("Boundary_Ceiling")

    # Save it.
    les.save_current_level()
    unreal.log("[Template] Saved. Build your map on top, then cook + publish.")
    unreal.log("[Template] meta.json mapPackagePath -> %s" % PACKAGE_PATH)
    unreal.log("[Template] cook with: -DLCName=%s" % MAP_NAME)


main()
