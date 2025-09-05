const encodeCTID = (ledger_seq: number, txn_index: number, network_id: number): string =>
{
  if (ledger_seq > 0xFFFFFFF || ledger_seq < 0)
    throw new Error("ledger_seq must not be greater than 268435455 or less than 0.");

  if (txn_index > 0xFFFF || txn_index < 0)
    throw new Error("txn_index must not be greater than 65535 or less than 0.");

  if (network_id > 0xFFFF || network_id < 0)
    throw new Error("network_id must not be greater than 65535 or less than 0.");

  return (((BigInt(0xC0000000) +
    BigInt(ledger_seq)) << 32n) +
    (BigInt(txn_index) << 16n) +
    BigInt(network_id)).toString(16).toUpperCase();
}

const decodeCTID = (ctid: string | bigint): {ledger_seq: number, txn_index: number, network_id: number} =>
{
  let ctidValue: bigint;
  if (typeof ctid === 'string')
  {
    if (!/^[0-9A-F]+$/.test(ctid))
        throw new Error("ctid must be a hexadecimal string or BigInt");
    if (ctid.length !== 16)
      throw new Error("ctid must be exactly 16 nibbles and start with a C");

    ctidValue = BigInt(`0x${ctid}`);
  }
  else
    ctidValue = ctid;

  if (ctidValue > 0xFFFFFFFFFFFFFFFFn || (ctidValue & 0xF000000000000000n) !== 0xC000000000000000n)
    throw new Error("ctid must be exactly 16 nibbles and start with a C");

  const ledger_seq = Number((ctidValue >> 32n) & 0xFFFFFFFn);
  const txn_index = Number((ctidValue >> 16n) & 0xFFFFn);
  const network_id = Number(ctidValue & 0xFFFFn);
  return { ledger_seq, txn_index, network_id };
}

// NOTE TO DEVELOPER:
// you only need the two functions above, below are test cases, if you want them.
import { strict as assert } from 'assert';
const tests = () : void =>
{
  console.log("Running test cases...");
  // Test cases For encodeCTID

  // Test case 1: Valid input values
  assert.equal(encodeCTID(0xFFFFFFF, 0xFFFF, 0xFFFF), "CFFFFFFFFFFFFFFF");
  assert.equal(encodeCTID(0, 0, 0), "C000000000000000");
  assert.equal(encodeCTID(1, 2, 3), "C000000100020003");
  assert.equal(encodeCTID(13249191, 12911, 49221), "C0CA2AA7326FC045");

  // Test case 2: ledger_seq greater than 0xFFFFFFF
  assert.throws(() => encodeCTID(0x10000000, 0xFFFF, 0xFFFF), /ledger_seq must not be greater than 268435455 or less than 0./);
  assert.throws(() => encodeCTID(-1, 0xFFFF, 0xFFFF), /ledger_seq must not be greater than 268435455 or less than 0./);

  // Test case 3: txn_index greater than 0xFFFF
  assert.throws(() => encodeCTID(0xFFFFFFF, 0x10000, 0xFFFF), /txn_index must not be greater than 65535 or less than 0./);
  assert.throws(() => encodeCTID(0xFFFFFFF, -1, 0xFFFF), /txn_index must not be greater than 65535 or less than 0./);

  // Test case 4: network_id greater than 0xFFFF
  assert.throws(() => encodeCTID(0xFFFFFFF, 0xFFFF, 0x10000), /network_id must not be greater than 65535 or less than 0./);
  assert.throws(() => encodeCTID(0xFFFFFFF, 0xFFFF, -1), /network_id must not be greater than 65535 or less than 0./);

  // Test cases For decodeCTID

  // Test case 5: Valid input values
  assert.deepEqual(decodeCTID("CFFFFFFFFFFFFFFF"), { ledger_seq: 0xFFFFFFF, txn_index: 0xFFFF, network_id: 0xFFFF });
  assert.deepEqual(decodeCTID("C000000000000000"), { ledger_seq: 0, txn_index: 0, network_id: 0 });
  assert.deepEqual(decodeCTID("C000000100020003"), { ledger_seq:1, txn_index: 2, network_id: 3 });
  assert.deepEqual(decodeCTID("C0CA2AA7326FC045"), { ledger_seq:13249191, txn_index: 12911, network_id: 49221 });

  // Test case 6: ctid not a string or big int
  // impossible in typescript, left commented for completeness
  //assert.throws(() => decodeCTID(0xCFF), /ctid must be a hexadecimal string or BigInt/);

  // Test case 7: ctid not a hexadecimal string
  assert.throws(() => decodeCTID("C003FFFFFFFFFFFG"), /ctid must be a hexadecimal string or BigInt/);

  // Test case 8: ctid not exactly 16 nibbles
  assert.throws(() => decodeCTID("C003FFFFFFFFFFF"), /ctid must be exactly 16 nibbles and start with a C/);

  // Test case 9: ctid too large to be a valid CTID value
  assert.throws(() => decodeCTID("CFFFFFFFFFFFFFFFF"), /ctid must be exactly 16 nibbles and start with a C/);

  // Test case 10: ctid doesn't start with a C nibble
  assert.throws(() => decodeCTID("FFFFFFFFFFFFFFFF"), /ctid must be exactly 16 nibbles and start with a C/);

  // Test case 11: Valid input values
  assert.deepEqual(decodeCTID(0xCFFFFFFFFFFFFFFFn), { ledger_seq: 0xFFFFFFF, txn_index: 0xFFFF, network_id: 0xFFFF });
  assert.deepEqual(decodeCTID(0xC000000000000000n), { ledger_seq: 0, txn_index: 0, network_id: 0 });
  assert.deepEqual(decodeCTID(0xC000000100020003n), { ledger_seq:1, txn_index: 2, network_id: 3 });
  assert.deepEqual(decodeCTID(0xC0CA2AA7326FC045n), { ledger_seq:13249191, txn_index: 12911, network_id: 49221 });

  // Test case 12: ctid not exactly 16 nibbles
  assert.throws(() => decodeCTID(0xC003FFFFFFFFFFFn), /ctid must be exactly 16 nibbles and start with a C/);

  // Test case 13: ctid too large to be a valid CTID value
  assert.throws(() => decodeCTID(0xCFFFFFFFFFFFFFFFFn), /ctid must be exactly 16 nibbles and start with a C/);

  // Test case 14: ctid doesn't start with a C nibble
  assert.throws(() => decodeCTID(0xFFFFFFFFFFFFFFFFn), /ctid must be exactly 16 nibbles and start with a C/);

  console.log("Done.");
}

tests();
