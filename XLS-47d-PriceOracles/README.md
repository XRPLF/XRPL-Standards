<pre> 
   Title:        <b>Oracles on XRP Ledger</b>
   Revision:     <b>2</b> (2023-09-27)
 <hr>  Author: <a href="mailto:gtsipenyuk@ripple.com">Gregory Tsipenyuk</a>
   Affiliation:  <a href="https://ripple.com">Ripple</a>
 
 </pre>
 
 # Oracles on XRP Ledger
 
 ## Abstract

 This proposal adds on-chain `PriceOracle` object to XRPL ledger. A blockchain oracle is a system or service that acts as a bridge between a blockchain network and the external world, providing off-chain data or information to decentralized applications (dApps) on the blockchain. Oracles are used to bring real-world data, for instance  market prices, exchange rates, interest rates, or weather conditions onto the blockchain, enabling dApps to access and utilize information that resides outside the blockchain. This document outlines the protocols involved in `PriceOracle` on XRPL ledger and provides guidelines for developers and system architects to implement and utilize this solution effectively. It introduces a new on-ledger `PriceOracle` object and the transactions to create, delete, and update the `PriceOracle` and adds `get_aggregate_price` API to retrieve an aggregate mean, trimmed mean, and median for the provided price oracles. This feature requires an amendment.

### Terminology

- Oracle Provider is a service or technology that enables the integration of external data and real-world events into a blockchain network.
- dApp, short for decentralized application, refers to an application that is built on a blockchain network and operates using smart contracts or rely on other mechanisms or protocols for their functionality.

## Creating `PriceOracle` instance on XRPL

### On-Ledger Data Structure

#### `PriceOracle` object

The `PriceOracle` ledger entry represents the `PriceOracle` object on XRPL ledger and contains the following fields:

|FieldName | Required? | JSON Type | Internal Type|
|:---------|:-----------|:---------------|:---------------|
| `OracleID` | :heavy_check_mark: | `string` | `HASH256` |
| `Owner` | :heavy_check_mark: | `string` | `ACCOUNTID` |
| `Provider` | :heavy_check_mark: | `string` | `BLOB` |
| `PriceDataSeries` | :heavy_check_mark: | `array` | `ARRAY` |
| `LastUpdateTime` | :heavy_check_mark: | `number` | `UINT32` |
| `URI` | | `string` | `BLOB` |
| `SymbolClass` | :heavy_check_mark: | `string` | `BLOB` |
| `PreviousTxnID` | :heavy_check_mark: | `string` | `UINT256` |
| `PreviousTxnLgrSeq`| :heavy_check_mark: | `string` | `UINT32` |

- `OracleID`. The ID of a PriceOracle object is the SHA-512Half of the following values, concatenated in order:
  - The Oracle space key `ORACLE` (0x52)
  - Owner field
  - Provider's Oracle unique ID. This is a unique `UINT32` number, which identifies this Oracle instance for the Oracle Provider.
