from mfcc_data import mfcc_loader
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
import joblib

import pandas as pd
import warnings
warnings.filterwarnings(action='ignore')
def get_clf_eval(y_test, pred):
    eps = 1e-7
    confusion = confusion_matrix(y_test, pred)
    accuracy = accuracy_score(y_test, pred)
    precision = precision_score(y_test, pred)
    recall = recall_score(y_test, pred)
    f1 = 2 *(precision*recall)/(precision+recall + eps)
    print('Confusion Matrix')
    print(confusion)
    print('정확도:{}, 정밀도:{}, 재현율:{}, F-1: {}'.format(accuracy, precision, recall,f1))

df = pd.read_csv('mfcc_data/mfcc_feature.csv')

y = df['label']
x = df.drop(['label','file_path'],axis=1)

X_train,X_test, y_train,y_test = train_test_split(x,y,test_size=0.2,
                                                  random_state=13,
                                                  stratify=y)



estimators = [('scaler',StandardScaler()),
              ('clf',MLPClassifier())]

pipe = Pipeline(estimators)

pipe.fit(X_train,y_train)

pred = pipe.predict(X_test)
get_clf_eval(y_test,pred)

mfcc_extract = mfcc_loader.mfcc_loader
pipe.steps.insert(0,('mfcc_extract', mfcc_extract()))

joblib.dump(pipe,'model.joblib')