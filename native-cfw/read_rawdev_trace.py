"""Decode a bounded RAW Development diagnostic snapshot from the camera SD."""
from pathlib import Path
import argparse,json,struct

EVENTS={1:'selection',2:'preview_begin',3:'preview_end',4:'jpeg_request',5:'export_enrolled',
        6:'writer_no_match',7:'writer_matched',8:'job_released',9:'native_capture',10:'missing_job_export_rejected',11:'development_stopped',13:'user_selection'}
def decode(data):
    if len(data)%4 or len(data)<36:raise ValueError('Truncated trace')
    w=struct.unpack('<'+'I'*(len(data)//4),data)
    magic,version,total,n,mode,flags,index,depth=w[:8]
    if magic!=0x31544452 or version!=1 or n>32 or len(w)!=9+4*n:raise ValueError('Invalid trace header')
    checksum=0
    for value in w[:-1]:checksum^=value
    if checksum!=w[-1]:raise ValueError('Trace checksum mismatch')
    events=[]
    for event,a,b,c in struct.iter_unpack('<4I',data[32:-4]):
        row={'event':EVENTS.get(event,event),'a':hex(a),'b':hex(b),'c':hex(c)}
        if event==4:row.update(width=a>>16,height=a&65535,preview_depth=c>>16,flags=c&65535)
        if event==1:row.update(incoming_choice=a>>16,effective_choice=a&65535)
        if event==9:row.update(mode=a,model_state=c>>16,flags=c&65535)
        events.append(row)
    return dict(total_events=total,mode=mode,flags=flags,job=index,preview_depth=depth,events=events)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=Path);args=p.parse_args()
    print(json.dumps(decode(args.file.read_bytes()),indent=2))
