from datetime import timedelta
from Utils import util
from Utils import git_reader
from Utils import generate_blind_data

from KE import keyword_extraction

from TF import time_filtering


class Phantom:
    def __init__(self, repo_dir, TIME_INTERVAL_BEFORE=timedelta(days=3), TIME_INTERVAL_AFTER=timedelta(days=3),
                 DUPLICATE_RATE=0.66, verbose=0, keyword_extraction_dict_path=None, blind_rate=None):
        """
        TIME_INTERVAL_{BEFORE|AFTER}: time interval before or after a linked commit. if another non-linked commit
                                      is located this interval, these two commits would be linked
        DUPLICATE_RATE: proportion of duplicated files between two commits. if these two commits shared
                        the files over or equal to this rate, these two commits would be linked
        """
        self.repo_dir = repo_dir
        self.TIME_INTERVAL_BEFORE = TIME_INTERVAL_BEFORE
        self.TIME_INTERVAL_AFTER = TIME_INTERVAL_AFTER

        self.DUPLICATE_RATE = DUPLICATE_RATE
        self.verbose = verbose
        self.keyword_extraction_dict_path=keyword_extraction_dict_path
        self.blind_rate = blind_rate

    def extract_linked_non_linked_hash(self, data_dict, hash_list):
        """
        Return linked and non-linked commit hashes.

        Arguments:
        data_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes (associated by a certain filter).
        hash_list [list<commit hash>] -- studied commit hash list

        Returns:
        linked_hash_set [set<commit hash>] -- linked commit hashes
        non_linked_hash_set [set<commit hash>] -- non-linked commit hashes
        """

        if self.verbose > 0:
            print("extract linked and non linked hash")

        len_data_dict = len(data_dict)

        linked_hash_set = set()
        for idx_issue_id, issue_id in enumerate(data_dict.keys()):

            if self.verbose > 0:
                if idx_issue_id%1000==0:
                    print("Done issue id {0}/{1}".format(idx_issue_id, len_data_dict))

            linked_hash_set = linked_hash_set | set(data_dict[issue_id])

        non_linked_hash_set = set(hash_list) - linked_hash_set

        return linked_hash_set, non_linked_hash_set


    def dev_condition(self, date_repo_dict, linked_hash_set, non_linked_hash_set):
        """
        Check the dev condition

        Arguments:
        date_repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        linked_hash_set [set<commit hash>] -- linked commit hashes
        non_linked_hash_set [set<commit hash>] -- non-linked commit hashes

        Returns:
        hash_pair_set [set<tuple<linked hash, non-linked hash>>] -- having all commit hash pairs that have the same author
        """

        if self.verbose > 0:
            print("dev condition")

        len_linked_hash_set = len(linked_hash_set)

        hash_pair_set = set()
        for idx_linked_hash, linked_hash in enumerate(linked_hash_set):

            if self.verbose > 0:
                if idx_linked_hash%1000==0:
                    print("Done issue id {0}/{1}".format(idx_linked_hash, len_linked_hash_set))

            for non_linked_hash in non_linked_hash_set:

                hash_pair_set.add((linked_hash, non_linked_hash))


        return hash_pair_set

    def time_condition(self, date_repo_dict, hash_pair_set):
        """
        Check the time condition

        Arguments:
        date_repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        hash_pair_set [set<tuple<linked hash, non-linked hash>>] -- having all commit hash pairs that have the same author

        Returns:
        return_hash_pair_set [set<tuple<linked hash, non-linked hash>>] -- having all commit hash pairs that have the same author and meet the time condition
        """
        time_filtering_obj = time_filtering.TimeFiltering()
        COMMIT_DATE_KEYWORD = time_filtering_obj.COMMIT_DATE_KEYWORD

        if self.verbose > 0:
            print("time condition")
        len_hash_pair_set = len(hash_pair_set)

        return_hash_pair_set = set()
        for idx_pair, pair in enumerate(hash_pair_set):

            if self.verbose > 0:
                if idx_pair%1000==0:
                    print("Done issue id {0}/{1}".format(idx_pair, len_hash_pair_set))

            linked_hash_date = date_repo_dict[pair[0]][COMMIT_DATE_KEYWORD]
            non_linked_hash_date = date_repo_dict[pair[1]][COMMIT_DATE_KEYWORD]

            if linked_hash_date.date() <= (non_linked_hash_date.date() + self.TIME_INTERVAL_AFTER) and linked_hash_date.date() >= (non_linked_hash_date.date() - self.TIME_INTERVAL_BEFORE):
                return_hash_pair_set.add(pair)

        return return_hash_pair_set

    def extract_modified_file_repo(self, hash_list):
        """
        Extract all modified files for each commit hash in the (org) repository

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list

        Returns:
        return_dict [dict<commit hash, list<modified files>>] -- modified files list for each commit hash
        """

        print("Extract modified files")
        return_dict = {}
        num_hash_list = len(hash_list)
        for idx, commit_hash in enumerate(hash_list):
            if idx%1000==0:
                print("{0}/{1}".format(idx, num_hash_list))
            return_dict[commit_hash] = git_reader.get_all_modified_files(self.repo_dir, commit_hash)

        return return_dict

    def resource_condition(self, hash_pair_set):
        """
        Check the resource condition

        Arguments:
        hash_pair_set [set<tuple<linked hash, non-linked hash>>] -- having all commit hash pairs that have the same author and meet the time condition

        Returns:
        return_hash_pair_set [set<tuple<linked hash, non-linked hash>>] -- having all commit hash pairs that have the same author, meet the time condition, and the meet the resource condition
        """
        all_hash_set = set()
        for pair in hash_pair_set:
            all_hash_set.add(pair[0])
            all_hash_set.add(pair[1])


        if self.verbose > 0:
            print("resource condition")
        len_hash_pair_set = len(hash_pair_set)

        # modified_file_repo_dict [dict<commit hash, list<modified files>>] -- modified files list for each commit hash
        modified_file_repo_dict = self.extract_modified_file_repo(list(all_hash_set))
        return_hash_pair_set = set()
        for idx_pair, pair in enumerate(hash_pair_set):

            if self.verbose > 0:
                if idx_pair%1000==0:
                    print("Done issue id {0}/{1}".format(idx_pair, len_hash_pair_set))

            linked_hash_set = set(modified_file_repo_dict[pair[0]])
            non_linked_hash_set = set(modified_file_repo_dict[pair[1]])

            if len(linked_hash_set)==0:
                continue
            if len(linked_hash_set.intersection(non_linked_hash_set))/len(linked_hash_set) < self.DUPLICATE_RATE:
                continue

            return_hash_pair_set.add(pair)

        return return_hash_pair_set


    def make_issue2hash_dict(self, keyword_extraction_dict, hash_pair_set):
        """
        Combine the issue2hash_dict generated by the keyword extraction phase with the commit hashes that were detected by the phantom heuristics

        Arguments:
        keyword_extraction_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes that include the issue id
        hash_pair_set [set<tuple<linked hash, non-linked hash>>] -- having all commit hash pairs that have the same author, meet the time condition, and the meet the resource condition

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes including those meeting the phantom heuristics
        """

        hash_pair_dict = {}
        for pair in hash_pair_set:
            hash_pair_dict[pair[0]] = pair[1]

        if self.verbose > 0:
            print("make issue2hash dict")
        len_keyword_extraction = len(keyword_extraction_dict)

        return_dict = {}
        for idx_issue_id, issue_id in enumerate(keyword_extraction_dict.keys()):

            if self.verbose > 0:
                if idx_issue_id%1000==0:
                    print("Done issue id {0}/{1}".format(idx_issue_id, len_keyword_extraction))

            temp_commit_set = set()
            for commit_hash in keyword_extraction_dict[issue_id]:
                if not commit_hash in hash_pair_dict:
                    continue

                temp_commit_set.add(hash_pair_dict[commit_hash])

            return_dict[issue_id] = list(set(keyword_extraction_dict[issue_id]) | temp_commit_set)

        return return_dict

    def run(self, hash_list, issue_id_list, log_message_info_path):
        """
        Combine issue ids and commit hashes using shared files matching.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        log_messgae_info_pickle_path [string] -- path to log_message_info.pickle

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes modified the same files with the patches in issue id
        """

        # extract linked and non-linked commit hash sets
        if self.keyword_extraction_dict_path:
            keyword_extraction_dict = util.load_pickle(self.keyword_extraction_dict_path)
        else:
            ins = keyword_extraction.KeywordExtraction()
            keyword_extraction_dict = ins.run(hash_list, issue_id_list, log_message_info_path) # train data
            keyword_extraction_dict = generate_blind_data.main(keyword_extraction_dict, self.blind_rate)

        linked_hash_set, non_linked_hash_set = self.extract_linked_non_linked_hash(keyword_extraction_dict, hash_list)

        """
        date_repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        """
        date_repo_dict = util.load_pickle(log_message_info_path) #

        # dev condition
        hash_pair_set = self.dev_condition(date_repo_dict, linked_hash_set, non_linked_hash_set)

        # time condition
        hash_pair_set = self.time_condition(date_repo_dict, hash_pair_set)

        # resource condition
        hash_pair_set = self.resource_condition(hash_pair_set)
        #hash_pair_set = resource_condition(p_name, set({('cf2fd0bad1750400d9a654d9f53450c7900062e9','5011f075a6c8fcbfaf21e21f183dd693eddfde79'),('f3f6ca7d8ce34c20ed6ae311b113cb4c35be7beb','9d7dfd4fe01b3a5735da7dd80c08aaa98039e953')}))
        #print(hash_pair_set)

        issue2hash_dict = self.make_issue2hash_dict(keyword_extraction_dict, hash_pair_set)
        #issue2hash_dict = self.make_issue2hash_dict(keyword_extraction_dict, set({('cf2fd0bad1750400d9a654d9f53450c7900062e9','b8cb4035eb418882ed5185f8c3b46d63da53c46c'),('f76750a2af7107c6636c3f966a471765d2cb0e42','adcfc550345b8a1656a3efe63c2c969639422845')}))

        return issue2hash_dict




