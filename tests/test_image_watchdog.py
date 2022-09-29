import datetime 
import hashlib
import os
import shutil
import sys


path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"
sys.path.insert(0, path_to_satyendra)

from satyendra.code.image_watchdog import ImageWatchdog


def check_sha_hash(my_bytes, checksum_string):
    m = hashlib.sha256() 
    m.update(my_bytes) 
    return m.hexdigest() == checksum_string


IMAGE_FILE_EXTENSION_STRING = '.fits'
TEST_EXTENSION_STRING = '.txt'
SAVEFOLDER_PATH = 'resources/savefolder_temp' 
WATCHFOLDER_PATH = 'resources/watchfolder_temp'
WATCHFOLDER_REF_PATH = 'resources/watchfolder_ref'
IMAGE_SPEC_LIST = ['ImageA', 'ImageB']


class TestImageWatchdog:



    @staticmethod 
    def test_clean_filenames():
        MODERN_FILENAMES_SHA_HEX_STRING = '51c0c0aca7d807d54bdd3c290d31a3113be25cff228f5c5c0af3fe15646b9516'
        SIDE_FILENAMES_SHA_HEX_STRING = '717e497d9a50973f06aa05ded3b0f9e023bb3976c3f73dbfe993e4480cf212ab'
        TOP_FILENAMES_SHA_HEX_STRING = '20667b444a200cfa8888a645ae8e44e498dd4e3bbfb0eb62fcf9cd07781250f7'
        try:
            shutil.copytree('resources/Old_Top_Format_Filenames', 'resources/Top_Temp')
            shutil.copytree('resources/Old_Side_Format_Filenames', 'resources/Side_Temp')
            shutil.copytree('resources/Modern_Format_Filenames', 'resources/Modern_Temp')
            ImageWatchdog.clean_filenames('resources/Top_Temp')
            ImageWatchdog.clean_filenames('resources/Side_Temp', image_type_default = 'Side')
            ImageWatchdog.clean_filenames('resources/Modern_Temp')
            assert TestImageWatchdog.get_checksum_from_folder_filenames('resources/Top_Temp') == TOP_FILENAMES_SHA_HEX_STRING
            assert TestImageWatchdog.get_checksum_from_folder_filenames('resources/Side_Temp') == SIDE_FILENAMES_SHA_HEX_STRING
            assert TestImageWatchdog.get_checksum_from_folder_filenames('resources/Modern_Temp') == MODERN_FILENAMES_SHA_HEX_STRING
        finally:
            shutil.rmtree('resources/Top_Temp')
            shutil.rmtree('resources/Side_Temp')
            shutil.rmtree('resources/Modern_Temp')

    @staticmethod 
    def init_watchdog():
            my_watchdog = ImageWatchdog(WATCHFOLDER_PATH, SAVEFOLDER_PATH, 
                                    IMAGE_SPEC_LIST, image_extension = '.txt')
            return my_watchdog
        

    @staticmethod 
    def test_init():
        try:
            shutil.copytree(WATCHFOLDER_REF_PATH, WATCHFOLDER_PATH)
            my_watchdog = TestImageWatchdog.init_watchdog() 
            assert True 
        finally:
            shutil.rmtree(WATCHFOLDER_PATH)
            shutil.rmtree(SAVEFOLDER_PATH)

    @staticmethod 
    def test_associate_images_with_run():
        WATCHFOLDER_CHECKSUM_STRING = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        SAVEFOLDER_CHECKSUM_STRING = "640a84f1e41aa2c95d0d63b226101c95ff9041ff1d2f8da4a62e5e979948baf5"
        NO_ID_CHECKSUM_STRING = "e43350b2c85f30b47c6c79e98f531d24d095306adf2ef81a1554ea2396cd669d"

        try:
            shutil.copytree(WATCHFOLDER_REF_PATH, WATCHFOLDER_PATH)
            my_watchdog = TestImageWatchdog.init_watchdog()
            my_watchdog.associate_images_with_run()
            no_ids_path = os.path.join(SAVEFOLDER_PATH, 'no_id')
            watchfolder_checksum = TestImageWatchdog.get_checksum_from_folder_filenames(WATCHFOLDER_PATH, extension = '.txt')
            savefolder_checksum = TestImageWatchdog.get_checksum_from_folder_filenames(SAVEFOLDER_PATH, extension = '.txt')
            no_id_folder_checksum = TestImageWatchdog.get_checksum_from_folder_filenames(no_ids_path, extension = '.txt')
            assert watchfolder_checksum == WATCHFOLDER_CHECKSUM_STRING
            assert savefolder_checksum == SAVEFOLDER_CHECKSUM_STRING 
            assert no_id_folder_checksum == NO_ID_CHECKSUM_STRING
        finally:
            shutil.rmtree(WATCHFOLDER_PATH)
            shutil.rmtree(SAVEFOLDER_PATH)

    @staticmethod 
    def get_checksum_from_folder_filenames(folder_path, extension = IMAGE_FILE_EXTENSION_STRING):
        sorted_stripped_filenames = [f for f in sorted(os.listdir(folder_path)) if extension in f]
        m = hashlib.sha256()
        for filename in sorted_stripped_filenames:
            m.update(filename.encode("ASCII"))
        return m.hexdigest()

        
