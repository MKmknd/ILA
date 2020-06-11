
from KE import keyword_extraction
from Utils import util



def run():

    from Utils import git_reader
    from Utils import issue_db_reader

    repodir = "./../repository/avro"
    db_path = "./../tests/test_data/exp15/avro_issue_field_data.db"
    hash_list = git_reader.get_all_hash_without_merge(repodir)
    issue_id_list = issue_db_reader.read_issue_id_list(db_path)
    ins = keyword_extraction.KeywordExtraction(hash_list, issue_id_list,
                                               "./../preprocess/data_AVRO/avro_log_message_info.pickle")
    data = ins.run()

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

    test_data = util.load_pickle("./test_data/KE/avro_keyword_extraction.pickle")

    test(test_data, data)




if __name__=="__main__":


    run()
