import datetime
import importlib.resources as pkg_resources
import json
import os

from cryptography.fernet import Fernet


from .. import secrets as s

#WARNING: Removing the word 'secret' from a filename will cause it to no longer be ignored by Git!!! 
KEY_FILENAME = 'satyendra_encryption_key_secret.bin'

EXPERIMENT_PARAMETERS_PLAINTEXT_FILENAME = 'experiment_parameters_secret.json'
EXPERIMENT_PARAMETERS_ENCRYPTED_FILENAME = 'experiment_parameters_encrypted.bin'

DATETIME_FORMAT_STRING = "%Y-%m-%d--%H-%M-%S"



def initialize_fernet():
    with pkg_resources.path(s, KEY_FILENAME) as key_path:
        with open(key_path, 'rb') as my_key_file:
            my_key = my_key_file.read()
    f = Fernet(my_key) 
    return f


'''
Updates the encrypted experiment parameters using the local plaintext.'''
def update_encrypted_experiment_parameters(plaintext_filename = EXPERIMENT_PARAMETERS_PLAINTEXT_FILENAME, 
                                            encrypted_filename = EXPERIMENT_PARAMETERS_ENCRYPTED_FILENAME):
    with pkg_resources.path(s, plaintext_filename) as plaintext_parameters_path, \
        pkg_resources.path(s, '__init__.py') as secrets_init_path:
        with open(plaintext_parameters_path) as plaintext_parameters_file:
            plaintext_parameters_dict = json.load(plaintext_parameters_file)
            plaintext_parameters_dump_bytes = json.dumps(plaintext_parameters_dict).encode('ASCII')
        f = initialize_fernet()
        encrypted_bytes = f.encrypt(plaintext_parameters_dump_bytes)
        secrets_path = os.path.dirname(secrets_init_path)
        encrypted_parameters_path = os.path.join(secrets_path, encrypted_filename)
        with open(encrypted_parameters_path, 'wb') as encrypted_parameters_file:
            encrypted_parameters_file.write(encrypted_bytes)
    return True

"""
Updates the plaintext parameters' dictionary of change times using the encrypted parameters.
"""
def refresh_plaintext_update_times(plaintext_filename = EXPERIMENT_PARAMETERS_PLAINTEXT_FILENAME, 
                                    encrypted_filename = EXPERIMENT_PARAMETERS_ENCRYPTED_FILENAME):
    with pkg_resources.path(s, plaintext_filename) as plaintext_parameters_path, \
        pkg_resources.path(s, encrypted_filename) as encrypted_parameters_path:
        with open(plaintext_parameters_path) as plaintext_parameters_file, \
            open(encrypted_parameters_path, 'rb') as encrypted_parameters_file:
            plaintext_parameters_dict = json.load(plaintext_parameters_file)
            encrypted_bytes = encrypted_parameters_file.read()
        plaintext_parameter_values = plaintext_parameters_dict["Values"] 
        plaintext_parameter_update_times = plaintext_parameters_dict["Update_Times"]
        f = initialize_fernet() 
        decrypted_bytes = f.decrypt(encrypted_bytes)
        decrypted_string = decrypted_bytes.decode("ASCII") 
        decrypted_dict = json.loads(decrypted_string)
        decrypted_parameter_values = decrypted_dict["Values"]
        for key in plaintext_parameter_values:
            if not key in decrypted_parameter_values or decrypted_parameter_values[key] != plaintext_parameter_values[key]:
                plaintext_parameter_update_times[key] = datetime.datetime.now().strftime(DATETIME_FORMAT_STRING)
        with open(plaintext_parameters_path, 'w') as plaintext_parameters_file:
            json.dump(plaintext_parameters_dict, plaintext_parameters_file)




'''Updates or creates the local plaintext of the experiment parameters using the encrypted parameters.'''

#TODO: Currently, this one hacks the path for the plaintext parameters in case they don't exist.
def update_plaintext_experiment_parameters(plaintext_filename = EXPERIMENT_PARAMETERS_PLAINTEXT_FILENAME, 
                                            encrypted_filename = EXPERIMENT_PARAMETERS_ENCRYPTED_FILENAME):
    with pkg_resources.path(s, '__init__.py') as secrets_init_path, \
        pkg_resources.path(s, encrypted_filename) as encrypted_parameters_path:
        with open(encrypted_parameters_path, 'rb') as encrypted_parameters_file:
            encrypted_bytes = encrypted_parameters_file.read()
        f = initialize_fernet()
        plaintext_bytes = f.decrypt(encrypted_bytes)
        plaintext_string = plaintext_bytes.decode('ASCII')
        secrets_path = os.path.dirname(secrets_init_path) 
        plaintext_parameters_path = os.path.join(secrets_path, plaintext_filename)
        with open(plaintext_parameters_path, 'w') as plaintext_parameters_file:
            plaintext_parameters_file.write(plaintext_string)
    return True



"""Returns a dict containing the plaintext experiment parameters."""
def get_plaintext_experiment_parameters(plaintext_filename = EXPERIMENT_PARAMETERS_PLAINTEXT_FILENAME):
    with pkg_resources.path(s, plaintext_filename) as plaintext_parameters_path: 
        with open(plaintext_parameters_path, 'r') as plaintext_parameters_file:
            return json.load(plaintext_parameters_file)