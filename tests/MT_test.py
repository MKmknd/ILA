
from MT import nsd_similarity
from Utils import util
import sqlite3
from datetime import datetime

def extract_description(db_path):
    """
    extract description of issue for each issue id.

    Arguments:
    dp_path [string] -- database path

    Returns:
    return_dict [dict<issue id, description] -- description for each issue id
    """

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT issue_id, description FROM basic_fields;')
    return_dict = {}
    for row in cur.fetchall():

        return_dict[row[0]] = row[1]
    cur.close()
    conn.close()


    return return_dict

def extract_comment(db_path):
    """
    extract comments for each issue id.

    Arguments:
    dp_path [string] -- database path

    Returns:
    return_dict [dict<issue id, comments (a string)] -- a string of comments for each issue id
    """

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT issue_id, body FROM comments;')
    return_dict = {}
    for row in cur.fetchall():
        if not row[0] in return_dict:
            return_dict[row[0]] = ""
        return_dict[row[0]] += row[1] + "\n"
    cur.close()
    conn.close()


    return return_dict


def run():

    from Utils import git_reader
    from Utils import issue_db_reader

    repodir = "./../repository/avro"
    db_path = "./../tests/test_data/exp15/avro_issue_field_data.db"
    hash_list = git_reader.get_all_hash_without_merge(repodir)
    issue_id_list = issue_db_reader.read_issue_id_list(db_path)
    target_issue_id_list = issue_id_list[0:100]

    dsc_issue_dict = extract_description(db_path)
    comment_issue_dict = extract_comment(db_path)


    ins = nsd_similarity.NSDSimilarity(repodir=repodir, verbose=1, output_dir_cosine_sim="./test_data/MT/data")
    target_data = ins.run(hash_list, issue_id_list,
                          target_issue_id_list,
                          dsc_issue_dict, comment_issue_dict)

    util.dump_pickle("./test_data/MT/test_pickle/target_data.pickle", target_data)


    def test(test_data, target_data):
        target_hash_list = sorted(list(target_data.keys()))

        # check contents
        for target_hash in target_hash_list:
            assert test_data[target_hash]==target_data[target_hash], "content is different"

        print("TEST DONE")


    test_data = util.load_pickle("./test_data/MT/data/avro_nsd_similarity_costh2.pickle")
    target_data = util.load_pickle("./test_data/MT/test_pickle/target_data.pickle")

    test(test_data, target_data)




if __name__=="__main__":


    run()
    #_test()
