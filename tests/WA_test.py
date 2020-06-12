
from WA import word_association
from Utils import util
import sqlite3


def run():

    from Utils import git_reader
    from Utils import issue_db_reader

    repodir = "./../repository/avro"
    db_path = "./../tests/test_data/exp15/avro_issue_field_data.db"
    hash_list = git_reader.get_all_hash_without_merge(repodir)
    issue_id_list = issue_db_reader.read_issue_id_list(db_path)
    #test_target_issue_list = issue_id_list[0:30]
    test_target_issue_list = issue_id_list

    log_message_info_path = "./../preprocess/data_AVRO/avro_log_message_info.pickle"
    lscp_processed_data_pickle_path = "./test_data/WA/dsc_comment_string"
    output_dir = "./test_data/WA/pickle"

    keyword_extraction_dict_path = "./test_data/WA/data/avro_keyword_extraction_10.pickle"

    #ins = word_association.WordAssociation(blind_rate=10,
    #                                       keyword_extraction_dict_path=keyword_extraction_dict_path)
    ins = word_association.WordAssociation(blind_rate=10)
    target_data = ins.run(hash_list, test_target_issue_list,
                          log_message_info_path,
                          lscp_processed_data_pickle_path,
                          output_dir)

    util.dump_pickle("./test_data/WA/test_pickle/target_data.pickle", target_data)

    def test(test_data, target_data, test_target_issue_list):

        # check contents
        for issue_id in test_target_issue_list:
            print(issue_id)

            if not issue_id in test_data and not issue_id in target_data:
                continue

            print("==")
            print(test_data[issue_id])
            print(target_data[issue_id])

            assert set(test_data[issue_id])==set(target_data[issue_id]), "content is different"

        print("TEST DONE")

    test_data = util.load_pickle("./test_data/WA/data/avro_10_word_association_th5.pickle")

    test(test_data, target_data, test_target_issue_list)




if __name__=="__main__":


    run()
