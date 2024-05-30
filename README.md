# Miscellaneous Utilities

This repository contains a collection of assorted utilities designed to simplify and automate various tasks.

## Blender Image Launcher

The `blenderimagelauncher.py` script automates the creation of a Blender scene by importing an image or video as a plane. It adjusts several settings to make the render look as natural as possible, similar to its appearance in image/video processing apps. Each adjustment can be toggled via command-line arguments.

- Remove the default cube
- Use emission shader for plane and import the plane with Z+ up axis
- Change render resolution to match the image dimensions
- Change the view to orthographic top
- Change the camera type to orthographic and adjust the orthographic scale to fit the image
- Change the world lighting to use emission shader with zero strength

### Installation

1. Download the script using `wget`:
   ```bash
    wget https://raw.githubusercontent.com/Shriinivas/misc/master/blenderimagelauncher.py
   ```
   Alternatively, download it from the URL:
   ```
    https://raw.githubusercontent.com/Shriinivas/misc/master/blenderimagelauncher.py
   ```
2. Make the script executable (Linux):
   ```bash
   chmod +x blenderimagelauncher.py
   ```

### Usage

To use the script, you need to provide it with the path to the image you want to import into Blender. You can also specify various flags to control the script's behavior.

```
   blenderimagelauncher.py <image_path> <optional-flags>
```

#### Optional Flags

The flags can be specified before or after the image.

- `-kc`: Keep the default cube in the scene.
- `-ne`: Use a principled shader instead of an emission shader for the imported plane.
- `-nr`: Do not adjust the render resolution based on the image.
- `-nv`: Do not adjust the view to fit the imported image.
- `-nc`: Do not adjust camera settings.
- `-nl`: Do not modify the default lighting setup.
- `-term=<terminal>`: Specify an alternative terminal for launching Blender.

#### Examples

# Launch with default settings but keep the default lighting

```
blenderimagelauncher.py /path/to/image_or_video -nl
```

# Use a principled shader and do not change the camera settings and launch in `kitty`

```
blenderimagelauncher.py -term=kitty -ne -nc /path/to/image_or_video
```

## Disclaimer

The scripts and apps in this collection are in continuous development and have not been extensively tested. They are provided as-is, without warranty of any kind. Users should use them with caution and are encouraged to report any issues.
