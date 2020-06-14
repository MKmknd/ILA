
from PH import phantom
from Utils import util
import sqlite3
from datetime import datetime


def run():

    from Utils import git_reader
    from Utils import issue_db_reader

    repodir = "./../repository/avro"
    db_path = "./../tests/test_data/exp15/avro_issue_field_data.db"
    hash_list = git_reader.get_all_hash_without_merge(repodir)
    issue_id_list = issue_db_reader.read_issue_id_list(db_path)

    log_message_info_path = "./../preprocess/data_AVRO/avro_log_message_info.pickle"


    keyword_extraction_dict_path = "./test_data/exp20/blinded_data/avro_keyword_extraction_50.pickle"
    ins = phantom.Phantom(repo_dir=repodir, verbose=0, keyword_extraction_dict_path=keyword_extraction_dict_path,
                          blind_rate=50)
    target_data = ins.run(hash_list, issue_id_list,
                          log_message_info_path)

    util.dump_pickle("./test_data/PH/test_pickle/target_data.pickle", target_data)


    def test(test_data, target_data):
        test_hash_list = sorted(list(test_data.keys()))
        target_hash_list = sorted(list(target_data.keys()))

        # check length
        assert len(test_hash_list) == len(target_hash_list), "{0} and {1}".format(len(test_hash_list), len(target_hash_list))

        # check contents
        for test_hash, target_hash in zip(test_hash_list, target_hash_list):
            print(test_hash)
            assert test_hash==target_hash, "commit hash is not same"

            assert set(test_data[test_hash])==set(target_data[target_hash]), "content is different"

        print("TEST DONE")


    target_data = util.load_pickle("./test_data/PH/test_pickle/target_data.pickle")
    test_data = util.load_pickle("./test_data/PH/data/avro_50_phantom.pickle")

    test(test_data, target_data)




if __name__=="__main__":


    run()
    #_test()
