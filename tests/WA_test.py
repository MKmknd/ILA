
from WA import word_association
from Utils import util
import sqlite3

def _test():

    delete_rate = 10

    from Utils import git_reader
    from Utils import issue_db_reader

    db_path = "./../tests/test_data/exp15/avro_issue_field_data.db"
    issue_id_list = issue_db_reader.read_issue_id_list(db_path)

    var_mu_CB_dict = util.load_pickle("./test_data/WA/pickle/{0}_var_mu_CB.pickle".format(delete_rate))
    #var_mu_CB_dict = util.load_pickle("./test_data/WA/pickle/avro_{0}_var_mu_CB.pickle".format(delete_rate))
    count_num_issue = len(var_mu_CB_dict)
    print("number of processed issues: {0}".format(count_num_issue))

    #for cosine_sim in range(2, 10):
    cosine_sim = 5
    THRESHOLD_COSINE_SIM = cosine_sim/10
    print("cosine sim: {0}".format(THRESHOLD_COSINE_SIM))

    issue2hash_dict = {}
    for issue_id in issue_id_list:
        for commit_hash in var_mu_CB_dict.keys():
            if var_mu_CB_dict[commit_hash][issue_id] >= THRESHOLD_COSINE_SIM:
                if not issue_id in issue2hash_dict:
                    issue2hash_dict[issue_id] = []
                issue2hash_dict[issue_id].append(commit_hash)

    def test(test_data, target_data, test_target_issue_list):

        cnt = 0
        for issue_id in test_data.keys():

            if not issue_id in test_data and not issue_id in target_data:
                continue

            if not issue_id in target_data:
                cnt += 1
                continue
            #print("==")
            #print(test_data[issue_id])
            #print(target_data[issue_id])
            #print(len(target_data[issue_id]))


            #assert set(test_data[issue_id])==set(target_data[issue_id]), "content is different"
            if set(test_data[issue_id])!=set(target_data[issue_id]):
                cnt += 1

        print("cnt: {0}/{1}".format(cnt, len(test_target_issue_list)))

        print("TEST DONE")

    test_data = util.load_pickle("./test_data/WA/data/avro_10_word_association_th5.pickle")
    test(test_data, issue2hash_dict, issue_id_list)






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

    #ins = word_association.WordAssociation(delete_rate=10,
    #                                       keyword_extraction_dict_path=keyword_extraction_dict_path)
    ins = word_association.WordAssociation(ASSOC_THRESHOLD=0.5, delete_rate=10)
    target_data = ins.run(hash_list, test_target_issue_list,
                          log_message_info_path,
                          lscp_processed_data_pickle_path,
                          output_dir)

    util.dump_pickle("./test_data/WA/test_pickle/target_data.pickle", target_data)

    def test(test_data, target_data, test_target_issue_list):

        # check contents
        cnt = 0
        for issue_id in test_data.keys():

            if not issue_id in test_data and not issue_id in target_data:
                continue

            if not issue_id in target_data:
                cnt += 1
                continue
            #print("==")
            #print(test_data[issue_id])
            #print(target_data[issue_id])
            #print(len(target_data[issue_id]))


            #assert set(test_data[issue_id])==set(target_data[issue_id]), "content is different"
            if set(test_data[issue_id])!=set(target_data[issue_id]):
                cnt += 1

        print("cnt: {0}/{1}".format(cnt, len(test_target_issue_list)))

        print("TEST DONE")

    test_data = util.load_pickle("./test_data/WA/data/avro_10_word_association_th5.pickle")

    test(test_data, target_data, test_target_issue_list)




if __name__=="__main__":


    run()
    #_test()
