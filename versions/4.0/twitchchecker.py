import datetime
import logging
import os
import re
import time
import tkinter.filedialog
try:
  import cv2 ## pip install opencv-python
  cv_module = True
except ModuleNotFoundError:
  cv_module = False

class twitchchecker():

  def setting(self):
    self.location_force = ""                 # 강제 위치 지정
    self.location = 1                        # 0: 실행 위치 # 1: 프로그램 위치
    self.files = 2                           # 0: GUI # 1: 작업 경로 # 2: 하위 작업 경로 포함
    self.files_slug = [".ts",".mkv",".mp4"]  # 파일 확장자
    self.log = 2                             # 0: 출력만 # 1:단일 로그 # 2: 대상 파일별 로그
    self.log_force = False                   # 로그 강제 갱신
    self.log1_name = "twitchchecker.txt"     # 단일 로그 파일명 (datetime 포멧 사용가능)
    self.log1_mode = "wt"                    # 단일 로그 파일 모드 (wt/at)
    self.log2_slug = ".txt"                  # 다중 로그 확장자
    self.loop = False                        # 루프 옵션
    self.loop_delay = 60                     # 루프 딜레이 (files!=0)

  def system(self):
    self.dir_execution = os.getcwd()
    self.dir_program = os.path.dirname(__file__)
    self.once = not self.loop

  def title(self, message):
    if os.name=="nt":
      message = str(message).replace("^","^^").replace("&","^&")
      os.system(f"title {message}")

  def get_files(self):
    if self.files==0:
      return list(tkinter.filedialog.askopenfilenames(initialdir="./",title="파일선택",filetypes=(("filtering"," ".join(map(lambda x:f"*{x}",self.files_slug))),("all files","*.*"))))
    elif self.files==1:
      filenames = list(filter(lambda a: any(list(map(lambda b:a.endswith(b),self.files_slug))),os.listdir("./")))
    elif self.files==2:
      filenames = sum(list(map(lambda a:list(map(lambda b:os.path.join(a[0],b),list(filter(lambda c:any(map(lambda d:c.endswith(d),self.files_slug)),a[2])))),os.walk("."))),list())
    filenames = list(filter(lambda x:not re.fullmatch("\d*(-muted)?.ts",x.split("\\")[-1]),filenames))
    filenames = list(filter(lambda x:not re.fullmatch("index-\d{10}.ts",x.split("\\")[-1]),filenames))
    return filenames

  def bind_loss(self,loss):
    result = []
    tmp = []
    a = loss.pop(0)
    tmp.append(a)
    while loss:
      b = loss.pop(0)
      if a+1 != b:
        result.append(tmp)
        tmp = []
      tmp.append(b)
      a = b
    result.append(tmp)
    return result

  def segment_index(self,segment,index):
    for i in segment:
      if i['index']==index:
        return i

  def get_cv(self,filename):
    if cv_module:
      capture = cv2.VideoCapture(filename)
      width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
      hight = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
      frame = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
      fps = int(capture.get(cv2.CAP_PROP_FPS))
      capture.release()
      return (width,hight,frame,fps)

  def __init__(self):
    self.setting()
    self.system()
    if self.location_force:
      os.chdir(self.location_force)
    elif self.location==0:
      os.chdir(self.dir_execution)
    elif self.location==1:
      os.chdir(self.dir_program)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.terminator = ""
    logger.addHandler(stream_handler)
    while self.loop or self.once:
      self.once = False
      self.title("[TwitchChecker]")
      filenames = self.get_files()
      if self.files==0 and not filenames:
        break
      if self.log==1:
        file_handler = logging.FileHandler(datetime.datetime.now().strftime(self.log1_name),self.log1_mode,"utf8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        file_handler.terminator = ""
        logger.addHandler(file_handler)
      for filename in filenames:
        try:
          runcounter = time.perf_counter()
          with open(filename,"rb") as fp:
            if not re.search("index-\d{10}.ts",str(fp.read(1880))):
              continue
            size = fp.seek(0,2)
            sizefmt = format(size,",")
            logname = filename[:filename.rfind(".")]+self.log2_slug
            if not self.log_force:
              if os.path.isfile(logname):
                with open(logname,"rt",encoding="utf8") as fp_log:
                  if f"{sizefmt}/{sizefmt} (100.00%)" in fp_log.read():
                    continue
            self.title(f"[TwitchChecker] {os.path.basename(filename)}")
            fp.seek(0,0)
            segment = []
            index = []
            location = 0
            error = 0
            timestamp = None
            if self.log==2:
              file_handler = logging.FileHandler(logname,"wt","utf8")
              file_handler.setFormatter(formatter)
              file_handler.setLevel(logging.INFO)
              file_handler.terminator = ""
              logger.addHandler(file_handler)
            logger.info(f"* {os.path.basename(filename)}\n")
            while True:
              packet = fp.read(188)
              if packet:
                if packet[0]!=71:
                  error = fp.tell()
                  break
                pid = (packet[1]*256+packet[2])%8192
                if pid==258:
                  i = packet.find(b"index-")
                  if i!=-1:
                    index.append(int(packet[i+6:i+16]))
                    logger.debug(f"- 로딩중   : {format(fp.tell(),',')}/{format(size,',')} ({fp.tell()*100/size:.2f}%)\r")
                    regex = re.search("20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",str(packet))
                    if regex:
                      timestamp = datetime.datetime.strptime(regex.group(),"%Y-%m-%dT%H:%M:%S")+datetime.timedelta(hours=9)
                      segment.append({'index':int(packet[i+6:i+16]),'location':location,'timestamp':timestamp})
                  elif pid==0:
                    location = fp.tell()-188
              else:
                index = list(map(lambda x:x['index'],segment))
                loss = [i for i in range(segment[0]['index'],segment[-1]['index']+1) if i not in index]
                logger.info(f"- 로딩완료 : {format(fp.tell(),',')}/{format(size,',')} ({fp.tell()*100/size:.2f}%)\n")
                if cv_module:
                  width, hight, frame, fps = self.get_cv(filename)
                  logger.info(f"- 해상도   : {width}x{hight}p{fps}\n")
                  logger.info(f"- 영상길이 : {datetime.timedelta(seconds=int(frame/fps))}\n")
                  segtime = round((datetime.timedelta(seconds=int(frame/fps))/(index[-1]-index[0]+1)).total_seconds(),3)
                else:
                  logger.info(f"- 추정길이 : {segment[-1]['timestamp']-segment[0]['timestamp']}\n")
                  segtime = round((segment[-1]['timestamp']-segment[0]['timestamp']).total_seconds()/(index[-1]-index[0]+1),3)
                logger.info(f"- 최초시간 : {segment[0]['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
                logger.info(f"- 최후시간 : {segment[-1]['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
                logger.info(f"- 세그먼트 : {index[0]} ~ {index[-1]} ({index[-1]-index[0]+1})\n")
                logger.info(f"- 손실률   : {len(loss)}/{index[-1]-index[0]+1} ({len(loss)*100/(index[-1]-index[0]+1):.2f}%)\n")
                logger.info(f"- 손실값   : {loss}\n")
                if loss:
                  for n, los in enumerate(self.bind_loss(loss),1):
                    losa = self.segment_index(segment,los[0]-1)
                    losz = self.segment_index(segment,los[-1]+1)
                    logger.info(f"- 손실정보 : [#{n}] {len(los)} ({los[0]} / {(losa['timestamp']+datetime.timedelta(seconds=segtime))-segment[0]['timestamp']} / {(losa['timestamp']+datetime.timedelta(seconds=segtime)).strftime('%Y-%m-%dT%H:%M:%SZ')}) ~ ({los[-1]} / {losz['timestamp']-segment[0]['timestamp']} / {losz['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')})\n")
                logger.info(f"- 런타임   : {time.perf_counter()-runcounter:.2f} sec\n")
                break
            if error:
              error = format(fp.tell()-188,",")
              logger.info(f"- 에러발생 : {error}/{sizefmt} ({fp.tell()*100/size:.2f}%)\n")
        except KeyboardInterrupt:
          logger.debug(f"\n")
        except Exception as exc:
          logger.debug(f"- 에러발생 : ({exc}) \n")
        finally:
          if self.log==2:
            logger.removeHandler(file_handler)
          logger.info(f"\n")
          self.title("[TwitchChecker]")
      if self.loop:
        if self.files==0:
          input('press enter to continue')
          logger.debug('\n')
        else:
          logger.debug(f"* 루프 기다리는 중 ({self.loop_delay}초)\n\n")
          time.sleep(self.loop_delay)
      else:
        input('press enter to exit')

if __name__=="__main__":
  twitchchecker()
