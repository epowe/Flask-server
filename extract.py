import joblib
import os, sys
import torch
from torch import nn
import pydub
import numpy as np
import pandas as pd
from pydub import AudioSegment
import pydub
from utils import data_utils

from kospeech.infer_ import pred_sentence
import torch
import os
from hanspell import spell_checker


# from clf.mfcc_data import mfcc_loader\
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
        self.sr = 16000

        self.dialectCount = 0
        self.intonation = 0.
        self.speechRate = 0.
        self.word = list(str)

    def predict(self, audio_path):
        sentence = pred_sentence(audio_path, self.model, self.device)[0]
        is_dialect = self.mfcc_pipe(audio_path) # {1:True, 0:False}
        time = np.memmap(audio_path, dtype='h', mode='r').astype('float32')/self.sr
        return {'sentence':sentence,
                'is_dialect':is_dialect,
                'time':time}

    def convert_wave_to_pcm(self, filename):
        file = open(filename, 'rb')
        byteBuffer = bytearray(file.read())
        file.close()
        fn_ext = os.path.splitext(filename)
        if fn_ext[1] == '.wav':
            out_filename = fn_ext[0] + '.pcm'
        else:
            out_filename = fn_ext[0] + fn_ext[1] + '.pcm'
        out_file = open(out_filename, 'wb')
        out_file.write(byteBuffer[44:])
        out_file.close()
        return out_filename
    def audio(self, path, min_silence_length=150, duration=3500):
        '''
        input: wav file path
        return: filename_start_end.pcm
        '''
        dir = os.path.split(path)[0]
        file = os.path.split(path)[-1]
        csv = []
        audio = AudioSegment.from_file(file=path,
                                       format='wav')
        times = pydub.silence.detect_nonsilent(audio,
                                               min_silence_len=min_silence_length,
                                               silence_thresh=-32.64)
        t = []
        st = times[0][0]
        sums = 0
        for [start, end] in times:
            sums += (end - start)
            if sums >= duration:
                t.append([st, end])
                st = end
                sums = 0
        for idx, time in enumerate(t):
            dic = {}
            file_name = file.split('.')[0]
            folder = os.path.join(dir,file_name)
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder,'wav',str(idx)+'.wav')
            newAudio = audio[time[0]:time[1]]
            newAudio.export(file_path,format='wav')
            dic['file_path'] =file_path
            dic['start'] = time[0]
            dic['end'] = time[1]
            csv.append(dic)
        self.df = pd.DataFrame(csv)
        self.csv = os.path.join(folder,'train.csv')
        self.df.to_csv(self.csv, index=False)
    def extract(self, csv_path=None):
        text = []
        n_dialect = []
        speechRates = []

        if csv_path ==None:
            df = pd.read_csv(self.csv)
        for rows in df.iterrows():
            file_path = rows['file_path']
            start = rows['start']
            end = rows['end']
            pcm = self.convert_wave_to_pcm(file_path)
            sentence = pred_sentence(pcm,self.model,self.device)
            isDialect = self.mfcc_pipe.predict(pcm)
            speechRate = ((end-start)/1000)/ len(sentence)

            text.append(sentence)
            n_dialect.append(isDialect[0])
            speechRates.append(speechRate)

        df['text'] = text
        df['isDialect'] = n_dialect
        df['speechRate'] = speechRates
        df.to_csv('total.csv',index = None)
        # return {'dialectCount' : dialectCount,
        #         'intonation' : self.intonation,
        #         'speechRate' : speechRate,
        #         'word' : word}

