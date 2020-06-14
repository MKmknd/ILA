
from LO import loner
from Utils import util
import sqlite3
from datetime import datetime

def extract_datetime_from_string(target):
    return datetime.strptime(target, "%Y-%m-%dT%H:%M:%S.%f%z")

def extract_dates(db_path):
    """
    extract created, updated and resolutiondate for each issue id.

    Arguments:
    dp_path [string] -- database path

    Returns:
    return_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are created, updated, and resolutiondate
    """

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT issue_id, created, updated, resolutiondate FROM basic_fields;')
    return_dict = {}
    for row in cur.fetchall():

        return_dict[row[0]] = {'created': extract_datetime_from_string(row[1]),
                               'updated': extract_datetime_from_string(row[2]),
                               'resolutiondate': extract_datetime_from_string(row[3])}
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

    """
    date_issue_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are created, updated, and resolutiondate
    """
    date_issue_dict = extract_dates(db_path)

    keyword_extraction_dict_path = "./test_data/exp20/blinded_data/avro_keyword_extraction_50.pickle"
    ins = loner.Loner(time_interval_after=30, blind_rate=50,
                      keyword_extraction_dict_path=keyword_extraction_dict_path)
    #ins = loner.Loner(time_interval_after=30, blind_rate=50)
    target_data = ins.run(hash_list, issue_id_list,
                          log_message_info_path,
                          date_issue_dict)

    util.dump_pickle("./test_data/LO/test_pickle/target_data.pickle", target_data)


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


    test_data = util.load_pickle("./test_data/LO/data/avro_50_loner.pickle")

    test(test_data, target_data)




if __name__=="__main__":


    run()
    #_test()
