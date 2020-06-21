from datetime import timedelta
from Utils import util
from Utils import generate_delete_data

from KE import keyword_extraction

from TF import time_filtering



class Loner:

    def __init__(self, keyword_extraction_flag=1, name_type_repo="committer", time_interval_after=30, verbose=1, keyword_extraction_dict_path=None, delete_rate=None):
        """

        Note that keyword_extraction_flag should be 1 since this flag corresponds to
        NonLinkedCommit(y) condition in the paper (schermann2015ICPC.pdf).
        If you want to use this class in a special case
        (to compute the precision and recall in comparison with the keywowrd extraction result),
        please use 0
        """
        self.keyword_extraction_flag = keyword_extraction_flag
        self.name_type_repo = name_type_repo
        self.time_interval_after = time_interval_after
        self.verbose = verbose
        self.keyword_extraction_dict_path=keyword_extraction_dict_path
        self.delete_rate = delete_rate

    def update_hash_issue_list_not_match(self, data_dict, hash_list, issue_id_list):
        """
        Check the original hash_list and issue_id_list for removing entities that
        were already detected by a certain filter

        Arguments:
        data_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes (associated by a certain filter).
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        return_hash_list [list<commit hash>] -- studied commit hash list (already removed the detected commit hashes)
        return_issue_id_list [list<issue id>] -- studied issue id list (already removed the detected issue ids)
        """
        return_hash_list = []
        return_issue_id_list = []
        detected_hash_set = set()
        detected_issue_id_set = set(data_dict.keys())

        for issue_id in data_dict.keys():
            detected_hash_set = detected_hash_set | set(data_dict[issue_id])

        for commit_hash in hash_list:
            if commit_hash in detected_hash_set:
                continue
            return_hash_list.append(commit_hash)

        for issue_id in issue_id_list:
            if issue_id in detected_issue_id_set:
                continue
            return_issue_id_list.append(issue_id)

        return return_hash_list, return_issue_id_list

    def update_hash_issue_list_match(self, data_dict):
        """
        Check the original hash_list and issue_id_list for removing entities that
        were not matched by this certain filter (so only extract all info from data_dict)

        Arguments:
        data_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes (associated by a certain filter).

        Returns:
        return_hash_list [list<commit hash>] -- studied commit hash list (already removed the detected commit hashes)
        return_issue_id_list [list<issue id>] -- studied issue id list (already removed the detected issue ids)
        """
        return_hash_set = set()
        return_issue_id_list = list(data_dict.keys())

        for issue_id in data_dict.keys():
            return_hash_set = return_hash_set | set(data_dict[issue_id])


        return list(return_hash_set), return_issue_id_list

    def combine_filter(self, pre_dict, af_dict):
        """
        Combine the result of the two filters.
        A filter indicates our filter such as the developer filter.

        Arguments:
        pre_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are selected for each issue id in terms of a filter
        af_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are selected for each issue id in terms of a filter. this filter is applied to the data after appling the first filter (pre_dict)

        Returns:
        return_dict [dict<issue id, list<commit_hash>>] -- issue id to list of commit hashes. this pair satisfied the both conditions of pre and af.
        """

        return_dict = {}
        for issue_id in af_dict.keys():
            if not issue_id in pre_dict:
                return_dict[issue_id] = af_dict[issue_id]

            pre_commit_hash_set = set(pre_dict[issue_id])
            af_commit_hash_set = set(af_dict[issue_id])

            uni_list = list(pre_commit_hash_set & af_commit_hash_set)

            return_dict[issue_id] = uni_list

        return return_dict


    def check_commit_condition(self, date_issue_dict, date_repo_dict, comb_filtering_dict, time_filtering_obj):
        """
        Check commit condition: there does not exist any commits that were offered by a developer
        who offered a commit to resolve an issue between that commit date and the resolved date.
        In addition, check the loner condition: an issue has just one commit hash.
        Since the remaining condition is the reopen condition, we can apply this loner condition
        before that final condition

        Arguments:
        date_issue_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are created, updated, and resolutiondate
        date_repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        comb_filtering_dict [dict<issue id, list<commit_hash>>] -- issue id to list of commit hashes. this pair satisfied the both conditions of pre and af.

        Returns
        return_dict [dict<issue id, list<commit_hash>>] -- issue id to list of commit hashes. this pair satisfied the both conditions of pre and af.
        """
        ISSUE_DATE_KEYWORD = time_filtering_obj.ISSUE_DATE_KEYWORD
        COMMIT_DATE_KEYWORD = time_filtering_obj.COMMIT_DATE_KEYWORD
        NAME_TYPE_REPO = self.name_type_repo

        return_dict = {}

        print("comb filtering execution")
        num_comb_filtering_dict = len(comb_filtering_dict)
        for idx_issue_id, issue_id in enumerate(comb_filtering_dict.keys()):

            if self.verbose>0:
                if (idx_issue_id%1000)==0:
                    print("Done -- comb filtering issue: {0}/{1}".format(idx_issue_id, num_comb_filtering_dict))

            if len(comb_filtering_dict[issue_id]) != 1:
                continue

            return_dict[issue_id] = comb_filtering_dict[issue_id]

        return return_dict


    def run(self, hash_list, issue_id_list, log_message_info_pickle_path, date_issue_dict):
        """
        Combine issue ids and commit hashes using shared files matching.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        log_messgae_info_pickle_path [string] -- path to log_message_info.pickle
        date_issue_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are ``created'', ``updated'', and ``resolutiondate''

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes modified the same files with the patches in issue id
        """

        # interlink condition
        # keyword_extraction_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes' log messages include issue ids
        # if keyword_extraction_flag==1, we remove the pairs that were detected by keyword_extraction results.
        if self.keyword_extraction_flag>0:
            if self.keyword_extraction_dict_path:
                keyword_extraction_dict = util.load_pickle(self.keyword_extraction_dict_path)
            else:
                ins = keyword_extraction.KeywordExtraction()
                keyword_extraction_dict = ins.run(hash_list, issue_id_list, log_message_info_pickle_path) # train data
                keyword_extraction_dict = generate_delete_data.main(keyword_extraction_dict, self.delete_rate)

            hash_list, issue_id_list = self.update_hash_issue_list_not_match(keyword_extraction_dict, hash_list, issue_id_list)

        # developer condition
        # dev_filtering_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes and this issue id are modified by the same author


        # time condition
        # time_filtering_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes modified the same files with the patches in issue id

        print("time filtering start...")
        time_filtering_obj = time_filtering.TimeFiltering(TIME_INTERVAL_AFTER=timedelta(minutes=self.time_interval_after), verbose=self.verbose)
        time_filtering_dict = time_filtering_obj.run(hash_list, issue_id_list, date_issue_dict, log_message_info_pickle_path)
        hash_list, issue_id_list = self.update_hash_issue_list_match(time_filtering_dict)


        comb_filtering_dict = time_filtering_dict


        """
        date_repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        """
        date_repo_dict = util.load_pickle(log_message_info_pickle_path)

        commit_filtering_dict = self.check_commit_condition(date_issue_dict, date_repo_dict, comb_filtering_dict, time_filtering_obj)


        # Reopen condition
        """
        [WIP] WE NEED REOPEN CONDITION HERE
        """
        issue2hash_dict = commit_filtering_dict # need to update
        """
        HERE
        """


        return issue2hash_dict




