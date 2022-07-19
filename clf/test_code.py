import joblib
import os, sys
# from mlp_pipline import get_clf_eval
import time
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import StandardScaler
# from sklearn.neural_network import MLPClassifier
# from mfcc_data import mfcc_loader
import warnings
warnings.filterwarnings(action='ignore')


print('load model...')
mfcc_pipe = joblib.load('model.joblib')
print('finish')
path = 'test_data'
files = os.listdir(path)
# print(files)

files = [file[:-3] for file in files if file.endswith('pcm')]

for file in files:
    start = time.time()
    if file.startswith('DKSR'):
        print('방언 데이터')
        cls = mfcc_pipe.predict(os.path.join(path,file+'pcm'))
        print(cls)
    else:
        print('표준어 데이터')
        cls = mfcc_pipe.predict(os.path.join(path, file + 'pcm'))
        print(cls)
    print('execute time: {:.4f}'.format(time.time()-start))
    print('-'*20)