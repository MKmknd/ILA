#import unittest

from preprocess.extract_log_msg_repository import ExtractRawCommitMessage
from Utils import util


#class TestPreprocessCheckAllLogRepository(unittest.TestCase):
#
#    def commit_hash(self):
#
#        test_data = util.load_pickle("./test_data/avro_log_message_info.pickle")
#        target_data = util.load_pickle("./../preprocess/data_AVRO/avro_log_message_info.pickle")
#
#        tset_hash_list = sorted(list(test_data.keys()))
#        target_hash_list = sorted(list(target_data.keys()))
#
#        # check length
#        self.assertEqual(len(tset_hash_list), len(target_hash_list))
#
#        # check contents
#        for test_hash, target_hash in zip(tset_hash_list, target_hash_list):
#            self.assertEqual(test_hash, target_hash)

def run():
    ins = ExtractRawCommitMessage(repo_dir="./../repository/avro",
                               p_name="avro", apache_issue_id_prefix="AVRO",
                               output_dir="./../preprocess/data_AVRO")
    ins.run()

    def test(test_data, target_data):
        test_hash_list = sorted(list(test_data.keys()))
        target_hash_list = sorted(list(target_data.keys()))

        # check length
        assert len(test_hash_list) == len(target_hash_list), "{0} and {1}".format(len(tset_hash_list), len(target_hash_list))

        # check contents
        for test_hash, target_hash in zip(test_hash_list, target_hash_list):
            assert test_hash==target_hash, "commit hash is not same"

            assert test_data[test_hash]==target_data[target_hash], "content is different"

        print("TEST DONE")

    test_org_data = util.load_pickle("./test_data/avro_log_message.pickle")
    test_mod_data = util.load_pickle("./test_data/avro_log_message_without_issueid.pickle")

    target_data = util.load_pickle("./../preprocess/data_AVRO/avro_log_message.pickle")
    test(test_org_data, target_data)
    target_data = util.load_pickle("./../preprocess/data_AVRO/avro_log_message_without_issueid.pickle")
    test(test_mod_data, target_data)




if __name__=="__main__":


    run()