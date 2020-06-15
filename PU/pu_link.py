import sqlite3

import numpy as np
import scipy

import os
import sys

from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from Utils import generate_blind_data
from Utils import git_reader
from Utils import util

from PU import PUModel
from MT import nsd_similarity
from TF import time_filtering
from KE import keyword_extraction
from TS import ntext_similarity


class PULink:
    def __init__(self, repo_dir, db_path, ISSUE_DATE_KEYWORD="resolutiondate", COMMIT_DATE_KEYWORD="commit_date", NAME_TYPE_REPO="committer", CANDIDATE_TIME_FILTER_BEFORE=timedelta(days=7), CANDIDATE_TIME_FILTER_AFTER=timedelta(days=7), execute_flag_ntext=0, max_iteration=25, random_state=None, verbose=0, keyword_extraction_dict_path=None, blind_rate=None):
        """
        ISSUE_DATE_KEYWORD [string] -- select the date for each issue for the time filtering. the default is resolution date
        COMMIT_DATE_KEYWORD [string] -- select the date for each commit for the time filtering. the default is commit date
        NAME_TYPE_REPO [string] -- select the developer type for each commit for the developer filtering. the default is committer
        CANDIDATE_TIME_FILTER_BEFORE [time delta object] -- To reduce the data size, we decide the time interval for the candidates links (if we consider all links, the memory size would be gigantic)
        CANDIDATE_TIME_FILTER_AFTER [time delta object] -- To reduce the data size, we decide the time interval for the candidates links (if we consider all links, the memory size would be gigantic)
        execute_flag_ntext [int] -- if it is 0, we don't reexecute the ntext filtering and use the pickle file. if it is not 0, we reexecute the ntext filtering
        verbose [int] -- verbose parameter
        max_iteration [int] -- number of iterations for extractiong ntext features
        random_state [int] -- random state
        """
        self.repo_dir = repo_dir
        self.db_path = db_path

        self.ISSUE_DATE_KEYWORD = ISSUE_DATE_KEYWORD
        self.COMMIT_DATE_KEYWORD = COMMIT_DATE_KEYWORD
        self.NAME_TYPE_REPO = NAME_TYPE_REPO
        self.CANDIDATE_TIME_FILTER_BEFORE = CANDIDATE_TIME_FILTER_BEFORE
        self.CANDIDATE_TIME_FILTER_AFTER = CANDIDATE_TIME_FILTER_AFTER

        self.execute_flag_ntext = execute_flag_ntext

        self.verbose = verbose
        self.max_iteration = max_iteration
        self.random_state = random_state

        self.keyword_extraction_dict_path=keyword_extraction_dict_path
        self.blind_rate = blind_rate

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


    def extract_commit_modified_file_features(self, hash_list):
        """
        Extract the proportion of source code and number of modified source code files
        for each commit hash

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list

        Returns:
        pro_modified_file_dict [dict<commit hash, % of source files>] -- proportion of modified source files in this commit
        num_modified_file_dict [dict<commit hash, # of source files>] -- number of modified source files in this commit
        """

        # modified_file_repo_dict [dict<commit hash, list<modified files>>] -- modified files list for each commit hash
        modified_file_repo_dict = self.extract_modified_file_repo(hash_list)

        pro_modified_file_dict = {}
        num_modified_file_dict = {}

        nsd_similarity_obj = nsd_similarity.NSDSimilarity(repodir=self.repo_dir)
        extension_set = nsd_similarity_obj.extension_set

        if self.verbose > 0:
            len_commit_hash = len(modified_file_repo_dict)

        for idx_commit_hash, commit_hash in enumerate(modified_file_repo_dict.keys()):

            if self.verbose > 0:
                if (idx_commit_hash%1000)==0:
                    print("modified file feature -- Done {0}/{1}".format(idx_commit_hash, len_commit_hash))

            cnt = 0
            for f_path in modified_file_repo_dict[commit_hash]:
                root, ext = os.path.splitext(f_path)
                if ext in extension_set:
                    cnt += 1

            len_modified_file_repo_dict = len(modified_file_repo_dict[commit_hash])
            if len_modified_file_repo_dict==0:
                pro_modified_file_dict[commit_hash] = 0
            else:
                pro_modified_file_dict[commit_hash] = cnt/len_modified_file_repo_dict
            num_modified_file_dict[commit_hash] = cnt

        return pro_modified_file_dict, num_modified_file_dict

    def extract_datetime_from_string(self, target):
        return datetime.strptime(target, "%Y-%m-%dT%H:%M:%S.%f%z")


    def extract_dates(self, db_path):
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

            return_dict[row[0]] = {'created': self.extract_datetime_from_string(row[1]),
                                   'updated': self.extract_datetime_from_string(row[2]),
                                   'resolutiondate': self.extract_datetime_from_string(row[3])}
        cur.close()
        conn.close()


        return return_dict

    def extract_time_features(self, hash_list, issue_id_list, log_message_info_path):
        """
        Return absolute time difference between a commit and an issue

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        time_diff_dict [dict<issue id, dict<commit hash, time diff>>] -- time difference between an issue and a commit
        time_diff_type_dict [dict<issue id, dict<commit hash, time diff type>>] -- type diff type (if the issue is later (bigger) than the commit, let it be 0 (correct). Otherwise, it would be 1 (wrong))
        """

        time_filtering_obj = time_filtering.TimeFiltering(ISSUE_DATE_KEYWORD=self.ISSUE_DATE_KEYWORD, COMMIT_DATE_KEYWORD=self.COMMIT_DATE_KEYWORD)
        # date_issue_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are created, updated, and resolutiondate
        date_issue_dict = self.extract_dates(self.db_path)

        # repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        date_repo_dict = util.load_pickle(log_message_info_path) #

        if self.verbose > 0:
            len_issue_id = len(issue_id_list)

        time_diff_dict = {}
        time_diff_type_dict = {}
        candidate_issue2hash_dict = {}
        ISSUE_DATE_KEYWORD = time_filtering_obj.ISSUE_DATE_KEYWORD
        COMMIT_DATE_KEYWORD = time_filtering_obj.COMMIT_DATE_KEYWORD
        for idx_issue_id, issue_id in enumerate(issue_id_list):

            if self.verbose > 0:
                if (idx_issue_id%1000)==0:
                    print("time feature -- Done {0}/{1}".format(idx_issue_id, len_issue_id))

            time_diff_dict[issue_id] = {}
            time_diff_type_dict[issue_id] = {}
            for commit_hash in hash_list:

                candidate_flag = 0
                for issue_date_key in ['created', 'updated', 'resolutiondate']:
                    for commit_date_key in ['author_date', 'commit_date']:
                        if date_issue_dict[issue_id][issue_date_key] <= (date_repo_dict[commit_hash][commit_date_key] + self.CANDIDATE_TIME_FILTER_AFTER) and date_issue_dict[issue_id][issue_date_key] >= (date_repo_dict[commit_hash][commit_date_key] - self.CANDIDATE_TIME_FILTER_BEFORE):
                            candidate_flag = 1

                if candidate_flag==0:
                    continue
                
                if not issue_id in candidate_issue2hash_dict:
                    candidate_issue2hash_dict[issue_id] = set()
                candidate_issue2hash_dict[issue_id].add(commit_hash)

                if date_issue_dict[issue_id][ISSUE_DATE_KEYWORD] <= date_repo_dict[commit_hash][COMMIT_DATE_KEYWORD]:
                    time_diff_dict[issue_id][commit_hash] = (date_repo_dict[commit_hash][COMMIT_DATE_KEYWORD] - date_issue_dict[issue_id][ISSUE_DATE_KEYWORD]).total_seconds()
                    time_diff_type_dict[issue_id][commit_hash] = 0
                elif date_issue_dict[issue_id][ISSUE_DATE_KEYWORD] > date_repo_dict[commit_hash][COMMIT_DATE_KEYWORD]:
                    time_diff_dict[issue_id][commit_hash] = (date_issue_dict[issue_id][ISSUE_DATE_KEYWORD] - date_repo_dict[commit_hash][COMMIT_DATE_KEYWORD]).total_seconds()
                    time_diff_type_dict[issue_id][commit_hash] = 1
                else:
                    print("ERROR")
                    print(commit_hash)
                    print(issue_id)
                    sys.exit()

        return time_diff_dict, time_diff_type_dict, candidate_issue2hash_dict

    def extract_ntext_feature(self, hash_list, issue_id_list, candidate_issue2hash_dict, execute_flag,
                               log_message_without_issueid_path, dsc_issue_dict, comment_issue_dict,
                              output_dir):
        """
        Compute cosine similarity between the commit log message and
        the description + comments with the TFIDF vectorization.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        execute_flag [integer] -- if this value is not 0, we re-execute the developer filtering. if it is 0, we read the pickle file

        Returns:
        return_dict [dict<issue id, dict<commit hash, ntext similarity>>] -- cosine similarity between the commit log message in a repository
                                                                             and the description + comments in an issue
        """

        if execute_flag==0:

            return_dict = {}
            for num_ite in range(1, self.max_iteration+1):
                if self.verbose > 0:
                    print("ntext feature num ite: {0}/{1}".format(num_ite, self.max_iteration))

                temp_dict = util.load_pickle("{0}/cosine_similarity_dict_ite{1}.pickle".format(output_dir, num_ite))

                if self.verbose > 0:
                    len_issue_id = len(temp_dict)

                for idx_issue_id, issue_id in enumerate(temp_dict.keys()):

                    if self.verbose > 0:
                        if (idx_issue_id%100)==0:
                            print("ntext feature -- Done {0}/{1}".format(idx_issue_id, len_issue_id))

                    if not issue_id in candidate_issue2hash_dict:
                        continue

                    return_dict[issue_id] = {}
                    for commit_hash in candidate_issue2hash_dict[issue_id]:
                        return_dict[issue_id][commit_hash] = temp_dict[issue_id][commit_hash]
        else:
            ntext_similarity_obj = ntext_similarity.NtextSimilarity(verbose=self.verbose)

            # repo_dict [dict<commit hash, log message] -- log message for each commit
            log_msg_repo_dict = util.load_pickle(log_message_without_issueid_path) #

            corpus, processed_dsc_issue_dict, processed_comment_issue_dict, processed_log_msg_repo_dict = ntext_similarity_obj.make_corpus_and_input(dsc_issue_dict, comment_issue_dict, log_msg_repo_dict, hash_list, issue_id_list)
            vectorizer = TfidfVectorizer()
            vectorizer.fit(corpus)

            log_msg_vec_dict = {}
            for commit_hash in hash_list:
                log_msg_vec_dict[commit_hash] = vectorizer.transform([processed_log_msg_repo_dict[commit_hash]])

            if self.verbose > 0:
                len_issue_id = len(candidate_issue2hash_dict)

            return_dict = {}
            for idx_issue_id, issue_id in enumerate(candidate_issue2hash_dict.keys()):

                if self.verbose > 0:
                    if (idx_issue_id%100)==0:
                        print("ntext feature -- Done {0}/{1}".format(idx_issue_id, len_issue_id))

                return_dict[issue_id] = {}
                issue_text_vec = vectorizer.transform([processed_dsc_issue_dict[issue_id] + " " + processed_comment_issue_dict[issue_id]])
                for commit_hash in candidate_issue2hash_dict[issue_id]:
                    return_dict[issue_id][commit_hash] = cosine_similarity(issue_text_vec, log_msg_vec_dict[commit_hash])[0,0]

        return return_dict


    def extract_features(self, hash_list, issue_id_list, keyword_extraction_dict,
                         log_message_info_path, log_message_without_issueid_path,
                         dsc_issue_dict, comment_issue_dict, output_dir):
        """
        Arguments:
        p_name [string] -- project name string
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        keyword_extraction_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes include issue id in their log message

        Returns:
        data_array [np.array<np.array<features>>] -- features that were converted by z-score (standarlization)
        label_list [np.array<labels>] -- labels. If it has label, it would be 1; otherwise, it would be 0. 
                                         Nobody knows label=0 means no link.
        name_list [list<string>] -- corresponding issue id and commit hash
        """
        # extract commits' modified file features
        c_pro_modified_file_dict, c_num_modified_file_dict = self.extract_commit_modified_file_features(hash_list)

        # extract the interval between commits and issues
        ci_time_diff_dict, ci_time_diff_type_dict, candidate_issue2hash_dict = self.extract_time_features(hash_list, issue_id_list, log_message_info_path)

        # extract cosine similarity on natural language
        ci_ntext_dict = self.extract_ntext_feature(hash_list, issue_id_list, candidate_issue2hash_dict, self.execute_flag_ntext,
                                                    log_message_without_issueid_path, dsc_issue_dict, comment_issue_dict,
                                                   output_dir)


        keyword_extraction_set_dict = {}
        for issue_id in keyword_extraction_dict:
            keyword_extraction_set_dict[issue_id] = set()
            for commit_hash in keyword_extraction_dict[issue_id]:
                keyword_extraction_set_dict[issue_id].add(commit_hash)


        data_array = []
        data_array_binary = []
        label_list = []
        name_list = []
        for issue_id in candidate_issue2hash_dict.keys():
            for commit_hash in candidate_issue2hash_dict[issue_id]:
                name_list.append("{0}:{1}".format(issue_id, commit_hash))

                #temp = [c_pro_modified_file_dict[commit_hash], c_num_modified_file_dict[commit_hash],
                #        ci_time_diff_dict[issue_id][commit_hash], ci_time_diff_type_dict[issue_id][commit_hash],
                #        ci_dev_dict[issue_id][commit_hash], ci_ntext_dict[issue_id][commit_hash],
                #        ci_code_dict[issue_id][commit_hash], ci_diff_file_dict[issue_id][commit_hash]]
                temp = [c_pro_modified_file_dict[commit_hash], c_num_modified_file_dict[commit_hash],
                        ci_time_diff_dict[issue_id][commit_hash], ci_ntext_dict[issue_id][commit_hash]]

                temp_binary = [ci_time_diff_type_dict[issue_id][commit_hash]]

                data_array.append(temp)
                data_array_binary.append(temp_binary)

                if not issue_id in keyword_extraction_set_dict:
                    label_list.append(0)
                elif commit_hash in keyword_extraction_set_dict[issue_id]:
                    label_list.append(1)
                else:
                    label_list.append(0)

        print("sample size: {0:,}".format(len(label_list)))
        data_array = scipy.stats.zscore(np.array(data_array))
        data_array = np.concatenate([data_array, data_array_binary], 1)

        label_list = np.array(label_list)

        return data_array, label_list, name_list, candidate_issue2hash_dict

    def run(self, hash_list, issue_id_list, log_message_info_path,
            log_message_without_issueid_path, dsc_issue_dict, comment_issue_dict,
            output_dir):
        """
        Combine issue ids and commit hashes using shared files matching.
        Please check prefix of the variables:
        c_ - commit feature [dict<commit hash, feature>]
        i_ - issue feature [dict<issue id, feature>]
        ci_ - link features [dict<issue id, dict<commit hash, feature>>]

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        output_dir [string] -- path to the directory where the cosine similarity is stored that was computed by TS

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes modified the same files with the patches in issue id
        """

        # extract train data
        if self.keyword_extraction_dict_path:
            keyword_extraction_dict = util.load_pickle(self.keyword_extraction_dict_path)
        else:
            ins = keyword_extraction.KeywordExtraction()
            keyword_extraction_dict = ins.run(hash_list, issue_id_list, log_message_info_path) # train data
            keyword_extraction_dict = generate_blind_data.main(keyword_extraction_dict, self.blind_rate)


        data_array, label_list, name_list, candidate_issue2hash_dict = self.extract_features(hash_list, issue_id_list,
                                                                                             keyword_extraction_dict, log_message_info_path,
                                                                                             log_message_without_issueid_path,
                                                                                             dsc_issue_dict, comment_issue_dict,
                                                                                             output_dir)

        pu = PUModel.PUModel(random_state=self.random_state)
        pu.fit(data_array, label_list)
        prediction_result = pu.predict(data_array)

        issue2hash_dict = {}
        for issue_id in candidate_issue2hash_dict.keys():
            for commit_hash in candidate_issue2hash_dict[issue_id]:
                idx = name_list.index("{0}:{1}".format(issue_id, commit_hash))
                if prediction_result[idx]:
                    if not issue_id in issue2hash_dict:
                        issue2hash_dict[issue_id] = []
                    issue2hash_dict[issue_id].append(commit_hash)

        return issue2hash_dict