- `Owner` is the account that has the update and delete privileges. It is recommended that this account has an associated [`signer list`](https://xrpl.org/set-up-multi-signing.html).
- `Provider` identifies an Oracle Provider. It can be URI or any data, for instance `chainlink`. It is a string of up to 32 ASCII hex encoded characters (0x20-0x7E).
- `PriceDataSeries` is an array of up to ten `PriceData` objects, where `PriceData` represents the price information for a token pair. `PriceOracle` with more than five `PriceData` objects requires two XRP reserves. `PriceData` includes the following fields:

  |FieldName | Required? | JSON Type | Internal Type|
  |:---------|:-----------|:---------------|:---------------|
  | `Symbol` | :heavy_check_mark: | `string` | `CURRENCY` |
  | `PriceUnit` | :heavy_check_mark: | `string` | `CURRENCY` |
  | `SymbolPrice` | :heavy_check_mark: | `number` | `UINT64` |
  | `Scale` | :heavy_check_mark: | `number` | `UINT8` |

  - `Symbol` is the symbol to be priced. Any arbitrary value should be allowed and interpreted exactly like other asset code fields in the ledger. A new enum value STI_CURRENCY and class STCurrency are introduced to support the `CURRENCY` field.
  - `PriceUnit` is the denomination in which the prices are expressed. Any arbitrary value should be allowed and interpreted exactly like other asset code fields in the ledger.
  - `SymbolPrice` is the scaled asset price, which is the price value after applying the scaling factor.
  - `Scale` is the price's scaling factor. It represents the price's precision level. For instance, if `Scale` is `6` and the original price is `0.155` then the scaled price is `155000`. Formally, $scaledPrice = originalPrice*{10}^{scale}$. Valid `Scale` range is {0-10}.

- `URI` is an optional URI field to reference the price data off-chain.
- `SymbolClass` describes a type of the assets, for instance "currency", "commodity", "index". It is a string of up to ten ASCII hex encoded characters (0x20-0x7E).
- `LastUpdateTime` is the specific point in time when the data was last updated. The `LastUpdateTime` is the ripple epoch time.
- `PreviousTxnID` is the hash of the previous transaction to modify this entry. (Same as on other objects with this field.).
- `PreviousTxnLgrSeq` is the ledger index of the ledger when this object was most recently updated/created. (Same as other objects with this field.)

#### Example of `PriceOracle` JSON

    {
        "LedgerEntryType": "PriceOracle",
        "OracleID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
        "Owner": "rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW",
        "Provider": "70726F7669646572",
        "SymbolClass": "63757272656E6379",
        "PriceDataSeries": [
          {
            "PriceData": {
              "Symbol": "XRP",
              "PriceUnit": "USD",
              "SymbolPrice": 74,
              "Scale": 2,
            }
          },
        ],
        "LastUpdateTime": 743609414,
        "PreviousTxnID": "C53ECF838647FA5A4C780377025FEC7999AB4182590510CA461444B207AB74A9",
        "PreviousTxnLgrSeq": 56865244
    }

## Transactions

This proposal introduces several new transactions to allow for the creation, update, and deletion of the `PriceOracle` object.

### Transaction for creating or updating `PriceOracle` instance

We define a new transaction **SetOracle** for creating or updating a `PriceOracle` instance.  Before the transaction can be submitted to create a new `PriceOracle` instance, the Oracle Provider has to do the following:

- Create or own the `Account` XRPL account with sufficient XRP balance to meet the XRP reserve and the transaction fee requirements.
- The Oracle Provider has to publish the `Account` account public key so that it can be used for verification by dApp’s.

#### Transaction fields for **SetOracle** transaction

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `TransactionType` | :heavy_check_mark: | `string`| UINT16 |

Indicates a new transaction type `SetOracle`. The integer value is 41.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `Account` | :heavy_check_mark: | `string` | `ACCOUNTID` |

`Account` is the account that has the Oracle update and delete privileges.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `Provider` | | `string` | `BLOB` |

`Provider` identifies an Oracle Provider. `Provider` must be included when creating a new instance of `PriceOracle`.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `URI` | | `string` | `BLOB` |

`URI` is an optional field to reference the price data off-chain.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `SymbolClass` | :heavy_check_mark: | `string` | `BLOB` |

`SymbolClass` describes the assets type.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:-----------|
| `LastUpdateTime` | :heavy_check_mark: | `number` | `UINT32` |

`LastUpdateTime` is the specific point in time when the data was last updated.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `PriceDataSeries` | :heavy_check_mark: | `array` | `ARRAY` |

`PriceDataSeries` is an array of up to ten `PriceData` objects, where `PriceData` represents the price information for a token pair. `PriceData` includes the following fields:

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `Symbol` | :heavy_check_mark: | `string` | `CURRENCY` |

`Symbol` is the symbol to be priced.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `PriceUnit` | :heavy_check_mark: | `string` | `CURRENCY` |

`PriceUnit` is the denomination in which the prices are expressed.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `SymbolPrice` | :heavy_check_mark: | `number` | `UINT64` |

`SymbolPrice` is the scaled asset price, which is the price value after applying the scaling factor.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `Scale` | :heavy_check_mark: | `number` | `UINT8` |

`Scale` is the price's scaling factor.

The transaction fails if:

- A required field is missing.
- XRP reserve is insufficient. If the Oracle instance has less or equal than five pairs then the XRP reserve requirements is one, otherwise the XRP reserve requirements is ten.
- Transaction's `PriceDataSeries` array size exceeds ten when creating a new Oracle instance or Oracle's instance `PriceDataSeries` array size exceeds ten after updating the Oracle instance.
- `PriceDataSeries` has duplicate token pairs.
- The `Account` account doesn't exist or `Account` is not equal to `Owner` field when updating the Oracle instance.
- The transaction is not signed by the `Account` account or the account's multi signers.

If an object with the `OracleID` already exists then the new token pairs are added to the Oracle instance `PriceDataSeries` array. Note that the order of the token pairs in the `PriceDataSeries` array is not important since the token pair uniquely identifies location in the `PriceDataSeries` array of the `PriceOracle` object. Also note that not every token pair price has to be updated. I.e., even though the `PriceOracle` may define ten token pairs, `SetOracle` transaction may contain only one token pair price update.

On success the transaction creates a new or updates existing `PriceOracle` object. If a new object is created then the owner reserve requirement is incremented by one or two depending on the `PriceDataSeries` array size.

#### Example of SetOracle transaction JSON

    {
        "TransactionType": "SetOracle",
        "Account": "rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW",
        "Provider": "70726F7669646572",
        "LastUpdateTime": 743609014,
        "SymbolClass": "63757272656E6379",
        "PriceDataSeries": [
          {
            "PriceData": {
              "Symbol": "XRP",
              "PriceUnit": "USD",
              "SymbolPrice": 740,
              "Scale": 3
            }
          }
        ]
    }

### Transaction for deleting Oracle instance

We define a new transaction **DeleteOracle** for deleting an Oracle instance.

#### Transaction fields for **DeleteOracle** transaction

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `TransactionType` | :heavy_check_mark: | `string` | `UINT16` |

Indicates a new transaction type `DeleteOracle`. The integer value is 42.

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `OracleID` | :heavy_check_mark: | `string` | `HASH256 `|

The ID of an Oracle object.

|FieldName | Required? | JSON Type | Internal Type |
|:---------|:-----------|:---------------|:------------|
| `Account` | :heavy_check_mark: | `string` | `ACCOUNTID` |

`Account` is the account that has the Oracle update and delete privileges.

**DeleteOracle** transaction deletes the `Oracle` object from the ledger.

The transaction fails if:

- Object with the `OracleID` doesn't exist.
- The transaction is not signed by the `Account` account or the account's multi signers.

On success the transaction deletes the `Oracle` object and the owner’s reserve requirement is reduced by one or two depending on the `PriceDataSeries` array size.

#### Example of DeleteOracle transaction JSON

    {
        "TransactionType": "DeleteOracle",
        "OracleID": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000",
        "Account": "rsA2LpzuawewSBQXkiju3YQTMzW13pAAdW"
    }

### API's

#### Retrieving The Oracle

An Oracle object can be retrieved with the `ledger_entry` API call by specifying the `OracleID` ID.

##### Example of `ledger_entry` API JSON

###### Request JSON

    {
         "method ":  "ledger_entry ",
         "params" : [
             "oracle ":  "D08D87CE50F215520D7AFEABADFD0669F7B89F9E40036FCA1906056E229FA800",
             "ledger_index ":  "validated "
         ]
    }

###### Response JSON

    {
       "index" : "CF2C20122022DE908C4F521A96DC2C1E5EFFD1EFD47AA244E9EE9A442451162E",
       "ledger_current_index" : 23,
       "node" : {
          "Flags" : 0,
          "LastUpdateTime" : 743609014,
          "LedgerEntryType" : "Oracle",
          "Owner" : "rp847ow9WcPmnNpVHMQV5A4BF6vaL9Abm6",
          "SymbolClass" : "63757272656E6379",
          "Provider": "70726F7669646572",
          "PreviousTxnID" : "6F120537D0D212FEA6E11A0DCC5410AFCA95BD98D451D046832E6C4C4398164D",
          "PreviousTxnLgrSeq" : 22,
          "PriceDataSeries": [
            {
              "PriceData: {
                "PriceUnit" : {
                   "currency" : "USD"
                },
                "Symbol" : {
                   "currency" : "XRP"
                },
                "Scale" : 1,
                "SymbolPrice" : "740",
              }
            }
          ],
          "index" : "CF2C20122022DE908C4F521A96DC2C1E5EFFD1EFD47AA244E9EE9A442451162E"
       },
       "status" : "success",
       "validated" : true
    }

