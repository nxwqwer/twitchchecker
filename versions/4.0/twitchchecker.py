import datetime
import logging
import os
import re
import sys
import time
import tkinter.filedialog
try:
  import cv2
  cv_module = True
except ModuleNotFoundError:
  cv_module = False

class twitchchecker():

  ########## ########## 사용자 설정 ########## ##########
  def user_setting(self):
    self.location = 0                             # 0: 실행 위치 # 1: 프로그램 위치
    self.files = 0                                # 0: GUI # 1: 작업 경로 # 2: 하위 작업 경로 포함 # sys.argv 가 존재한다면 우선 실행
    self.log = 2                                  # 0: 출력만 # 1:단일 로그 # 2: 대상 파일별 로그 (log=2 인 경우, 기존에 온전한 로그파일이 있다면 자동으로 건너뜀)
    self.log1_name = "twitchchecker.txt"          # 단일 로그 파일명 (datetime 포멧을 사용하여 동적인 파일명으로 로깅가능, ex: %Y %m %d %H %M %S)
    self.log1_mode = "wt"                         # 단일 로그 파일 모드 (log1_name 이 정적인 경우 덮어쓸지 이어쓸지 여부, wt: 덮어쓰기 / at: 이어쓰기)
    self.log2_slug = ".txt"                       # 다중 로그 확장자

  ########## ########## 고급 설정 (특별한 목적이 있는게 아니라면 그대로 두는걸 권장) ########## ########## 
  def advanced_setting(self):
    self.location_force = ""                      # 강제 위치 지정
    self.files_slug = [".ts"]                     # 검사할 파일 확장자
    self.seg_pass = True                          # 세그먼트 파일 건너뛰기 옵션 (ex. 0.ts, 0-muted.ts, index-0000000000.ts)
    self.log2_force = False                       # 온전한 log2 파일이 있어도 강제로 검사 (로그 파일이 있더라도 재검사가 필요한 경우는 재검사하니 굳이 건들지 마세요)
    self.loop = False                             # 루프 옵션
    self.loop_delay = 60                          # 루프 딜레이 (loop가 True 이며 files가 1 또는 2 인 경우 해당 딜레이 이후 다시 실행)
    self.exitmessage = True                       # 검사 종료시 enter 메세지가 뜨게 할지 여부 (로그 파일만 남기는게 목적이라면 False로)
    self.utc = 9                                  # 시간 기준
    if len(sys.argv)>1: self.loop = False         # sys.argv 가 주어진 경우 loop 옵션을 비활성화 (주석으로 비활성화 가능)
    if len(sys.argv)>1: self.log = 2              # sys.argv 가 주어진 경우 log=2 를 활성화 (주석으로 비활성화 가능)
    if len(sys.argv)>1: self.exitmessage = False  # sys.argv 가 주어진 경우 종료 메세지 비활성화 (주석으로 비활성화 가능)
    if self.loop: self.log = 2                    # loop 가 활성화 된 경우 log=2 를 활성화 (주석으로 비활성화 가능)

  ########## ########## 참고사항 ########## ##########
  # 트위치 녹화 파일을 검사하는 프로그램입니다. (version:4.0)
  # 트위치 메타데이터가 손상되지 않은 원본 상태로 녹화된 ts 파일만 검사할 수 있습니다.
  # pip install opencv-python 명령어를 이용하여 cv2 모듈을 를 설치하는걸 권장드립니다.
  # 다만 cv2 모듈 설치에 어려움을 겪는 분들이 있어서 4.0에서는 cv2 모듈을 설치하지 않고도 작동할 수 있도록 수정했습니다.
  # cv2 모듈이 설치되지 않은 경우 화질 및 프레임 정보를 확인할 수 없으며, 시간과 관련된 정보들이 살짝 다를 수 있습니다.
  # log=2 옵션으로 이전에 온전히 작성된 로그가 있다면 이후 해당 파일 검사를 건너 뜁니다.
  # 여기서 온전히 작성된 로그란, 이전에 해당 파일을 검사했을때와 검사 파일 용량이 동일한 경우를 의미합니다.
  # 프로그램 관련 문의, 버그 제보, 개선 의견 등이 있다면 https://arca.live/b/nxwqwer 문의탭에 작성해주세요.

  ########## ########## 이 아래 부분은 건들지 마세요 ########## ########## 
  def system(self):
    self.dir_execution = os.getcwd()
    self.dir_program = os.path.dirname(__file__)
    self.once = not self.loop

  def title(self, message):
    if os.name=="nt":
      message = str(message).replace("^","^^").replace("&","^&")
      os.system(f"title {message}")

  def get_files(self):
    if len(sys.argv)>1:
      filenames = list(sys.argv[1:])
    elif self.files==0:
      filenames = list(tkinter.filedialog.askopenfilenames(initialdir="./",title="파일선택",filetypes=(("filtering"," ".join(map(lambda x:f"*{x}",self.files_slug))),("all files","*.*"))))
    elif self.files==1:
      filenames = list(filter(lambda a: any(list(map(lambda b:a.endswith(b),self.files_slug))),os.listdir("./")))
    elif self.files==2:
      filenames = sum(list(map(lambda a:list(map(lambda b:os.path.join(a[0],b),list(filter(lambda c:any(map(lambda d:c.endswith(d),self.files_slug)),a[2])))),os.walk("."))),list())
    if self.seg_pass:
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
    self.user_setting()
    self.advanced_setting()
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
        with open(filename,"rb") as fp:
          if not re.search("index-\d{10}.ts",str(fp.read(1880))):
            continue
          size = fp.seek(0,2)
          sizefmt = format(size,',')
        logname = filename[:filename.rfind(".")]+self.log2_slug
        if not self.log2_force and os.path.isfile(logname):
          with open(logname,"rt",encoding="utf8") as fp_log:
            fpdata = fp_log.read()
            if re.search(f"- 로딩완료 : {sizefmt}\/{sizefmt} \(100\.00%\)",fpdata) or re.search(f"- 에러발생 : [\d\,]*\/{sizefmt}",fpdata):
              logger.debug(f"* [pass] {os.path.basename(filename)} ({sizefmt})\n")
              continue
        try:
          if self.log==2:
            file_handler = logging.FileHandler(logname,"wt","utf8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            file_handler.terminator = ""
            logger.addHandler(file_handler)
          with open(filename,"rb") as fp:
            runcounter = time.perf_counter()
            self.title(f"[TwitchChecker] {os.path.basename(filename)}")
            segment = []
            index = []
            error = 0
            timestamp = None
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
                      timestamp = datetime.datetime.strptime(regex.group(),"%Y-%m-%dT%H:%M:%S")+datetime.timedelta(hours=self.utc)
                      segment.append({'index':int(packet[i+6:i+16]),'timestamp':timestamp})
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
        if self.exitmessage:
          input('press enter to exit')

if __name__=="__main__":
  twitchchecker()
