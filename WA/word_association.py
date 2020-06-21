import re
import sys


from Utils import util
from Utils import generate_delete_data

from KE import keyword_extraction


class WordAssociation:

    # the default value of ASSOC_THRESHOLD: refer to Figure 10 in Section 8.2.1 in nguyen2012FSE
    def __init__(self, extension_set=set([".java"]), ASSOC_THRESHOLD=0.5, verbose=0, max_iteration=25,
                 keyword_extraction_dict_path=None, delete_rate=0):
        """
        Arguments:
        extension_set [set<string>] -- extensions' set that would be analyzed
        ASSOC_THRESHOLD [int] -- the threshold for association
        delete_rate [int] -- percentage of delete rate (e.g., 50% delete rate: 50)
        """
        self.extension_set = extension_set
        self.ASSOC_THRESHOLD = ASSOC_THRESHOLD
        self.verbose = verbose
        self.max_iteration = max_iteration
        self.keyword_extraction_dict_path=keyword_extraction_dict_path
        self.delete_rate = delete_rate
        #self.tmp_prefix = tmp_prefix
        #self.parallel_iteration = parallel_iteration


    def compute_mu_ew(self, var_n_we, var_n_w, var_n_e):
        """
        Compute the formula in (1) in Nguyen et al. FSE2012.

        Arguments:
        var_n_we [dict<word_issue, dict<file path, number of commits>>] -- n_{w,e} in page 6 in Nguyen et al., FSE2012. w indicates a word; e indicates a file. n_{w,e} indicates the number of commits, which modified the file e for the issues that include the word w.
        var_n_w = {} [dict<word_issue, number of issues>] -- number of issues that include the word w
        var_n_e = {} [dict<file path, number of commits>] -- number of commits that modify the file

        Returns:
        var_mu_ew [dict<file path, dict<word_issue, Mu_{e}(w)>>] -- the value of formula (1) in the paper. 
        """
        var_mu_ew = {}

        for f_path in var_n_e.keys():
            var_mu_ew[f_path] = {}
            for word_issue in var_n_w.keys():
                var_mu_ew[f_path][word_issue] = 0
                if not f_path in var_n_we[word_issue]:
                    continue
                var_mu_ew[f_path][word_issue] = var_n_we[word_issue][f_path]/(1+min(var_n_w[word_issue], var_n_e[f_path]))

        return var_mu_ew

    def compute_mu_eB(self, var_mu_ew, dsc_com_content_dict):
        """
        Compute the formula in (2) in Nguyen et al. FSE2012.

        Arguments:
        var_mu_ew [dict<file path, dict<word_issue, Mu_{e}(w)>>] -- the value of formula (1) in the paper. 
        dsc_com_content_dict [dict<issue id,  set<words in the description and comments> -- words in the description and comments for each issue id

        Returns:
        var_mu_eB [dict<file path, dict<issue id, Mu_{e}(B)>>] -- the value of formula (2) in the paper
        """
        var_mu_eB = {}

        for f_path in var_mu_ew.keys():
            var_mu_eB[f_path] = {}
            for issue_id in dsc_com_content_dict.keys():
                var_mu_eB[f_path][issue_id] = 0
                temp_set = set([0])
                for word_issue in dsc_com_content_dict[issue_id]:
                    temp_set.add(var_mu_ew[f_path][word_issue])

                var_mu_eB[f_path][issue_id] = max(temp_set)

        return var_mu_eB

    def compute_mu_CB(self, var_mu_eB, word_repo_commit_dict, dsc_com_content_dict):
        """
        Compute the formula in (3) in Nguyen et al. FSE2012.

        Arguments:
        var_mu_eB [dict<file path, dict<issue id, Mu_{e}(B)>>] -- the value of formula (2) in the paper
        word_repo_commit_dict [dict<commit hash, dict<file path, set<words in the file content>>>] -- words for each file for each commit hash
        dsc_com_content_dict [dict<issue id,  set<words in the description and comments> -- words in the description and comments for each issue id

        Returns:
        var_mu_CB [dict<commit hash, dict<issue id, Mu_{C}(B)>>] -- the value of formula (3) in the paper
        """

        var_mu_CB = {}
        for commit_hash in word_repo_commit_dict.keys():
            var_mu_CB[commit_hash] = {}
            for issue_id in dsc_com_content_dict.keys():
                var_mu_CB[commit_hash][issue_id] = 0
                temp_set = set([0])
                for f_path in word_repo_commit_dict[commit_hash].keys():
                    if not f_path in var_mu_eB: # here, we ignore some file pathes that were not included in the commits that involve with issue ids
                        continue
                    temp_set.add(var_mu_eB[f_path][issue_id])

                var_mu_CB[commit_hash][issue_id] = max(temp_set)

        return var_mu_CB

    def train_association_model(self, keyword_extraction_dict, modified_file_content_repo_dict, dsc_com_content_dict, issue_id_list):
        """
        Arguments:
        keyword_extraction_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes' log messages include issue ids
        modified_file_content_repo_dict [dict<commit hash, dict<file path, set<words in the file content>>>] -- words for each file for each commit hash
        dsc_com_content_dict [dict<issue id,  set<words in the description and comments> -- words in the description and comments for each issue id
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        var_mu_CB [dict<commit hash, dict<issue id, Mu_{C}(B)>>] -- the value of formula (3) in the paper

        Note:
        Please check the following words in the comments
        word(s)_repo -- word(s) in the modified files for each commit hash
        word(s)_issue -- word(s) at an issue
        """
        
        word_issue_id_dict = {} # key: word_issue, value: set of issue ids which include this word_issue
        word_repo_commit_dict = modified_file_content_repo_dict # key: commit hash, value: dict <key: file path, value: set of word_repo>
        # preparing data for n_we
        for issue_id in issue_id_list:
            for word_issue in dsc_com_content_dict[issue_id]:
                if not word_issue in word_issue_id_dict:
                    word_issue_id_dict[word_issue] = set()
                word_issue_id_dict[word_issue].add(issue_id)


        if self.verbose > 0:
            num_word_issue_id = len(word_issue_id_dict)
        
        var_n_we = {} # n_{w,e} in page 6 in Nguyen et al., FSE2012. w indicates a word; e indicates a file. n_{w,e} indicates the number of commits, which modified the file e for the issues that include the word w. (dict<word_issue, dict<file path, number of commits>>
        var_n_w = {} # n_{w} indicates the number of issues that include the word w. key - a word_issue, value - the number of issues which include this word_issue
        var_n_e = {} # n_{e}
        for idx_word_issue, word_issue in enumerate(word_issue_id_dict.keys()):
            if self.verbose > 0:
                if idx_word_issue%100==0:
                    print("Done word issue id: {0}/{1}".format(idx_word_issue, num_word_issue_id))

            if not word_issue in var_n_we:
                var_n_we[word_issue] = {}
                var_n_w[word_issue] = len(word_issue_id_dict[word_issue])
            for issue_id in word_issue_id_dict[word_issue]:
                if not issue_id in keyword_extraction_dict:
                    continue
                for commit_hash in keyword_extraction_dict[issue_id]:
                    for f_path in word_repo_commit_dict[commit_hash]:
                        if not f_path in var_n_we[word_issue]:
                            var_n_we[word_issue][f_path] = 0
                        var_n_we[word_issue][f_path] += 1

                        if not f_path in var_n_e:
                            var_n_e[f_path] = 0
                        var_n_e[f_path] += 1

        var_mu_ew = self.compute_mu_ew(var_n_we, var_n_w, var_n_e)

        # after here, we should use the test version of dsc_com_content_dict
        var_mu_eB = self.compute_mu_eB(var_mu_ew, dsc_com_content_dict)
        var_mu_CB = self.compute_mu_CB(var_mu_eB, word_repo_commit_dict, dsc_com_content_dict)

        return var_mu_CB

    def compare_association(self,
                            hash_list, issue_id_list, log_message_info_pickle_path,
                            lscp_processed_data_pickle_path, output_dir):
        """
        Compare the description and comment in issue with log message at a commit.
        We identify this is a pair if they are similar

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        log_messgae_info_pickle_path [string] -- path to log_message_info.pickle
        lscp_processed_data_pickle_path [string] -- path the directory where we can see the data that was processed by lscp
        output_dir [string] -- output directory to store the values

        Returns:
        return_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes have the association values over a certain threshold
        """

        # keyword_extraction_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes' log messages include issue ids

        if self.keyword_extraction_dict_path:
            keyword_extraction_dict = util.load_pickle(self.keyword_extraction_dict_path)
        else:
            ins = keyword_extraction.KeywordExtraction()
            keyword_extraction_dict = ins.run(hash_list, issue_id_list, log_message_info_pickle_path)
            keyword_extraction_dict = generate_delete_data.main(keyword_extraction_dict, self.delete_rate)

        # extract words for each file for each commit hash (dict<commit hash, dict<file path, set<words in the file content>>>)

        print("read modified file content ... ")
        modified_file_content_repo_dict = {}
        for num_ite in range(1, self.max_iteration+1):
            if self.verbose > 0:
                print("num ite: {0}/{1}".format(num_ite, self.max_iteration))
            temp_dict = util.load_pickle("{0}/modified_file_content_repo_dict_ite{1}.pickle".format(
                lscp_processed_data_pickle_path, num_ite))

            for commit_hash in temp_dict.keys():
                if commit_hash in modified_file_content_repo_dict:
                    print("SOMETHIN HAPPEND")
                    sys.exit()
                modified_file_content_repo_dict[commit_hash] = temp_dict[commit_hash]



        # key: issue id, value: words in the parsed diff code in attached files by lscp
        dsc_com_content_dict = {}
        if self.verbose > 0:
            print("lscp processing ...")
            len_issue_id_list = len(issue_id_list)
        for idx_issue_id, issue_id in enumerate(issue_id_list):
            if self.verbose > 0:
                if idx_issue_id%1000==0:
                    print("Done issue id: {0}/{1}".format(idx_issue_id, len_issue_id_list))

            content = util.load_pickle("{0}/{1}_dsc_comment_string.pickle".format(
                lscp_processed_data_pickle_path, issue_id))
            dsc_com_content_dict[issue_id] = set(content.split())

        if self.verbose > 0:
            print("train association model ...")
        var_mu_CB = self.train_association_model(keyword_extraction_dict, modified_file_content_repo_dict, dsc_com_content_dict, issue_id_list)
        if self.delete_rate:
            util.dump_pickle("{0}/{1}_var_mu_CB.pickle".format(output_dir, self.delete_rate), var_mu_CB)
        else:
            util.dump_pickle("{0}/var_mu_CB.pickle".format(output_dir), var_mu_CB)

        return_dict = {}
        for issue_id in issue_id_list:
            for commit_hash in modified_file_content_repo_dict.keys():
                if var_mu_CB[commit_hash][issue_id]>=self.ASSOC_THRESHOLD:
                    if not issue_id in return_dict:
                        return_dict[issue_id] = []
                    return_dict[issue_id].append(commit_hash)

        return return_dict


    def run(self, hash_list, issue_id_list, log_message_info_pickle_path,
            lscp_processed_data_pickle_path, output_dir):
        """
        Combine issue ids and commit hashes using word association.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        log_messgae_info_pickle_path [string] -- path to log_message_info.pickle
        lscp_processed_data_pickle_path [string] -- path the directory where we can see the data that was processed by lscp
        output_dir [string] -- output directory to store the values

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are the similar wording with word association
        """

        issue2hash_dict = self.compare_association(hash_list, issue_id_list,
                                                   log_message_info_pickle_path,
                                                   lscp_processed_data_pickle_path,
                                                   output_dir)
        return issue2hash_dict




