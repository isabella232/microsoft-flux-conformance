import pytest
import os


# Function to append logs from the test run into a result file
def append_result_output(message, result_file_path):
    # Make the directory if not already exists
    dir_path = os.path.dirname(result_file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    try:
        with open(result_file_path, "a") as result_file:
            result_file.write(message)
    except Exception as e:
        pytest.fail("Error while appending message '{}' to results file: ".format(message) + str(e))