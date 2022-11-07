import importlib.resources as pkg_resources
import json
import os

from cryptography.fernet import Fernet


from .. import secrets as s

#WARNING: Removing the word 'secret' from a filename will cause it to no longer be ignored by Git!!! 
KEY_FILENAME = 'analysis_encryption_key_secret.bin'

EXPERIMENT_PARAMETERS_PLAINTEXT_FILENAME = 'experiment_parameters_secret.json'
EXPERIMENT_PARAMETERS_ENCRYPTED_FILENAME = 'experiment_parameters_encrypted.bin'



def initialize_fernet():
    with pkg_resources.path(s, KEY_FILENAME) as key_path:
        with open(key_path, 'rb') as my_key_file:
            my_key = my_key_file.read()
    f = Fernet(my_key) 
    return f


'''
Updates the encrypted experiment parameters using the local plaintext.'''

#TODO: Currently this uses a hack to get the path for the encrypted parameters in case they don't exist.
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


'''Updates or creates the local plaintext of the experiment parameters using the encrypted parameters.'''

#TODO: Likewise, this one hacks the path for the plaintext parameters in case they don't exist.
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



