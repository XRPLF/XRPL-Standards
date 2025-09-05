def encodeCTID(ledger_seq, txn_index, network_id):
    if not isinstance(ledger_seq, int):
        raise ValueError("ledger_seq must be a number.")
    if ledger_seq > 0xFFFFFFF or ledger_seq < 0:
        raise ValueError("ledger_seq must not be greater than 268435455 or less than 0.")

    if not isinstance(txn_index, int):
        raise ValueError("txn_index must be a number.")
    if txn_index > 0xFFFF or txn_index < 0:
        raise ValueError("txn_index must not be greater than 65535 or less than 0.")

    if not isinstance(network_id, int):
        raise ValueError("network_id must be a number.")
    if network_id > 0xFFFF or network_id < 0:
        raise ValueError("network_id must not be greater than 65535 or less than 0.")

    ctid_value = ((0xC0000000 + ledger_seq) << 32) + (txn_index << 16) + network_id
    return format(ctid_value, 'x').upper()

def decodeCTID(ctid):
    if isinstance(ctid, str):
        if not ctid.isalnum():
            raise ValueError("ctid must be a hexadecimal string or BigInt")

        if len(ctid) != 16:
            raise ValueError("ctid must be exactly 16 nibbles and start with a C")

        ctid_value = int(ctid, 16)
    elif isinstance(ctid, int):
        ctid_value = ctid
    else:
        raise ValueError("ctid must be a hexadecimal string or BigInt")

    if ctid_value > 0xFFFFFFFFFFFFFFFF or ctid_value & 0xF000000000000000 != 0xC000000000000000:
        raise ValueError("ctid must be exactly 16 nibbles and start with a C")

    ledger_seq = (ctid_value >> 32) & 0xFFFFFFF
    txn_index = (ctid_value >> 16) & 0xFFFF
    network_id = ctid_value & 0xFFFF
    return {
        'ledger_seq': ledger_seq,
        'txn_index': txn_index,
        'network_id': network_id
    }

// NOTE TO DEVELOPER:
// you only need the two functions above, below are test cases, if you want them.

import unittest

class TestEncodeAndDecodeCTID(unittest.TestCase):
    def test(self):
        # Test case 1: Valid input values
        self.assertEqual(encodeCTID(0xFFFFFFF, 0xFFFF, 0xFFFF), "CFFFFFFFFFFFFFFF")
        self.assertEqual(encodeCTID(0, 0, 0), "C000000000000000")
        self.assertEqual(encodeCTID(1, 2, 3), "C000000100020003")
        self.assertEqual(encodeCTID(13249191, 12911, 49221), "C0CA2AA7326FC045")

        # Test case 2: ledger_seq greater than 0xFFFFFFF or less than 0
        with self.assertRaises(ValueError, msg="ledger_seq must not be greater than 268435455 or less than 0."):
            encodeCTID(0x10000000, 0xFFFF, 0xFFFF)
            encodeCTID(-1, 0xFFFF, 0xFFFF)

        # Test case 3: txn_index greater than 0xFFFF or less than 0
        with self.assertRaises(ValueError, msg="txn_index must not be greater than 65535 or less than 0."):
            encodeCTID(0xFFFFFFF, 0x10000, 0xFFFF)
            encodeCTID(0xFFFFFFF, -1, 0xFFFF)

        # Test case 4: network_id greater than 0xFFFF or less than 0
        with self.assertRaises(ValueError, msg="network_id must not be greater than 65535 or less than 0."):
            encodeCTID(0xFFFFFFF, 0xFFFF, -1)

        # Test case 5: Valid input values
        self.assertDictEqual(decodeCTID("CFFFFFFFFFFFFFFF"), {'ledger_seq': 0xFFFFFFF, 'txn_index': 0xFFFF, 'network_id': 0xFFFF})
        self.assertDictEqual(decodeCTID("C000000000000000"), {'ledger_seq': 0, 'txn_index': 0, 'network_id': 0})
        self.assertDictEqual(decodeCTID("C000000100020003"), {'ledger_seq': 1, 'txn_index': 2, 'network_id': 3})
        self.assertDictEqual(decodeCTID("C0CA2AA7326FC045"), {'ledger_seq': 13249191, 'txn_index': 12911, 'network_id': 49221})

        # Test case 6: ctid not a string or big int
        with self.assertRaises(ValueError, msg="ctid must be a hexadecimal string or BigInt"):
            decodeCTID(0xCFF)

        # Test case 7: ctid not a hexadecimal string
        with self.assertRaises(ValueError, msg="ctid must be a hexadecimal string or BigInt"):
            decodeCTID("C003FFFFFFFFFFFG")
            
        # Test case 8: ctid not exactly 16 nibbles
        with self.assertRaises(ValueError, msg="ctid must be exactly 16 nibbles and start with a C"):
            decodeCTID("C003FFFFFFFFFFF")

        # Test case 9: ctid too large to be a valid CTID value
        with self.assertRaises(ValueError, msg="ctid must be exactly 16 nibbles and start with a C"):
            decodeCTID("CFFFFFFFFFFFFFFFF")

        # Test case 10: ctid doesn't start with a C nibble
        with self.assertRaises(ValueError, msg="ctid must be exactly 16 nibbles and start with a C"):
            decodeCTID("FFFFFFFFFFFFFFFF")

        # the same tests again but using bigint instead of string
        #

        # Test case 11: Valid input values
        self.assertDictEqual(decodeCTID(0xCFFFFFFFFFFFFFFF), {'ledger_seq': 0xFFFFFFF, 'txn_index': 0xFFFF, 'network_id': 0xFFFF})
        self.assertDictEqual(decodeCTID(0xC000000000000000), {'ledger_seq': 0, 'txn_index': 0, 'network_id': 0})
        self.assertDictEqual(decodeCTID(0xC000000100020003), {'ledger_seq': 1, 'txn_index': 2, 'network_id': 3})
        self.assertDictEqual(decodeCTID(0xC0CA2AA7326FC045), {'ledger_seq': 13249191, 'txn_index': 12911, 'network_id': 49221})

        # Test case 12: ctid not exactly 16 nibbles
        with self.assertRaises(ValueError, msg="ctid must be exactly 16 nibbles and start with a C"):
            decodeCTID(0xC003FFFFFFFFFFF)

        # Test case 13: ctid too large to be a valid CTID value
        with self.assertRaises(ValueError, msg="ctid must be exactly 16 nibbles and start with a C"):
            decodeCTID(0xCFFFFFFFFFFFFFFFF)

        # Test case 14: ctid doesn't start with a C nibble
        with self.assertRaises(ValueError, msg="ctid must be exactly 16 nibbles and start with a C"):
            decodeCTID(0xFFFFFFFFFFFFFFFF)


if __name__ == '__main__':
    (TestEncodeAndDecodeCTID()).test()
