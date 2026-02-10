<pre>
  xls: 62
  title: Options
  description: A new framework for options trading on the XRPL protocol
  author: Denis Angell (@dangell7)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/186
  created: 2024-03-25
  updated: 2025-04-22
  status: Stagnant
  category: Amendment
</pre>

# XLS-62: Options on XRPL Protocol Chains

## Amendment

The proposed amendment introduces a new framework for options trading on the XRPL protocol, providing a lightweight and flexible way to create, trade, and exercise options, thus expanding the financial capabilities of the XRPL for decentralized finance applications.

The amendment adds:

### New Ledger Entry Types

- **ltOPTION_PAIR** (`0x0083`): Represents an option listing for a specific asset/strike asset pair.
- **ltOPTION** (`0x0084`): Represents both an option listing (for a specific asset/strike asset pair) and a specific option contract.
- **ltOPTION_OFFER** (`0x0085`): Represents an offer to buy or sell an option contract.

### New Serialized Fields

- **sfStrikePrice** (`Amount`, code `32`): The strike price of the option.
- **sfExpiration** (`UInt32`): The expiration time of the option as a UNIX timestamp.
- **sfOptionPairID** (`Hash256`, code `35`): An identifier for the parent OptionPair.
- **sfOptionID** (`Hash256`, code `36`): An identifier for the `Option` object.
- **sfOptionOfferID** (`Hash256`, code `37`): An identifier for the `OptionOffer` object.
- **sfQuantity** (`UInt32`, code `53`): The quantity of options (number of contracts).
- **sfOpenInterest** (`UInt32`, code `52`): The quantity of options available (unsealed amount).
- **sfPremium** (`Amount`, code `33`): The premium amount per option contract.
- **sfSealedOption** (`Object`, code `34`): An object representing a sealed (matched) option between counterparties.
- **sfSealedOptions** (`Array`, code `29`): An array of `sfSealedOption` objects in an `OptionOffer`.

### New Transaction Types

- **OptionPairCreate** (`ttOPTION_PAIR_CREATE`, code `64`): Creates a new pseudo account for an option listing with a specific asset/asset2 pair.
- **OptionCreate** (`ttOPTION_CREATE`, code `64`): Creates a new option offer for an existing option contract.
- **OptionSettle** (`ttOPTION_SETTLE`, code `65`): Settles an option contract through exercise, expiration, or closing.

### New Transaction Flags

#### For OptionCreate Transactions

- **tfPut** (`0x00010000`): Indicates a Put option (default is Call if unset).
- **tfMarket** (`0x00020000`): Indicates a Market order (default is Limit if unset).
- **tfSell** (`0x00080000`): Indicates a Sell offer (default is Buy if unset).
- **Mask:** `tfOptionCreateMask = ~(tfUniversal | tfPut | tfMarket | tfSell)`

#### For OptionSettle Transactions

- **tfExpire** (`0x00010000`): Indicates intent to expire the option.
- **tfClose** (`0x00020000`): Indicates intent to close the option.
- **tfExercise** (`0x00040000`): Indicates intent to exercise the option.
- **Mask:** `tfOptionSettleMask = ~(tfUniversal | tfExpire | tfClose | tfExercise)`

## Pseudo Account Approach for Options

Each option listing is represented by a pseudo account without an owner, similar to the AMM implementation. This creates consistency in the XRPL protocol for derivative products.

### Option Pair Pseudo Account Creation and Identification

1. The `OptionPairCreate` transaction creates a new `AccountRoot` object and associated `OptionPair` object for a specific asset/asset2 pair (e.g., GME/USD).
2. The `OptionPairID` is the AccountID of the pseudo account.
3. The master key is disabled and the regular key is set to account zero, making it impossible for the account to originate transactions.

## New Ledger Object Type: `OptionPair`

The `OptionPair` ledger object represents an option listing for a specific asset/asset2 pair on the XRPL. This object is created when an `OptionPairCreate` transaction is processed.

### Fields

