import re
import sqlite3
import sys
sys.path.append("./../../Utils")
import util
import git_reader

DUPLICATE_RATE = 0.66 # if the proportion of the duplication of modified files between issue and commit is over or equal to this threshold, we identify these issue and commit are a pair

def extract_attached_files(db_path):
    """
    WIP: IN THE FUTURE, WE NEED TO SORTE THE ATTACHED FILES BY THEIR CREATED DATE

    Arguments:
    dp_path [string] -- database path

    Returns:
    return_dict [dict<issue id, list<file name>>] -- attached file list for each issue. Note that extracting issues including "patch"
    """

    re_patch = re.compile(".*patch.*")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT issue_id, file_name FROM attached_files;')
    return_dict = {}
    for row in cur.fetchall():
        if not re_patch.match(row[1]):
            continue

        if not row[0] in return_dict:
            return_dict[row[0]] = []
        return_dict[row[0]].append(row[1])
    cur.close()
    conn.close()

    """
    WIP: WE NEED TO SORT ATTACHED FILES BY THEIR CREATED DATE FOR EACH ISSUE ID
    """

    return return_dict

def extract_attached_file_content(db_path, issue_id, file_name):

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT content FROM attached_files WHERE issue_id="{0}" AND file_name="{1}";'.format(issue_id, file_name))
    for idx, row in enumerate(cur.fetchall()):
        content = row[0]
    cur.close()
    conn.close()

    if idx!=0:
        print("SOMETHING WEIRD HAPPEND IN extract_attached_file_content")
        sys.exit()

    return content

def extract_modified_file_issue(db_path, attached_file_dict, issue_id_list):
    """
    WIP: Return a dictionary. key: issue id, value: modified file list in the patches

    Arguments:
    dp_path [string] -- database path
    attached_file_dict [dict<issue id, list<file names of an attached patch>>] -- file names of all attached patches for each issue id
    issue_id_list [list<studied issue id>] -- studied issue id

    Returns:
    return_dict [dict<issue id, dict<cur or pre file, list<modified file pathes>>>] -- modified file pathes for each issue id.
    """

    re_pre_f_name = re.compile("---\s(\S*).*")
    re_cur_f_name = re.compile("\+\+\+\s(\S*).*")

    return_dict = {}
    for issue_id in issue_id_list:
        if not issue_id in return_dict:
            return_dict[issue_id] = {'pre_f':[], 'cur_f':[]}

        if not issue_id in attached_file_dict:
            return_dict[issue_id] = {}
            continue

        content = extract_attached_file_content(db_path, issue_id, attached_file_dict[issue_id][-1]) # only check the final file (in the future, this would be the latest added file
        #print(issue_id)
        #print(attached_file_dict[issue_id][-1])
        #print(content)

        for row in content.splitlines():
            match = re.search(re_pre_f_name, row)
            if match:
                return_dict[issue_id]['pre_f'].append(match.group(1))

            match = re.search(re_cur_f_name, row)
            if match:
                return_dict[issue_id]['cur_f'].append(match.group(1))

    return return_dict

def extract_modified_file_repo(p_name, hash_list):
    """
    Extract all modified files for each commit hash in the (org) repository

    Arguments:
    p_name [string] -- project name string
    hash_list [list<commit hash>] -- studied commit hash list

    Returns:
    return_dict [dict<commit hash, list<modified files>>] -- modified files list for each commit hash
    """

    print("Extract modified files")
    repo_dir = "./../../repository/{0}".format(p_name)
    return_dict = {}
    num_hash_list = len(hash_list)
    for idx, commit_hash in enumerate(hash_list):
        if idx%1000==0:
            print("{0}/{1}".format(idx, num_hash_list))
        return_dict[commit_hash] = git_reader.get_all_modified_files(repo_dir, commit_hash)

    return return_dict

