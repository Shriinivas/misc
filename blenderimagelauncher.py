#!/usr/bin/env python3

"""
This script is designed to automate the launching of Blender with image imported as a plane.
Usage: blenderimagelauncher.py <image_path> <options>
Author: Shrinivas Kulkarni (khemadeva@gmail.com)
"""

import sys, os
from typing import List
import bpy, mathutils


def launch(args: List[str], term: str) -> None:
    """Launch Blender with specified arguments in a detached process.

    Args:
        args (List[str]): The command line arguments for Blender.
        term (str): Optional terminal to use for launching Blender.
    """
    import subprocess

    command = (
        ([term] if term else [])
        + [
            "blender",
            "--python",
            os.path.abspath(__file__),
            "--",
            "embedded",
        ]
        + args
    )
    kwargs = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.STDOUT,
        "close_fds": True,
    }

    # Adjust parameters for different operating systems
    if sys.platform.startswith("win"):
        # Windows-specific settings
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
        )
    else:
        # POSIX-specific settings
        kwargs["start_new_session"] = True

    # Start the subprocess detached from the parent process
    subprocess.Popen(command, **kwargs)


def import_svg(svg_file_path):
    before_import = set(obj.name for obj in bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=svg_file_path)
    after_import = set(obj.name for obj in bpy.data.objects)
    # Determine newly added objects by finding the difference
    new_objects = after_import - before_import
    if new_objects:
        # Just take one of the new objects to find the collection
        new_obj_name = next(iter(new_objects))
        return bpy.data.objects[new_obj_name]
    return None


def get_svg_bound_box(svg_obj):
    if svg_obj:
        # Find the parent collection of the active object
        parent_collection = (
            svg_obj.users_collection[0] if svg_obj.users_collection else None
        )

        if parent_collection:
            # Calculate the combined bounding box of all objects in the collection
            min_x, min_y, min_z = (float("inf"), float("inf"), float("inf"))
            max_x, max_y, max_z = (float("-inf"), float("-inf"), float("-inf"))

            for obj in parent_collection.objects:
                if obj.type == "CURVE" and obj.bound_box:
                    bbox_corners = [
                        obj.matrix_world @ mathutils.Vector(corner)
                        for corner in obj.bound_box
                    ]
                    for corner in bbox_corners:
                        min_x = min(min_x, corner.x)
                        max_x = max(max_x, corner.x)
                        min_y = min(min_y, corner.y)
                        max_y = max(max_y, corner.y)
                        min_z = min(min_z, corner.z)
                        max_z = max(max_z, corner.z)
            return (min_x, min_y, min_z, max_x, max_y, max_z)


def setup(
    image_path: str,
    keep_cube: bool,
    no_emit: bool,
    no_res: bool,
    no_view: bool,
    no_camera: bool,
    no_light: bool,
    ds_spl: bool,
    en_spl: bool,
) -> None:
    """Script passed to blender from command line, configure the scene based on provided parameters.

    Args:
        image_path (str): Path to the image file.
        keep_cube (bool): If True, keep the default cube.
        no_emit (bool): If True, use a principled shader; otherwise use an emission shader.
        no_res (bool): If True, do not adjust the render resolution to match the image.
        no_view (bool): If True, do not adjust the 3D view to fit the imported image.
        no_camera (bool): If True, do not adjust the camera settings.
        no_light (bool): If True, do not adjust lighting settings.
        ds_spl (bool): If True, disable splash screen
        en_spl (bool): If True, enable splash screen
    """

    c = bpy.context
    d = bpy.data
    o = bpy.ops

    if not keep_cube:
        d.objects.remove(d.objects["Cube"], do_unlink=True)

    if ds_spl:
        c.preferences.view.show_splash = False
    if en_spl:
        c.preferences.view.show_splash = True

    is_svg = False
    dims = None
    location = (0, 0, 0)
    if image_path.endswith(".svg"):
        is_svg = True
        # Import SVG
        obj = import_svg(image_path)
        bbox = get_svg_bound_box(obj)
        print(bbox, obj)
        if bbox:
            dims = [bbox[3] - bbox[0], bbox[4] - bbox[1]]
            location = [bbox[0] + dims[0] / 2, bbox[1] + dims[1] / 2, 0]
    else:
        # Ensure the 'Import Images as Planes' add-on is enabled
        o.preferences.addon_enable(module="io_import_images_as_planes")
        shader = "PRINCIPLED" if no_emit else "EMISSION"
        o.import_image.to_plane(
            files=[{"name": image_path, "name": image_path}],
            directory="",
            shader=shader,
            align_axis="Z+",
            relative=False,
        )

        plane = c.object
        dims = plane.dimensions[:2]
    if not dims:
        return
    max_dim = max(dims)

    if not no_res:
        # Adjust render resolution
        ratio = dims[0] / dims[1]
        r = c.scene.render
        x, y = r.resolution_x, r.resolution_y
        r.resolution_x, r.resolution_y = (
            (int(y * ratio), y) if x < y else (x, int(x / ratio))
        )

    if not no_view:
        # Set the view to rendered mode
        for area in c.screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.shading.type = "RENDERED"
                space.region_3d.view_perspective = "ORTHO"
                space.region_3d.view_rotation = (1.0, 0.0, 0.0, 0.0)

                # Fit the view to the object's bounding box
                space.region_3d.view_location = location
                # Adjust multiplier to suit best fit
                space.region_3d.view_distance = max_dim * 1.5

    if not no_camera:
        camera = d.objects["Camera"]
        camera.location = (*location[:2], 2)
        camera.rotation_euler = (0, 0, 0)
        camera.data.type = "ORTHO"
        camera.data.ortho_scale = max_dim
        camera.hide_set(True)

    if not no_light:
        # Adjust lighting
        c.scene.view_settings.view_transform = "Standard"

        # Setup environment emission node with 0 strength
        world = d.worlds["World"]
        world.use_nodes = True
        nodes = world.node_tree.nodes

        output = (
            [n for n in nodes if n.type == "OUTPUT_WORLD"]
            or [nodes.new(type="ShaderNodeOutputWorld")]
        )[0]

        for input in output.inputs:
            for link in input.links:
                world.node_tree.links.remove(link)

        node = nodes.new(type="ShaderNodeEmission")
        node.inputs["Strength"].default_value = 0.8 if is_svg else 0

        # Link emission to the output node
        world.node_tree.links.new(node.outputs["Emission"], output.inputs["Surface"])


if __name__ == "__main__":
    args = sys.argv[1:]

    if "embedded" in args:
        args = args[args.index("embedded") + 1 :]

        opts = {
            "-kc": 0,
            "-ne": 1,
            "-nr": 2,
            "-nv": 3,
            "-nc": 4,
            "-nl": 5,
            "-ds": 6,
            "-es": 7,
        }
        # keep_cube, no_emit, no_res, no_view, no_camera, no_light, dis_spl, en_spl
        flags = [False] * len(opts)

        image_path = None
        for arg in args:
            if arg in opts:
                flags[opts[arg]] = True
            elif not arg.startswith("-"):
                image_path = arg

        if image_path:
            setup(image_path, *flags)
        else:
            script_name = os.path.basename(__file__)
            print(f"Usage: {script_name} <optional_flags> /path/to/your/image_or_video")
    else:
        terms = [a for a in args if a.startswith("-term=")]
        term = terms[0].split("=")[1] if terms else ""
        launch(args, term)
