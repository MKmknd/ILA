import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GridSearchCV

class PUModel:
    """
    This class implements the PU model that was introduced in the paper [1]

    [1] C. Elkan and K. Noto, 'Learning Classifiers from Only Positive and Unlabeled Data' 2008
    """
    def __init__(self, random_state=None, clf=None):
        self.clf = clf
        self.random_state = random_state

    def fit(self, X, s):
        """
        Train the g(x) and generate the value of c for the lemma in the paepr (Elkan and Noto, 2008)
        self.clf corresponds to g(x)=p(s=1|x) in the paper. Here we use SGDClassifier (= support vector machine)
        if self.clf is not initialized yet.
        self.c corresponds to c in the paper. Here, we use e1 to compute c.

        Arguments:
        X [numpy.array<entities, features>] -- n x m numpy array. n indicates the number of entities; m indicates
                                               the number of features. This is the training data
        s [numpy.array<integer>] -- An one-dimentional numpy array. Each element indicates whether
                                    this entity has label (y) or not. If it has label, it should be 1; otherwise
                                    it should be 0.
        """

        if self.clf is None:
            self.clf = GridSearchCV(SGDClassifier(loss="log", penalty="l2", max_iter=1000, random_state=self.random_state), param_grid={"alpha": np.logspace(-4, 0, 10)}, verbose=1, n_jobs=-1)

        self.clf.fit(X, s)

        self.c = self.clf.predict_proba(X[s==1])[:,1].mean()

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
        label = prob>=(0.5*self.c) # from the lemma 1 in the paper.
        return label

