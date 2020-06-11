import re

from Utils import util
from Utils import git_reader

#project_name_list = ["hadoop"]
#project_name_list = ["commons-lang", "commons-math"]
#project_name_list = ["avro"]
#project_name_list = ["zookeeper"]
#project_name_list = ["tez"]

class ExtractRawCommitMessage:
    """
    repo_dir: [str] -- path to the target repository directory
    p_name: [str] -- project name
    apache_issue_id_prefix [str] -- apache's issue id. E.g., HADOOP. If no prefix, we use the upper project name
    output_dir [str] -- output the result in this directory

    OUTPUT:
    The results is outputted in output_dir as a pickle file
    ({{ output_dir }}/{{ apache_issue_id_prefix }}_log_message.pickle).
    ({{ output_dir }}/{{ apache_issue_id_prefix }}_log_message_without_issueid.pickle).
    These pickle files are dictionary:
    dict<commit hash, commit log messages>

    We remove issue ids from the original log messages and outputted as
    *_log_message_without_issueid.pickle.
    The original commit message is outputted as the other one.
    """

    def __init__(self, repo_dir=None, p_name=None, apache_issue_id_prefix=None, output_dir=None):
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

        assert not self.repo_dir is None, "Need to give the repository path"
        assert not self.p_name is None, "Need to give the project name"

    def match_basic_regexp(self, text, regexp):
        match = re.match(regexp, text)
        info = None
        if match:
            info = match.group(1)
        return info

    def parse_log(self, log):
        """
        Returns:
        return_dict [dict<commit hash, dict<key name, data>>] -- key name list: author_date, commit_date, author, committer, issue_id
        """
        re_commit = r'^commit ([0-9a-f]{5,40})$'
        re_msg = r'^\s+(.*)$'
        re_issue_id = r'{0}-[0-9]*'.format(self.apache_issue_id_prefix)


        return_dict = {}
        return_dict_without_issueid = {}
        cur_commit_hash = None
        for row in log.splitlines():
            commit_hash = self.match_basic_regexp(row, re_commit)
            if commit_hash:
                cur_commit_hash = commit_hash
                if not cur_commit_hash in return_dict:
                    return_dict[cur_commit_hash] = ""
                    return_dict_without_issueid[cur_commit_hash] = ""

            match = re.match(re_msg, row)
            if match:
                return_dict[cur_commit_hash] += match.group(0) + "\n"
                return_dict_without_issueid[cur_commit_hash] += re.sub(re_issue_id, "ISSUE_ID", match.group(0) + "\n")


        return return_dict, return_dict_without_issueid


    def process_log(self):
        log = git_reader.git_log_all(self.repo_dir)
        #print(log)

        parsed_log_dict, parsed_log_dict_without_issueid = self.parse_log(log)
        util.dump_pickle("{0}/{1}_log_message.pickle".format(self.output_dir, self.p_name),
                         parsed_log_dict)
        util.dump_pickle("{0}/{1}_log_message_without_issueid.pickle".format(self.output_dir,self.p_name),
                         parsed_log_dict_without_issueid)

    def run(self):
        self.process_log()



if __name__=="__main__":
    ins = ExtractRawCommitMessage(repo_dir="./../repository/avro", p_name="avro",
                                  apache_issue_id_prefix="AVRO")
    ins.run()
