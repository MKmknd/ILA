
import subprocess
import sys
import re
from datetime import datetime as dt

"""
Get commit hash list (following time flow)
"""
def get_hashlist_with_author_date(repodir):
    hash_list = []
    hash_list = subprocess.check_output(
            ['git', '-C', '{}'.format(repodir), 'log', '--all', '--pretty=format:%H,%ai'],
            universal_newlines=True
            ).splitlines()
    hash_list.reverse()  # sort by time

    return_dict = {}
    for row in hash_list:
        h_str, t_str = row.split(',')
        return_dict[h_str] = dt.strptime(t_str, '%Y-%m-%d %H:%M:%S %z')

    return return_dict


def get_all_hash(repodir):
    hash_list = subprocess.check_output(
            ['git', '-C', '{}'.format(repodir), 'log', '--all', '--pretty=format:%H'],
            universal_newlines=True
            ).splitlines()
    return hash_list

def get_all_hash_without_merge(repodir):
    hash_list = subprocess.check_output(
            ['git', '-C', '{}'.format(repodir), 'log', '--all', '--no-merges', '--pretty=format:%H'],
            universal_newlines=True
            ).splitlines()
    return hash_list

"""
Get commit hash in a specific interval
"""
def get_hashlist_in_interval(repodir, maxtime, mintime):
    hash_list = []
    hash_list = subprocess.check_output(
            ['git', '-C', '{}'.format(repodir), 'log', '--all', '--pretty=format:%H,%ai'],
            universal_newlines=True
            ).splitlines()
    hash_list.reverse()  # sort by time

    return_list = []
    for row in hash_list:
        h_str, t_str = row.split(',')
        time_date = dt.strptime(t_str, '%Y-%m-%d %H:%M:%S %z')
        if maxtime >= time_date and mintime <= time_date:
            return_list.append(h_str)

    return return_list


def get_commit_message(repodir, commit_hash):
    commit_msg_list = subprocess.check_output(
            ['git', '-C', '{}'.format(repodir), 'log', '--format=%B',
            '-n', '1', commit_hash],
            universal_newlines=True
            ).splitlines()

    return "\n".join(commit_msg_list)


"""
Get all logs
"""
def git_log_all(dirname):
    log = subprocess.check_output(
            ['git', '-C', '{}'.format(dirname), 'log', '--all', '--pretty=fuller'],
            #['git', '-C', '{}'.format(dirname), 'log', '-10', '--pretty=fuller'],
            universal_newlines=True
            )
    return log

def git_log_all_without_merge(dirname):
    log = subprocess.check_output(
            ['git', '-C', '{}'.format(dirname), 'log', '--all', '--pretty=fuller', '--no-merges'],
            #['git', '-C', '{}'.format(dirname), 'log', '-10', '--pretty=fuller'],
            universal_newlines=True
            )
    return log


"""
Get all modified files (that exist in the previous commit already) in a commit.
if it is a new added file in that commit, (e.g., 
--- /dev/null
+++ b/doc/mockito
)
this function doesn't return anything

update:
return all modified files with the file name after applying the modifications
"""
def get_all_modified_files(repodir, commit_hash):
    #files = subprocess.check_output(
    #        ['git', '-C', '{}'.format(repodir), 'diff-tree', '--no-commit-id',
    #        '--name-only', '-r', commit_hash],
    #        universal_newlines=True
    #        ).splitlines()
    files = subprocess.check_output(
            ['git', '-C', '{}'.format(repodir), 'diff-tree', '--no-commit-id',
            '--name-only', '-r', commit_hash,  '--diff-filter=ACMRTUX'],
            universal_newlines=True
            ).splitlines()
    
    return files

"""
Get the content of a file in a specific commit.
Here we retrieve the content before applying the modification in this commit
if it is a newly added commit (/dev/null), return "fatal: Invalid object name '{commit hash}^'."
"""
def get_entier_file(repodir, commit_hash, f_path):
    try:
        content = subprocess.check_output(
                ['git', '-C', '{}'.format(repodir), 'show', '{0}^:{1}'.format(commit_hash, f_path)],
                universal_newlines=True
                )
    except UnicodeDecodeError:
        content = subprocess.check_output(
                ['git', '-C', '{}'.format(repodir), 'show', '{0}^:{1}'.format(commit_hash, f_path)]
                ).decode('utf-8','replace')
    
    return content


