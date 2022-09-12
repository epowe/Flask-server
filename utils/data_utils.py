import sys
import os.path
import os
import subprocess
import sys
import pandas as pd
import pydub

def add_path():
    paths = ['kospeech','hanspell']
    for path in paths:
        sys.path.append(path)
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from pydub import AudioSegment
except:
    print('pydub not found')
    install('pydub')
    from pydub import AudioSegment

ext = None


class voice_split():
    '''
    it use total audio_path(wav) to split audio/audio.wav, csv
    '''
    def __init__(self):
        self.path = ''# path
        self.dir = ''# os.path.split(self.path)[0]
        self.file = ''# os.path.split(self.path)[-1]

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

    def split_wav(self, t1,t2,wav,out_folder):
        t1 = int(t1 * 1000)
        t2 = int(t2 * 1000)
        newAudio = AudioSegment.from_wav(wav)
        newAudio = newAudio[t1:t2]
        out_path = ''.join(wav.split('.')[:-1])
        out_path = os.path.split(out_folder)[-1]
        out_path = os.path.join(out_folder,out_path)
        newAudio.export(out_path, format="wav")
        return out_path

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
        self.df.to_csv(os.path.join(folder,file_name+'.csv'),index=False)


import os
from pydub import AudioSegment
from pydub.utils import make_chunks

#audioSegment = AudioSegment.from_file('/Users/mac/Downloads/speech_command/left/sample-1.webm', 'webm')
#audioSegment.export('/Users/mac/Downloads/speech_command/left/sample-1.wav', format='wav')

data_dir = "C:\\Users\\hyunsoo\\epowe\\sampledata"
# folder_names = os.listdir(data_dir)
# folder_names = [folder_name for folder_name in folder_names if not folder_name.startswith ('.')] #.DS_Store 제외
# for folder_name in folder_names:
#     print(folder_name) #left
#     file_names = os.listdir('{}/{}'.format(data_dir, folder_name))
#     file_names = [file_name for file_name in file_names if not file_name.startswith ('.')] #.DS_Store 제외
#     #file_names = file_names[:100] #데이터를 100개로 제한
#     for file_name in file_names:
# file_name = os.path.join(data_dir,'a.webm')
file_path = 'C:\\Users\\hyunsoo\\epowe\\sampledata\\a.webm'
# if file_name.endswith('webm'):
    # print(file_name) #/Users/mac/Downloads/speech_command/right/sample-1.wav
    # # file_path = '{}/{}/{}'.format(data_dir. file_name)
    # file_path = file_name
    # '''
    # audioSegment = AudioSegment.from_file(file_path, 'webm')
    # new_file_path = file_path.replace('webm', 'wav')
    # audioSegment.export(new_file_path, format='wav')
    # print(new_file_path)
    # '''
# audioSegment = AudioSegment.from_file(file_path, 'webm')
# chunk_length_ms = 1000 #1밀리 초
# chunks = make_chunks(audioSegment, chunk_length_ms)
# for i, chunk in enumerate(chunks):
#     if len(chunk) < 1000:
#         continue
#     new_file_path = file_path.replace('.webm', '-{0}.wav').format(i + 1)
#     chunk.export(new_file_path, format='wav')
#     print(new_file_path) #/Users/mac/Downloads/speech_command/right/sample-1-1.wav


# p = "C:\\Users\\hyunsoo\\epowe\\sampledata\\a.webm"

