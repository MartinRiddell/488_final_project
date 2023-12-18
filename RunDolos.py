import os
import time
import json
from multiprocessing import Pool

results = {}
times = []
zip_directory = "/home/mr2489/project/Martin-Riddell-Summer-2023/dolos_zip"
folder_names = os.listdir(zip_directory)

# itereate through folders in the zip folder

def run():
    stream = os.popen("python --version")
    output = stream.read()
    print("python version: ", output)

    with Pool() as p:
        results = p.map(call_dolos, folder_names)
        print(results)


def call_dolos(folder_name):
    start = time.time()
    program_index = folder_name[len("problem_"):-len("_zipped")]
    program_results = []
    
    
    folder_path = os.path.join(zip_directory, folder_name)
    
    for file in os.listdir(folder_path):
        # the order of the result is stored in the file's title
        index = int(file[len("high_score_number_"):-len("_zipped.zip")])

        print(f"-------- output of file {file} --------")
        
        file_path = os.path.join(folder_path, file)
        stream = os.popen(f"apptainer exec dolos.sif dolos run -f terminal --language python {file_path}")
        output = stream.read()
        # print("output:\n", output)
        output = output.split("\n")
        print("output split:\n", output)
        
        for line in output:
            if "ilarity sco:" in line:
                print("line: ", line)
                score = float(line[len(" Similarity score: "):])
                print("score: ", score)
                break
            else:
                print(f"line {line} doesn't contain 'similarity score'")
                print("length of above line: ", len(line))

        
        program_results.append({"high_score_number": index, "score": score})

    sorted_program_results = sorted(program_results, key=lambda d: d["score"], reverse = True)

    end = time.time()
    run_time = end-start
    print("run time: ", run_time)

    result_dict = {
        "program_number": program_index,
        "sorted_program_results": sorted_program_results,
        "time": run_time
    }

    # outputs the results to a file in the results folder
    output_path = "/home/mr2489/project/Martin-Riddell-Summer-2023/dolos_results"
    output_path = os.path.join(output_path, f"program_number_{program_index}")
    try:
        with open(output_path, "a+") as f:
            f.write(json.dumps(result_dict) + "\n")
    except FileNotFoundError:
        with open(output_path, "x") as f:
            f.write(json.dumps(result_dict) + "\n")


    return (program_index, sorted_program_results, run_time)