def get_cur_entier_file(repodir, commit_hash, f_path):
    try:
        content = subprocess.check_output(
                ['git', '-C', '{}'.format(repodir), 'show', '{0}:{1}'.format(commit_hash, f_path)],
                universal_newlines=True
                )
    except UnicodeDecodeError:
        content = subprocess.check_output(
                ['git', '-C', '{}'.format(repodir), 'show', '{0}:{1}'.format(commit_hash, f_path)]
                ).decode('utf-8','replace')
    
    return content

def ignore_somecode(text):
    """
    Ignore new pages and CR.
    In git, these are represented as '\r' and '\f'
    If we add '\0' to database, we get error.
    """
    text = re.sub('\r', '', text)
    text = re.sub('\f', '', text)
    text = re.sub('\0', '', text)
    return text

"""
Execute git show
"""
def git_show(dirname, commit_hash):
    show = subprocess.check_output(
            ['git', '-C', '{}'.format(dirname), 'show',
             commit_hash],
            ).decode('utf-8', errors='ignore')
    show = ignore_somecode(show)
    return show

"""
Execute git show --unified=0
"""
def git_show_with_context(dirname, commit_hash, context):
    show = subprocess.check_output(
            ['git', '-C', '{}'.format(dirname), 'show',
             '--unified={0}'.format(context), commit_hash],
            ).decode('utf-8', errors='ignore')
    show = ignore_somecode(show)
    return show


def subversion_hash_to_commit_hash(dirname):
    """
    Extract all pairs between svn id to commit hash

    Arguments:
    dirname [string] -- path to directory

    Returns:
    svn_id_to_commit_hash_dict [dict<svn id, commit hash>] -- svn id to commit hash
    """
    log_list = get_all_hash(dirname)

    re_svn_id = r"git-svn-id: \S+?@([\d]+)\s\S+$"
    svn_id_to_commit_hash_dict = {}
    for commit_hash in log_list:
        message = get_commit_message(dirname, commit_hash)

        for row in message.splitlines():
            match = re.match(re_svn_id, row)
            if match:
                if not match.group(1) in svn_id_to_commit_hash_dict:
                    svn_id_to_commit_hash_dict[match.group(1)] = []
                svn_id_to_commit_hash_dict[match.group(1)].append(commit_hash)
    return svn_id_to_commit_hash_dict

def commit_hash_to_subversion_hash(dirname):
    """
    Extract all pairs between commit hash to svn id

    Arguments:
    dirname [string] -- path to directory

    Returns:
    commit_hash_to_svn_id_dict [dict<commit hash, svn id>] -- commit hash to svn id
    """
    log_list = get_all_hash(dirname)

    re_svn_id = r"git-svn-id: \S+?@([\d]+)\s\S+$"
    commit_hash_to_svn_id_dict = {}
    for commit_hash in log_list:
        message = get_commit_message(dirname, commit_hash)

        commit_hash_to_svn_id_dict[commit_hash] = []
        for row in message.splitlines():
            match = re.match(re_svn_id, row)
            if match:
                commit_hash_to_svn_id_dict[commit_hash].append(match.group(1))
    return commit_hash_to_svn_id_dict

if __name__=="__main__":
    #repodir = "./../repository/mockito"
    #commit_hash = "7cf6470d88491fe472e28493b50eba8a6fbf0433"
    #print(get_all_modified_files(repodir, commit_hash))
    #commit_hash = "2ffc8aee826fe81ed8cee1e26da1f7f329b0b2b4"
    #print(get_all_modified_files(repodir, commit_hash))

    #commit_hash = "2ffc8aee826fe81ed8cee1e26da1f7f329b0b2b4"
    #print(get_entier_file(repodir, commit_hash, "version.properties"))
    #commit_hash = "7cf6470d88491fe472e28493b50eba8a6fbf0433"
    #try:
    #    print(get_entier_file(repodir, commit_hash, "doc/mockito"))
    #except subprocess.CalledProcessError:
    #    print("SKIP: this is a newly added file")

    repodir = "./../repository/commons-lang"
    svn_hash_dict = {'895322': {'813971', '137221'}, '891316': {'137762'}, '1407973': {'137379'}, '906676': {'906673', '137353'}}
    svn_id_to_commit_hash_dict = subversion_hash_to_commit_hash(repodir)

    for svn_id in svn_hash_dict.keys():
        print("key: svn id: {0}, commit hash: {1}".format(svn_id, svn_id_to_commit_hash_dict[svn_id]))
        for value in svn_hash_dict[svn_id]:
            print("key: svn id: {0}, commit hash: {1}".format(value, svn_id_to_commit_hash_dict[value]))

