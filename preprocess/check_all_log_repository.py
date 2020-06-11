import re
from datetime import datetime
from collections import Counter

import sys
sys.path.append("./../Utils")
import util
import git_reader

#project_name_list = ["hadoop"]
#project_name_list = ["commons-lang", "commons-math"]
#project_name_list = ["avro"]
#project_name_list = ["zookeeper"]
#project_name_list = ["tez"]
#project_name_dict_for_issue_display = {"hadoop": "HADOOP", "commons-lang":"LANG", "commons-math":"MATH", "avro": "AVRO", "zookeeper": "ZOOKEEPER", "tez": "TEZ"}


class ExtractCommitMessage:
    def __init__(self, repo_dir=None, p_name=None, apache_issue_id_prefix=None, output_dir=None, verbose=0):
        """
        repo_dir: [str] -- path to the target repository directory
        p_name: [str] -- project name
        apache_issue_id_prefix [str] -- apache's issue id. E.g., HADOOP. If no prefix, we use the upper project name
        output_dir [str] -- output the result in this directory
        verbose: [int] -- if it is not zero, this script shows the basict information

        OUTPUT:
        The results is outputted in output_dir as a pickle file
        ({{ output_dir }}/{{ apache_issue_id_prefix }}_log_message_info.pickle).
        This pickle file is a dictionary:
        dict<commit hash, dict<info name, info data>>

        info name can be found at initialize_dict
        """
        self.repo_dir = repo_dir
        self.p_name = p_name

        if apache_issue_id_prefix is None:
            self.apache_issue_id_prefix = p_name.upper()
        else:
            self.apache_issue_id_prefix = apache_issue_id_prefix

        if output_dir is None:
            self.output_dir = "./data_{0}".format(self.apache_issue_id_prefix)
        else:
            self.output_dir = output_dir

        self.verbose = verbose

        assert not self.repo_dir is None, "Need to give the repository path"
        assert not self.p_name is None, "Need to give the project name"

    def initialize_dict(self, dic):
        dic['issue_id'] = set()
        dic['author_date'] = None
        dic['commit_date'] = None

        #dic['author'] = {'name': None, 'email': None}
        #dic['committer'] = {'name': None, 'email': None}


    def match_basic_regexp(self, text, regexp):
        match = re.match(regexp, text)
        info = None
        if match:
            info = match.group(1)
        return info

    def match_issue_regexp(self, text, regexp_msg, regexp_issue):
        match_msg = re.match(regexp_msg, text)
        issue_ids=[]
        if match_msg:
            issue_ids = re.findall(regexp_issue, match_msg.group(1))
            #if len(issue_ids)==0:
            #    issue_ids=[]

        return issue_ids

    def extract_datetime_from_string(self, target):
        return datetime.strptime(target, "%a %b %d %H:%M:%S %Y %z")

    def insert_basicdate_info(self, text, regexp, dic, key):
        data = self.match_basic_regexp(text, regexp)
        if data:
            dic[key] = self.extract_datetime_from_string(data)

    #def extract_author_from_string(self, target):
    #    re_str = "^(.*) <(.*)>$"
    #    author_info = re.search(re_str, target)
    #    if author_info:
    #        return author_info.group(1), author_info.group(2)
    #    else:
    #        return None, None

    #def insert_basicauthor_info(self, text, regexp, dic, key):
    #    data = self.match_basic_regexp(text, regexp)
    #    if data:
    #        name, email = self.extract_author_from_string(data)
    #        dic[key]['name'] = name
    #        dic[key]['email'] = email

    def parse_log(self, log):
        """
        Returns:
        return_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        """
        re_commit = r'^commit ([0-9a-f]{5,40})$'
        #re_author = r'^Author:\s+(.*)$'
        #re_commitauthor = r'^Commit:\s+(.*)$'
        re_authordate = r'^AuthorDate:\s+(.*)$'
        re_commitdate = r'^CommitDate:\s+(.*)$'
        re_msg = r'^\s+(.*)$'
        re_issue_id = r'{0}-[0-9]*'.format(self.apache_issue_id_prefix)

        return_dict = {}
        cur_commit_hash = None
        for row in log.splitlines():
            #for regexp in re_list:
            #    info = match_basic_regexp(row, regexp)
            commit_hash = self.match_basic_regexp(row, re_commit)
            if commit_hash:
                cur_commit_hash = commit_hash
                if not commit_hash in return_dict:
                    return_dict[commit_hash] = {}
                    self.initialize_dict(return_dict[commit_hash])

            self.insert_basicdate_info(row, re_authordate, return_dict[cur_commit_hash], 'author_date')
            self.insert_basicdate_info(row, re_commitdate, return_dict[cur_commit_hash], 'commit_date')

            #self.insert_basicauthor_info(row, re_author, return_dict[cur_commit_hash], 'author')
            #self.insert_basicauthor_info(row, re_commitauthor, return_dict[cur_commit_hash], 'committer')

            issue_ids = self.match_issue_regexp(row, re_msg, re_issue_id)
            for issue_id in issue_ids:
                return_dict[cur_commit_hash]['issue_id'].add(issue_id)

        return return_dict


    def count_issue(self, parsed_log_dict):
        issue_id_list = []
        for commit_hash in parsed_log_dict.keys():
            for issue_id in parsed_log_dict[commit_hash]['issue_id']:
                issue_id_list.append(issue_id)

        issue_id_set = set(issue_id_list)
        print("number of issue: {0}".format(len(issue_id_list)))
        print("number of unique issue: {0}".format(len(issue_id_set)))
        #print("Count issue:")
        #cnt = Counter(issue_id_list)
        #print(cnt)



    def process_log(self):
        log = git_reader.git_log_all(self.repo_dir)

        parsed_log_dict = self.parse_log(log)
        util.dump_pickle("{0}/{1}_log_message_info.pickle".format(self.output_dir,
                                                                  self.apache_issue_id_prefix),
                                                                  parsed_log_dict)

        if self.verbose!=0:
            self.count_issue(parsed_log_dict)

    def run(self):
        self.process_log()



if __name__=="__main__":
    ins = ExtractCommitMessage(repo_dir="./../repository/avro", p_name="avro", apache_issue_id_prefix="AVRO", verbose=1)
    ins.run()
