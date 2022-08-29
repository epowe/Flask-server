import joblib
import moviepy.editor as moviepy
import os, sys
import torch
from torch import nn
import pydub
import numpy as np
import pandas as pd
from pydub import AudioSegment
from utils import data_utils
from clf.mfcc_data import mfcc_loader
from kospeech.infer_ import pred_sentence
from hanspell import spell_checker
import subprocess
packages = ['clf','kospeech','py-hanspell','utils']
for package in packages:
    sys.path.append(package)

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
        self.word = []

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
    def webm_to_wav(self,webm,wav):
        clip = moviepy.VideoFileClip(webm)
        clip.audio.write_audiofile(wav)
        return wav

    def convert_webm_to_wav(self,file):
        command = ['ffmpeg', '-i', file, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', file[:-5] + '.wav']
        subprocess.run(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        return file[:-5] + '.wav'
    def audio(self, path, min_silence_length=150, duration=3500):
        '''
        input: wav file path
        return: filename_start_end.pcm
        '''
        if path.endswith('.webm'):
            path = self.convert_webm_to_wav(path)
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
        file_name = file.split('.')[0]
        folder = os.path.join(dir, file_name)
        os.makedirs(folder, exist_ok=True)
        for [start, end] in times:
            sums += (end - start)
            if sums >= duration:
                t.append([st, end])
                st = end
                sums = 0
        if len(t) < 1:
            t = [[times[0][0],times[-1][-1]]]
        for idx, time in enumerate(t):
            dic = {}
            os.makedirs(os.path.join(folder,'wav'), exist_ok=True)
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
        return self.csv
    def extract(self, csv_path=None):
        text = []
        n_dialect = []
        speechRates = []

        if csv_path ==None:
            csv_path = self.csv
        df = pd.read_csv(csv_path)
        save_path = os.path.join(os.path.split(csv_path)[0],'total.csv')
        for idx, rows in df.iterrows():
            file_path = rows['file_path']
            start = rows['start']
            end = rows['end']
            pcm = self.convert_wave_to_pcm(file_path)
            sentence = pred_sentence(pcm,self.model,self.device)
            isDialect = self.mfcc_pipe.predict(pcm)
            speechRate = ((end-start)/1000)/ len(sentence[0])

            text.append(sentence[0])
            n_dialect.append(isDialect[0])
            speechRates.append(speechRate)

        df['text'] = text
        df['isDialect'] = n_dialect
        df['speechRate'] = speechRates
        df.to_csv(save_path,encoding='utf-8-sig',index = None)
        # return {'dialectCount' : dialectCount,
        #         'intonation' : self.intonation,
        #         'speechRate' : speechRate,
        #         'word' : word}

