#!/usr/bin/env python3

"""
This script is designed to automate the launching of Blender with image imported as a plane.
Usage: blenderimagelauncher.py <image_path> <options>
Author: Shrinivas Kulkarni (khemadeva@gmail.com)
"""

import sys, os
from typing import List


def launch(args: List[str], term="") -> None:
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
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # POSIX-specific settings
        kwargs["start_new_session"] = True

    # Start the subprocess detached from the parent process
    subprocess.Popen(command, **kwargs)


def setup(
    image_path: str,
    keep_cube: bool,
    no_emit: bool,
    no_res: bool,
    no_view: bool,
    no_camera: bool,
    no_light: bool,
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
    """
    import bpy

    c = bpy.context
    d = bpy.data
    o = bpy.ops

    if not keep_cube:
        d.objects.remove(d.objects["Cube"], do_unlink=True)

    # Ensure the 'Import Images as Planes' add-on is enabled
    o.preferences.addon_enable(module="io_import_images_as_planes")
    c.preferences.view.show_splash = False

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
                space.region_3d.view_location = plane.location
                # Adjust multiplier to suit best fit
                space.region_3d.view_distance = max_dim * 1.5

    if not no_camera:
        camera = d.objects["Camera"]
        camera.location = (0, 0, 2)
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
        node.inputs["Strength"].default_value = 0

        # Link emission to the output node
        world.node_tree.links.new(node.outputs["Emission"], output.inputs["Surface"])


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) == 0:
        print(
            f"Usage: {os.path.basename(__file__)} /path/to/your/image.[jpg, png etc.] <optional_flags>"
        )
    elif "embedded" in args:
        args = args[args.index("embedded") + 1 :]
        print(args)
        if len(args) > 0:
            image_path = args[0]
            keep_cube = "keep_cube" in args
            no_emit = "no_emit" in args
            no_res = "no_res" in args
            no_view = "no_view" in args
            no_camera = "no_camera" in args
            no_light = "no_light" in args
            setup(image_path, keep_cube, no_emit, no_res, no_view, no_camera, no_light)
    else:
        term = ""
        if "--term" in args:
            idx = args.index("--term")
            if len(args) > idx + 1:
                term = args[idx + 1]
                args.remove("--term")
                args.remove(term)
        launch(args, term)
