from TS import ntext_similarity


class Comment:

    def __init__(self, THRESHOLD_COSINE_SIM=0.4, verbose=0, parallel_iteration=0, p_name=None):
        """
        Arguments:
        THRESHOLD_COSINE_SIM [float] -- cosine similarity threshold for ntext_similarity.py (NtextSimilarity)
        verbose [int] -- verbose parameter
        parallel_iteration [int] -- parallel iteration indicator
        """
        self.THRESHOLD_COSINE_SIM = THRESHOLD_COSINE_SIM # NEED TO OPTIMIZE
        self.verbose = verbose
        self.parallel_iteration = parallel_iteration
        self.p_name = p_name




    def compare_comment_dsc(self, dsc_issue_dict, comment_issue_dict, repo_javadoc_dict, hash_list, issue_id_list, ntext_similarity_obj, target_issue_id_list, output_dir):
        """
        Extract the relationship between commit hash and issue id

        Arguments:
        dsc_issue_dict [dict<issue id, description] -- description for each issue
        comment_issue_dict [dict<issue id, comments (a string)] -- a string of comments for each issue id
        repo_javadoc_dict [dict<commit_hash, javadocs (a string)>] -- all javadocs that were extracted
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are the same name with the issue 
        """
        
        issue2hash_dict = ntext_similarity_obj.compare_ntext(dsc_issue_dict, comment_issue_dict, repo_javadoc_dict, hash_list, issue_id_list, target_issue_id_list, output_dir)

        return issue2hash_dict


    def run(self, hash_list, issue_id_list, target_issue_id_list,
            dsc_issue_dict, comment_issue_dict, repo_javadoc_dict,
            output_dir):
        """
        Combine issue ids and commit hashes using word association.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        target_issue_id_list [list<issue id>] -- studied issue id list for parallel execution
        dsc_issue_dict [dict<issue id, description>] -- issue report description for each issue report
        comment_issue_dict [dict<issue id, comments (a string)>] -- a string of comments for each issue id
        repo_javadoc_dict [dict<commit_hash, javadocs (a string)>] -- all javadocs that were extracted

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are the similar wording with word association
        """


        """
        dsc_issue_dict [dict<issue id, description>] -- description for each issue id
        comment_issue_dict [dict<issue id, comments (a string)>] -- a string of comments for each issue id
        # dsc_com_content_dict [dict<issue id, words>] -- words in the parsed description and comments
        """
        ntext_similarity_obj = ntext_similarity.NtextSimilarity(THRESHOLD_COSINE_SIM=self.THRESHOLD_COSINE_SIM, verbose=self.verbose, parallel_iteration=self.parallel_iteration)




        print("comparison start")
        issue2hash_dict = self.compare_comment_dsc(dsc_issue_dict, comment_issue_dict, repo_javadoc_dict, hash_list, issue_id_list, ntext_similarity_obj, target_issue_id_list, output_dir)
        return issue2hash_dict




if __name__=="__main__":

    """
    ANSWER:
    HADOOP-5213 (May. 1 resolved) -- cf2fd0bad1750400d9a654d9f53450c7900062e9, 5011f075a6c8fcbfaf21e21f183dd693eddfde79, a20c705c8ee8bf2cb00504e4eb09a07dc17470e7
    HADOOP-4840 (Dec. 19 resolved) -- f3f6ca7d8ce34c20ed6ae311b113cb4c35be7beb, 9d7dfd4fe01b3a5735da7dd80c08aaa98039e953, 6960cbca35264c7a2240b70e225b9b2f70f11605, f59975a1a5df6576b2ed0c7a30ee039ee29d7054
    HADOOP-4854 (Dec. 23 resolved) -- 0bedee128820c09ed60a07fd4ee11ad39e22e76a, f76750a2af7107c6636c3f966a471765d2cb0e42

    no tag name -- 412035b47a1b0116cb53ce612a61cd087d5edc41 (Dec. 20), 705b172b95db345a99adf088fca83c67bd13a691 (Dec. 6)
    """
    hash_list = ['cf2fd0bad1750400d9a654d9f53450c7900062e9', '5011f075a6c8fcbfaf21e21f183dd693eddfde79', 'a20c705c8ee8bf2cb00504e4eb09a07dc17470e7', '412035b47a1b0116cb53ce612a61cd087d5edc41', '705b172b95db345a99adf088fca83c67bd13a691', 'f3f6ca7d8ce34c20ed6ae311b113cb4c35be7beb', '9d7dfd4fe01b3a5735da7dd80c08aaa98039e953', '6960cbca35264c7a2240b70e225b9b2f70f11605', 'f59975a1a5df6576b2ed0c7a30ee039ee29d7054', '0bedee128820c09ed60a07fd4ee11ad39e22e76a', 'f76750a2af7107c6636c3f966a471765d2cb0e42'] 
    issue_id_list = ['HADOOP-5213', 'HADOOP-4840', 'HADOOP-4854']
    target_issue_id_list = ['HADOOP-5213', 'HADOOP-4840', 'HADOOP-4854']
    #print(run("hadoop", hash_list, issue_id_list))

    comment_obj = Comment()
    print(comment_obj.run("hadoop", hash_list, issue_id_list, target_issue_id_list))
