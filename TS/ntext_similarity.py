from string import punctuation

import nltk
try:
    nltk.find('tokenizers/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.find('tokenizers/wordnet')
except LookupError:
    nltk.download('wordnet')

from nltk.corpus import stopwords
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from Utils import util


class NtextSimilarity:
    def __init__(self, THRESHOLD_COSINE_SIM=0.3, verbose=0, parallel_iteration=0):
        self.THRESHOLD_COSINE_SIM = THRESHOLD_COSINE_SIM # NEED TO OPTIMIZE
        self.verbose = verbose
        self.parallel_iteration = parallel_iteration


    def remove_punctuation(self, word_tokens):
        return [word for word in word_tokens if not word in punctuation]

    def preprocess_text(self, text):
        """
        Preprocess a text. Concretely, this function applies the following processing:
        - tokenization
        - filtering out stop words
        - Using one term representing all synonymous
        - Stemming analysis

        All of them are implemented based on the NLTK toolkit

        Arguments:
        text [string] -- a text that we want to proprocess

        Returns:
        return token text [a string] -- proprocessed input text into one string separated by " "
        """
        stop_words = set(stopwords.words("english"))
        ps = PorterStemmer()

        text = text.lower()
        word_tokens = word_tokenize(text) # tokenization
        word_tokens = self.remove_punctuation(word_tokens) # remove punctuation
        filtered_word_tokens = [word for word in word_tokens if not word in stop_words] # filtering out stop words
        synonym_word_tokens = []
        for word in filtered_word_tokens:
            syns = wordnet.synsets(word)
            if len(syns)==0:
                synonym_word_tokens.append(word) # if no synonymous, not replace
            else:
                synonym_word_tokens.append(syns[0].lemmas()[0].name()) # if there exist synonymous, use the first one
        assert len(synonym_word_tokens)==len(filtered_word_tokens), "Invalid synonym processing"
        stemmed_word_tokens = [ps.stem(word) for word in synonym_word_tokens]

        #print("=== org ===")
        #print(word_tokens)
        #print("=== filtering out stop words ===")
        #print(filtered_word_tokens)
        #print("=== replace sysnonym ===")
        #print(synonym_word_tokens)
        #print("=== stemming ===")
        #print(stemmed_word_tokens)
        return " ".join(stemmed_word_tokens)

    def make_corpus_and_input(self, dsc_issue_dict, comment_issue_dict, log_msg_repo_dict, hash_list, issue_id_list):
        """
        dsc_issue_dict [dict<issue id, description] -- description for each issue
        comment_issue_dict [dict<issue id, comments (a string)] -- a string of comments for each issue id
        log_msg_repo_dict [dict<commit hash, log message] -- log message for each commit
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        corpus [list<text>] -- list of description and comments for all issue ids
        processed_dsc_issue_dict [dict<issue id, description] -- preprocessed description for each issue
        processed_comment_issue_dict [dict<issue id, comments (a string)] -- a string of preprocessed comments for each issue id
        processed_log_msg_repo_dict [dict<commit hash, log message] -- preprocessed log message for each commit
        """
        corpus = []
        processed_dsc_issue_dict = {}
        processed_comment_issue_dict = {}
        processed_log_msg_repo_dict = {}
        for issue_id in issue_id_list:
            if not issue_id in dsc_issue_dict:
                processed_dsc_issue_dict[issue_id] = ""
            elif dsc_issue_dict[issue_id] is None:
                processed_dsc_issue_dict[issue_id] = ""
            else:
                processed_dsc_issue_dict[issue_id] = self.preprocess_text(dsc_issue_dict[issue_id])

            if not issue_id in comment_issue_dict:
                processed_comment_issue_dict[issue_id] = ""
            elif comment_issue_dict[issue_id] is None:
                processed_comment_issue_dict[issue_id] = ""
            else:
                processed_comment_issue_dict[issue_id] = self.preprocess_text(comment_issue_dict[issue_id])

            corpus.append(processed_dsc_issue_dict[issue_id])
            corpus.append(processed_comment_issue_dict[issue_id])
        for commit_hash in hash_list:
            if log_msg_repo_dict[commit_hash] is None:
                processed_log_msg_repo_dict[commit_hash] = ""
            else:
                processed_log_msg_repo_dict[commit_hash] = self.preprocess_text(log_msg_repo_dict[commit_hash])

            corpus.append(processed_log_msg_repo_dict[commit_hash])

        return corpus, processed_dsc_issue_dict, processed_comment_issue_dict, processed_log_msg_repo_dict

    def compare_ntext(self, dsc_issue_dict, comment_issue_dict, log_msg_repo_dict, hash_list, issue_id_list, target_issue_id_list, output_dir):
        """
        Compare the description and comment in issue with log message at a commit.
        We identify this is a pair if they are similar

        Arguments:
        dsc_issue_dict [dict<issue id, description] -- description for each issue
        comment_issue_dict [dict<issue id, comments (a string)] -- a string of comments for each issue id
        log_msg_repo_dict [dict<commit hash, log message] -- log message for each commit (already replaced: issue ids to ISSUE_ID)
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        target_issue_id_list [list<issue id>] -- studied issue id list for parallel execution
        output_dir [string] -- path to a directory to store the text similarity values as pickle files

        Returns:
        return_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are the similar text
        """

        #print(preprocess_text(dsc_issue_dict['HADOOP-12']))
        #sys.exit()
        corpus, processed_dsc_issue_dict, processed_comment_issue_dict, processed_log_msg_repo_dict = self.make_corpus_and_input(dsc_issue_dict, comment_issue_dict, log_msg_repo_dict, hash_list, issue_id_list)

        vectorizer = TfidfVectorizer()
        vectorizer.fit(corpus)

        log_msg_vec_dict = {}
        for commit_hash in hash_list:
            log_msg_vec_dict[commit_hash] = vectorizer.transform([processed_log_msg_repo_dict[commit_hash]])

        num_issue_id_list = len(target_issue_id_list)
        return_dict = {}
        cosine_similarity_dict = {}
        for idx_issue_id, issue_id in enumerate(target_issue_id_list):
            cosine_similarity_dict[issue_id] = {}
            if self.verbose > 0:
                if idx_issue_id%80==0:
                    print("{0} -- Done issue id: {1}/{2}".format(self.parallel_iteration, idx_issue_id, num_issue_id_list))
            issue_text_vec = vectorizer.transform([processed_dsc_issue_dict[issue_id] + " " + processed_comment_issue_dict[issue_id]])
            for commit_hash in hash_list:
                cosine_sim = cosine_similarity(issue_text_vec, log_msg_vec_dict[commit_hash])[0,0]
                cosine_similarity_dict[issue_id][commit_hash] = cosine_sim
                if cosine_sim >= self.THRESHOLD_COSINE_SIM:
                    if not issue_id in return_dict:
                        return_dict[issue_id] = []
                    return_dict[issue_id].append(commit_hash)

        util.dump_pickle("{0}/cosine_similarity_dict_ite{1}.pickle".format(output_dir, self.parallel_iteration), cosine_similarity_dict)

        return return_dict

    def run(self, hash_list, issue_id_list, target_issue_id_list, dsc_issue_dict,
            comment_issue_dict, log_message_without_issueid_path, output_dir):
        """
        Combine issue ids and commit hashes using shared files matching.

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list
        target_issue_id_list [list<issue id>] -- studied issue id list for parallel execution
        dsc_issue_dict [dict<issue id, description>] -- issue report description for each issue report
        comment_issue_dict [dict<issue id, comments (a string)>] -- a string of comments for each issue id
        log_messgae_without_issueid_path [string] -- path to log_message_info.pickle
        output_dir [string] -- path to a directory to store the text similarity values as pickle files

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. these commit hashes are the similar natural language with that issue
        """

        """
        repo_dict [dict<commit hash, log message] -- log message for each commit
        """
        log_msg_repo_dict = util.load_pickle(log_message_without_issueid_path) #


        issue2hash_dict = self.compare_ntext(dsc_issue_dict, comment_issue_dict, log_msg_repo_dict, hash_list, issue_id_list, target_issue_id_list, output_dir)
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
    #target_issue_id_list = ['HADOOP-5213', 'HADOOP-4840', 'HADOOP-4854']
    #target_issue_id_list = ['HADOOP-5213']
    #target_issue_id_list = ['HADOOP-4840']
    target_issue_id_list = ['HADOOP-4854']
    #print(run("hadoop", hash_list, issue_id_list))

    ntext_similarity_obj = NtextSimilarity()
    print(ntext_similarity_obj.run("hadoop", hash_list, issue_id_list, target_issue_id_list))
