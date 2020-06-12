
from TS import ntext_similarity
from Utils import util
import sqlite3
from datetime import datetime, timedelta

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

    dsc_issue_dict = extract_description(db_path)
    comment_issue_dict = extract_comment(db_path)

    log_message_without_issueid_path = "./../preprocess/data_AVRO/avro_log_message_without_issueid.pickle"

    test_target_hash_list = issue_id_list[0:100]

    ins = ntext_similarity.NtextSimilarity(parallel_iteration=1)
    target_data = ins.run(hash_list, issue_id_list, test_target_hash_list, dsc_issue_dict,
                   comment_issue_dict, log_message_without_issueid_path,
                   "./test_data/TS/test_pickle")

    util.dump_pickle("./test_data/TS/test_pickle/target_data.pickle", target_data)

    def test(test_data, test_pickle, target_data, target_pickle, test_target_hash_list):

        # check contents
        for hash in test_target_hash_list:

            if not hash in test_data and not hash in target_data:
                continue

            assert set(test_data[hash])==set(target_data[hash]), "content is different"
            #assert test_pickle[hash]==target_pickle[hash], "content is different"
            #assert test_data[hash]==target_data[hash], "content is different"
            #assert test_pickle[hash]==target_pickle[hash], "content is different"

        print("TEST DONE")

    test_data = util.load_pickle("./test_data/TS/data/avro_ntext_similarity_costh3.pickle")
    test_pickle = util.load_pickle("./test_data/TS/pickle/avro_cosine_similarity_dict_ite1.pickle")
    target_pickle = util.load_pickle("./test_data/TS/test_pickle/cosine_similarity_dict_ite1.pickle")

    test(test_data, test_pickle, target_data, target_pickle, test_target_hash_list)




if __name__=="__main__":


    run()
