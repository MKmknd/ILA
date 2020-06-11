#import unittest

from preprocess.check_all_log_repository import ExtractCommitMessage
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
    ins = ExtractCommitMessage(repo_dir="./../repository/avro",
                               p_name="avro", apache_issue_id_prefix="AVRO",
                               output_dir="./../preprocess/data_AVRO", verbose=1)
    ins.run()

    test_data = util.load_pickle("./test_data/avro_log_message_info.pickle")
    target_data = util.load_pickle("./../preprocess/data_AVRO/avro_log_message_info.pickle")

    tset_hash_list = sorted(list(test_data.keys()))
    target_hash_list = sorted(list(target_data.keys()))

    # check length
    assert len(tset_hash_list) == len(target_hash_list), "{0} and {1}".format(len(tset_hash_list), len(target_hash_list))

    # check contents
    for test_hash, target_hash in zip(tset_hash_list, target_hash_list):
        assert test_hash==target_hash, "commit hash is not same"

        for target_row in ["issue_id", "author_date", "commit_date"]:
            assert test_data[test_hash][target_row]==target_data[target_hash][target_row], "content is different: {0}".format(target_row)

    print("TEST ODNE")


if __name__=="__main__":


    run()