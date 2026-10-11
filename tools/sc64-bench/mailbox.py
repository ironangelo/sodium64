"""Decode the 64-byte physical USB diagnostic mailbox (host SRAM 0x03fe7f80)."""
from pathlib import Path
import argparse, json, struct

def decode(data):
    if len(data) != 64:
        raise ValueError('Expected exactly 64 mailbox bytes')
    words = struct.unpack('>16I', data)
    if words[0] != 0x53363452 or words[1] != 1:
        raise ValueError('No supported S64R mailbox signature')
    if sum(words) & 0xffffffff:
        raise ValueError('Mailbox checksum mismatch; partial or stale read')
    keys = ('magic', 'version', 'phase', 'present', 'transport_error', 'identifier',
            'render_frames', 'poll_calls', 'last_command', 'sc64_status', 'data0',
            'pi_status', 'count32', 'reserved0', 'reserved1', 'checksum')
    result = dict(zip(keys, words))
    result['identifier_hex'] = f'{words[5]:08x}'
    result['last_command_char'] = chr(words[8]) if 32 <= words[8] < 127 else None
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    a = p.parse_args()
    print(json.dumps(decode(a.input.read_bytes()), indent=2))
