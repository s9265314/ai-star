#encoding=utf-8
import speech_recognition as sr
import RPi.GPIO as GPIO
import pyaudio
import wave
import os
import sys
import jieba
#jieba.set_dictionary("/home/pi/dict.txt")
#print(''.join(jieba.cut("start",cut_all=False)))
# 隐藏错误消息，因为会有一堆ALSA和JACK错误消息，但其实能正常录音
#os.close(sys.stderr.fileno())

BUTT = 17   # 开始录音的按钮：一边接GPIO26，一边接地
GPIO.setmode(GPIO.BCM)
# 设GPIO26脚为输入脚，电平拉高，也就是说26脚一旦读到低电平，说明按了按钮
GPIO.setup(BUTT, GPIO.IN, pull_up_down = GPIO.PUD_UP)
# wav文件是由若干个CHUNK组成的，CHUNK我们就理解成数据包或者数据片段。
CHUNK = 16
FORMAT = pyaudio.paInt16  # pyaudio.paInt16表示我们使用量化位数 16位来进行录音
RATE = 44100  # 采样率 44.1k，每秒采样44100个点。
WAVE_OUTPUT_FILENAME = "user_speak.wav"

def rec_fun():

    print('press button...')
    GPIO.wait_for_edge(BUTT, GPIO.FALLING)

    # To use PyAudio, first instantiate PyAudio using pyaudio.PyAudio(), which sets up the portaudio system.
    p = pyaudio.PyAudio()
    stream = p.open(format = FORMAT,
                    channels = 1,    # cloud speecAPI只支持单声道
                    rate = RATE,
                    input = True,
                    frames_per_buffer = CHUNK)
    print("start recording...")
    os.system('play --no-show-progress --null --channels 1 synth %s sine %f' %(0.1,600))
    frames = []
    # 按住按钮录音，放开时结束
    while GPIO.input(BUTT) == 0:
        data = stream.read(CHUNK,exception_on_overflow = False)
        frames.append(data)
    #print("錄音完成，輸出文件：" + WAVE_OUTPUT_FILENAME + '\n')
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(FORMAT))    # Returns the size (in bytes) for the specified sample format.
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    #wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    return
def recognize_():
    r = sr.Recognizer()                        #預設辨識英文
    with sr.WavFile("user_speak.wav") as source:  #讀取wav檔
        audio = r.record(source)
    try:
        txt=r.recognize_google(audio,language="zh-TW")
        return txt
        #使用Google的服務
    except:
        print("Could not understand audio")
if __name__ == '__main__':
    rec_fun()
    txt = recognize_()
    try:
        print("Transcription: " + txt)
    except:
        pass