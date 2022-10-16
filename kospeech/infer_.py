# Copyright (c) 2020, Soohwan Kim. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from random import sample

import argparse
# from typing_extensions import Required
import torch
import torch.nn as nn
import numpy as np
import torchaudio
from torch import Tensor

from kospeech.vocabs.ksponspeech import KsponSpeechVocabulary
from kospeech.data.audio.core import load_audio
from kospeech.models import (
    SpeechTransformer,
    Jasper,
    DeepSpeech2,
    ListenAttendSpell,
    Conformer,
)
import sys
sys.path.append('../')

# from hanspell import spell_checker

def revise(sentence):
    words = sentence[0].split()
    result = []
    for word in words:
        tmp = ''
        for t in word:
            if not tmp:
                tmp += t
            elif tmp[-1]!= t:
                tmp += t
        if tmp == '스로':
            tmp = '스스로'
        result.append(tmp)
    return ' '.join(result)

def parse_audio(audio_path: str, del_silence: bool = False, audio_extension: str = 'pcm') -> Tensor:
    signal = load_audio(audio_path, del_silence, extension=audio_extension)
    # print(len(signal))
    feature = torchaudio.compliance.kaldi.fbank(
        waveform=Tensor(signal).unsqueeze(0),
        num_mel_bins=80,
        frame_length=20,
        frame_shift=10,
        window_type='hamming'
    ).transpose(0, 1).numpy()

    feature -= feature.mean()
    feature /= np.std(feature)

    return torch.FloatTensor(feature).transpose(0, 1)




def pred_sentence(audio_path,model,device):
    # device = torch.device('cpu')
    feature = parse_audio(audio_path,del_silence=True)

    input_length = torch.LongTensor([len(feature)])
    vocab = KsponSpeechVocabulary('kospeech/data/vocab/aihub_character_vocabs.csv')


    # model = torch.load(model_path, map_location=lambda storage, loc: storage).to(device)
    # if isinstance(model, nn.DataParallel):
    #     model = model.module
    model.eval()



    if isinstance(model, ListenAttendSpell):
        model.encoder.device = device
        model.decoder.device = device

        y_hats = model.recognize(feature.unsqueeze(0), input_length)
    elif isinstance(model, DeepSpeech2):
        model.device = device
        y_hats = model.recognize(feature.unsqueeze(0), input_length)
    elif isinstance(model, SpeechTransformer) or isinstance(model, Jasper) or isinstance(model, Conformer):
        y_hats = model.recognize(feature.unsqueeze(0), input_length)

    sentence = vocab.label_to_string(y_hats.cpu().detach().numpy())
    return sentence
    # print(sentence)
    # print("finish")

#
# nums = 5
# d_path = 'E:\DKSL_main'
# d_path2 = 'E:\sample\Kspon_total\\tot'
# datas = os.listdir(d_path)
# datas = sample(datas,nums)
# datas2 = os.listdir(d_path2)
# datas2 = sample(datas2,nums)
# model_path = 'outputs/model.pt'
# model_path = 'outputs/2022-04-30/12-03-24/model_ds2.pt'
# # model_path = 'outputs/2022-04-30/model.pt'
# device = torch.device('cpu')
#
# print('경상도 테스트')
# for data in datas:
#     audio_path = os.path.join(d_path,data,data+'.pcm')
#     txt_path = os.path.join(d_path,data,data+'.txt')
#     with open(txt_path,'r') as f:
#         s = f.readline()
#     print('target:',s)
#     sentence = pred_sentence(audio_path, model_path, device)[0]
#     print('pred:',sentence)
#     # print('pred2:', revise(sentence))
#     print('spell check:',spell_checker.check(sentence).as_dict()['checked'])
#     print('-'*20)
#
# print('표준어 테스트')
# for data in datas2:
#     audio_path = os.path.join(d_path2,data,data+'.pcm')
#     txt_path = os.path.join(d_path2,data,data+'.txt')
#     with open(txt_path,'r') as f:
#         s = f.readline()
#     print('target:',s)
#     sentence = pred_sentence(audio_path, model_path, device)[0]
#     print('pred:',sentence)
#     # print('pred2:', revise(sentence))
#     print('spell check:',spell_checker.check(sentence).as_dict()['checked'])
#     print('-'*20)
