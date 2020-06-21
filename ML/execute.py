from ML import RF
from ML import SVM

from Utils import util
from Utils import generate_delete_data

from KE import keyword_extraction

from PU import pu_link

class MLModel:
    def __init__(self, repo_dir, db_path, model_name="RF", execute_flag_ntext=0,
                 random_state=None, verbose=0, keyword_extraction_dict_path=None,
                 delete_rate=None, max_iteration=25):

        self.repo_dir = repo_dir
        self.db_path = db_path
        self.model_name = model_name

        self.execute_flag_ntext = execute_flag_ntext

        self.random_state=random_state
        self.verbose = verbose

        self.keyword_extraction_dict_path=keyword_extraction_dict_path
        self.delete_rate = delete_rate
        self.max_iteration = max_iteration

    def run(self, hash_list, issue_id_list, log_message_info_path,
            log_message_without_issueid_path, dsc_issue_dict, comment_issue_dict,
            output_dir):
        """
        Use randomforest for the prediction

        Arguments:
        hash_list [list<commit hash>] -- studied commit hash list
        issue_id_list [list<issue id>] -- studied issue id list

        Returns:
        issue2hash_dict [dict<issue id, list<commit hash>>] -- issue id to list of commit hashes. 
        """

        # extract train data
        if self.keyword_extraction_dict_path:
            keyword_extraction_dict = util.load_pickle(self.keyword_extraction_dict_path)
        else:
            ins = keyword_extraction.KeywordExtraction()
            keyword_extraction_dict = ins.run(hash_list, issue_id_list, log_message_info_path) # train data
            keyword_extraction_dict = generate_delete_data.main(keyword_extraction_dict, self.delete_rate)


        pu_link_obj = pu_link.PULink(repo_dir=self.repo_dir, db_path=self.db_path, random_state=self.random_state, verbose=self.verbose,
                                     keyword_extraction_dict_path=self.keyword_extraction_dict_path,
                                     delete_rate=self.delete_rate, max_iteration=self.max_iteration,
                                     execute_flag_ntext=self.execute_flag_ntext)
        data_array, label_list, name_list, candidate_issue2hash_dict = pu_link_obj.extract_features(hash_list, issue_id_list, keyword_extraction_dict,
                                                                                                    log_message_info_path, log_message_without_issueid_path,
                                                                                                    dsc_issue_dict, comment_issue_dict, output_dir)

        if self.model_name=="RF":
            self.Model = RF.RF(random_state=self.random_state)
        elif self.model_name=="SVM":
            self.Model = SVM.SVM(random_state=self.random_state)
        else:
            exit('Illegal model name: {0}'.format(self.model_name))
            

        self.Model.fit(data_array, label_list)
        
        prediction_result = self.Model.predict(data_array)

        issue2hash_dict = {}
        for issue_id in candidate_issue2hash_dict.keys():
            for commit_hash in candidate_issue2hash_dict[issue_id]:
                idx = name_list.index("{0}:{1}".format(issue_id, commit_hash))
                if prediction_result[idx]:
                    if not issue_id in issue2hash_dict:
                        issue2hash_dict[issue_id] = []
                    issue2hash_dict[issue_id].append(commit_hash)

        return issue2hash_dict

    def extract_important_features(self):
        return self.Model.extract_important_features()

