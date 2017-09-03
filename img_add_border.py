#!/usr/bin/env python3

import argparse
import os
import os.path
import re
import shutil
import subprocess
import tempfile

# TODO tests
# TODO pylama

# Adds border (color, thickness [mm]) to an image by adding more pixels to the
# edges. Enforces exact aspect ratio of the resulting image by cropping some of
# its edges, if needed. Finally converts the image to specified DPI.
#
# Sample invocation:
#   ./img_add_border.py \
#       --units=inch \
#       --img_size=4x6 --dpi=300 \
#       --border_size=0.078740157 --border_color=#ffffff \
#       --out_dir=border_2mm-4x6_inch-300dpi/ orig-photos/*


MM_TO_INCH = 0.03937007874


def add_border(img, ratio, img_dims_mm, border_mm, color, dpi=None):
    '''Adds border of given size to the image, possibly cropping it on sides
    to have exactly the ratio defined by img_dims_mm.

    img Path to the image.
    ratio Target aspect ratio of the image as tuple of integers (x, y).
          Order of the dimensions is independent of the image orientation.
          Eg. (3,2) for image 10x15 cm.
    img_dims_mm Target size of the image with border as tuple (x_mm, y_mm)
                in millimeters. Order of the dimensions is independent of image
                orientation.
                Eg. (150,100) for 10x15 cm.
    border_mm Width of the target border. In millimeters.
    color Color of the border to be added. Eg. '#ffffff'.
    dpi Target DPI of the image. If given the image is resized so that
        the final pixel size divided by DPI results in img_dims_mm.
    '''
    commands = []

    (img_w_px, img_h_px) = get_image_dimensions(img)

    if img_w_px > img_h_px:
        # landscape
        (ratio_w, ratio_h) = (max(ratio), min(ratio))
        (img_w_mm, img_h_mm) = (max(img_dims_mm), min(img_dims_mm))
    else:
        # portrait
        (ratio_w, ratio_h) = (min(ratio), max(ratio))
        (img_w_mm, img_h_mm) = (min(img_dims_mm), max(img_dims_mm))

    # Grow border until it reaches the desired mm thickness in any dimension.
    border_px = 0
    # while (
    #         2 * border_px / (img_w_px + 2 * border_px) < 2 * border_mm / (img_w_mm + 2 * border_mm)
    #         and
    #         2 * border_px / (img_h_px + 2 * border_px) < 2 * border_mm / (img_h_mm + 2 * border_mm)):
    while (
            border_px / (img_w_px + 2 * border_px) < border_mm / img_w_mm
            and
            border_px / (img_h_px + 2 * border_px) < border_mm / img_h_mm):
        border_px += 1

    # Pre-crop if needed - we want aspect ratio of the final image with border
    # to match the specified ratio.
    mul = min(
            (img_w_px + 2 * border_px) // ratio_w,
            (img_h_px + 2 * border_px) // ratio_h)
    crop_w = (img_w_px + 2 * border_px) - (ratio_w * mul)
    crop_h = (img_h_px + 2 * border_px) - (ratio_h * mul)
    assert crop_w >= 0 and crop_h >= 0, 'Invalid state: ' + str(locals())

    if crop_w > 0 or crop_h > 0:
        commands.append([
            'convert',
            '-gravity', 'center',
            '-extent', '%dx%d' % (img_w_px - crop_w, img_h_px - crop_h),
            '{ifile}', '{ofile}'])

    # Add border.
    commands.append([
        'convert',
        '-border', '%dx%d' % (border_px, border_px),
        '-bordercolor', color,
        '{ifile}', '{ofile}'])

    # Optionally convert to DPI matching exactly the img_dims_mm.
    if dpi:
        dpi_img_w_px = int((MM_TO_INCH * img_w_mm) * dpi)
        dpi_img_h_px = int((MM_TO_INCH * img_h_mm) * dpi)
        commands.append([
            'convert',
            '-density', str(dpi),
            '-units', 'PixelsPerInch',
            '-resize', '%dx%d' % (dpi_img_w_px, dpi_img_h_px),
            '{ifile}', '{ofile}'])

    return commands


def run_shell(cmd, raise_on_error=True):
    '''Runs command, eg. ['ls', '-l'].'''
    print('  $ %s' % ' '.join(cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0 and raise_on_error:
        raise Exception(
            'Command "%s" returned exit code %d, stdout: [%s], stderr: [%s]' % (
                cmd, result.returncode, result.stdout, result.stderr))
    return (result.returncode, result.stdout.decode(), result.stderr.decode())


def run_commands(commands, first_in, last_out):
    '''Runs a set of commands. The commands may contain placeholders
    {ifile}, {ofile} which will be replaced by file names.
    The output of the first command is chained as input to the second command
    etc., and output of the last command is written at path last_out.
    '''
    def run_command(command, ifile, ofile):
        # Substitute input and output file parameters.
        run_shell([x.format(ifile=ifile, ofile=ofile) for x in command])

    files = (
        [first_in] +
        [tempfile.mkstemp()[1] for i in range(len(commands) - 1)] +
        [last_out])

    for i in range(len(commands)):
        run_command(commands[i], files[i], files[i + 1])

    for tmp in files[1:-1]:
        os.remove(tmp)


def get_image_dimensions(img):
    command = ['identify', '-format', '%[fx:w]x%[fx:h]', img]
    (_, dim_str, _) = run_shell(command)
    return parse_dimensions(dim_str)


def parse_dimensions(dims):
    '''Parses dimension string into a tupe, eg. '400x600' -> (400, 600).'''
    if not re.match(r'^\d+x\d+$', dims):
        raise ValueError(
            'Input "%s" does not match pattern "[0-9]+x[0-9]+"' % dims)
    (w, h) = map(int, dims.split("x"))
    return (w, h)


def convert_to_mm(value, unit):
    if unit == 'mm':
        return value
    elif unit == 'inch':
        return value / MM_TO_INCH
    else:
        raise ValueError('Unrecognized unit %s' % unit)


def normalize(a, b):
    def gcd(a, b):
        return (b == 0 and a) or gcd(b, a - b)
    norm = gcd(max(a, b), min(a, b))
    return (a // norm, b // norm)


def process_args():
    parser = argparse.ArgumentParser(
        description='Add border to images and resize them to specified size.')
    parser.add_argument('images', metavar='IMAGES', nargs='+',
                        help='Paths to the input images.')
    parser.add_argument('--out_dir', metavar='OUT_DIR', required=True,
                        help='Path to the output directory.')
    parser.add_argument('--img_size', metavar='<UNITS>x<UNITS>', required=True,
                        type=parse_dimensions,
                        help='Desired size of the resulting image in '
                             'millimeters, eg. "100x150". The image may be '
                             'cropped on sides to make it fit. Orientation '
                             'does not matter.')
    parser.add_argument('--dpi', metavar='DPI', type=int,
                        help='Optional. DPI to which the image will be '
                             're-sampled.')
    parser.add_argument('--border_size', metavar='UNITS', required=True,
                        type=float,
                        help='Width of the border to add, in millimeters.')
    parser.add_argument('--border_color', metavar='COLOR', required=True,
                        help='Color of the border, eg. "#ffffff" for white.')
    parser.add_argument('--units', metavar='UNIT_TYPE', choices=['mm', 'inch'],
                        default='cm',
                        help='Units of: --border_mm, --img_mm. Default is mm.')
    return parser.parse_args()


if __name__ == '__main__':
    if not shutil.which('convert'):
        print('Error: "convert" command was not found on this system. '
              'Install it, eg. via "apt-get install imagemagick".')
    else:
        args = process_args()

        os.makedirs(args.out_dir, exist_ok=True)

        # Convert arguments to metric units.
        convert = lambda v: convert_to_mm(v, args.units)
        border_mm = convert(args.border_size)
        (img_x_mm, img_y_mm) = map(convert, args.img_size)

        # Compute ratio based on img_size which is integers.
        img_ratio = normalize(*args.img_size)

        for in_image in args.images:
            print('Processing image "%s" (%d/%d)' % (
                in_image, args.images.index(in_image) + 1, len(args.images)))
            out_image = os.path.join(args.out_dir, os.path.basename(in_image))
            commands = add_border(in_image, img_ratio, (img_x_mm, img_y_mm),
                                  border_mm, args.border_color,
                                  dpi=args.dpi)
            run_commands(commands, first_in=in_image, last_out=out_image)
