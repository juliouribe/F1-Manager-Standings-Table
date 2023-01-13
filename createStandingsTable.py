import argparse
import os
import zlib
import struct
import mmap

CHNUK1_NAME = "chunk1"
MAIN_DB_NAME = "main.db"
BACKUP_DB_NAME = "backup1.db"
BACKUP_DB2_NAME = "backup2.db"


def write_db(file_name, decompressed_db, _start, _end):
    with open(file_name, 'wb') as f:
        f.write(decompressed_db[_start:_end])


def unpack_save_file(input_path, result_path):
    with open(input_path, 'rb') as f:
        mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)

    # None None just before the packed DB Section.
    none_none_sig = b'\x00\x05\x00\x00\x00\x4E\x6F\x6E\x65\x00\x05\x00\x00\x00\x4E\x6F\x6E\x65\x00'

    db_section_off = mm.find(none_none_sig) + len(none_none_sig)
    db_section_off += 4  # Unk 4 Bytes

    # Part of the file that we ignore as it's not database
    # But we need it later to "pack" new save
    with open(os.path.join(result_path, CHNUK1_NAME), 'wb') as f:
        f.write(mm.read(db_section_off))

    zlib_sz = struct.unpack('i', mm.read(4))[0]

    databases = {
        os.path.join(result_path, MAIN_DB_NAME): struct.unpack('i', mm.read(4))[0],
        os.path.join(result_path, BACKUP_DB_NAME): struct.unpack('i', mm.read(4))[0],
        os.path.join(result_path, BACKUP_DB2_NAME): struct.unpack('i', mm.read(4))[0]
    }

    decompressed_dbs = zlib.decompress(mm.read())

    _start = 0
    for file_name, db_size in databases.items():
        # print(f'{file_name}:{db_size}')
        if db_size == 0:
            break
        write_db(file_name, decompressed_dbs, _start, _start + db_size)
        _start += db_size


def process_unpack(input_path, result_path):
    if not os.path.exists(input_path):
        print(f"Can't find {input_path}")
        return

    if not os.path.exists(result_path):
        os.makedirs(result_path)

    unpack_save_file(input_path, result_path)


def main(operation, input_path, result_path):
    # python script.py --operation unpack --input autosave.sav --result result
    if operation == "table":
        print("Creating table.")
    elif operation == "unpack":
        process_unpack(input_path, result_path)
    elif operation == "repack":
        print("Don't need this")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Repack F1 Manager 2022 Save Files.')
    parser.add_argument('--operation', help='Type of the operation.',
                        choices=["unpack", "repack"], required=True)
    parser.add_argument(
        '--input',
        help='Full path to the input file. (to savefile for unpack, or to directory for repack)',
        required=True
    )
    parser.add_argument(
        '--result',
        help='Full path to the result file. (to directory for unpack, or to file for repack)',
        required=True
    )
    args = parser.parse_args()
    main(args.operation, args.input, args.result)
