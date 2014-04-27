import sys
import os, os.path
import struct

# http://encode.ru/threads/1400-VMware-tar-modification?p=27025


vmtar = struct.Struct('<'
    '100s'      # [0]  0x000 name
    '8s'        # [1]  0x064 mode
    '8s'        # [2]  0x06C uid
    '8s'        # [3]  0x074 gid
    '12s'       # [4]  0x07C size
    '12s'       # [5]  0x088 mtime
    '8s'        # [6]  0x094 chksum
    'c'         # [7]  0x09C type
    '100s'      # [8]  0x09D linkname
    '6s'        # [9]  0x101 magic
    '2s'        # [10] 0x107 version
    '32s'       # [11] 0x109 uname
    '32s'       # [12] 0x129 gname
    '8s'        # [13] 0x149 devmajor
    '8s'        # [14] 0x151 devminor
    '151s'      # [15] 0x159 prefix
    'I'         # [16] 0x1F0 offset
    'I'         # [17] 0x1F4 textoffset
    'I'         # [18] 0x1F8 textsize
    'I'         # [19] 0x1FC numfixuppgs
)               #      0x200 (total size)

TAR_TYPE_FILE         = '0'
TAR_TYPE_LINK         = '1'
TAR_TYPE_SYMLINK      = '2'
TAR_TYPE_CHARDEV      = '3'
TAR_TYPE_BLOCKDEV     = '4'
TAR_TYPE_DIR          = '5'
TAR_TYPE_FIFO         = '6'
TAR_TYPE_SHAREDFILE   = '7'
TAR_TYPE_GNU_LONGLINK = 'K'
TAR_TYPE_GNU_LONGNAME = 'L'

def main():
    if len(sys.argv) < 2:
        print 'Usage: {0} xxx.vtar'.format(os.path.basename(sys.argv[0]))
        return 1
        
    extract = True
        
    with open(sys.argv[1], 'rb') as f:
    
        print 'pos         type offset   txtoff   txtsz    nfix size     name'
    
        while True:
            pos = f.tell()
            
            buf = f.read(vmtar.size)
            if len(buf) < vmtar.size:
                raise Exception('Short read at 0x{0:X}'.format(pos))
            
            obj = vmtar.unpack(buf)
            
            hdr_magic       = obj[9]
            if hdr_magic != 'visor ': break
            
            hdr_type        = obj[7]
            hdr_offset      = obj[16]
            hdr_textoffset  = obj[17]
            hdr_textsize    = obj[18]
            hdr_numfixuppgs = obj[19]
            hdr_size        = int(obj[4].rstrip('\0'), 8)
            hdr_name        = obj[0].rstrip('\0')
            
            print '0x{0:08X}  {1}    {2:08X} {3:08X} {4:08X} {5:04X} {6:08X} {7}'.format(
                pos, hdr_type, hdr_offset, hdr_textoffset, hdr_textsize, hdr_numfixuppgs, hdr_size, hdr_name)
                
            if not extract: continue
            
            if hdr_type == TAR_TYPE_DIR:
                try:
                    os.mkdir(hdr_name)
                except OSError:
                    pass
            
            if hdr_type == TAR_TYPE_FILE:
                pos = f.tell()
                f.seek(hdr_offset, os.SEEK_SET)
                
                blob = f.read(hdr_size)
                with open(hdr_name, 'wb') as outf:
                    outf.write(blob)
                
                f.seek(pos, os.SEEK_SET)


if __name__ == '__main__':
    sys.exit(main())
    
    
