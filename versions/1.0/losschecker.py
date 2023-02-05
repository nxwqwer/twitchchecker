import datetime, os, re, time, tkinter.filedialog
os.chdir(os.path.dirname(__file__))

TIMEPARSE = '(20\d{2}).?(\d{2}).?(\d{2}).?(\d{2}).?(\d{2}).?(\d{2})'
SEGLENGTH = [2,4.167][0]

for filename in tkinter.filedialog.askopenfilenames(initialdir='./ts',title='파일선택',filetypes=(('ts files','*.ts'),('all files','*.*'))):
  try:
    timestamp=time.perf_counter()
    with open(filename,'rb') as fp:
      print(f'* {os.path.basename(fp.name)}')
      size=fp.seek(0,2)
      fp.seek(0,0)
      index=[]
      while packet:=fp.read(188):
        if packet[0]==71:
          if (packet[1]*256+packet[2])%8192==258:
            if (i:=packet.find(b'index-'))!=-1:
              index.append(int(packet[i+6:i+16]))
              print(f'\r> 로딩중  : {format(fp.tell(), ",")}/{format(size, ",")} ({fp.tell()*100/size:.2f}%)',end='')
        else:
          raise Exception('0x47')
      print(f'\r> 로딩완료 : {format(fp.tell(), ",")}/{format(size, ",")} ({fp.tell()*100/size:.2f}%)')
      if index:
        print(f'> 세그먼트 : {index[0]} ~ {index[-1]} ({index[-1]-index[0]+1})')
        if loss:=[i for i in range(index[0],index[-1]+1) if i not in index]:
          print(f'> 손실률   : {len(loss)}/{index[-1]-index[0]+1} ({len(loss)*100/(index[-1]-index[0]+1):.2f}%)')
          print(f'> 손실값   : {loss}')
        if regex:= re.search(TIMEPARSE, os.path.basename(fp.name)):
          init=datetime.datetime.strptime(''.join(regex.groups()),'%Y%m%d%H%M%S')
          print(f'> 녹화시작 : {init+datetime.timedelta(seconds=SEGLENGTH*0)}')
          if loss:
            print(f'> 최초로스 : {init+datetime.timedelta(seconds=SEGLENGTH*(loss[0]-index[0]))}')
            print(f'> 최종로스 : {init+datetime.timedelta(seconds=SEGLENGTH*(loss[-1]-index[0]))}')
          print(f'> 녹화종료 : {init+datetime.timedelta(seconds=SEGLENGTH*(index[-1]-index[0]))}')
        print(f'> 런타임   : {time.perf_counter()-timestamp:.5f} sec',end='\n\n')
  except KeyboardInterrupt:
    print(end='\n\n')
  except Exception as exc:
    print(f'> 에러     : {exc}',end='\n\n')
input('* 엔터를 눌러 종료')