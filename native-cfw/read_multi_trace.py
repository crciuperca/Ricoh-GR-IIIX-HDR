"""Read a camera MRSTATE.BIN snapshot. Requires only Python 3."""
from pathlib import Path
import argparse,json,struct,zlib

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=Path);args=p.parse_args()
    data=args.file.read_bytes()
    if len(data)!=704 or data[:4]!=b'MRT1':p.error('Not a Multi RAW state snapshot')
    words=struct.unpack('<176I',data)
    if zlib.crc32(data[:700])!=words[175]:p.error('Snapshot CRC mismatch')
    n=min(words[10],32)
    signed=lambda v:v-0x100000000 if v&0x80000000 else v
    result={'phase':{0:'closed',1:'configure',2:'processing',3:'finished',4:'error'}.get(words[1],words[1]),
            'error':signed(words[2]),'total':words[3],'current':words[4],'developed':words[5],
            'skipped':words[6],'pending':bool(words[7]),'loading':bool(words[8]),'JPEG_closed':bool(words[9]),
            'source':data[48:112].split(b'\0')[0].decode('ascii',errors='replace'),
            'destination':data[112:176].split(b'\0')[0].decode('ascii',errors='replace'),
            'events':[list(words[44+4*i:48+4*i]) for i in range(n)]}
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
