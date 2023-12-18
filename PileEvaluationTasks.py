import time
import json
import os
import multiprocessing
import cProfile
# import asyncio
from tqdm import tqdm
from datasets import load_dataset
from multiprocessing import Pool
from thefuzz import fuzz


class EvaluationTask:
    def __init__(self, gold_programs_path: str, output_path: str, start_index: int, end_index: int, num_workers: int=None):
        self.start_index = start_index
        self.end_index = end_index
        self.gold_programs_path = gold_programs_path
        self.gold_programs = []
        self.read_data()
        self.dataset = []
        self.output_path = output_path
        self.num_workers = num_workers


    def read_data(self):
        """Reads data from the input file. Saves it in json format in self.examples for later reference.
            It only saves the programs in the inputted range though."""
        
        if self.gold_programs_path == "human_eval":
            ds = load_dataset("openai_humaneval")
            start = self.start_index - 1
            end = self.end_index
            self.gold_programs = ds['test'][start:end]
            
    def start_scoring(self):
        """begins to find similarity scores between generated answers and training  dataset"""

        strings = self.gold_programs
        times = []
        first = True
        i = 0
        for string in tqdm(strings['canonical_solution']):
            print("searching for string:\n", string)
            print("length of the program: ", len(string))
            times.append(self.score_string(string))          

        print("total time: ", sum(times), "average time per string: ", sum(times) / len(times))

    def score_string(self, string_metadata):
        """finds the top 5 most similar substrings within the training dataset to the string"""

        stats, t = self.find_similar_substrings(string_metadata)
        json_object = {
        "time": t,
        "gold_program": string_metadata
        }
        print("json object:\n", json_object)

        count = 1
        for stat in stats:
            stat_dict = {
                "score": stat[0],
                "substring": stat[1],
                "string": stat[2]
            }
            try:
                stat_dict["repo_path"] = stat[3]
                stat_dict["repo_name"] = stat[4]
            except:                                 # Some repos don't have a path or name
                stat_dict["repo_path"] = None
                stat_dict["repo_name"] = None

            json_object[f"high_score_number_{count}"] = stat_dict
            count += 1
        try:
            with open(self.output_path, "a+") as f:
                f.write(json.dumps(json_object) + "\n")
        except FileNotFoundError:
            f = open(self.output_path, "x")
            f.write(json.dumps(json_object) + "\n")

        return t

    def find_similar_substrings(self, string):
        """takes a string and a dataset, and prints to a jsonl file the 5 most similar substrings
            along with their similarity scores and the substring matched. 
            
            string - string being searched for
            dataset_strings - strings from the dataset to be searched through
            length - only searches the first n items in the dataset. This is to allow for quick testing"""
    
        start = time.time()
        
        directory_path = "Github_Split"
        file_list = os.listdir(directory_path)
        top_ten_thousand_stats = []

        # block_size = 2_000_000
        # for i in tqdm(range(0, len(all_file_strings), block_size)):
        #     ds = all_file_strings[i:i+block_size]

        for file_name in tqdm(file_list):
            file_path = os.path.join(directory_path, file_name)
            with open(file_path, "r") as f:
                ds = [json.loads(s) for s in f.readlines()]
                        
                dataset_strings = ds #[0:100]  # used to append ds, make sure it's the full thing when being done for real
                # dataset_strings = self.dataset
    #            print("length of dataset before multiprocessing: ", len(dataset_strings))
    
                args = []
                for x in dataset_strings:
                    args.append((string, x))
    
                # print("there are {} cpus available, we are using {} of them".format(multiprocessing.cpu_count(), self.num_workers))
                with Pool(self.num_workers) as p:
                    stats = p.map(find_most_similar_substring, args)       # returns the highest scores and most similar substrings to the gold program for each 
    
    #            print("number of things returned from multiprocessing: ", len(stats))
    
                top_ten_thousand_stats.extend(stats)
                top_ten_thousand_stats = sorted(top_ten_thousand_stats, key=lambda d: d[0], reverse = True)
    
    #            print("length of sorted stats: ", len(top_ten_thousand_stats))
                top_ten_thousand_stats = top_ten_thousand_stats[0:10_000]       # returns the top 10,000 scores
    #            print("sanity check for top 10,000: ", len(top_ten_thousand_stats))

        end = time.time()
        return top_ten_thousand_stats, (end - start)

def find_most_similar_substring(arg):
    """finds the substring in the string from the dataset that has the highest similarity score
        with the string generated by the model. Returns the highest similarity score found, and the substring
        
        generated_string - string generated by the model
        dataset_string - string from training dataset"""
    gold_program, dataset_info = arg


    # splits the dataset string for searching line-by-line
    dataset_string = dataset_info['text']               # the pile uses the key 'text' to store the full string

    # if len(dataset_string) < (len(gold_program)):
    #     """if the dataset string is smaller than the generated string, we just return the similarity score and 
    #         the entire dataset string"""

    #     similarity_score = fuzz.ratio(dataset_string, gold_program)
    #     return similarity_score, dataset_string, dataset_string
    
    # creates substrings from the datastet string of equal length to the generated string
    n = len(gold_program)
    substrings = [dataset_string[i:i+n] for i in range(0, len(dataset_string))]    
    highest_score = 0
    most_similar = ""
    

    # runs through all substrings of length equal to the generated string to find the most similar substring
    for i in range(0, len(dataset_string), 3): # we only look at every 3rd substring here
        substring = dataset_string[i:i+n]


        if len(substring) < len(gold_program):
            continue
        score = fuzz.ratio(gold_program, substring)
        if score > highest_score:
            start = max(0, i-3)
            end = min(len(dataset_string), i+n+3)
            most_similar = dataset_string[start:end]
            highest_score = score

    # the pile doesn't have repo info
    repo_path = None
    repo_name = None
            
    # returns the highest score and most similar substring
    return (highest_score, most_similar, dataset_string, repo_path, repo_name)