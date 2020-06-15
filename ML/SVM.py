import numpy as np

from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GridSearchCV

class SVM():
    def __init__(self, clf=None, random_state=None):
        self.clf=clf
        self.random_state=random_state

    def fit(self, X, y):
        if self.clf is None:
            self.clf = GridSearchCV(SGDClassifier(loss="log", penalty="l2", max_iter=1000, random_state=self.random_state), param_grid={"alpha": np.logspace(-4, 0, 10)}, n_jobs=-1)

        self.clf.fit(X, y)

        return self

    
    def predict_prob(self, X):
        """
        Compute the probabilities for each entity

        Arguments:
        X [numpy.array<entities, features>] -- n x m numpy array. n indicates the number of entities; m indicates
                                               the number of features. This is the training data

        Returns:
        prob [numpy.array<entities, numpy.array<probability of y=0, probability of y=1>>]
                                            -- Return the probability of y
        """
        prob = self.clf.predict_proba(X)
        return prob
    
    def predict(self, X):
        """
        Decide the label (y) for each entity

        Arguments:
        X [numpy.array<entities, features>] -- n x m numpy array. n indicates the number of entities; m indicates
                                               the number of features. This is the training data

        Returns:
        label [numpy.array<label>] -- Return the label of y
        """
        prob = self.predict_prob(X)[:,1]
        label = prob>=0.5 # from the lemma 1 in the paper.
        return label



    def extract_important_features(self):

        return self.clf.best_estimator_.feature_importances_

