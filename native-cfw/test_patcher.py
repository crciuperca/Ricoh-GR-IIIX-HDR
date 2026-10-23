"""Real-firmware smoke and failure tests for the standard-library delta patcher."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import struct
import tempfile
import zlib
from patch import apply, load_package, PACKAGE, MAGIC, STOCK_SHA, CUSTOM_SHA


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stock', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    assert hashlib.sha256(args.stock.read_bytes()).hexdigest() == STOCK_SHA
    args.out.mkdir(parents=True, exist_ok=True)
    cases = []
    with tempfile.TemporaryDirectory(prefix='patch tests with spaces ', dir=args.out) as folder:
        root = Path(folder)
        source = root / 'original firmware.bin'
        source.write_bytes(args.stock.read_bytes())
        output = root / 'output with spaces' / 'fwdc243b.bin'
        apply(source, output)
        assert hashlib.sha256(output.read_bytes()).hexdigest() == CUSTOM_SHA
        assert hashlib.sha256(source.read_bytes()).hexdigest() == STOCK_SHA
        cases.append('Exact current CFW produced; source unchanged; spaces in paths')
        for wrong_output in (output, source):
            before = wrong_output.read_bytes()
            try:
                apply(source, wrong_output)
                raise AssertionError('Existing output was accepted')
            except ValueError:
                pass
            assert wrong_output.read_bytes() == before
        cases.append('Existing output and same input/output refused without changes')
        wrong = root / 'wrong firmware.bin'
        wrong.write_bytes(b'not Ricoh firmware')
        try:
            apply(wrong, root / 'must-not-exist.bin')
            raise AssertionError('Wrong firmware accepted')
        except ValueError:
            pass
        assert not (root / 'must-not-exist.bin').exists()
        cases.append('Wrong firmware rejected before output creation')
        original = PACKAGE.read_bytes()
        for i, bad in enumerate((original[:-1], b'bad magic' + original[9:], original[:100])):
            path = root / ('corrupt-' + str(i) + '.cfwpatch')
            path.write_bytes(bad)
            try:
                apply(source, root / 'corrupt-output.bin', path)
                raise AssertionError('Corrupt package accepted')
            except (ValueError, zlib.error):
                pass
            assert not (root / 'corrupt-output.bin').exists()
        cases.append('Truncated data, invalid magic and truncated header rejected')
        # Preserve valid zlib and operation hashes while damaging a literal.
        # The pinned final firmware hash must reject this before publication.
        meta, operations = load_package()
        bad = bytearray(operations)
        at = 0
        while bad[at] == 0:
            at += 13
        assert bad[at] == 1
        bad[at+5] ^= 1
        meta['operations_sha256'] = hashlib.sha256(bad).hexdigest()
        header = json.dumps(meta).encode()
        corrupt = root / 'valid-container-wrong-output.cfwpatch'
        corrupt.write_bytes(MAGIC + struct.pack('<I', len(header)) + header + zlib.compress(bad))
        dest = root / 'partial-cleanup' / 'result.bin'
        try:
            apply(source, dest, corrupt)
            raise AssertionError('Incorrect final firmware accepted')
        except ValueError:
            pass
        assert not dest.exists() and not list(dest.parent.glob('*.partial'))
        assert not list(dest.parent.iterdir())
        cases.append('Final hash mismatch rejects publication and cleans temporary data')
    report = {'status': 'pass', 'cases': cases, 'expected_CFW_sha256': CUSTOM_SHA,
              'standard_library_only': True, 'no_card_access': True}
    (args.out / 'core-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
