#include <cassert>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <optional>
#include <regex>
#include <sstream>
#include <string>
#include <tuple>
#include <type_traits>

std::optional<std::string>
encodeCTID(uint32_t ledger_seq, uint16_t txn_index, uint16_t network_id) noexcept
{
  if (ledger_seq > 0xFFFFFFF)
    return {};

  uint64_t ctidValue =
      ((0xC0000000ULL + static_cast<uint64_t>(ledger_seq)) << 32) +
      (static_cast<uint64_t>(txn_index) << 16) + network_id;

  std::stringstream buffer;
  buffer << std::hex << std::uppercase << std::setfill('0') << std::setw(16)
         << ctidValue;
  return {buffer.str()};
}

template <typename T>
std::optional<std::tuple<uint32_t, uint16_t, uint16_t>>
decodeCTID(const T ctid) noexcept
{
  uint64_t ctidValue {0};
  if constexpr (std::is_same_v<T, std::string> || std::is_same_v<T, char *> ||
                std::is_same_v<T, const char *> ||
                std::is_same_v<T, std::string_view>)
  {
    const std::string ctidString(ctid);

    if (ctidString.length() != 16)
      return {};

    if (!std::regex_match(ctidString, std::regex("^[0-9A-F]+$")))
      return {};

    ctidValue = std::stoull(ctidString, nullptr, 16);
  } else if constexpr (std::is_integral_v<T>)
    ctidValue = ctid;
  else
    return {};

  if (ctidValue > 0xFFFFFFFFFFFFFFFFULL ||
      (ctidValue & 0xF000000000000000ULL) != 0xC000000000000000ULL)
    return {};

  uint32_t ledger_seq = (ctidValue >> 32) & 0xFFFFFFFUL;
  uint16_t txn_index = (ctidValue >> 16) & 0xFFFFU;
  uint16_t network_id = ctidValue & 0xFFFFU;
  return {{ledger_seq, txn_index, network_id}};
}

// NOTE TO DEVELOPER:
// you only need the two functions above, below are test cases, if
// you want them.

int main() {
  std::cout << "Running test cases..." << std::endl;
  // Test case 1: Valid input values
  assert(encodeCTID(0xFFFFFFFUL, 0xFFFFU, 0xFFFFU) ==
         std::optional<std::string>("CFFFFFFFFFFFFFFF"));
  assert(encodeCTID(0, 0, 0) == std::optional<std::string>("C000000000000000"));
  assert(encodeCTID(1U, 2U, 3U) ==
         std::optional<std::string>("C000000100020003"));
  assert(encodeCTID(13249191UL, 12911U, 49221U) ==
         std::optional<std::string>("C0CA2AA7326FC045"));

  // Test case 2: ledger_seq greater than 0xFFFFFFF
  assert(!encodeCTID(0x10000000UL, 0xFFFFU, 0xFFFFU));

  // Test case 3: txn_index greater than 0xFFFF
  // this test case is impossible in c++ due to the type, left in for
  // completeness assert(!encodeCTID(0xFFFFFFF, 0x10000, 0xFFFF));

  // Test case 4: network_id greater than 0xFFFF
  // this test case is impossible in c++ due to the type, left in for
  // completeness assert(!encodeCTID(0xFFFFFFFUL, 0xFFFFU, 0x10000U));

  // Test case 5: Valid input values
  assert((decodeCTID("CFFFFFFFFFFFFFFF") ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(0xFFFFFFFULL, 0xFFFFU, 0xFFFFU))));
  assert((decodeCTID("C000000000000000") ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(0, 0, 0))));
  assert((decodeCTID("C000000100020003") ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(1U, 2U, 3U))));
  assert((decodeCTID("C0CA2AA7326FC045") ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(13249191UL, 12911U, 49221U))));

  // Test case 6: ctid not a string or big int
  assert(!decodeCTID(0xCFF));

  // Test case 7: ctid not a hexadecimal string
  assert(!decodeCTID("C003FFFFFFFFFFFG"));

  // Test case 8: ctid not exactly 16 nibbles
  assert(!decodeCTID("C003FFFFFFFFFFF"));

  // Test case 9: ctid too large to be a valid CTID value
  assert(!decodeCTID("CFFFFFFFFFFFFFFFF"));

  // Test case 10: ctid doesn't start with a C nibble
  assert(!decodeCTID("FFFFFFFFFFFFFFFF"));

  // Test case 11: Valid input values
  assert((decodeCTID(0xCFFFFFFFFFFFFFFFULL) ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(0xFFFFFFFUL, 0xFFFFU, 0xFFFFU))));
  assert((decodeCTID(0xC000000000000000ULL) ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(0, 0, 0))));
  assert((decodeCTID(0xC000000100020003ULL) ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(1U, 2U, 3U))));
  assert((decodeCTID(0xC0CA2AA7326FC045ULL) ==
          std::optional<std::tuple<int32_t, uint16_t, uint16_t>>(
              std::make_tuple(13249191UL, 12911U, 49221U))));

  // Test case 12: ctid not exactly 16 nibbles
  assert(!decodeCTID(0xC003FFFFFFFFFFF));

  // Test case 13: ctid too large to be a valid CTID value
  // this test case is not possible in c++ because it would overflow the type,
  // left in for completeness assert(!decodeCTID(0xCFFFFFFFFFFFFFFFFULL));

  // Test case 14: ctid doesn't start with a C nibble
  assert(!decodeCTID(0xFFFFFFFFFFFFFFFFULL));

  std::cout << "Done!" << std::endl;
  return 0;
}
