import random

from Utils import util

random_seed = 200

def extract_all_commit_hash(issue2hash_dict):
    """
    Extract all commit hashes from issue2hash_dict

    Arguments:
    issue2hash_dict [dict<issue id, list<commit_hashes>>] -- list of all linked commit hashes for each issue id

    Returns:
    all_commit_hash_set [set<commit hashes>] -- set of all commit hashes where all log messages have issues ids
    """

    all_commit_hash_set = set()
    for issue_id in issue2hash_dict.keys():
        all_commit_hash_set = all_commit_hash_set | set(issue2hash_dict[issue_id])

    return all_commit_hash_set

def convert_issue2hash_dict(issue2hash_dict):
    """
    Convert issue2hash_dict. Concretely, each issue id has not list but set

    Arguments:
    issue2hash_dict [dict<issue id, list<commit_hashes>>] -- list of all linked commit hashes for each issue id

    Returns:
    return_dict [dict<issue id, set<commit_hashes>>] -- set of all linked commit hashes for each issue id
    """

    return_dict = {}
    for issue_id in issue2hash_dict.keys():
        return_dict[issue_id] = set(issue2hash_dict[issue_id])
        
    return return_dict

def store_blinded_issue2hash_dict(all_commit_hash_set, issue2hash_dict, blind_num):
    """
    Return a blinded issue2hash_dict. Concretely, blind_num of commit hashes
    are excluded from the original issue2hash_dict.

    Arguments:
    all_commit_hash_set [set<commit hashes>] -- set of all commit hashes where all log messages have issues ids
    issue2hash_dict [dict<issue id, list<commit_hashes>>] -- list of all linked commit hashes for each issue id
    blind_num [int] -- the number of commit hashes that is blinded

    Returns:
    return_dict [dict<issue id, list<commit_hashes>>] -- list of all linked commit hashes for each issue id. However, we exclude some commit hashes that were randomly selected
    """

    all_commit_hash_list = sorted(list(all_commit_hash_set))
    issue2hash_dict_set = convert_issue2hash_dict(issue2hash_dict)

    blind_commit_hash_list = random.sample(all_commit_hash_list, blind_num)
    blind_commit_hash_set = set(blind_commit_hash_list)

    return_dict = {}
    for issue_id in issue2hash_dict.keys():
        temp_set = set([])
        temp_set = set(issue2hash_dict[issue_id]) - blind_commit_hash_set
        if len(temp_set)>0:
            return_dict[issue_id] = list(temp_set)
        else:
            pass

    return return_dict

def main(issue2hash_dict, blind_rate):
    """
    Exclude some randomly selected commit hashes from the original issue2hash_dict.
    The rate of blind is defined as blind_proportion.
    The results of the modified issue2hash_dict is stored in ./../blinded_data/
    """

    blind_pro = blind_rate/100

    all_commit_hash_set = extract_all_commit_hash(issue2hash_dict)
    num_all_commit_hash = len(all_commit_hash_set)
    print("The number of linked commits (unique): {0:,}".format(num_all_commit_hash))

    random.seed(random_seed)
    return store_blinded_issue2hash_dict(all_commit_hash_set, issue2hash_dict,
                                         int(blind_pro*num_all_commit_hash))



if __name__=="__main__":

    #for p_name in project_name_list:
    #    main(p_name)
    pass
