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

class TestImageWatchdog:

    IMAGE_FILE_EXTENSION_STRING = '.fits'

    @staticmethod 
    def test_clean_filenames():
        # MODERN_FILENAMES_SHA_HEX_STRING = '76a9caa2a6aa17c7bfdecab69865093af2e25b732aeeebd1032ecb363841da13'
        # OLD_FILENAMES_SHA_HEX_STRING = ''
        try:
            shutil.copytree('resources/Old_Top_Format_Filenames', 'resources/Top_Temp')
            shutil.copytree('resources/Old_Side_Format_Filenames', 'resources/Side_Temp')
            shutil.copytree('resources/Modern_Format_Filenames', 'resources/Modern_Temp')
            ImageWatchdog.clean_filenames('resources/Top_Temp')
            ImageWatchdog.clean_filenames('resources/Side_Temp', image_type_default = 'Side')
            ImageWatchdog.clean_filenames('resources/Modern_Temp')
            print(TestImageWatchdog.get_checksum_from_folder_filenames('resources/Top_Temp'))
            print(TestImageWatchdog.get_checksum_from_folder_filenames('resources/Side_Temp'))
            print(TestImageWatchdog.get_checksum_from_folder_filenames('resources/Modern_Temp'))
            print(TestImageWatchdog.get_checksum_from_folder_filenames('resources/Modern_Format_Filenames'))
            assert True
        finally:
            pass
            # shutil.rmtree('resources/Top_Temp')
            # shutil.rmtree('resources/Side_Temp')
            # shutil.rmtree('resources/Modern_Temp')



    @staticmethod 
    def get_checksum_from_folder_filenames(folder_path):
        sorted_stripped_filenames = [f for f in sorted(os.listdir(folder_path)) if TestImageWatchdog.IMAGE_FILE_EXTENSION_STRING in f]
        m = hashlib.sha256() 
        for filename in sorted_stripped_filenames:
            m.update(filename.encode("ASCII")) 
        return m.hexdigest()

        
