import re
import sqlite3
import sys
import os

from Utils import git_reader

from TS import ntext_similarity


class NSDSimilarity:
    
    def __init__(self, repodir, extension_set=set([".md",".txt"]), THRESHOLD_COSINE_SIM=0.2, CONTEXT_LINE=3, verbose=0, parallel_iteration=0, output_dir_cosine_sim="./data"):

        self.repodir = repodir
        self.extension_set = extension_set
        self.THRESHOLD_COSINE_SIM = THRESHOLD_COSINE_SIM
        self.CONTEXT_LINE = CONTEXT_LINE
        self.verbose = verbose
        self.parallel_iteration = parallel_iteration
        self.output_dir_cosine_sim = output_dir_cosine_sim

    def compare_nsd(self, dsc_issue_dict, comment_issue_dict, nsd_dict, hash_list, issue_id_list, ntext_similarity_obj, target_issue_id_list):
        """
        Compare the description and comment in issue with changed source code in natural language at a commit.
        We identify this is a pair if they are similar

        Arguments:
        dsc_issue_dict [dict<issue id, description] -- description for each issue
        comment_issue_dict [dict<issue id, comments (a string)] -- a string of comments for each issue id
        nsd_dict [dict<commit hash, nsd text (a string)] -- all modified and context words of all modified nsds for each commit (not parsed yet)
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        return_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are the similar text
        """

        return_dict = ntext_similarity_obj.compare_ntext(dsc_issue_dict, comment_issue_dict,
                                                         nsd_dict, hash_list, issue_id_list,
                                                         target_issue_id_list,
                                                         self.output_dir_cosine_sim)

        return return_dict

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
            return_dict[commit_hash] = git_reader.get_all_modified_files(self.repodir, commit_hash)

        return return_dict

    def extract_diff_with_fpath(self, content):
        """
        Extract diff code from a git show output

        Arguments:
        content [string] -- a git show output

        Returns:
        diff_content_dict [dict<file path, the string of diff code>] -- extracted diff code from the git show output
        """
        #re_start_line = re.compile("^@@ [\s]-(\d+).+\+(\d+)")
        re_start_line = re.compile("^@@[\s]-(\d+).+\+(\d+),(\d+)\s@@")
        re_f_path_line = re.compile("^\+\+\+\s(b/)?(\S*)")
        re_deletedLine = re.compile("^-")
        re_addedLine = re.compile("^\+")
        diff_start = 0
        diff_content_dict = {}
        f_path = None
        for line in content.splitlines():
            match_f_path = re_f_path_line.match(line)
            if match_f_path:
                f_path = match_f_path.group(2)
                diff_content_dict[f_path] = ""

            match_start_line = re_start_line.match(line)
            if match_start_line and diff_start==0:
                remain_line = int(match_start_line.group(3))
                #print(remain_line)
                diff_start = 1
                sum_diff_line = 0
                continue

            if diff_start==1:
                sum_diff_line += 1
                if re_deletedLine.match(line):
                    sum_diff_line -= 1
                elif re_addedLine.match(line):
                    #print("test")
                    diff_content_dict[f_path] += " " + line[1:] + "\n"
                else:
                    diff_content_dict[f_path] += line + "\n"

                if sum_diff_line==remain_line:
                    diff_start=0

        return diff_content_dict

    def extract_nsd_text(self, hash_list, context):
        """
        Extract all modified and context tokens for each commit hash

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        context [integer] -- context line for the git show command

        Returns:
        nsd_dict [dict<commit_hash, tokens as a string>] -- modified and context tokens of all the modified text files in this modification.
        """

        """
        modified_file_repo_dict [dict<commit hash, list<modified files>>] -- modified files list for each commit hash
        """
        modified_file_repo_dict = self.extract_modified_file_repo(hash_list)

        nsd_dict = {}
        error_information = {}
        rename_information = {}
        len_hash_list = len(hash_list)
        if self.verbose>0:
            print("start extract nsd text")
        for idx_commit_hash, commit_hash in enumerate(hash_list):

            if self.verbose>0:
                if (idx_commit_hash%100)==0:
                    print("Done commit hash: {0}/{1}".format(idx_commit_hash, len_hash_list))

            nsd_dict[commit_hash] = ""
            content = git_reader.git_show_with_context(self.repodir, commit_hash, context)
            diff_content_dict = self.extract_diff_with_fpath(content)

            for f_path in modified_file_repo_dict[commit_hash]:
                root, ext = os.path.splitext(f_path)
                if ext in self.extension_set:

                    if not f_path in diff_content_dict:
                        print("f_path error in :{0}:{1}".format(commit_hash, f_path))
                        if not commit_hash in error_information:
                            error_information[commit_hash] = []
                        error_information[commit_hash].append(f_path)
                        f_path = f_path.split()[0]

                    if not f_path in diff_content_dict:
                        print("f_path rename in :{0}:{1}".format(commit_hash, f_path))
                        if not commit_hash in rename_information:
                            rename_information[commit_hash] = []
                        rename_information[commit_hash].append(f_path)
                        continue

                    nsd_dict[commit_hash] += diff_content_dict[f_path]


        #if len(error_information) > 0:
        #    util.dump_pickle("./error/{0}_file_path_error_ite{1}.pickle".format(self.p_name, self.parallel_iteration), error_information)
        #if len(rename_information) > 0:
        #    util.dump_pickle("./error/{0}_file_path_rename_ite{1}.pickle".format(self.p_name, self.parallel_iteration), rename_information)


        return nsd_dict

    def run(self, hash_list, issue_id_list, target_issue_id_list,
            dsc_issue_dict, comment_issue_dict):
        """
        Combine issue ids and commit hashes using shared files matching.

        Arguments:
        p_name [string] -- project name string
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        target_issue_id_list [list<issue id>] -- studied issue id list for parallel execution

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are the similar natural language with that issue
        """

        ntext_similarity_obj = ntext_similarity.NtextSimilarity(THRESHOLD_COSINE_SIM=self.THRESHOLD_COSINE_SIM, verbose=self.verbose, parallel_iteration=self.parallel_iteration)

        nsd_dict = self.extract_nsd_text(hash_list, self.CONTEXT_LINE)

        issue2hash_dict = self.compare_nsd(dsc_issue_dict, comment_issue_dict, nsd_dict, hash_list, issue_id_list, ntext_similarity_obj, target_issue_id_list)
        return issue2hash_dict




