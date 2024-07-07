#!/usr/bin/env python3

"""
This script is designed to automate the launching of Blender with importing images and SVGs.
Usage: blenderimagelauncher.py <image_or_svg_paths_or_folders> <options>
Author: Shrinivas Kulkarni (khemadeva@gmail.com)
"""

import sys, os
from types import FunctionType
from typing import Any, Dict, List, Optional, Set, Tuple, cast
from pathlib import Path
from glob import glob


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
        # Windows-specific settings (not tested)
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
        )
    else:
        # POSIX-specific settings
        kwargs["start_new_session"] = True

    # Start the subprocess detached from the parent process
    subprocess.Popen(command, **kwargs)


def get_file_list(ip_paths: List[str]) -> List[str]:
    file_list: List[str] = []

    for ip_path in ip_paths:
        path_ip = Path(ip_path)
        if path_ip.is_dir():
            # Images
            extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
            # Videos
            extensions.update({".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv"})
            file_list = sorted(
                [
                    str(f)
                    for f in path_ip.iterdir()
                    if f.suffix in extensions or "*" in extensions
                ]
            )
        else:
            file_list += glob(ip_path)
    return file_list


def import_svg(svg_file_path: str, importer: str) -> Set:
    before_import = set(bpy.data.objects)
    components = importer.split(".")
    mod = bpy
    for comp in components[1:]:
        mod = getattr(mod, comp)
    cast(FunctionType, mod)(filepath=svg_file_path)

    return set(bpy.data.objects) - before_import


def get_svg_bound_box(svg_objs: Set) -> Optional[Tuple[float, ...]]:
    corners = [
        obj.matrix_world @ mathutils.Vector(corner)
        for obj in svg_objs
        if obj.type == "CURVE"
        for corner in obj.bound_box
    ]
    return (
        (
            tuple(min(c[i] for c in corners) for i in range(3))
            + tuple(max(c[i] for c in corners) for i in range(3))
        )
        if corners
        else None
    )


def shift_origin(obj: "bpy.types.Object", origin: "mathutils.Vector") -> None:
    o_loc = obj.location.copy()
    inv_mw = obj.matrix_world.inverted_safe()
    delta = inv_mw @ o_loc - inv_mw @ origin
    for s in cast(bpy.types.Curve, obj.data).splines:
        for bpt in s.bezier_points:
            lht, rht = bpt.handle_left_type, bpt.handle_right_type
            bpt.handle_left_type = bpt.handle_right_type = "FREE"
            bpt.co += delta
            bpt.handle_left += delta
            bpt.handle_right += delta
            bpt.handle_left_type, bpt.handle_right_type = lht, rht
    obj.location = origin


def process_svg(image_path: str, importer: str) -> Optional[Tuple[Any, List[float]]]:
    new_objs = import_svg(image_path, importer)
    bbox = get_svg_bound_box(new_objs)
    if not bbox:
        return None
    dims = [bbox[3] - bbox[0], bbox[4] - bbox[1]]
    obj_origin = mathutils.Vector([bbox[0] + dims[0] / 2, bbox[1] + dims[1] / 2, 0])
    for obj in new_objs.copy():
        if obj.type == "CURVE":
            data = cast(bpy.types.Curve, obj.data)
            # Do some cleanup (single point curves create issue with bound_box)
            if len(data.splines) == 0 or len(data.splines[0].bezier_points) <= 1:
                bpy.data.objects.remove(obj, do_unlink=True)
                new_objs.remove(obj)
            else:
                shift_origin(obj, obj_origin)
                obj.location = (0, 0, 0)
    return new_objs, dims


def process_image(image_path: str, no_emit: bool) -> Optional[Tuple[Any, List[float]]]:
    bpy.ops.preferences.addon_enable(module="io_import_images_as_planes")
    bpy.ops.import_image.to_plane(  # type: ignore
        files=[{"name": image_path}],
        directory="",
        shader="PRINCIPLED" if no_emit else "EMISSION",
        align_axis="Z+",
        relative=False,
    )
    obj = bpy.context.object
    return [obj], obj.dimensions[:2]  # type: ignore


def adjust_render_resolution(first_dims: List[float]) -> None:
    ratio = first_dims[0] / first_dims[1]
    render = bpy.context.scene.render
    x, y = render.resolution_x, render.resolution_y
    render.resolution_x, render.resolution_y = (
        (int(y * ratio), y) if x < y else (x, int(x / ratio))
    )


def set_view_mode(camera_loc: List[float], first_dims: List[float]) -> None:
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            space = cast(bpy.types.SpaceView3D, area.spaces.active)
            space.shading.type = "RENDERED"
            space.region_3d.view_perspective = "ORTHO"
            space.region_3d.view_rotation = (1.0, 0.0, 0.0, 0.0)
            space.region_3d.view_location = camera_loc
            space.region_3d.view_distance = max(first_dims) * 1.5