| Field             | JSON Name           | Type      | Required | Description                                                              |
| ----------------- | ------------------- | --------- | -------- | ------------------------------------------------------------------------ |
| LedgerEntryType   | `OptionPair`        | UInt16    | Required | The type of ledger object (value `0x0083`).                              |
| Account           | `Account`           | AccountID | Required | The ID of the pseudo account for this option listing.                    |
| OwnerNode         | `OwnerNode`         | UInt64    | Required | The owner directory node index.                                          |
| Asset             | `Asset`             | Issue     | Required | The underlying asset of the option (an `Issue` structure).               |
| Asset2            | `Asset2`            | Issue     | Required | The strike price asset of the option (an `Issue` structure).             |
| PreviousTxnID     | `PreviousTxnID`     | Hash256   | Required | The ID of the transaction that modified this object.                     |
| PreviousTxnLgrSeq | `PreviousTxnLgrSeq` | UInt32    | Required | The ledger sequence number of the transaction that modified this object. |

### Related AccountRoot Extension

The `AccountRoot` object for an option listing includes:

| Field        | JSON Name      | Type    | Required | Description                                |
| ------------ | -------------- | ------- | -------- | ------------------------------------------ |
| OptionPairID | `OptionPairID` | Hash256 | Required | The ID of the associated OptionPair object |

### Example `OptionPair` Object

```json
{
  "LedgerEntryType": "OptionPair",
  "Account": "rOPTIONListingAddress",
  "OwnerNode": "0000000000000000",
  "Asset": {
    "currency": "GME",
    "issuer": "rGMEissuerAddress"
  },
  "Asset2": {
    "currency": "USD",
    "issuer": "rUSDissuerAddress"
  },
  "PreviousTxnID": "C24DAF43927556F379F7B8616176E57ACEFF1B5D016DC896222603A6DD11CE05",
  "PreviousTxnLgrSeq": 54321
}
```

## New Ledger Object Type: `Option` (for Contracts)

The `Option` ledger object can also represent a specific option contract on the XRPL with a designated strike price and expiration date. This object is created when an `OptionCreate` transaction is processed for the first time with a unique combination of parameters.

### Fields (for Option Contracts)

| Field             | JSON Name           | Type    | Required | Description                                                                    |
| ----------------- | ------------------- | ------- | -------- | ------------------------------------------------------------------------------ |
| LedgerEntryType   | `Option`            | UInt16  | Required | The type of ledger object (value `0x0083`).                                    |
| OptionID          | `OptionID`          | Hash256 | Required | The ID of the parent Option listing (AccountID of the listing pseudo account). |
| OwnerNode         | `OwnerNode`         | UInt64  | Required | The owner directory node index.                                                |
| StrikePrice       | `StrikePrice`       | Amount  | Required | The strike price of the option (as an `Amount`).                               |
| Expiration        | `Expiration`        | UInt32  | Required | The expiration time of the option (as a UNIX timestamp).                       |
| OptionType        | `OptionType`        | UInt8   | Required | The type of option: 0 for Call, 1 for Put.                                     |
| PreviousTxnID     | `PreviousTxnID`     | Hash256 | Required | The ID of the transaction that modified this object.                           |
| PreviousTxnLgrSeq | `PreviousTxnLgrSeq` | UInt32  | Required | The ledger sequence number of the transaction that modified this object.       |

### Example `Option` Contract Object

```json
{
  "LedgerEntryType": "Option",
  "OptionID": "rOPTIONListingAddress",
  "OwnerNode": "0000000000000000",
  "StrikePrice": {
    "currency": "USD",
    "issuer": "rUSDissuerAddress",
    "value": "20"
  },
  "Expiration": 743171558,
  "OptionType": 0,
  "PreviousTxnID": "C24DAF43927556F379F7B8616176E57ACEFF1B5D016DC896222603A6DD11CE05",
  "PreviousTxnLgrSeq": 54321
}
```

## New Ledger Object Type: `OptionOffer`

The `OptionOffer` ledger object represents an offer to buy or sell an option contract on the XRPL. This object is used to match buyers and sellers in the options market, facilitating the trading of options contracts.

### Fields

