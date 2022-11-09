import sys 
import os 

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code import crypto_functions 


def main():
    crypto_functions.update_plaintext_experiment_parameters() 


if __name__ == "__main__":
    main()