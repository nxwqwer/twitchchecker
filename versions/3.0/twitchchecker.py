#!/usr/bin/env python
#-*- coding: utf-8 -*-
import cv2, datetime, logging, os, re, time, tkinter.filedialog

GUI = 1   # 0:Disable / 1:Enable
LOG = 0   # 0:Disable / 1:Log / 2:Logs

os.chdir(os.path.dirname(__file__))
if os.name=="nt":  os.system("title [twitchchecker]")
filenames = tkinter.filedialog.askopenfilenames(initialdir="./ts",title="파일선택",filetypes=(("ts files","*.ts"),("all files","*.*"))) if GUI else filter(lambda x: x.endswith(".ts"), os.listdir("./"))
if not filenames: exit()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
stream_handler.terminator = ""
logger.addHandler(stream_handler)
if LOG==1:
  file_handler = logging.FileHandler(datetime.datetime.now().strftime(f"twitchchecker.txt"),"wt","utf8")
  file_handler.setFormatter(formatter)
  file_handler.setLevel(logging.INFO)
  file_handler.terminator = ""
  logger.addHandler(file_handler)
for filename in filenames:
  if LOG==2:
    file_handler = logging.FileHandler(f"{os.path.abspath(filename[:filename.rfind('.')])}.txt","wt","utf8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    file_handler.terminator = ""
    logger.addHandler(file_handler)
  try:
    logger.info(f"* {os.path.basename(filename)}\n")
    if os.name=="nt": os.system(f"title [twitchchecker] {os.path.basename(filename)}\n")
    runcounter = time.perf_counter()
    capture = cv2.VideoCapture(filename)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    hight = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(capture.get(cv2.CAP_PROP_FPS))
    capture.release()
    with open(filename,"rb") as fp:
      if fp.read(1)!=b'G':
        raise Exception("Invalid File")
      size = fp.seek(0,2)
      fp.seek(0,0)
      index = []
      timestamp = None
      while packet:=fp.read(188):
        if packet[0]==71:
          if (packet[1]*256+packet[2])%8192==258 and (i:=packet.find(b"index-"))!=-1:
            index.append(int(packet[i+6:i+16]))
            logger.debug(f"- 로딩중   : {format(fp.tell(),',')}/{format(size,',')} ({fp.tell()*100/size:.2f}%)\r")
            if regex:=re.search("20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",str(packet)):
              if not timestamp:
                timestamp = datetime.datetime.strptime(regex.group(),"%Y-%m-%dT%H:%M:%S")+datetime.timedelta(hours=9)
              laststamp = datetime.datetime.strptime(regex.group(),"%Y-%m-%dT%H:%M:%S")+datetime.timedelta(hours=9)
        else:
          raise Exception(f"0x47|- 로딩중   : {format(fp.tell()-188,',')}/{format(size,',')} ({fp.tell()*100/size:.2f}%)\n")
      logger.info(f"- 로딩완료 : {format(fp.tell(),',')}/{format(size,',')} ({fp.tell()*100/size:.2f}%)\n")
      if index:
        loss = [i for i in range(index[0],index[-1]+1) if i not in index]
        logger.info(f"- 해상도   : {width}x{hight}p{fps}\n")
        logger.info(f"- 영상길이 : {datetime.timedelta(seconds=int(frame/fps))}\n")
        logger.info(f"- 최초시간 : {timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
        logger.info(f"- 최후시간 : {laststamp.strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
        logger.info(f"- 세그먼트 : {index[0]} ~ {index[-1]} ({index[-1]-index[0]+1})\n")
        logger.info(f"- 손실률   : {len(loss)}/{index[-1]-index[0]+1} ({len(loss)*100/(index[-1]-index[0]+1):.2f}%)\n")
        logger.info(f"- 손실값   : {loss}\n")
        logger.info(f"- 런타임   : {time.perf_counter()-runcounter:.2f} sec\n")
  except KeyboardInterrupt:
    logger.debug(f"\n")
  except Exception as exc:
    if str(exc)=="Invalid File":
      logger.info(f"- 에러발생 : ts파일이 아닙니다.\n")
    elif str(exc).startswith("0x47"):
      logger.info(str(exc).split('|')[1])
      logger.info(f"- 에러발생 : 0x47\n")
    else:
      logger.info(f"- 에러발생 : {exc}\n")
  finally:
    if LOG==2:
      logger.removeHandler(file_handler)
    logger.info(f"\n")
if os.name=="nt": os.system("title [twitchchecker]")
input("* 엔터를 눌러 종료")