| Field             | JSON Name           | Type      | Required | Description                                                              |
| ----------------- | ------------------- | --------- | -------- | ------------------------------------------------------------------------ |
| LedgerEntryType   | `OptionOffer`       | UInt16    | Required | The type of ledger object (value `0x0084`).                              |
| Owner             | `Owner`             | AccountID | Required | The account that created the offer.                                      |
| OwnerNode         | `OwnerNode`         | UInt64    | Required | The owner directory node index.                                          |
| OptionID          | `OptionID`          | Hash256   | Required | The ID of the `Option` object this offer is for.                         |
| Premium           | `Premium`           | Amount    | Required | The premium of the option contract (price per option).                   |
| Quantity          | `Quantity`          | UInt32    | Required | The quantity of options (number of contracts).                           |
| OpenInterest      | `OpenInterest`      | UInt32    | Required | The quantity available (unsealed amount).                                |
| Amount            | `Amount`            | Amount    | Optional | The locked amount (for sellers, the collateral in the underlying asset). |
| BookDirectory     | `BookDirectory`     | Hash256   | Required | The directory listing offers at the same price.                          |
| BookNode          | `BookNode`          | UInt64    | Required | The order book directory node index.                                     |
| SealedOptions     | `SealedOptions`     | Array     | Optional | An array of `SealedOption` objects representing matched offers.          |
| PreviousTxnID     | `PreviousTxnID`     | Hash256   | Required | The ID of the transaction that modified this object.                     |
| PreviousTxnLgrSeq | `PreviousTxnLgrSeq` | UInt32    | Required | The ledger sequence number of the transaction that modified this object. |

#### `SealedOption` Object in `SealedOptions` Array

Each `SealedOption` object represents a matched (sealed) option offer with a counterparty.

##### Fields

| Field         | JSON Name       | Type      | Required | Description                                 |
| ------------- | --------------- | --------- | -------- | ------------------------------------------- |
| Owner         | `Owner`         | AccountID | Required | The account ID of the counterparty.         |
| OptionOfferID | `OptionOfferID` | Hash256   | Required | The ID of the counterparty's `OptionOffer`. |
| Quantity      | `Quantity`      | UInt32    | Required | The quantity sealed with the counterparty.  |

### Example `OptionOffer` Object

```json
{
  "LedgerEntryType": "OptionOffer",
  "Owner": "rU9XRmcZiJXp5J1LDJq8iZFujU6Wwn9cV9",
  "OwnerNode": "0000000000000000",
  "OptionID": "D79DE793C6934943D5389CB4E5392A05A8E00881202F05FE41ADC2AE83B24E91",
  "Premium": {
    "currency": "USD",
    "issuer": "rUSDissuer",
    "value": "0.5"
  },
  "Quantity": 100,
  "OpenInterest": 50,
  "Amount": {
    "currency": "GME",
    "issuer": "rGMEissuerAddress",
    "value": "100"
  },
  "BookDirectory": "00B15D0B5E...",
  "BookNode": "0000000000000000",
  "SealedOptions": [
    {
      "Owner": "rBuyerAccountID",
      "OptionOfferID": "E5F6AEBCC10B8C2A9C3B2A1C4A6EEBDBF5D48D6749F3A5B07B9FCDABB3F70279",
      "Quantity": 50
    }
  ],
  "PreviousTxnID": "D79DE793C6934943D5389CB4E5392A05A8E00881202F05FE41ADC2AE83B24E91",
  "PreviousTxnLgrSeq": 54322
}
```

## New Transaction Type: `OptionPairCreate`

The `OptionPairCreate` transaction is used to create a new option listing for a specific asset/asset2 pair on the XRPL by creating a dedicated pseudo account for the option listing. This establishes the option listing parameters and creates the necessary ledger objects.

### Fields

| Field             | Type      | Required | Description                                                  |
| ----------------- | --------- | -------- | ------------------------------------------------------------ |
| `TransactionType` | UInt16    | Required | The type of transaction (`OptionPairCreate`, value `64`).    |
| `Account`         | AccountID | Required | The account creating the option listing.                     |
| `Asset`           | Issue     | Required | The underlying asset of the option (an `Issue` structure).   |
| `Asset2`          | Issue     | Required | The strike price asset of the option (an `Issue` structure). |

