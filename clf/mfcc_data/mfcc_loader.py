import librosa
import numpy as np
import os, sys
import pandas as pd
from collections import defaultdict

from sklearn.base import BaseEstimator, TransformerMixin


# s = np.memmap(pcm, dtype='h', mode='r').astype('float32')
# s = s / 32767
# mfcc = librosa.feature.mfcc(y=s, sr=16000, n_mfcc=32)

class mfcc_loader(BaseEstimator, TransformerMixin):
    '''
    load pcm file to mfcc feature
    use_example = sr=1600
    fit_params ={ 'sr' : 16000,
                  'n_mfcc' : 32
                  }
    input = pcm file path
    output = mfcc feature
    '''
    def __init__(self, **fit_params):
        if len(fit_params) != 0:
            self.params = fit_params
        else:
            self.params = {'sr': 16000,
                          'n_mfcc': 32
                          }
    def fit(self, X,y=None):
        return self
    def transform(self, file_path, y=None):
        mfcc = np.memmap(file_path, dtype='h', mode='r').astype('float32')
        mfcc = mfcc / 32767
        mfcc = librosa.feature.mfcc(y=mfcc,
                                    sr=self.params['sr'],
                                    n_mfcc=self.params['n_mfcc'])
        mfcc = np.mean(mfcc,axis=1).reshape(1,-1)
        return mfcc