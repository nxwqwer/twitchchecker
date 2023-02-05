import cv2, datetime, os, re, time, tkinter.filedialog
os.chdir(os.path.dirname(__file__))
for filename in tkinter.filedialog.askopenfilenames(initialdir='./ts',title='파일선택',filetypes=(('ts files','*.ts'),('all files','*.*'))):
  try:
    print(f'* {os.path.basename(filename)}')
    runcounter = time.perf_counter()
    capture = cv2.VideoCapture(filename)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    hight = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(capture.get(cv2.CAP_PROP_FPS))
    capture.release()
    with open(filename,'rb') as fp:
      size=fp.seek(0,2)
      fp.seek(0,0)
      index=[]
      timestamp=None
      while packet:=fp.read(188):
        if packet[0]==71:
          if (packet[1]*256+packet[2])%8192==258 and (i:=packet.find(b'index-'))!=-1:
            index.append(int(packet[i+6:i+16]))
            print(f'\r- 로딩중   : {format(fp.tell(), ",")}/{format(size, ",")} ({fp.tell()*100/size:.2f}%)',end='')
            if not timestamp:
              if regex:=re.search('20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',str(packet)):
                timestamp = (datetime.datetime.strptime(regex.group(),'%Y-%m-%dT%H:%M:%S')+datetime.timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
          raise Exception('0x47')
      print(f'\r- 로딩완료 : {format(fp.tell(), ",")}/{format(size, ",")} ({fp.tell()*100/size:.2f}%)')
      if index:
        loss = [i for i in range(index[0],index[-1]+1) if i not in index]
        print(f"- 해상도   : {width}x{hight}p{fps}")
        print(f'- 추정시간 : {timestamp}')
        print(f"- 영상길이 : {datetime.timedelta(seconds=int(frame/fps))}")
        print(f'- 세그먼트 : {index[0]} ~ {index[-1]} ({index[-1]-index[0]+1})')
        print(f'- 손실률   : {len(loss)}/{index[-1]-index[0]+1} ({len(loss)*100/(index[-1]-index[0]+1):.2f}%)')
        print(f'- 손실값   : {loss}')
        print(f'- 런타임   : {time.perf_counter()-runcounter:.5f} sec')
  except KeyboardInterrupt:
    print()
    continue
  except Exception as exc:
    print(f"- 에러발생 : {exc}")
  finally:
    print()
input('* 엔터를 눌러 종료')