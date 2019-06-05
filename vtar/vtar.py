import sys
import os, os.path
import struct
import argparse
import gzip

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

GZIP_MAGIC = '\037\213'


def parse_args():
    parser = argparse.ArgumentParser(description='Extracts VMware ESXi .vtar files')
    parser.add_argument('vtarfile', help='.vtar file')
    parser.add_argument('-C', '--directory', metavar='DIR', help='Change to directory DIR')

    # Actions
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument('-x', '--extract', action='store_true', help='Extract contents of vtarfile')
    # TODO: Create

    return parser.parse_args()


def main():
    args = parse_args()
    print args

    with open(args.vtarfile, 'rb') as raw_input_file:

        gzip_header = raw_input_file.read(2)
        raw_input_file.seek(0)
        f = raw_input_file

        if gzip_header == GZIP_MAGIC:
            print('Detected GZIP archive. For significant speed improvement decompress before running')
            f = gzip.GzipFile(fileobj=raw_input_file)

        if args.directory:
            os.chdir(args.directory)

        print 'pos         type offset   txtoff   txtsz    nfix size     name'
        
        # storage location when a longname is detected
        long_name=""
        while True:
            pos = f.tell()

            buf = f.read(vmtar.size)
            if len(buf) < vmtar.size:
                raise Exception('Short read at 0x{0:X}'.format(pos))

            obj = vmtar.unpack(buf)

            hdr_magic       = obj[9]
            
            # Most likely means we are at the end of the file. Or something went wrong
            if hdr_magic != 'visor ':
                break

            hdr_type        = obj[7]
            hdr_offset      = obj[16]
            hdr_textoffset  = obj[17]
            hdr_textsize    = obj[18]
            hdr_numfixuppgs = obj[19]
            hdr_size        = int(obj[4].rstrip('\0'), 8)
            hdr_name        = obj[0].rstrip('\0')

            print '0x{0:08X}  {1}    {2:08X} {3:08X} {4:08X} {5:04X} {6:08X} {7}'.format(
                pos, hdr_type, hdr_offset, hdr_textoffset, hdr_textsize, hdr_numfixuppgs, hdr_size, hdr_name)

            if not args.extract:
                continue

            if hdr_type == TAR_TYPE_DIR:
                try:
                    file_name = hdr_name
                    if long_name:
                        file_name = long_name
                        long_name = ""
                    os.mkdir(file_name)
                except OSError:
                    pass

            if hdr_type == TAR_TYPE_FILE:
                pos = f.tell()
                f.seek(hdr_offset, os.SEEK_SET)

                file_name = hdr_name
                if long_name:
                    file_name = long_name
                    long_name = ""

                blob = f.read(hdr_size)
                with open(file_name, 'wb') as outf:
                    outf.write(blob)

                f.seek(pos, os.SEEK_SET)

            if hdr_type == TAR_TYPE_GNU_LONGNAME:
                # Seek to the end of the current block
                f.seek(f.tell(), os.SEEK_SET)
                # Read the whole next block as the file name.
                long_name = f.read(vmtar.size).rstrip('\0')
                #@todo not sure this handles files whose name is greater than 1 block in length
                # Great explanation here: https://stackoverflow.com/a/2079165/429544


if __name__ == '__main__':
    sys.exit(main())