# http://nishi.dreamhosters.com/u/vmtar_1.rar
# vmtar2shar.cpp
'''

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#pragma pack(1)

typedef unsigned short word;
typedef unsigned int   uint;
typedef unsigned char  byte;
typedef unsigned long long qword;

enum {
TAR_TYPE_FILE         = '0',
TAR_TYPE_LINK         = '1',
TAR_TYPE_SYMLINK      = '2',
TAR_TYPE_CHARDEV      = '3',
TAR_TYPE_BLOCKDEV     = '4',
TAR_TYPE_DIR          = '5',
TAR_TYPE_FIFO         = '6',
TAR_TYPE_SHAREDFILE   = '7',
TAR_TYPE_GNU_LONGLINK = 'K',
TAR_TYPE_GNU_LONGNAME = 'L'
};

uint oct2bin( char* s, uint l ) {
  uint c, i, x = 0;
  for( i=0; i<l; i++ ) {
    c = s[i]; if( (c>='0') && (c<='7') ); else break;
    (x<<=3) += c - '0';
  }
  return x;
} 

template< int N > uint oct2bin( char (&s)[N] ) { return oct2bin( s, N ); }

struct vmtar {

  char name[100];
  char mode[8];
  char uid[8];

  char gid[8];
  char size[12];
  char mtime[12];
  char chksum[8];
  char type;
  char linkname[100];

  char magic[6];
  char version[2];

  char uname[32];
  char gname[32];

  char devmajor[8];
  char devminor[8];

  char prefix[151];

  uint offset;
  uint textoffset;
  uint textsize;
  uint numfixuppgs;

/*
      obj = cls(StrFromNTS(buf[:100]))
      obj.mode = int(StrFromNTS(buf[100:108]) or "0", 8)
      obj.uid = int(StrFromNTS(buf[108:116]) or "0", 8)
      obj.gid = int(StrFromNTS(buf[116:124]) or "0", 8)
      obj.size = int(StrFromNTS(buf[124:136]) or "0", 8)
      obj.mtime = int(StrFromNTS(buf[136:148]) or "0", 8)
      chksum = int(StrFromNTS(buf[148:156]), 8)
      obj.type = buf[156]
      obj.linkname = StrFromNTS(buf[157:257])
      magic = buf[257:263]
      version = buf[263:265] # Unused, apparently.
      obj.uname = StrFromNTS(buf[265-297])
      obj.gname = StrFromNTS(buf[297-329])
      obj.devmajor = int(StrFromNTS(buf[329:337]) or "0", 8)
      obj.devminor = int(StrFromNTS(buf[337:345]) or "0", 8)

      obj.prefix = buf[345-496]
      obj.offset = struct.unpack("<I", buf[496:500])[0]
      obj.textoffset = struct.unpack("<I", buf[500:504])[0]
      obj.textsize = struct.unpack("<I", buf[504:508])[0]
      obj.numfixuppgs = struct.unpack("<I", buf[508:512])[0]
*/

};


vmtar hdr;

enum{ bufsize=1<<16 };
byte buf[bufsize];

int main( int argc, char** argv ) {

  FILE* f = fopen( argv[1], "rb" ); if( f==0 ) return 1;
  FILE* g = fopen( argv[2], "wb" ); if( g==0 ) g=fopen("nul","wb");

  while(1) {
uint pos = ftell(f);
    hdr.magic[0]=0;
    fread( &hdr, 1,sizeof(hdr), f );
    if( strncmp(hdr.magic,"visor ",6)!=0 ) break;

    printf( "%08X <%c> %X %X %X %X %X [%s]\n", pos, hdr.type, hdr.offset, hdr.textoffset, hdr.textsize, hdr.numfixuppgs, oct2bin(hdr.size), hdr.name );

    if( hdr.type==TAR_TYPE_SHAREDFILE ) hdr.type=TAR_TYPE_FILE;

    if( (hdr.type==TAR_TYPE_DIR) || (hdr.type==TAR_TYPE_FILE) ) {
      putc( (hdr.type==TAR_TYPE_DIR)?'D':'F', g );
      uint i,n,l = strlen(hdr.name);
      fwrite( &l, 1,2, g );
      for( i=0; i<l; i++ ) if( hdr.name[i]=='/' ) hdr.name[i]='\\';
      fwrite( hdr.name, 1,l, g );
      if( hdr.type==TAR_TYPE_FILE ) {
        n = oct2bin(hdr.size);
        uint pos = ftell(f);
        fseek(f,hdr.offset,SEEK_SET);
        fwrite( &n, 1,4, g ); i=0; fwrite( &i, 1,4, g );
        for( i=0; i<n; i+=l ) {
          l = n-i; if( l>bufsize ) l=bufsize;
          fread( buf, 1,l, f );
          fwrite( buf,1,l, g );
        }
        fseek( f, pos, SEEK_SET );
      }
    }
  }

}


'''