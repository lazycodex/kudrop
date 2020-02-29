import numpy as np 
import pandas as pd 

from sklearn import preprocessing
import matplotlib.pyplot as plt 
plt.rc("font", size=14)
import seaborn as sns
sns.set(style="white") #white background style for seaborn plots
sns.set(style="whitegrid", color_codes=True)

import warnings
warnings.simplefilter(action='ignore')

# Read CSV train data file into DataFrame
train_df = pd.read_csv("input/train_female_fail.csv")

# Read CSV test data file into DataFrame
test_df = pd.read_csv("input/test.csv")

#create categorical variables and drop some variables
train_data = train_df.copy()
#print(train_data.head())
training=pd.get_dummies(train_data, columns=["Sex"])
training.drop('Sex_female', axis=1, inplace=True)

final_train = training

#print(final_train.head())

final_train['IsMinor']=np.where(final_train['MidTerm']>=60, 1, 0)
test_df['IsMinor']=np.where(test_df['MidTerm']>=60, 1, 0)

#print(final_train.head())

test_data = test_df.copy()


testing = pd.get_dummies(test_data, columns=["Sex"])
testing.drop('Sex_female', axis=1, inplace=True)
final_test = testing

#print(final_test.head())

from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import RFE

cols = ["Age","MidTerm","Sex_male","IsMinor"] 
X = final_train[cols]
y = final_train['Grade']
# Build a logreg and compute the feature importances
model = LogisticRegression()
# create the RFE model and select 4 attributes
rfe = RFE(model, 4)
rfe = rfe.fit(X, y)
# summarize the selection of the attributes
print('Selected features: %s' % list(X.columns[rfe.support_]))

from sklearn.feature_selection import RFECV
# Create the RFE object and compute a cross-validated score.
# The "accuracy" scoring is proportional to the number of correct classifications
rfecv = RFECV(estimator=LogisticRegression(), step=1, cv=10, scoring='accuracy')
rfecv.fit(X, y)

print("Optimal number of features: %d" % rfecv.n_features_)
print('Selected features: %s' % list(X.columns[rfecv.support_]))

# Plot number of features VS. cross-validation scores
plt.figure(figsize=(10,6))
plt.xlabel("Number of features selected")
plt.ylabel("Cross validation score (nb of correct classifications)")
plt.plot(range(1, len(rfecv.grid_scores_) + 1), rfecv.grid_scores_)
#plt.show()

Selected_features = ["Sex_male","Age","MidTerm","IsMinor"] 
X = final_train[Selected_features]

plt.subplots(figsize=(4, 5))
sns.heatmap(X.corr(), annot=True, cmap="RdYlGn")
#plt.show()

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, precision_score, recall_score 
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve, auc, log_loss

# 10-fold cross-validation logistic regression
logreg = LogisticRegression()
# Use cross_val_score function
# We are passing the entirety of X and y, not X_train or y_train, it takes care of splitting the data
# cv=10 for 10 folds
# scoring = {'accuracy', 'neg_log_loss', 'roc_auc'} for evaluation metric - althought they are many
scores_accuracy = cross_val_score(logreg, X, y, cv=10, scoring='accuracy')
scores_log_loss = cross_val_score(logreg, X, y, cv=10, scoring='neg_log_loss')
scores_auc = cross_val_score(logreg, X, y, cv=10, scoring='roc_auc')
print('K-fold cross-validation results:')
print(logreg.__class__.__name__+" average accuracy is %2.3f" % scores_accuracy.mean())
print(logreg.__class__.__name__+" average log_loss is %2.3f" % -scores_log_loss.mean())
print(logreg.__class__.__name__+" average auc is %2.3f" % scores_auc.mean())

from sklearn.model_selection import GridSearchCV

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline

#Define simple model
###############################################################################
C = np.arange(1e-05, 5.5, 0.1)
scoring = {'Accuracy': 'accuracy', 'AUC': 'roc_auc', 'Log_loss': 'neg_log_loss'}
log_reg = LogisticRegression()

#Simple pre-processing estimators
###############################################################################
std_scale = StandardScaler(with_mean=False, with_std=False)
#std_scale = StandardScaler()

#Defining the CV method: Using the Repeated Stratified K Fold
###############################################################################

n_folds=5
n_repeats=5

rskfold = RepeatedStratifiedKFold(n_splits=n_folds, n_repeats=n_repeats, random_state=2)

#Creating simple pipeline and defining the gridsearch
###############################################################################

log_clf_pipe = Pipeline(steps=[('scale',std_scale), ('clf',log_reg)])

log_clf = GridSearchCV(estimator=log_clf_pipe, cv=rskfold,
              scoring=scoring, return_train_score=True,
              param_grid=dict(clf__C=C), refit='Accuracy')

log_clf.fit(X, y)
results = log_clf.cv_results_

final_test['Grade'] = log_clf.predict(final_test[Selected_features])
final_test['Name'] = test_df['Name']
submission = final_test[['Name','Grade']]
submission.to_csv("submission.csv", index=False)
#print(submission.tail())
