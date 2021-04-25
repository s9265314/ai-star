import sys
sys.path.append("../EHowNetAPI")
import math
import string
import time
from ehownet_python3 import *
#import win32api
#encoding=utf-8
import jieba
jieba.set_dictionary("/home/pi/Desktop/dict.txt")
tree=EHowNetTree("/home/pi/Desktop/EHowNetAPI/db/ehownet_ontology.sqlite")

#0=開心 1= 害怕 2= 傷心 3= 生氣
def jieba_pos(txt):
        success = 1
        try:
            list1 = list(jieba.cut(txt, cut_all=False))
        #print(list1)
        except:
            success = 0
        if success == 1:
            for feel_seq,pos in enumerate(list1):
                    uf_class=None
                    if pos == "好":
                            pos = None
                    try:
                            user_feel = tree.searchWord(pos)[0].ehownet.strip('{ }')
                            uf_class=get_feel_num(user_feel)
                    except:
                            pass
                    #print("USER_FEEL:",user_feel,"POS:",pos,"FEEL_SEQ",feel_seq)
                    if uf_class != None :
                            return uf_class,feel_seq,list1
        return None,None,None
def adv(uf_class,f_seq,txt_pos):
        if f_seq == 0:
                return uf_class
        else:
                if txt_pos[f_seq-1] == "不":
                        if uf_class == 0:
                                return 3
        return uf_class

def get_feel_num(feel):
        feel_dict=[['GoodFeeling|好情', 'joyful|喜悅', 'FondOf|喜歡'],
                   ['fear|害怕','uneasy|不安'],
                   ['sorrowful|悲哀','disappointed|失望'],
                   ['disgust|厭惡','angry|生氣']]
        #uf_n =user feel class, feel_dict :使用者精確情緒
        for uf_n,uf in enumerate(feel_dict):
                for i in uf:
                        #print("uf_n:",uf_n,"feel_dict:",i)
                        if i in feel:
                                return(uf_n)
if __name__ == '__main__':
    txt0 = "今天我很難過因為今天一直打雷"
    txt1 = "今天打lol一直輸好傷心"
    uf_class,feel_seq,list1=jieba_pos("我今天好暴怒")
    print("情緒",uf_class,"位置",feel_seq,"\n",list1)
    try:
            uf_class = adv(uf_class,feel_seq,list1)
    except:
            pass
    print("情緒",uf_class,"位置",feel_seq)