#### Oracle Aggregation

`get_aggregate_price` API retrieves the aggregate price of the PriceOracle.

API fields are:

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `ledger_index` | | `string` or `number` (positive integer)|

The ledger index of the max ledger to use, or a shortcut string to choose a ledger automatically.

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `ledger_hash` | | `string` |

A 20-byte hex string for the max ledger version to use.

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `symbol` | :heavy_check_mark: | `string` |

`symbol` is the symbol to be priced.

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `price_unit` | :heavy_check_mark: | `string` |

`price_unit` is the denomination in which the prices are expressed.

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `oracles` | :heavy_check_mark: | `array` |

`oracles` is an array of `oracle_id` objects to aggregate over.

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `trim` | | `number` |

`trim` is the percentage of outliers to trim. Valid trim range is 1-25.

|FieldName | Required? | JSON Type |
|:---------|:-----------|:---------------|
| `flags` | :heavy_check_mark: | `number` |

`flags` specifies aggregation type. At least one flag must be specified. The flags can be bitwise added.

| Flag Name | Flag Value | Description |
|:---------|:-----------|:---------------|
| `fSimpleAverage` | 0x01 | Calculate the average price by summing up the prices of all the individual transactions or assets and dividing it by the total number of transactions/assets. This method treats each transaction or asset equally.
| `fMedian` | 0x02 | Arrange the prices of all the transactions or assets in ascending order and select the middle value as the median price. This method can be used when there are extreme outliers that may skew the average.
| `fTrimmedMean` | 0x04 | Calculate the average price after removing a specified percentage of extreme values from both ends of the data distribution. `trim` parameter should specify the percentage to trim. For instance, if `trim` is set to 10% then the lowest 5% and highest 5% of price points are removed.

##### Example of get_aggregate_price API JSON

###### Request JSON

    {
    "method": "get_aggregate_price",
    "params": [
        {
            "ledger_index": "current",
            "symbol": "XRP",
            "price_unit": "USD",
            "flags": 7,
            "trim": 20,
            "oracles": [
              {
                "oracle_id": "00070C4495F14B0E44F78A264E41713C64B5F89242540EE255534400000000000000"
              },
              {
                "oracle_id": "1B4F0E9851971998E732078544C96B36C3D01CEDF7CAA332359D6F1D835670140000"
              },
              {
                "oracle_id": "A4E624D686E03ED2767C0ABD85C14426B0B1157D2CE81D27BB4FE4F6F01D688A0000"
              },
              {
                "oracle_id": "FD61A03AF4F77D870FC21E05E7E80678095C92D808CFB3B5C279EE04C74ACA130000"
              },
              {
                "oracle_id": "A140C0C1EDA2DEF2B830363BA362AA4D7D255C262960544821F556E16661B6FF0000"
              }
            ]
        }
    ]
    }

##### Response JSON

    {
       "ledger_current_index" : 23,
       "simple_average" : "74.45",
       "median" : "74.45",
       "trimmed_mean": "70",
       "status" : "success",
       "validated" : false
    }
