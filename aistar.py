from button_gcp import*
from jieba_pos import*
import jieba
import subprocess
import multiprocessing
import os, random ,time ,sys
os.system("amixer set PCM -- 100%")
case=0
def play_wav(file):
    os.system("aplay "+file)
def user_f(user_txt):
    uf_class,feel_seq,list1=jieba_pos(user_txt)
    try:
            uf_class = adv(uf_class,feel_seq,list1)
    except:
            pass
    return uf_class
def user_speak2txt():
    rec_fun()
    txt=recognize_()
    return txt
#play_wav("command.wav")
def play(uf_c):
    files=os.listdir('.'+path)
    file=random.choice(files)
    play_wav(file)
    print("playing",file)
def num2feel(uf_c):
    n2f={
        0:'happy',
        1:'afraid',
        2:'sad',
        3:'angry'
        }
    feel=n2f[uf_c]
    return feel
def play_story(uf_c):
    feel = num2feel(uf_c)
    story_path="/home/pi/Desktop/EHowNetAPI/story/"+str(feel)
    files=os.listdir(story_path)
    file=story_path+"/"+random.choice(files)
    play_wav(file)
    #print(file)
def main():
    txt = user_speak2txt()
    return txt
def choose(case_n,msg=None):
    case = {
        0:case0,
        1:case1,
        2:understand
        }
    function = case.get(case_n)
    if function:
        n_case=function(msg)
    return n_case
        
def case0(msg):
    return 0
def case1(uf_c):
    if uf_c == None:
        return 2
    else:
        play_story(uf_c)
        return 0
def understand(msg):
    play_wav("/home/pi/Desktop/EHowNetAPI/wav/understand.wav")
    return 0
i=0
uf_c=-1
print("".join(jieba.cut("你好", cut_all=False)))
play_wav("/home/pi/Desktop/EHowNetAPI/wav/start_music.wav")
play_wav("/home/pi/Desktop/EHowNetAPI/wav/hello.wav")
while 1:
    i += 1
    print("loop",i)
    if case == 0:
        play_wav("/home/pi/Desktop/EHowNetAPI/wav/today.wav")
        user_ans = user_speak2txt()
        uf_c = user_f(user_ans)
        print(user_ans,uf_c,case)
        case = 1
    if "休息" == user_ans:
        print("true")
        while 1:
            user_ans = user_speak2txt()
            print(user_ans)
            if "關機" == user_ans:
                os.system('play --no-show-progress --null --channels 1 synth %s sine %f' %(0.1,1200))
                subprocess.call(['shutdown','-h','now'],shell=False)
            if "取消" == user_ans:
                case = 0
                break
    case = choose(case,uf_c)
print("end")
