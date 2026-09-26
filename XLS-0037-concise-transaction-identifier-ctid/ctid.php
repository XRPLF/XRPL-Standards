<?php

function encodeCTID($ledger_seq, $txn_index, $network_id)
{
  if (!is_numeric($ledger_seq))
    throw new Exception("ledger_seq must be a number.");
  if ($ledger_seq > 0xFFFFFFF || $ledger_seq < 0)
    throw new Exception("ledger_seq must not be greater than 268435455 or less than 0.");

  if (!is_numeric($txn_index))
    throw new Exception("txn_index must be a number.");
  if ($txn_index > 0xFFFF || $txn_index < 0)
    throw new Exception("txn_index must not be greater than 65535 or less than 0.");

  if (!is_numeric($network_id))
    throw new Exception("network_id must be a number.");
  if ($network_id > 0xFFFF || $network_id < 0)
    throw new Exception("network_id must not be greater than 65535 or less than 0.");

  $ledger_part = dechex($ledger_seq);
  $txn_part = dechex($txn_index);
  $network_part = dechex($network_id);

  if (strlen($ledger_part) < 7)
      $ledger_part = str_repeat("0", 7 - strlen($ledger_part)) . $ledger_part;
  if (strlen($txn_part) < 4)
      $txn_part = str_repeat("0", 4 - strlen($txn_part)) . $txn_part;
  if (strlen($network_part) < 4)
      $network_part = str_repeat("0", 4 - strlen($network_part)) . $network_part;

  return strtoupper("C" . $ledger_part . $txn_part . $network_part);
}

function decodeCTID($ctid)
{
  if (is_string($ctid))
  {
    if (!ctype_xdigit($ctid))
      throw new Exception("ctid must be a hexadecimal string");
    if (strlen($ctid) !== 16)
      throw new Exception("ctid must be exactly 16 nibbles and start with a C");
  } else
    throw new Exception("ctid must be a hexadecimal string");

  if (substr($ctid, 0, 1) !== 'C')
    throw new Exception("ctid must be exactly 16 nibbles and start with a C");

  $ledger_seq = substr($ctid, 1, 7);
  $txn_index = substr($ctid, 8, 4);
  $network_id = substr($ctid, 12, 4);
  return array(
    "ledger_seq" => hexdec($ledger_seq),
    "txn_index" => hexdec($txn_index),
    "network_id" => hexdec($network_id)
  );
}

// NOTE TO DEVELOPER:
// you only need the two functions above, below are test cases, if you want them.

print("Running tests...\n");

function assert_test($x)
{
    if (!$x)
        echo "test failed!\n";
    else
        echo "test passed\n";
}

// Test case 1: Valid input values
assert_test(encodeCTID(0xFFFFFFF, 0xFFFF, 0xFFFF) == "CFFFFFFFFFFFFFFF");
assert_test(encodeCTID(0, 0, 0) == "C000000000000000");
assert_test(encodeCTID(1, 2, 3) == "C000000100020003");
assert_test(encodeCTID(13249191, 12911, 49221) == "C0CA2AA7326FC045");

// Test case 2: ledger_seq greater than 0xFFFFFFF
try {
  encodeCTID(0x10000000, 0xFFFF, 0xFFFF);
  assert_test(false);
} catch (Exception $e) {
  assert_test(strcmp($e->getMessage(), "ledger_seq must not be greater than 268435455 or less than 0.") == 0);
}
try {
  encodeCTID(-1, 0xFFFF, 0xFFFF);
  assert_test(false);
} catch (Exception $e) {
  assert_test(strcmp($e->getMessage(), "ledger_seq must not be greater than 268435455 or less than 0.") == 0);
}

// Test case 3: txn_index greater than 0xFFFF
try {
  encodeCTID(0xFFFFFFF, 0x10000, 0xFFFF);
  assert_test(false);
} catch (Exception $e) {
  assert_test(strcmp($e->getMessage(), "txn_index must not be greater than 65535 or less than 0.") == 0);
}
try {
  encodeCTID(0xFFFFFFF, -1, 0xFFFF);
  assert_test(false);
} catch (Exception $e) {
  assert_test(strcmp($e->getMessage(), "txn_index must not be greater than 65535 or less than 0.") == 0);
}

// Test case 4: network_id greater than 0xFFFF
try {
  encodeCTID(0xFFFFFFF, 0xFFFF, 0x10000);
  assert_test(false);
} catch (Exception $e) {
  assert_test(strcmp($e->getMessage(), "network_id must not be greater than 65535 or less than 0.") == 0);
}
try {
  encodeCTID(0xFFFFFFF, 0xFFFF, -1);
  assert_test(false);
} catch (Exception $e) {
  assert_test(strcmp($e->getMessage(), "network_id must not be greater than 65535 or less than 0.") == 0);
}

// Test case 5: Valid input values
assert_test(decodeCTID("CFFFFFFFFFFFFFFF") == array("ledger_seq" => 0xFFFFFFF, "txn_index" => 0xFFFF, "network_id" => 0xFFFF));
assert_test(decodeCTID("C000000000000000") == array("ledger_seq" => 0, "txn_index" => 0, "network_id" => 0));
assert_test(decodeCTID("C000000100020003") == array("ledger_seq" =>1, "txn_index" => 2, "network_id" => 3));
assert_test(decodeCTID("C0CA2AA7326FC045") == array("ledger_seq" =>13249191, "txn_index" => 12911, "network_id" => 49221));


print("Done!\n");

?>
