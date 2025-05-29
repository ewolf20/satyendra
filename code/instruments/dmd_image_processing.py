import os

import numpy as np
import scipy
from matplotlib import pyplot as plt
from PIL import Image

from ..loading_functions import load_dmd_config

"""
Given a numpy array img, perform Floyd-Steinberg Dithering

Given img, a 2D numpy array representing a greyscale image, use Floyd-Steinberg dithering
(see e.g. https://en.wikipedia.org/wiki/Floyd%E2%80%93Steinberg_dithering)
to clip to integer values (by default, 0 or 1) while maintaining the local brightness of the image. 
"""
def fs_dither(img, clip_low = 0, clip_high = 1):
    '''
    Floyd-Steinberg dithering
    '''
    img_dither = np.copy(img)
    for y in range(img.shape[0] - 1):
        for x in range(img.shape[1] - 1):
            img_dither[y,x] = np.clip(np.round(img_dither[y,x]), amin = clip_low, amax = clip_high)

            error = img[y,x] - img_dither[y,x]

            img_dither[y,x+1] += error * 7./16.
            if x > 0:
                img_dither[y+1,x-1] += error * 3./16.
            img_dither[y+1,x]   += error * 5./16.
            img_dither[y+1,x+1] += error * 1./16.

        # Last column
        img_dither[y,img.shape[1]-1] = np.clip(np.round(img_dither[y,img.shape[1]-1]), amin = clip_low, amax = clip_high)

        error = img_dither[y,img.shape[1]-1] - img[y,img.shape[1]-1]

        img_dither[y+1,img.shape[1]-2] += error * 3./16.
        img_dither[y+1,img.shape[1]-1] += error * 5./16.
    # Last row
    for x in range(0, img.shape[1] - 1):
        img_dither[img.shape[0]-1,x] = np.clip(np.round(img_dither[img.shape[0]-1,x]), amin = clip_low, amax = clip_high)
        error = img_dither[img.shape[0]-1,x] - img[img.shape[0]-1,x]
        img_dither[img.shape[0]-1,x+1] += error * 7./16.
    return img_dither




"""
Condition a greyscale image for display on a DMD. 

Given a greyscale image representing a "real image", manipulate it to produce an 
output image suitable for projecting onto the DMD. 

In particular, the image is 
rescaled, rotated, etc. to deal with details of how DMD pixel addressing distorts the 
"real" image in the xy plane. 

Parameters:

    image: A 2D numpy array of greyscale values, with 0 mapped to full rejection and 1 mapped 
    to full transmission. Intermediate values, if present, are dithered to {0, 1} using Floyd-Steinberg.

    image_offset: A tuple (y_offset, x_offset) of distances by which to displace the center of the image on the DMD chip. 
        These displacements are real values in the xy plane - they translate the image purely vertically and horizontally, 
        respectively, and by equal amounts. 

    dmd_config_dict: A dictionary of various parameters specific to the DMD:
        number_rows
        number_columns
        row_pitch_um: The distance in micrometers between micromirrors in the _direction of the row increment_
        column_pitch_multiplier: The ratio of the column pitch to the row pitch
        rotation_angle_deg: The angle by which a "real image' is rotated when displayed on the DMD
        invert: If 0, then a logical value of 0 for light rejection is mapped to a physical value of 0 on the DMD. If 1, then it is mapped to 1. 
        background value: The _logical value_ to which pixels on the DMD outside the range of the image should be set. If 1, light is transmitted.

    #NOTE: For convenience, if dmd_config_dict is not passed, it is automatically loaded from satyendra.configs

    dmd_type: If dmd_config_dict is not passed, use the parameters stored under this key in satyendra/configs/dmd_config_local.json

    auto_resize: If True, an image is resized to take up the maximal amount of space on the DMD. If False, the original dimensions are kept.

Returns:
    A greyscale numpy array of values {0, 1}, representing the physical values which should be assigned to the dmd pixels at each pair of indices [row, column]

"""

dmd_parameter_dict = None

def dmd_image_convert(image, image_offset = (0, 0), dmd_background_value = 1, dmd_config_dict = None, dmd_type = "lc4500", auto_resize = False):
    if dmd_config_dict is None:
        global dmd_parameter_dict
        if dmd_parameter_dict is None:
            dmd_parameter_dict = load_dmd_config()
        dmd_config_dict = dmd_parameter_dict[dmd_type]

    dmd_conditioned_image, all_binary = _condition_image(image, image_offset, dmd_background_value, dmd_config_dict, auto_resize)

    dmd_invert = dmd_config_dict["invert"]
    if dmd_invert:
        physical_image = 1 - dmd_conditioned_image
    else:
        physical_image = dmd_conditioned_image
    
    if not all_binary:
        converted_image = fs_dither(physical_image)
    else:
        converted_image = physical_image
    return converted_image

