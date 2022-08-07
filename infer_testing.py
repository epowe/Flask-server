from kospeech.infer_ import pred_sentence
import torch
import os
from hanspell import spell_checker

device = torch.device('cpu')
model_path = 'kospeech/trained_model/model_ds2.pt'
d_path = 'clf/test_data'


model = torch.load(model_path, map_location=lambda storage, loc: storage).to(device)
if isinstance(model, torch.nn.DataParallel):
    model = model.module


d = os.listdir(d_path)
d = [x for x in d if x.endswith('pcm')]
for data in d:
    if data.startswith('Kspon'):
        print('표준어 데이터')
        txt = data[:-3] + 'txt'
        txt_path = os.path.join(d_path, txt)
        with open(txt_path, 'r', encoding='cp949') as f:
            s = f.readline()
    else:
        print('방언 데이터')
        txt = data[:-3] + 'txt'
        txt_path = os.path.join(d_path, txt)
        with open(txt_path, 'r', encoding='utf-8') as f:
            s = f.readline()

    audio_path = os.path.join(d_path,data)
    print('target:', s)
    sentence = pred_sentence(audio_path, model_path, device)[0]
    print('pred:',sentence)
    print('spell check:',spell_checker.check(sentence).as_dict()['checked'])
    print('-'*20)
# audio_path, model_path, device
