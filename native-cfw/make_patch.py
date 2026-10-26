"""Generate a reproducible copy/literal delta from supplied stock and CFW files.

Content-defined chunks re-synchronize after firmware container offsets shift.
The resulting package requires the exact stock file; it is not a full firmware.
Only the Python standard library is used. No SD access or camera flashing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib
from patch import MAGIC, STOCK_SHA, CUSTOM_SHA

GEAR = tuple(int.from_bytes(hashlib.sha256(bytes([i])).digest()[:8], 'little') for i in range(256))


def chunks(data):
    begin, size = 0, len(data)
    while begin < size:
        end = min(begin + 2048, size)
        limit, rolling = min(begin + 65536, size), 0
        while end < limit:
            rolling = ((rolling << 1) + GEAR[data[end]]) & 0xffffffffffffffff
            end += 1
            if rolling & 8191 == 0:
                break
        yield begin, end
        begin = end


def generate(stock, custom):
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise ValueError('Not the pinned original firmware')
    if hashlib.sha256(custom).hexdigest() != CUSTOM_SHA:
        raise ValueError('Not the pinned current custom firmware')
    index = {}
    for start, end in chunks(stock):
        index.setdefault(hashlib.sha256(stock[start:end]).digest(), (start, end-start))
    ops = bytearray()
    literal, copy = bytearray(), None
    copied = inserted = 0
    for start, end in chunks(custom):
        block = custom[start:end]
        match = index.get(hashlib.sha256(block).digest())
        if match is not None and stock[match[0]:match[0]+match[1]] == block:
            if literal:
                ops.extend(b'\x01' + struct.pack('<I', len(literal)) + literal)
                literal.clear()
            if copy is not None and copy[0]+copy[1] == match[0]:
                copy = (copy[0], copy[1]+match[1])
            else:
                if copy is not None:
                    ops.extend(b'\x00' + struct.pack('<QI', *copy))
                copy = match
            copied += len(block)
        else:
            if copy is not None:
                ops.extend(b'\x00' + struct.pack('<QI', *copy))
                copy = None
            literal.extend(block)
            inserted += len(block)
    if copy is not None:
        ops.extend(b'\x00' + struct.pack('<QI', *copy))
    if literal:
        ops.extend(b'\x01' + struct.pack('<I', len(literal)) + literal)
    ops.append(255)
    meta = {'format': 1, 'target': 'Ricoh GR IIIx 1.60',
            'cfw_build': 'native-cfw-smooth-profiles-1',
            'stock_sha256': STOCK_SHA, 'custom_sha256': CUSTOM_SHA,
            'stock_bytes': len(stock), 'custom_bytes': len(custom),
            'copied_from_stock_bytes': copied, 'literal_bytes': inserted,
            'operations_bytes': len(ops), 'operations_sha256': hashlib.sha256(ops).hexdigest(),
            'profiles': ['Natural', 'Natural+', 'Natural++', 'IR', 'Green', 'UV',
                         'Provia', 'Provia+', 'Provia++'],
            'features': ['Natural recalibrated from R0010752', 'Smoothed monotone tone curves for all six Natural and Provia profiles', 'Original Ricoh profiles retained',
                         'RAW+JPG HDR with full-resolution gain map and bounded adaptive compression', 'sRGB and Display P3',
                         'Custom P3/HDR and all nine profile icons', 'ADJ RAW+JPG HDR selection',
                         'HDR/P3 selections persisted in native active settings',
                         'RAW Development P3 and HDR P3 JPEG exports',
                         'Preview-isolated RAW export selection and bounded RDTRACE diagnostics',
                         'RAW selection survives native Adobe reload and shared processing callbacks',
                         'Multi RAW Development with latest-RAW recipe UI, sequential exports and X/Y progress',
                         'On-card RAW queue and alternating CRC-protected completion and recipe records',
                         'Resume remaining RAWs; regenerate deleted developed JPEGs'],
            'runtime_dependency': 'Python 3 standard library only'}
    header = json.dumps(meta, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return MAGIC + struct.pack('<I', len(header)) + header + zlib.compress(ops, 9), meta


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', required=True, type=Path)
    p.add_argument('--custom', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error('Output exists; choose a fresh path')
    package, meta = generate(args.stock.read_bytes(), args.custom.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as out:
        out.write(package)
    print(json.dumps({'package': str(args.output), 'package_bytes': len(package),
                      'package_sha256': hashlib.sha256(package).hexdigest(), **meta}, indent=2))


if __name__ == '__main__':
    main()
