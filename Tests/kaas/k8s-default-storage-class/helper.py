import yaml

manual_result_file_template = {
    "name": None,
    "status": None,
    "details": {
        "messages": None
    },
}


def gen_sonobuoy_result_file(error_n: int, error_msg: str, test_file_name: str):

    test_name = test_file_name.replace(".py", "")

    test_status = "passed"

    if error_n != 0:
        test_status = test_name + "_" + str(error_n)

    result_file = manual_result_file_template

    result_file["name"] = test_name
    result_file["status"] = test_status
    result_file["details"]["messages"] = error_msg

    with open(f"./{test_name}.result.yaml", "w") as file:
        yaml.dump(result_file, file)