def _condition_image(image, image_offset, dmd_background_value, dmd_config_dict, auto_resize):

    if not np.all(np.logical_and(image >= 0.0, image <= 1.0)):
        raise ValueError("Greyscale image must have values between 0 and 1")

    all_binary = np.all(np.logical_or(image == 0.0, image == 1.0))


    #Rotate image to align DMD axes with real axes
    dmd_rotation_deg = dmd_config_dict["rotation_angle_deg"]
    dmd_rotation_rad = np.deg2rad(dmd_rotation_deg)

    rotated_image = scipy.ndimage.rotate(image, dmd_rotation_deg, cval = dmd_background_value, reshape = True)

    y_offset, x_offset = image_offset

    #Adjust real offset to DMD axes
    post_rotation_dmd_yoffset = np.cos(dmd_rotation_rad) * y_offset + np.sin(dmd_rotation_rad) * x_offset 
    post_rotation_dmd_xoffset = np.cos(dmd_rotation_rad) * x_offset - np.sin(dmd_rotation_rad) * y_offset

    #Stretch image to compensate for different strides along different DMD indices
    dmd_ypix = dmd_config_dict["number_rows"]
    dmd_xpix = dmd_config_dict["number_columns"]
    dmd_column_ratio = dmd_config_dict["column_pitch_multiplier"]

    if dmd_column_ratio >= 1.0:
        stretch_adjusted_rotated_image = scipy.ndimage.zoom(rotated_image, (dmd_column_ratio, 1.0))
        final_dmd_yoffset = int(np.rint(dmd_column_ratio * post_rotation_dmd_yoffset))
        final_dmd_xoffset = int(np.rint(post_rotation_dmd_xoffset))
    else:
        dmd_row_ratio = 1.0 / dmd_column_ratio 
        stretch_adjusted_rotated_image = scipy.ndimage.zoom(rotated_image, (1.0, dmd_row_ratio))
        final_dmd_yoffset = int(np.rint(post_rotation_dmd_yoffset))
        final_dmd_xoffset = int(np.rint(post_rotation_dmd_xoffset * dmd_row_ratio))

    
    #Handle rounding errors by a small buffer... not the most professional but ok
    if final_dmd_yoffset >= 0.5 * dmd_ypix - 1:
        raise ValueError("DMD index of y offset too large; current value {0:d}, max value {1:d}".format(final_dmd_yoffset, int(np.rint(0.5 * dmd_ypix))))
    if final_dmd_xoffset >= 0.5 * dmd_xpix - 1:
        raise ValueError("DMD index of x offset too large; current value {0:d}, max value {1:d}".format(final_dmd_xoffset, int(np.rint(0.5 * dmd_xpix))))

    #Image can't be any bigger than this
    max_xpix_with_offset = dmd_xpix - 2 * np.abs(final_dmd_xoffset) - 2
    max_ypix_with_offset = dmd_ypix - 2 * np.abs(final_dmd_yoffset) - 2

    #Auto resize if stipulated
    if auto_resize:
        x_axis_rescale_factor = max_xpix_with_offset / stretch_adjusted_rotated_image.shape[1] 
        y_axis_rescale_factor = max_ypix_with_offset / stretch_adjusted_rotated_image.shape[0]
        minimum_rescale_factor = min((x_axis_rescale_factor, y_axis_rescale_factor))
        auto_resized_image = scipy.ndimage.zoom(stretch_adjusted_rotated_image, minimum_rescale_factor)
        if all_binary:
            final_image = np.rint(auto_resized_image)
        else:
            final_image = np.clip(auto_resized_image, amin = 0, amax = 1)
    elif max_xpix_with_offset < stretch_adjusted_rotated_image.shape[1]:
        raise ValueError("Image too large for DMD along x. Max dimension with current offset is {0:d}".format(max_xpix_with_offset))
    elif max_ypix_with_offset < stretch_adjusted_rotated_image.shape[0]:
        raise ValueError("Image too large for DMD along y. Max dimension with current offset is {0:d}".format(max_ypix_with_offset))
    else:
        final_image = stretch_adjusted_rotated_image

    #Pad image into correct dimensions for DMD
    dmd_residual_half_width_x = int(np.rint((dmd_xpix - final_image.shape[1]) / 2.0))
    pad_left = dmd_residual_half_width_x + final_dmd_xoffset
    pad_right = dmd_xpix - pad_left - stretch_adjusted_rotated_image.shape[1] 
    
    dmd_residual_half_width_y = int(np.rint((dmd_ypix - final_image.shape[0]) / 2.0))
    pad_down = dmd_residual_half_width_y + final_dmd_yoffset
    pad_up = dmd_ypix - pad_down - final_image.shape[0]

    padded_image = np.pad(
        final_image, 
        ((pad_up, pad_down), (pad_left, pad_right)), 
        mode = "constant", constant_values = dmd_background_value
    )
    return (padded_image, all_binary)


def convert_and_save_image(greyscale_image, image_basename, dmd_config_dict = None, dmd_type = "lc4500", show_plots = False):
    if dmd_config_dict is None:
        global dmd_parameter_dict
        if dmd_parameter_dict is None:
            dmd_parameter_dict = load_dmd_config()
        dmd_config_dict = dmd_parameter_dict[dmd_type]
    if show_plots:
        plt.imshow(greyscale_image)
        plt.suptitle(image_basename)
        plt.show()
    bit_depth = dmd_config_dict["image_bit_depth"]

    rescaled_image_array = greyscale_image.astype('uint{0:d}'.format(bit_depth)) * (2**bit_depth - 1)
    rgb_image = Image.fromarray(rescaled_image_array).convert('RGB') 

    image_save_dir = dmd_config_dict["image_savepath"]
    image_extension = dmd_config_dict["image_save_format"]

    image_filename = ".".join((image_basename, image_extension))
    full_image_path = os.path.join(image_save_dir, image_filename)

    rgb_image.save(full_image_path)

    

    
    
if __name__ == "__main__":
    main()
