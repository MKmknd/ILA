from Utils import util


class KeywordExtraction:
    def __init__(self, hash_list, issue_id_list, log_message_info_pickle_path):
        """
        Combine issue ids and commit hashes using issue id matching.
        Here we use matching from a Git repository to a issue tracking system (combine_issue2hash)

        WIP: In the future, we also need to implement issue id matching
        from a issue tracking system to a Git repository. Please check
        WIP: here in the combine_issue2hash function.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        log_messgae_info_pickle_path [string] -- path to log_message_info.pickle
        """

        self.hash_list = hash_list
        self.issue_id_list = issue_id_list
        self.log_message_info_pickle_path = log_message_info_pickle_path

    def combine_issue2hash(self, repo_dict, hash_list, issue_id_set):
        """
        Arguments:
        repo_dict [dict<commit, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_set [set<issue id>] -- studied issue id set

        Returns:
        return_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes fix the issue
        """

        return_dict = {}
        for commit_hash in hash_list:
            for issue_id in repo_dict[commit_hash]['issue_id']:
                if not issue_id in issue_id_set:
                    continue

                if not issue_id in return_dict:
                    return_dict[issue_id] = []

                return_dict[issue_id].append(commit_hash)

        """
        WIP: here
        """

        return return_dict



    def run(self):
        """
        The main script of this class.

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes include issue id in their log message
        """

        """
        repo_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        """
        repo_dict = util.load_pickle(self.log_message_info_pickle_path)

        issue2hash_dict = self.combine_issue2hash(repo_dict, self.hash_list, set(self.issue_id_list))

        return issue2hash_dict




if __name__=="__main__":

    from Utils import git_reader
    from Utils import issue_db_reader

    repodir = "./../repository/avro"
    db_path = "./../tests/test_data/exp15/avro_issue_field_data.db"
    hash_list = git_reader.get_all_hash_without_merge(repodir)
    issue_id_list = issue_db_reader.read_issue_id_list(db_path)
    ins = KeywordExtraction(hash_list, issue_id_list, "./../preprocess/data_AVRO/avro_log_message_info.pickle")
    data = ins.run()
    print(data)



