
from ML import execute
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

    log_message_info_path = "./../preprocess/data_AVRO/avro_log_message_info.pickle"
    log_message_without_issueid_path = "./../preprocess/data_AVRO/avro_log_message_without_issueid.pickle"

    """
    date_issue_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are created, updated, and resolutiondate
    """
    keyword_extraction_dict_path = "./test_data/exp20/blinded_data/avro_keyword_extraction_50.pickle"
    blind_rate = 50

    dsc_issue_dict = extract_description(db_path)
    comment_issue_dict = extract_comment(db_path)

    output_dir = "./test_data/TS/test_pickle"

    ins = execute.MLModel(repo_dir=repodir, db_path=db_path, random_state=200, verbose=1,
                         keyword_extraction_dict_path=keyword_extraction_dict_path,
                         blind_rate=blind_rate, max_iteration=25)
    target_data = ins.run(hash_list, issue_id_list,
                          log_message_info_path, log_message_without_issueid_path,
                          dsc_issue_dict, comment_issue_dict, output_dir)

    util.dump_pickle("./test_data/ML/test_pickle/target_data.pickle", target_data)


    def test(test_data, target_data):
        test_hash_list = sorted(list(test_data.keys()))
        target_hash_list = sorted(list(target_data.keys()))

        # check length
        assert len(test_hash_list) == len(target_hash_list), "{0} and {1}".format(len(test_hash_list), len(target_hash_list))

        # check contents
        for test_hash, target_hash in zip(test_hash_list, target_hash_list):
            assert test_hash==target_hash, "commit hash is not same"

            assert test_data[test_hash]==target_data[target_hash], "content is different"

        print("TEST DONE")


    target_data = util.load_pickle("./test_data/ML/test_pickle/target_data.pickle")
    test_data = util.load_pickle("./test_data/ML/data/avro_RF_50_model.pickle")

    test(test_data, target_data)




if __name__=="__main__":


    run()
    #_test()
