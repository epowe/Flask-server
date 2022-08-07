import sys
import os.path
import subprocess
import sys
import pandas as pd
import pydub


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