def setup_camera(camera_loc: List[float], first_dims, margin) -> None:
    camera = bpy.data.objects["Camera"]
    camera.location = (*camera_loc[:2], 2)
    camera.rotation_euler = (0, 0, 0)
    cdata = cast(bpy.types.Camera, camera.data)
    cdata.type = "ORTHO"
    cdata.ortho_scale = max(first_dims) * (1 + margin)
    camera.hide_set(True)


def adjust_lighting() -> None:
    bpy.context.scene.view_settings.view_transform = "Standard"

    world = bpy.data.worlds["World"]
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
    strength = cast(bpy.types.NodeSocketFloat, node.inputs["Strength"])
    strength.default_value = 0
    world.node_tree.links.new(node.outputs["Emission"], output.inputs["Surface"])


def get_override(area_type, region_type) -> Optional[Dict]:
    for area in bpy.context.screen.areas:
        if area.type == area_type:
            for region in area.regions:
                if region.type == region_type:
                    override = {
                        "area": area,
                        "region": region,
                        "screen": bpy.context.screen,
                        "window": bpy.context.window,
                        "blend_data": bpy.context.blend_data,
                    }
                    return override
    return None


def setBg(color=(1, 1, 1, 1)) -> None:
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree
    tree.nodes.new(type="CompositorNodeAlphaOver")
    alpha = cast(
        bpy.types.CompositorNodeAlphaOver,
        tree.nodes.new(type="CompositorNodeAlphaOver"),
    )
    alpha.premul = 1
    cast(bpy.types.NodeSocketColor, alpha.inputs["Image"]).default_value = color

    links = tree.links
    comp = tree.nodes["Composite"]
    links.new(alpha.outputs[0], comp.inputs[0])

    render = tree.nodes["Render Layers"]
    links.new(render.outputs[0], alpha.inputs[2])
    override = get_override("VIEW_3D", "WINDOW")
    if override:
        with bpy.context.temp_override(**override):
            bpy.context.space_data.shading.use_compositor = "ALWAYS"  # type: ignore


def setup_objects(
    ip_paths: List[str],
    no_emit: bool,
    x_offset: float,
    y_offset: float,
    max_width: float,
    col_count: int,
    importer: str,
) -> Tuple[Optional[List[float]], Optional[List[float]]]:
    next_x = 0
    next_y = 0
    row_objs = []
    row_height = 0

    dims: List[float] = [0, 0]
    camera_loc = None
    first_dims = None
    first_iter = True

    def shift_obj_y():
        nonlocal next_y, row_objs, row_height
        next_y -= row_height / 2
        for sobj in row_objs:
            sobj.location[1] += next_y

    image_paths = get_file_list(ip_paths)
    for i, image_path in enumerate(image_paths):
        result = (
            process_svg(image_path, importer)
            if image_path.endswith(".svg")
            else process_image(image_path, no_emit)
        )
        if not result:
            continue
        new_objs, dims = result

        if first_iter:
            first_dims = dims

        if row_objs and (
            (max_width and (next_x + dims[0]) > max_width)
            or (max_width <= 0 and col_count and not i % col_count)
        ):
            shift_obj_y()
            next_y -= row_height / 2 + y_offset
            row_objs, row_height, next_x = [], 0, 0
        next_x += dims[0] / 2
        for j, new_obj in enumerate(new_objs):
            new_obj.location[0] = next_x
            if first_iter and j == 0:
                camera_loc = new_obj.location
        next_x += dims[0] / 2 + x_offset
        row_objs += new_objs
        row_height = max(row_height, dims[1])
        first_iter = False
    shift_obj_y()
    return first_dims, camera_loc