### Failure Conditions

The `OptionPairCreate` transaction **MUST** fail if:

- The transaction does not meet the generic transaction requirements.
- The `Asset` field is missing or invalid.
- The `Asset2` field is missing or invalid.
- An option listing with identical parameters (same Asset and Asset2) already exists.

### State Changes

If the transaction is successful:

- A new `AccountRoot` object is created for the option listing.
- The regular key is set to account zero, and the master key is disabled for the `AccountRoot`.
- A new `OptionPair` object is created with the specified parameters, linked to the `AccountRoot`.
- A new `DirectoryNode` object is created linking the `AccountRoot` and `OptionPair` objects.
- The `OptionPairID` is the AccountID of the new pseudo account.

### Example `OptionPairCreate` Transaction

```json
{
  "TransactionType": "OptionPairCreate",
  "Account": "rAccountCreatingTheListing",
  "Asset": {
    "currency": "GME",
    "issuer": "rGMEissuerAddress"
  },
  "Asset2": {
    "currency": "USD",
    "issuer": "rUSDissuerAddress"
  }
}
```

## New Transaction Type: `OptionCreate`

The `OptionCreate` transaction is used to create a new option offer on the XRPL for an existing option contract (identified by its `OptionID`).

### Fields

| Field             | Type      | Required | Description                                                              |
| ----------------- | --------- | -------- | ------------------------------------------------------------------------ |
| `TransactionType` | UInt16    | Required | The type of transaction (`OptionCreate`, value `64`).                    |
| `Account`         | AccountID | Required | The account creating the option offer.                                   |
| `OptionID`        | Hash256   | Required | The ID of the existing Option (AccountID of the option pseudo account).  |
| `Premium`         | Amount    | Required | The premium per option contract.                                         |
| `Quantity`        | UInt32    | Required | The quantity of options (number of contracts). Must be divisible by 100. |
| `Flags`           | UInt32    | Optional | Flags to specify action (see below).                                     |

### `OptionCreate` Flags

The `OptionCreate` transaction uses flags to specify the type of option offer.

| Flag Name  | Hex Value    | Description                                   |
| ---------- | ------------ | --------------------------------------------- |
| `tfMarket` | `0x00020000` | Set for Market order (unset for Limit order). |
| `tfSell`   | `0x00080000` | Set for Sell option (unset for Buy).          |

The mask for valid flags is:

- `tfOptionCreateMask = ~(tfUniversal | tfMarket | tfSell)`

### Failure Conditions

The `OptionCreate` transaction **MUST** fail if:

- The transaction does not meet the generic transaction requirements.
- The `OptionID` field is missing or invalid.
- The specified `Option` does not exist.
- The `Premium` field is missing, invalid, or improperly formatted.
- The `Quantity` field is missing, invalid, not divisible by 100, or zero.
- The account does not have sufficient balance to cover the premium (for buyers) or does not have sufficient collateral (for sellers).
- Invalid flags are set (flags outside of `tfOptionCreateMask`).
- The option has expired (current ledger time is past the expiration).
- Any amount calculations result in an overflow or underflow.

### State Changes

If the transaction is successful:

- An `OptionOffer` ledger object is created with the specified parameters.
- The account's owner count is incremented.
- For buyers:
  - If the option is matched with a seller (sealed), the open interest is adjusted, and sealed options are recorded.
- For sellers:
  - The collateral (underlying asset) is locked in the `OptionOffer` object.
  - If the option is matched with a buyer, the premium is credited to the seller's balance, open interest is adjusted, and sealed options are recorded.
- Premium payments are transferred between buyers and sellers for matched (sealed) options.
- The transaction fee is deducted from the account's balance.

### Example `OptionCreate` Transaction (Buy Call)

```json
{
  "TransactionType": "OptionCreate",
  "Account": "rBuyerAccount",
  "OptionID": "rOPTIONaccountAddress",
  "Premium": {
    "currency": "USD",
    "issuer": "rUSDissuer",
    "value": "0.5"
  },
  "Quantity": 100,
  "Flags": 0 // Buy (tfSell unset), Limit (tfMarket unset)
}
```

