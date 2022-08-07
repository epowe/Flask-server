import joblib
import os, sys
import torch
from torch import nn
from kospeech.infer_ import pred_sentence
# model_path = os.path.join('clf','model.joblib')
# mfcc_pipe = joblib.load('clf/model.joblib')

class feature_extract():
    def __init__(self, model_path='kospeech/trained_model/model_ds2.pt'):
        self.mfcc_pipe = joblib.load('clf/model.joblib')
        self.device = torch.device('cpu')
        self.model_path = model_path
        self.model = torch.load(model_path, map_location=lambda storage, loc: storage).to(self.device)
        if isinstance(self.model, nn.DataParallel):
            self.model = self.model.module
        self.model.eval()

        self.dialectCount = 0
        self.intonation = 0.
        self.speechRate = 0.
        self.word = list(str)

    def predict(self, audio_path):
        sentence = pred_sentence(audio_path, self.model, self.device)[0]
        is_dialect = self.mfcc_pipe(audio_path) # {1:True, 0:False}

    def extract(self):
        return {'dialectCount' : self.dialectCount,
                'intonation' : self.intonation,
                'speechRate' : self.speechRate,
                'word' : self.word}