def compare_modified_files(modified_file_issue_dict, modified_file_repo_dict):
    """
    Compare modified files in a patch in an issue id with those at a commit.
    If the proportion of duplication is over DUPLICATE_RATE, it is identified
    as a pair.

    Arguments:
    modified_file_issue_dict [dict<issue id, dict<cur or pre file, list<modified file pathes>>>] -- modified file pathes for each issue id.
    modified_file_repo_dict [dict<commit hash, list<modified files>>] -- modified files list for each commit hash

    Returns:
    return_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes might fix the issue
    """

    return_dict = {}
    for issue_id in modified_file_issue_dict.keys():
        if len(modified_file_issue_dict[issue_id])==0:
            continue
        #print("issue id")
        #print(issue_id)
        #print(modified_file_issue_dict[issue_id]['pre_f'])
        issue_set = set(modified_file_issue_dict[issue_id]['pre_f'])
        for commit_hash in modified_file_repo_dict.keys():
            #print(commit_hash)
            #print(modified_file_repo_dict[commit_hash])
            repo_set = set(modified_file_repo_dict[commit_hash])
            #if len(issue_set.intersection(repo_set))/len(repo_set) < DUPLICATE_RATE:
            if len(issue_set.intersection(repo_set))/len(issue_set) < DUPLICATE_RATE:
                continue

            if not issue_id in return_dict:
                return_dict[issue_id] = []

            return_dict[issue_id].append(commit_hash)

    return return_dict




def run(p_name, hash_list, issue_id_list):
    """
    Combine issue ids and commit hashes using shared files matching.

    Arguments:
    p_name [string] -- project name string
    hash_list [list<commit hash>] -- studied commit hash list
    issue_id_list [list<issue id>] -- studied issue id list

    Returns:
    issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes modified the same files with the patches in issue id
    """

    db_path = "./../../exp15/db/{0}_issue_field_data.db".format(p_name)
    attached_file_dict = extract_attached_files(db_path)
    print("number of issue ids which have at least one patch file: {0}".format(len(attached_file_dict)))
    print("number of attached files which are patch files".format(len([row for key in attached_file_dict.keys() for row in attached_file_dict[key]])))

    modified_file_issue_dict = extract_modified_file_issue(db_path, attached_file_dict, issue_id_list)
    modified_file_repo_dict = extract_modified_file_repo(p_name, hash_list)

    issue2hash_dict = compare_modified_files(modified_file_issue_dict, modified_file_repo_dict)


    return issue2hash_dict




if __name__=="__main__":

    """
    ANSWER:
    HADOOP-5213 -- cf2fd0bad1750400d9a654d9f53450c7900062e9, 5011f075a6c8fcbfaf21e21f183dd693eddfde79, a20c705c8ee8bf2cb00504e4eb09a07dc17470e7
    HADOOP-4840 -- f3f6ca7d8ce34c20ed6ae311b113cb4c35be7beb, 9d7dfd4fe01b3a5735da7dd80c08aaa98039e953, 6960cbca35264c7a2240b70e225b9b2f70f11605, f59975a1a5df6576b2ed0c7a30ee039ee29d7054
    HADOOP-4854 -- 0bedee128820c09ed60a07fd4ee11ad39e22e76a, f76750a2af7107c6636c3f966a471765d2cb0e42

    no tag name -- 412035b47a1b0116cb53ce612a61cd087d5edc41, 705b172b95db345a99adf088fca83c67bd13a691
    """
    hash_list = ['cf2fd0bad1750400d9a654d9f53450c7900062e9', '5011f075a6c8fcbfaf21e21f183dd693eddfde79', 'a20c705c8ee8bf2cb00504e4eb09a07dc17470e7', '412035b47a1b0116cb53ce612a61cd087d5edc41', '705b172b95db345a99adf088fca83c67bd13a691', 'f3f6ca7d8ce34c20ed6ae311b113cb4c35be7beb', '9d7dfd4fe01b3a5735da7dd80c08aaa98039e953', '6960cbca35264c7a2240b70e225b9b2f70f11605', 'f59975a1a5df6576b2ed0c7a30ee039ee29d7054', '0bedee128820c09ed60a07fd4ee11ad39e22e76a', 'f76750a2af7107c6636c3f966a471765d2cb0e42'] 
    issue_id_list = ['HADOOP-5213', 'HADOOP-4840', 'HADOOP-4854']
    print(run("hadoop", hash_list, issue_id_list))