## New Transaction Type: `OptionSettle`

The `OptionSettle` transaction is used to settle an option contract on the XRPL. This transaction allows the holder of a call or put option to exercise their right to buy or sell the underlying asset at the specified strike price, or to expire or close the option.

### Fields

| Field             | Type      | Required | Description                                                       |
| ----------------- | --------- | -------- | ----------------------------------------------------------------- |
| `TransactionType` | UInt16    | Required | The type of transaction (`OptionSettle`, value `65`).             |
| `Account`         | AccountID | Required | The account settling the option.                                  |
| `OptionID`        | Hash256   | Required | The ID of the `Option` (AccountID of the option pseudo account).  |
| `OptionOfferID`   | Hash256   | Required | The ID of the `OptionOffer` ledger object representing the offer. |
| `Flags`           | UInt32    | Required | Flags indicating the settlement action (exactly one must be set). |

### `OptionSettle` Flags

| Flag Name    | Hex Value    | Description                       |
| ------------ | ------------ | --------------------------------- |
| `tfExpire`   | `0x00010000` | Set to expire the option.         |
| `tfClose`    | `0x00020000` | Set to close the option position. |
| `tfExercise` | `0x00040000` | Set to exercise the option.       |

The mask for valid flags is:

- `tfOptionSettleMask = ~(tfUniversal | tfExpire | tfClose | tfExercise)`

**Note:** Exactly one of these flags must be set.

### Failure Conditions

The `OptionSettle` transaction **MUST** fail if:

- The transaction does not meet the generic transaction requirements.
- The `OptionID` field is missing or invalid.
- The `OptionOfferID` field is missing or invalid.
- The `Option` ledger object or the `OptionOffer` ledger object does not exist.
- The account is not the owner of the option offer (does not have permission to settle it).
- More than one settlement flag is set or no settlement flag is set.
- Invalid flags are set (flags outside of `tfOptionSettleMask`).
- For `tfExercise`:
  - The option cannot be exercised by a seller (only buyers can exercise).
  - The account does not have sufficient balance to cover the cost of exercising.
- For `tfClose`:
  - No suitable replacement offers can be found to maintain sealed option relationships.

### State Changes

If the transaction is successful:

- For expiration (`tfExpire`):
  - If the option has already expired naturally or the flag is set:
    - Any locked collateral (for sell offers) is returned to the owner.
    - The `OptionOffer` is removed from the ledger.
    - Counterparty options are updated to remove references to the expired offer.
  - The transaction returns `tecEXPIRED`.

- For closing (`tfClose`):
  - The option position is closed, potentially replacing sealed option relationships with new counterparties.
  - For sell offers, locked collateral is returned to the owner.
  - For buy offers that have sealed options, payments may be received from new counterparties.
  - The `OptionOffer` is removed from the ledger.

- For exercising (`tfExercise`):
  - Assets and funds are transferred between the holder (buyer) and the writer (seller):
    - For a **Call Option Exercise**:
      - The holder pays the strike price amount (total value) to the writer.
      - The writer transfers the underlying asset (quantity of shares) to the holder.
    - For a **Put Option Exercise**:
      - The holder transfers the underlying asset (quantity of shares) to the writer.
      - The writer pays the strike price amount (total value) to the holder.
  - The `OptionOffer` is removed from the ledger after successful exercise.

### Example `OptionSettle` Transaction (Exercise)

```json
{
  "TransactionType": "OptionSettle",
  "Account": "rBuyerAccount",
  "OptionID": "rOPTIONaccountAddress",
  "OptionOfferID": "D5EB856370B233B4384D02613E6C71305C57BCA5FF4A5D857D4628DB9D72BC55",
  "Flags": 65536 // tfExercise flag set (0x00040000)
}
```

## Option Order Book

An option order book is maintained in the ledger to facilitate the matching of option offers. The order book indexes `OptionOffer` ledger objects based on the `OptionID` and sorts them by `Premium` using `OptionQuality`. This allows for efficient discovery and matching of compatible offers.

### Order Book Indexing

Offers are organized in directories similar to the existing `Offer` objects for trading currencies. The key differences are:

