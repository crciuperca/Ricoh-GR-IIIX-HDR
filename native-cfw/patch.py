"""Apply the pinned current CFW delta using only Python's standard library.

Never downloads firmware, flashes a camera, or overwrites an existing file.
The complete stock input and completed output must match their pinned SHA256.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import zlib

if sys.version_info < (3, 8):
    sys.exit('CFW patcher requires Python 3.8 or newer.')

MAGIC = b'GRCFWP1\n'
STOCK_SHA = '708e79f3b7b96a7e1581b4acf4c412233050a1832718ef7f06c8397db1b431c7'
CUSTOM_SHA = '6415d116b0bd6ac95fc538c08d8abbbb860832d3b176b9587b8326ff06341878'
PACKAGE = Path(__file__).resolve().parent / 'patches' / 'gr3x-160-profile-icons.cfwpatch'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_package(path=PACKAGE):
    data = path.read_bytes()
    if not data.startswith(MAGIC) or len(data) < 12:
        raise ValueError('Invalid CFW patch package')
    n = struct.unpack_from('<I', data, len(MAGIC))[0]
    at = len(MAGIC) + 4
    if not 2 <= n <= 65536 or at + n >= len(data):
        raise ValueError('Invalid patch header length')
    meta = json.loads(data[at:at+n].decode('utf-8'))
    if (meta.get('format') != 1 or meta.get('stock_sha256') != STOCK_SHA
            or meta.get('custom_sha256') != CUSTOM_SHA):
        raise ValueError('Package does not describe this pinned CFW version')
    for key in ('stock_bytes', 'custom_bytes', 'operations_bytes'):
        if type(meta.get(key)) is not int or not 0 < meta[key] <= 128 * 1024 * 1024:
            raise ValueError('Invalid package size: ' + key)
    decoder = zlib.decompressobj()
    ops = decoder.decompress(data[at+n:], meta['operations_bytes'] + 1)
    if (len(ops) != meta['operations_bytes'] or not decoder.eof
            or decoder.unconsumed_tail or decoder.unused_data
            or hashlib.sha256(ops).hexdigest() != meta.get('operations_sha256')):
        raise ValueError('Corrupt or truncated patch operations')
    return meta, ops


def write_firmware(source, dest, meta, ops):
    """Write validated copy/literal operations to an already owned temp file."""
    at = total = 0
    sha = hashlib.sha256()
    while at < len(ops):
        opcode = ops[at]
        at += 1
        if opcode == 255:
            if at != len(ops) or total != meta['custom_bytes']:
                raise ValueError('Invalid patch end/size')
            if sha.hexdigest() != CUSTOM_SHA:
                raise ValueError('Output firmware SHA256 mismatch; output not published')
            return
        if opcode == 0:
            if at + 12 > len(ops):
                raise ValueError('Truncated copy operation')
            offset, size = struct.unpack_from('<QI', ops, at)
            at += 12
            if size == 0 or offset + size > meta['stock_bytes']:
                raise ValueError('Copy extends beyond stock firmware')
            source.seek(offset)
        elif opcode == 1:
            if at + 4 > len(ops):
                raise ValueError('Truncated literal size')
            size = struct.unpack_from('<I', ops, at)[0]
            at += 4
            if size == 0 or at + size > len(ops):
                raise ValueError('Invalid literal bounds')
        else:
            raise ValueError('Unknown patch operation')
        if total + size > meta['custom_bytes']:
            raise ValueError('Operation exceeds output size')
        remaining = size
        while remaining:
            take = min(remaining, 1024 * 1024)
            if opcode == 0:
                block = source.read(take)
                if len(block) != take:
                    raise ValueError('Stock firmware changed or was truncated')
            else:
                block = ops[at:at+take]
                at += take
            dest.write(block)
            sha.update(block)
            remaining -= take
        total += size
    raise ValueError('Missing patch end marker')


def apply(source, output, package=PACKAGE):
    source, output = source.resolve(strict=True), output.absolute()
    meta, ops = load_package(package)
    if source == output.resolve():
        raise ValueError('Output must not be the input firmware')
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; choose another --output path: ' + str(output))
    if source.stat().st_size != meta['stock_bytes'] or digest(source) != STOCK_SHA:
        raise ValueError('Wrong firmware. Only original Ricoh GR IIIx 1.60 is accepted.\n'
                         'Required SHA256: ' + STOCK_SHA)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with source.open('rb') as src, tempfile.NamedTemporaryFile(
                mode='wb', dir=str(output.parent), prefix='.' + output.name + '.',
                suffix='.partial', delete=False) as dst:
            temporary = Path(dst.name)
            write_firmware(src, dst, meta, ops)
        if digest(temporary) != CUSTOM_SHA:
            raise ValueError('Temporary output readback mismatch')
        # Exclusive creation prevents replacing an existing file, even if it
        # appeared after the initial check. Works on FAT/exFAT as well as NTFS.
        published = False
        try:
            with output.open('xb') as dst, temporary.open('rb') as src:
                published = True
                shutil.copyfileobj(src, dst, 1024 * 1024)
            if digest(output) != CUSTOM_SHA:
                raise ValueError('Published output readback mismatch')
        except BaseException:
            if published:
                output.unlink()
            raise
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('firmware', nargs='?', type=Path, help='Original GR IIIx 1.60 .bin')
    parser.add_argument('-o', '--output', type=Path,
                        help='New output file; default: INPUT_FOLDER/custom-firmware/fwdc243b.bin')
    parser.add_argument('--info', action='store_true', help='Show pinned CFW details without writing files')
    args = parser.parse_args(argv)
    try:
        if args.info:
            meta, _ = load_package()
            print(json.dumps(meta, indent=2))
            return 0
        if args.firmware is None:
            parser.error('the stock firmware path is required')
        output = args.output or args.firmware.absolute().parent / 'custom-firmware' / 'fwdc243b.bin'
        result = apply(args.firmware, output)
        print('Created: ' + str(result))
        print('SHA256 verified: ' + CUSTOM_SHA)
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error, zlib.error) as exc:
        print('CFW patcher: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