if __name__=="__main__":

    """
    ANSWER:
    HADOOP-5213 (May. 1 resolved) -- cf2fd0bad1750400d9a654d9f53450c7900062e9, 5011f075a6c8fcbfaf21e21f183dd693eddfde79, a20c705c8ee8bf2cb00504e4eb09a07dc17470e7
    HADOOP-4840 (Dec. 19 resolved) -- f3f6ca7d8ce34c20ed6ae311b113cb4c35be7beb, 9d7dfd4fe01b3a5735da7dd80c08aaa98039e953, 6960cbca35264c7a2240b70e225b9b2f70f11605, f59975a1a5df6576b2ed0c7a30ee039ee29d7054
    HADOOP-4854 (Dec. 23 resolved) -- 0bedee128820c09ed60a07fd4ee11ad39e22e76a, f76750a2af7107c6636c3f966a471765d2cb0e42
    HADOOP-5179 (Jul. 21 (2014) resolved) -- None in this hash list
    HADOOP-5198 (Mar. 31 resolved) -- None in this hash list
    HADOOP-1367 (Jun. 27 (2007)) -- None in this hash list. but same author with ec9f534c0b8ff248902c43fca58b13062e4e5d63
    HADOOP-1504 (Jun. 20 (2007)) -- None in this hash list but same author with 10dcb92a40671924811125712a6b3e1115fa9e32
    HADOOP-2246 -- None in this hash list but same author with 6e03553e19d61f296f11c9a17539408d34a3526e and if we use TIME_INTERVAL_AFTER=2 in time_filtering.py, we would get the result in commit_filtering_dict

    no tag name -- 412035b47a1b0116cb53ce612a61cd087d5edc41 (Dec. 20), 705b172b95db345a99adf088fca83c67bd13a691 (Dec. 6)
    no associated issue id in this example: ec9f534c0b8ff248902c43fca58b13062e4e5d63 (Feb. 12, 2011), 10dcb92a40671924811125712a6b3e1115fa9e32 (Jun 20)
    """
    hash_list = ['cf2fd0bad1750400d9a654d9f53450c7900062e9', '5011f075a6c8fcbfaf21e21f183dd693eddfde79', 'a20c705c8ee8bf2cb00504e4eb09a07dc17470e7', '412035b47a1b0116cb53ce612a61cd087d5edc41', '705b172b95db345a99adf088fca83c67bd13a691', 'f3f6ca7d8ce34c20ed6ae311b113cb4c35be7beb', '9d7dfd4fe01b3a5735da7dd80c08aaa98039e953', '6960cbca35264c7a2240b70e225b9b2f70f11605', 'f59975a1a5df6576b2ed0c7a30ee039ee29d7054', '0bedee128820c09ed60a07fd4ee11ad39e22e76a', 'f76750a2af7107c6636c3f966a471765d2cb0e42', 'ec9f534c0b8ff248902c43fca58b13062e4e5d63', '10dcb92a40671924811125712a6b3e1115fa9e32', '6e03553e19d61f296f11c9a17539408d34a3526e'] 
    issue_id_list = ['HADOOP-5213', 'HADOOP-4840', 'HADOOP-4854', 'HADOOP-5179', 'HADOOP-5198', 'HADOOP-1367', 'HADOOP-1504', 'HADOOP-2246']
    #print(run("hadoop", hash_list, issue_id_list))

    #loner_obj = Loner(keyword_extraction_flag=1)
    loner_obj = Loner()

    print(loner_obj.run("hadoop", hash_list, issue_id_list))

    loner_obj = Loner()

    print(loner_obj.run("hadoop", hash_list, issue_id_list))
