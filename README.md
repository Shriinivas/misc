# Miscellaneous Utilities

This repository contains a collection of assorted utilities designed to simplify and automate various tasks.

## Blender Image Launcher

The `blenderimagelauncher.py` script allows the user to launch blender and import one or more image, video (as plane via Import Image as Plane add-on) or svg (as Bezier curves via Import SVG add-on) directly from command line. It also adjusts several settings to make the render look as natural as possible, similar to its appearance in image/video processing apps. Each adjustment can be toggled via command-line arguments.

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

To use the script, provide it with the path(s) to the image/SVG/video you want to import into Blender. You can also specify one or more folders, in which case all supported file types from these will be imported. Various flags and parameters can be used to control the script's behavior.

```
blenderimagelauncher.py <image_or_video_path> <optional-flags> <optional-parameters>
```

#### Optional Flags

These boolean flags can be specified before or after the image path:

- `-kc`: Keep the default cube in the scene.
- `-ne`: Use a principled shader instead of an emission shader for the imported plane.
- `-nr`: Do not adjust the render resolution based on the image.
- `-nv`: Do not adjust the view to fit the imported image.
- `-nc`: Do not adjust camera settings.
- `-nl`: Do not modify the default lighting setup.
- `-ds`: Disable splash screen.
- `-es`: Enable splash screen.
- `-nb`: Do not change default compositor background.

#### Optional Parameters

These parameters allow you to fine-tune various aspects of the import:

- `-margin=<float>`: Set margin around the first image/SVG (default: 0.1).
- `-x_off=<float>`: Set horizontal spacing between images (default: 0.1).
- `-y_off=<float>`: Set vertical spacing between images (default: 0.1).
- `-max_w=<float>`: Set maximum width for image layout (default: 5.0).
- `-col_cnt=<int>`: Set number of columns in image layout (default: 4, ignored if -max_w is set).
- `-term=<terminal>`: Specify an alternative terminal for launching Blender.

#### Examples

##### Launch with default settings but keep the default lighting

```
blenderimagelauncher.py /path/to/image_or_video_or_svg -nl
```

##### Use a principled shader, don't change camera settings, launch in `kitty`, and import all images/SVGs/videos from a folder

```
blenderimagelauncher.py -term=kitty -ne -nc /path/to/folder
```

##### Import images with custom margin and spacing

```
blenderimagelauncher.py /path/to/folder -margin=0.2 -x_off=0.15 -y_off=0.15
```

#### Bonus Tip for `ranger` Users

Add the following line in `rc.conf` to open the selected image in Blender by pressing the shortcut (e.g. space-o-b)

```

map <space>ob shell blenderimagelauncher.py %d/%f &>/dev/null & disown

```

## Disclaimer

The scripts and apps in this collection are in continuous development and have not been extensively tested. They are provided as-is, without warranty of any kind. Users should use them with caution and are encouraged to report any issues.

## License

[GPL 3.0](./LICENSE)

```

```

```

```
