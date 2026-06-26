# Creates a starting PropHunt map template with the actors the game mode needs, saved to
#   /Game/WorkshopMaps/<MAP_NAME>/<MAP_NAME>
#
# Run it from the editor Python console (Window -> Output Log -> Cmd: "Python"):
#   exec(open(r"<ModKit>\Plugins\PropHuntModKit\Scripts\create_map_template.py").read())
#
# Then save, build your geometry on top, and continue with the cook + publish steps in the
# creator guide. Edit MAP_NAME below to name your map (keep it short and alphanumeric).

import unreal

# ---------------------------------------------------------------------------
MAP_NAME       = "MyAwesomeMap"   # your map's name (also used as the DLC name + meta path)
PLAYER_STARTS  = 12               # number of spawn points to place in a ring
RING_RADIUS_CM = 1200.0           # spacing of the spawn ring (cm)
FLOOR_SIZE     = 40.0             # floor scale (each engine cube is 100cm; 40 -> 40m)
NAV_SCALE      = 50.0             # nav-mesh bounds volume scale (resize to cover your map)
# ---------------------------------------------------------------------------

PACKAGE_PATH = "/Game/WorkshopMaps/%s/%s" % (MAP_NAME, MAP_NAME)


def _level_subsystem():
    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def _actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def _spawn(cls, location, rotation=None):
    rot = rotation or unreal.Rotator(0.0, 0.0, 0.0)
    return _actor_subsystem().spawn_actor_from_class(cls, unreal.Vector(*location), rot)


def main():
    import math

    les = _level_subsystem()

    # New empty level at the Workshop content path the game scans.
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


main()
