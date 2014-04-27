/*
 * vmtar2shar.cpp
 * http://encode.ru/threads/1400-VMware-tar-modification?p=27025
 * http://nishi.dreamhosters.com/u/vmtar_1.rar
 */
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