- **Option Parameters**: The directory keys include the `OptionID` and the quality (premium).
- **Quality (OptionQuality)**: The premium per option contract is used as the quality for sorting offers within the directories.

The methods for indexing include:

- `getOptionBookBase`: Generates the base index for the option order book directory.
- `getOptionQualityNext`: Determines the next quality index for iteration.
- `getOptionQuality`: Retrieves the quality (premium) component from an index.

These methods facilitate the navigation and management of the option order book within the ledger.

### Matching Option Offers

When an `OptionCreate` transaction is processed, the ledger attempts to match the new `OptionOffer` with existing offers in the order book. Offers are matched based on option parameters and premiums. When a match occurs, the offers are sealed, and the `SealedOptions` arrays in the respective `OptionOffer` objects are updated to reflect the matched quantities and counterparties.

## RPC Changes

A new RPC method `option_book_offers` is introduced, enabling clients to query the current state of the option order book for a specific option. This allows users to retrieve active offers for buying or selling options, facilitating market transparency and price discovery.

### `option_book_offers` Method

#### Request Format

```json
{
  "method": "option_book_offers",
  "params": [
    {
      "ledger_index": "validated", // or "current", or a specific ledger index
      "option_id": "rOPTIONaccountAddress", // OptionID (Account ID of the option pseudo account)
      "limit": 10, // Optional
      "marker": "<opaque value>" // Optional, for pagination
    }
  ]
}
```

#### Request Parameters

- **option_id**: (Required) The ID of the option (Account ID of the option pseudo account).
- **ledger_index**: (Optional) The ledger version to use (default is "validated").
- **limit**: (Optional) Maximum number of offers to return (default is API limit).
- **marker**: (Optional) Opaque pagination marker from a previous response.

#### Response Format

```json
{
  "result": {
    "ledger_hash": "ABCD1234...",
    "ledger_index": 54321,
    "option": {
      "Account": "rOPTIONaccountAddress",
      "StrikePrice": {
        "currency": "USD",
        "issuer": "rUSDissuerAddress",
        "value": "20"
      },
      "Asset": { "currency": "GME", "issuer": "rGMEissuerAddress" },
      "Expiration": 743171558,
      "Type": "Call" // or "Put"
    },
    "offers": [
      {
        "OptionOffer": {
          // Fields from the OptionOffer object
        },
        "quality": "500000000",
        "owner_funds": "1000000" // Optional, if available
      }
      // More offers...
    ]
  }
}
```

#### Response Fields

- **ledger_hash**: The hash of the ledger version used.
- **ledger_index**: The ledger index of the ledger version used.
- **option**: Details of the referenced option.
- **offers**: An array of offer objects, each representing an `OptionOffer`.
- **OptionOffer**: The details of the option offer (as a JSON object).
- **quality**: The premium per option contract (used for sorting in the order book).
- **owner_funds**: (Optional) The amount of the asset that the owner has available.

#### Usage Notes

- The method supports pagination via the `limit` and `marker` parameters.
- The response lists active offers in the option order book matching the specified `option_id`.
- Offers are sorted by quality (premium) for efficient price discovery.

### Example Usage

#### Request

```json
{
  "method": "option_book_offers",
  "params": [
    {
      "ledger_index": "current",
      "option_id": "rOPTIONaccountAddress",
      "limit": 5
    }
  ]
}
```

#### Response

```json
{
  "result": {
    "ledger_hash": "ABCD1234...",
    "ledger_index": 6000000,
    "option": {
      "Account": "rOPTIONaccountAddress",
      "StrikePrice": {
        "currency": "USD",
        "issuer": "rUSDissuerAddress",
        "value": "20"
      },
      "Asset": { "currency": "GME", "issuer": "rGMEissuerAddress" },
      "Expiration": 743171558,
      "Type": "Call"
    },
    "offers": [
      {
        "OptionOffer": {
          "LedgerEntryType": "OptionOffer"
          // ... other fields ...
        },
        "quality": "500000000",
        "owner_funds": "1000000"
      }
      // ... up to 5 offers ...
    ]
  }
}
```
