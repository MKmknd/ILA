import re
from datetime import datetime, timedelta
import sqlite3
import sys

from Utils import util
from Utils import git_reader


class TimeFiltering:
    def __init__(self, TIME_INTERVAL_BEFORE=timedelta(days=0), TIME_INTERVAL_AFTER=timedelta(minutes=10), ISSUE_DATE_KEYWORD="resolutiondate", COMMIT_DATE_KEYWORD="commit_date", verbose=0):
        # how many days do we consider before or after the resolution date (days)
        self.TIME_INTERVAL_BEFORE = TIME_INTERVAL_BEFORE
        self.TIME_INTERVAL_AFTER = TIME_INTERVAL_AFTER

        self.ISSUE_DATE_KEYWORD = ISSUE_DATE_KEYWORD
        self.COMMIT_DATE_KEYWORD = COMMIT_DATE_KEYWORD

        self.verbose = verbose

    def _display_params(self):
        print(self.TIME_INTERVAL_BEFORE)
        print(self.TIME_INTERVAL_AFTER)
        print(self.ISSUE_DATE_KEYWORD)
        print(self.COMMIT_DATE_KEYWORD)


    def compare_date(self, date_issue_dict, date_repo_dict, hash_list, issue_id_list):
        """
        Compare the resolution date of a issue with all commit dates.
        If the diff is less than the thresholds (self.TIME_INTERVAL_AFTER and self.TIME_INTERVAL_BEFORE),
        we identify this is a pair

        Arguments:
        date_issue_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are created, updated, and resolutiondate
        date_repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        return_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes modified the same files with the patches in issue id
        """

        num_issue_id = len(issue_id_list)
        return_dict = {}
        for idx_issue_id, issue_id in enumerate(issue_id_list):
            if self.verbose>0:
                if idx_issue_id%1000==0:
                    print("Done issue: {0}/{1}".format(idx_issue_id, num_issue_id))
            for commit_hash in hash_list:

                if date_issue_dict[issue_id][self.ISSUE_DATE_KEYWORD] <= (date_repo_dict[commit_hash][self.COMMIT_DATE_KEYWORD] + self.TIME_INTERVAL_AFTER) and date_issue_dict[issue_id][self.ISSUE_DATE_KEYWORD] >= (date_repo_dict[commit_hash][self.COMMIT_DATE_KEYWORD] - self.TIME_INTERVAL_BEFORE):
                    if not issue_id in return_dict:
                        return_dict[issue_id] = []
                    return_dict[issue_id].append(commit_hash)

        return return_dict

    def run(self, hash_list, issue_id_list, date_issue_dict, log_message_info_pickle_path):
        """
        Combine issue ids and commit hashes using shared files matching.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        date_issue_dict [dict<issue id, dict<date keyword, date (datetime object)>>] -- extract date for each date keyword for each issue. date keywords are ``created'', ``updated'', and ``resolutiondate''
        log_messgae_info_pickle_path [string] -- path to log_message_info.pickle

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes modified the same files with the patches in issue id
        """

        """
        date_repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        """
        date_repo_dict = util.load_pickle(log_message_info_pickle_path) #


        issue2hash_dict = self.compare_date(date_issue_dict, date_repo_dict, hash_list, issue_id_list)
        return issue2hash_dict




if __name__=="__main__":
    pass

