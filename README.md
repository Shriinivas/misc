# Miscellaneous Utilities

This repository contains a collection of assorted utilities designed to simplify and automate various tasks.

## Blender Image Launcher

The `blenderimagelauncher.py` script is for launching Blender and setting up a scene to include an image imported as a plane from command-line. This script allows users to adjust scene settings like camera placement, lighting, and deleting the default cube as command-line arguments.

### Installation

#### Linux

1. Download the script:
   ```bash
    wget https://raw.githubusercontent.com/Shriinivas/misc/master/blenderimagelauncher.py
   ```
2. Make the script executable:
   ```bash
    chmod +x blender_image_launcher.py
   ```

#### Windows

1. Download the script from the following URL:
   ```
    https://raw.githubusercontent.com/Shriinivas/misc/master/blenderimagelauncher.py
   ```
2. Ensure the script is runnable from the command line. You may need to associate .py files with Python or run them directly from the command prompt with `python blenderimagelauncher.py`.

### Usage

To use the script, you need to provide it with the path to the image you want to import into Blender. You can also specify various flags to control the script's behavior.

```
   ./blenderimagelauncher.py /path/to/your/image.jpg <optional_flags>
```

#### Optional Flags

- `keep_cube`: Keep the default cube in the scene.
- `no_emit`: Use a principled shader instead of an emission shader for the imported plane.
- `no_res`: Do not adjust the render resolution based on the image.
- `no_view`: Do not adjust the view to fit the imported image.
- `no_camera`: Do not adjust camera settings.
- `no_light`: Do not modify the default lighting setup.
- `--term [terminal]`: Specify an alternative terminal for launching Blender.

## Disclaimer

The scripts and apps in this collection are in continuous development and have not been extensively tested. They are provided as-is, without warranty of any kind. Users should use them with caution and are encouraged to report any issues.
