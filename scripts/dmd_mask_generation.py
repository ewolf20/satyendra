import os
import sys

import numpy as np
from matplotlib import pyplot as plt

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code.loading_functions import load_dmd_config
from satyendra.code.instruments import dmd_image_processing


def ellipse(x, y, x_center, y_center, x_radius, aspect_ratio_yx):
    y_radius = x_radius * aspect_ratio_yx
    return np.square((x - x_center) / x_radius) + np.square((y - y_center) / y_radius)

def ellipse_function(x, y, x_center, y_center, x_radius, aspect_ratio_yx):
    return np.where(
        ellipse(x, y, x_center, y_center, x_radius, aspect_ratio_yx) >= 1.0, 
        1, 
        0)


def checkerboard_function(x, y, check_size):
    x_check = x // check_size 
    y_check = y // check_size
    return (x_check + y_check) % 2
    

def point_source_function(x, y, point_radius, point_center):
    y_center, x_center = point_center 
    return np.where(
        np.square(x - x_center) + np.square(y - y_center) <= np.square(point_radius), 
        1, 
        0)



def main():
    dmd_config_dict = load_dmd_config()["lc4500"]
    dmd_pixel_size_um = dmd_config_dict["row_pitch_um"] * dmd_config_dict["column_pitch_multiplier"]


    IMAGE_SIZE = 501
    y_indices, x_indices = np.indices((IMAGE_SIZE, IMAGE_SIZE))

    center_offset = (IMAGE_SIZE - 1) // 2


    x_indices_centered = x_indices - center_offset
    y_indices_centered = y_indices - center_offset
    
    ELLIPSE_OFFSET_X = -75
    ELLIPSE_OFFSET_Y = -30
    ELLIPSE_X_RADIUS_PIX = 150
    ellipse_real_radius = ELLIPSE_X_RADIUS_PIX * dmd_pixel_size_um

    ellipse_pattern = ellipse_function(x_indices_centered, y_indices_centered, 
                    ELLIPSE_OFFSET_X, ELLIPSE_OFFSET_Y, ELLIPSE_X_RADIUS_PIX, 
                    1.0)

    ellipse_dmd_array = dmd_image_processing.dmd_image_convert(ellipse_pattern, dmd_background_value = 1)
    ellipse_basename = "Ellipse_Mask_Radius_{0:.1f}um".format(ellipse_real_radius)
    dmd_image_processing.convert_and_save_image(ellipse_dmd_array, ellipse_basename, show_plots = True)

    #Generate point pattern to test for aberrations
    POINT_CENTER = (0, 0) 
    POINT_RADIUS_PIX = 1
    point_real_radius = POINT_RADIUS_PIX * dmd_pixel_size_um

    point_pattern = point_source_function(x_indices_centered, y_indices_centered, POINT_RADIUS_PIX, POINT_CENTER)
    point_dmd_array = dmd_image_processing.dmd_image_convert(point_pattern, dmd_background_value = 0) 
    point_basename = "Point_Source_Radius_{0:.1f}um".format(point_real_radius)
    dmd_image_processing.convert_and_save_image(point_dmd_array, point_basename, show_plots = True)


    #Generate checkerboards to test for, respectively, inclusion of Fourier components and focusing sharpness
    REAL_CHECKERBOARD_SIZE_PIX = 100
    real_checkerboard_real_feature_size = REAL_CHECKERBOARD_SIZE_PIX * dmd_pixel_size_um
    checkerboard_pattern_real = checkerboard_function(x_indices_centered, y_indices_centered, REAL_CHECKERBOARD_SIZE_PIX)

    FOURIER_CHECKERBOARD_SIZE_PIX = 10 
    fourier_checkerboard_real_feature_size = FOURIER_CHECKERBOARD_SIZE_PIX * dmd_pixel_size_um
    checkerboard_pattern_fourier = checkerboard_function(x_indices_centered, y_indices_centered, FOURIER_CHECKERBOARD_SIZE_PIX) 

    real_checkerboard_dmd_array = dmd_image_processing.dmd_image_convert(checkerboard_pattern_real, dmd_background_value = 0) 
    fourier_checkerboard_dmd_array = dmd_image_processing.dmd_image_convert(checkerboard_pattern_fourier, dmd_background_value = 0)
    real_checkerboard_basename = "Checkerboard_Block_Size_{0:.1f}um".format(real_checkerboard_real_feature_size) 
    fourier_checkerboard_basename = "Checkerboard_Block_Size_{0:.1f}um".format(fourier_checkerboard_real_feature_size)
    dmd_image_processing.convert_and_save_image(real_checkerboard_dmd_array, real_checkerboard_basename, show_plots = True)
    dmd_image_processing.convert_and_save_image(fourier_checkerboard_dmd_array, fourier_checkerboard_basename, show_plots = True)
    
    
    
if __name__ == "__main__":
    main()
