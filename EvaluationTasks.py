import time
import json
import os
import multiprocessing
from tqdm import tqdm
from datasets import load_dataset
from multiprocessing import Pool
from fuzzywuzzy import fuzz

# nProcs = int(os.environ['PROCS'])

# load files first
# all_files = [f"Github_Split/The_Pile_Github_Split_{i}.jsonl" for i in range(30)]
# all_file_strings = []
# print("start file reading")
# for fn in tqdm(all_files):
#     with open(fn, "r") as f:
#         file_strings = [json.loads(s) for s in f.readlines()]
#         all_file_strings.extend(file_strings)
# print("file reading completes")


class EvaluationTask:
    def __init__(self, gold_programs_path: str, output_path: str, start_index: int, end_index: int, num_workers: int=None):
        self.start_index = start_index
        self.end_index = end_index
        self.gold_programs_path = gold_programs_path
        self.gold_programs = []
        self.read_data()
        self.dataset = []
        # self.format_dataset()
        self.output_path = output_path
        self.num_workers = num_workers

    def read_data(self):
        """Reads data from the input file. Saves it in json format in self.examples for later reference.
            It only saves the programs in the inputted range though."""
        
        if self.gold_programs_path == "human_eval":
            # print("loading human eval dataset")
            # file = '/home/mr2489/StarcoderRobustness/gcloud/humanevalresults.jsonl'
            ds = load_dataset("openai_humaneval")
            start = self.start_index - 1
            end = self.end_index
            self.gold_programs = ds['test'][start:end]
        # else:

        # print("reading the data right now")
        # with open(self.gold_programs_path, "r") as f:
        #     gold_programs = [json.loads(s) for s in f.readlines()]
        #     start = self.start_index - 1
        #     end = self.end_index
        #     self.gold_programs = gold_programs[start:end]
        # print("done reading the data")

    def format_dataset(self):
        """formats the starcoder dataset"""
        ds = load_dataset("bigcode/starcoderdata", data_dir="python", split="train")
        ds = ds.select([1,2,3,4,5,6,7,8,9,19])
        self.dataset = ds.flatten()
        # print("first thing of the dataset: ", self.dataset[0])

        # print("beginning to load the github split")
        # with open('/home/mr2489/project/Martin-Riddell-Summer-2023/Full_Github_Split.jsonl', "r") as f:
        #     ds = [json.loads(s) for s in f.readlines()]
        # self.dataset = ds[0:10]
        # print("first thing of the dataset: ", self.dataset[0])


    def start_scoring(self):
        """begins to find similarity scores between generated answers and training  dataset"""

        strings = self.gold_programs
        times = []
        first = True
        i = 0
        if True:        # terrible coding practices
        # if self.gold_programs_path == "human_eval":         # the gold programs are stored differently in human eval dataset compared to the mbpp results
            for string in tqdm(strings['canonical_solution']):
                # print("string: ", string)
#                print("strings: ", strings)
                print("searching for string:\n", string)
                print("length of the program: ", len(string))
                times.append(self.score_string(string))          
        else:                                               # processes the mbpp results
            for string in tqdm(strings):
                print(string)
                # print("searching for the gold program:\n", string['metadata']['code'])
                # print("length of the gold program: ", len(string['metadata']['code']))
                
                print("searching for the generated program:\n", string['generated_program']['program'])
                print("length of the generated program: ", len(string['generated_program']['program']))
                times.append(self.score_string(string))

        print("total time: ", sum(times), "average time per string: ", sum(times) / len(times))

    def score_string(self, string_metadata):
        """finds the top 5 most similar substrings within the training dataset to the string"""

        if self.gold_programs_path == "human_eval":
            stats, t = self.find_similar_substrings(string_metadata)
            json_object = {
            "time": t,
            "gold_program": string_metadata
            }
            print("json object:\n", json_object)
        else:
            stats, t = self.find_similar_substrings(string_metadata['gold_program']['program'])
            json_object = {
                "time": t,
                "gold_program": string_metadata['gold_program']['program']
            }
        


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
            
                dataset_strings = ds#[0:5]  # used to append ds, make sure it's the full thing when being done for real
                # dataset_strings = self.dataset
    #            print("length of dataset before multiprocessing: ", len(dataset_strings))
    
                self.string = string            # this is set here so that it doesn't need to be passed along when mapping
                args = []
                for x in dataset_strings:
                    args.append((self.string, x))
    
    #            print("there are {} cpus available".format(multiprocessing.cpu_count()))
                with Pool(self.num_workers) as p:
                    stats = p.map(find_most_similar_substring, args)       # returns the highest scores and most similar substrings to the gold program for each 
    
    #            print("number of things returned from multiprocessing: ", len(stats))
    
                top_ten_thousand_stats.extend(stats)
                top_ten_thousand_stats = sorted(top_ten_thousand_stats, key=lambda d: d[0], reverse = True)
    
    #            print("length of sorted stats: ", len(top_ten_thousand_stats))
                top_ten_thousand_stats = top_ten_thousand_stats[0:10000]       # returns the top 10,000 scores
    #            print("sanity check for top 10,000: ", len(top_ten_thousand_stats))

        end = time.time()
        return top_ten_thousand_stats, (end - start)

def find_most_similar_substring(arg):
    """finds the substring in the string from the dataset that has the highest similarity score
        with the string generated by the model. Returns the highest similarity score found, and the substring
        
        generated_string - string generated by the model
        dataset_string - string from training dataset"""
    gold_program, dataset_info = arg

    # gold_program = gold_program.split('\n')

    # splits the dataset string for searching line-by-line
    # dataset_string = dataset_info['content']
    dataset_string = dataset_info['text']               # the pile uses the key 'text' to store the full string
    # dataset_string = dataset_string.split('\n')

    if len(dataset_string) < (len(gold_program)):
        """if the dataset string is smaller than the generated string, we just return the similarity score and 
            the entire dataset string"""

        # gold_program = "\n".join(gold_program)
        # dataset_string = "\n".join(dataset_string)

        similarity_score = fuzz.ratio(dataset_string, gold_program)
        return similarity_score, dataset_string, dataset_string
    
    # creates substrings from the datastet string of equal length to the generated string
    n = len(gold_program)
    substrings = [dataset_string[i:i+n] for i in range(0, len(dataset_string))]    
    highest_score = 0
    most_similar = ""
    
    # converts the gold program back to one string
    # gold_program = "\n".join(gold_program)

    # runs through all substrings of length equal to the generated string to find the most similar substring
    for i in range(0, len(dataset_string), 3): # we only look at every 3rd substring here
        substring = dataset_string[i:i+n]

        # converts the substring to one string
        # substring = "\n".join(substring)

        if len(substring) < len(gold_program):
            continue
        score = fuzz.ratio(gold_program, substring)
        if score > highest_score:
            start = max(0, i-3)
            end = min(len(dataset_string), i+n+3)
            most_similar = dataset_string[start:end]
            highest_score = score

    # the pile doesn't have repo info
    repo_path = dataset_info.get('max_stars_repo_path', None)
    repo_name = dataset_info.get('max_stars_repo_name', None)

    # dataset_string = "\n".join(dataset_string)
            
    # returns the highest score and most similar substring
    return (highest_score, most_similar, dataset_string, repo_path, repo_name)