def setup(
    ip_paths: List[str],
    keep_cube: bool,
    no_emit: bool,
    no_res: bool,
    no_view: bool,
    no_camera: bool,
    no_light: bool,
    ds_spl: bool,
    en_spl: bool,
    no_bg: bool,
    margin: float = 0.1,
    x_offset: float = 0.1,
    y_offset: float = 0.1,
    max_width: float = 3,
    col_count: int = 4,
    importer: str = "bpy.ops.import_curve.svg",
) -> None:
    """
    Configure the Blender scene based on provided parameters.

    Args:
        ip_path (str): Path to the directory containing image files or a glob pattern.
        keep_cube (bool): If True, keep the default cube.
        no_emit (bool): If True, use a principled shader; otherwise use an emission shader.
        no_res (bool): If True, do not adjust the render resolution to match the image.
        no_view (bool): If True, do not adjust the 3D view to fit the imported image.
        no_camera (bool): If True, do not adjust the camera settings.
        no_light (bool): If True, do not adjust lighting settings.
        ds_spl (bool): If True, disable splash screen.
        en_spl (bool): If True, enable splash screen.
        no_bg (bool): If True, do not change default compositor background
        margin (float): margin around first image / svg collection in camera view
        x_offset (float, optional): Horizontal spacing between images. Defaults to 0.1.
        y_offset (float, optional): Vertical spacing between rows of images. Defaults to 0.1.
        max_width (float, optional): Maximum width for image layout. Defaults to 3.
        col_count (int, optional): Number of columns in the image layout. Defaults to 4.
                                   Note: This is ignored if max_width has a non-zero positive value.
        importer (str): custom importer for svg import

    Returns:
        None

    Note:
        This function is designed to be called from the command line when running Blender.
        It configures the scene based on the provided parameters, importing and arranging
        images as specified.
    """

    first_dims, camera_loc = setup_objects(
        ip_paths, no_emit, x_offset, y_offset, max_width, col_count, importer
    )
    if first_dims and not no_res:
        adjust_render_resolution(first_dims)

    if first_dims and camera_loc and not no_view:
        set_view_mode(camera_loc, first_dims)

    if first_dims and camera_loc and not no_camera:
        setup_camera(camera_loc, first_dims, margin)

    if not no_light:
        adjust_lighting()

    if not keep_cube:
        bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)

    if not no_bg:
        setBg()

    if ds_spl:
        bpy.context.preferences.view.show_splash = False
    if en_spl:
        bpy.context.preferences.view.show_splash = True


def generate_help(bool_opts, param_opts):
    help_text = "Usage: blender [options] <image_paths>\n\nOptions:\n"
    sw = 15

    for opt, (_, desc) in bool_opts.items():
        help_text += f"  {opt:<{sw}} {desc}\n"

    for opt, (_, typ, default, desc) in param_opts.items():
        help_text += f"  {opt}=<{typ.__name__[0]}>{' '*(sw-len(opt)-4)} {desc} (default: {default})\n"

    help_text += "\n<image_paths> can be directories containing image/svg/video files or glob patterns."
    return help_text


if __name__ == "__main__":
    bool_opts = {
        "-kc": (0, "Keep default cube"),
        "-ne": (1, "Use principled shader instead of emission shader"),
        "-nr": (2, "Do not adjust render resolution to match image"),
        "-nv": (3, "Do not adjust 3D view to fit imported image"),
        "-nc": (4, "Do not adjust camera settings"),
        "-nl": (5, "Do not adjust lighting settings"),
        "-ds": (6, "Disable splash screen"),
        "-es": (7, "Enable splash screen"),
        "-nb": (8, "Do not change default compositor background"),
    }

    param_opts = {
        "-margin": (0, float, 0.1, "Set margin around first image/SVG"),
        "-x_off": (1, float, 0.1, "Set horizontal spacing between images"),
        "-y_off": (2, float, 0.1, "Set vertical spacing between images"),
        "-max_w": (3, float, 5.0, "Set maximum width for image layout"),
        "-col_cnt": (
            4,
            int,
            4,
            "Set number of columns in image layout (ignored if -max_w is set)",
        ),
        "-importer": (
            5,
            str,
            "bpy.ops.import_curve.svg",
            "Set custom importer for SVG import",
        ),
    }
    args = sys.argv[1:]

    if "embedded" in args:
        import bpy
        import mathutils

        args = args[args.index("embedded") + 1 :]

        # keep_cube, no_emit, no_res, no_view, no_camera, no_light, dis_spl, en_spl
        flags = [False] * len(bool_opts)

        # x_offset, y_offset, max_width, col_count
        params = [c[2] for c in param_opts.values()]

        image_paths = []
        for arg in args:
            if arg in bool_opts:
                flags[bool_opts[arg]][0] = True
            elif not arg.startswith("-"):
                image_paths.append(arg)
            else:
                keyval = arg.split("=")
                if len(keyval) == 2 and keyval[0] in param_opts:
                    param, value = keyval
                    param_idx = param_opts[param][0]
                    params[param_idx] = type(params[param_idx])(value)

        setup(image_paths, *(flags + params))  # type: ignore
    else:
        if "--help" in sys.argv:
            print(generate_help(bool_opts, param_opts))
        elif all(a.startswith("-") for a in sys.argv[1:]):
            script_name = os.path.basename(__file__)
            print(
                f"Usage: {script_name} <optional_flags> /paths/to/your/image_or_video_or_svg_or_folder"
                f"\n{script_name} --help for all options"
            )

        else:
            terms = [a for a in args if a.startswith("-term=")]
            term = terms[0].split("=")[1] if terms else ""
            launch(args, term)
