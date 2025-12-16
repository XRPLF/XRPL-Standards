## 1. SType: `[STypeName]`

> **Note:** Most specifications will not need this section, as the [existing types](https://xrpl.org/docs/references/protocol/binary-format#type-list) are generally sufficient. Only include this section if your specification introduces new serialized types (STypes).

_[If your specification introduces new serialized types, document each SType in its own numbered subsection below. Otherwise, delete this entire section.]_

### 1.1. SType Value

**Value:** `[Unique numeric value - see current values [here](https://github.com/XRPLF/rippled/blob/develop/include/xrpl/protocol/SField.h#L60)]`

_[Specify the unique numeric value for this SType]_

### 1.2. JSON Representation

_[Describe how instances of this SType are represented in JSON. For example: "Represented as a string in base64 format" or "Represented as an object with fields X, Y, Z"]_

### 1.3. Additional Accepted JSON Inputs _(Optional)_

_[If applicable, describe alternative JSON input formats that may be parsed. For example: "Can accept either a string or numeric format"]_

### 1.4. Binary Encoding

_[Describe how this SType is encoded in binary format, including byte order, length prefixes, etc.]_

### 1.5. Example JSON and Binary Encoding

**JSON Example:**

```json
[Provide JSON example]
```

**Binary Encoding Example:**

```
[Provide hexadecimal representation of binary encoding]
```

## 2. Ledger Entry: `[LedgerEntryName]`

_[If your specification introduces new ledger entry objects, document each entry in its own numbered section following this part of the template. Otherwise, do not include any sections with this title.]_

_[If your specification introduces new ledger entry common fields, you can have a section called `Transaction: Common Fields` before listing out any specific transactions.]_

### 2.1. Object Identifier

**Key Space:** `0x[XXXX]` _[Specify the 16-bit hex value for the key space]_

**ID Calculation Algorithm:**
_[Describe the algorithm for calculating the unique object identifier. Include the parameters used in the tagged hashing and ensure no collisions are possible. Example: "The ID is calculated by hashing [specific parameters] with the key space prefix 0xXXXX"]_

### 2.2. Fields

| Field Name        | Constant   | Required               | Internal Type | Default Value      | Description                                                           |
| ----------------- | ---------- | ---------------------- | ------------- | ------------------ | --------------------------------------------------------------------- |
| LedgerEntryType   | Yes        | Yes                    | UINT16        | `[EntryTypeValue]` | Identifies this as a `[LedgerEntryName]` object.                      |
| Account           | No         | Yes                    | ACCOUNT       | N/A                | The account that owns this object.                                    |
| `[CustomField1]`  | `[Yes/No]` | `[Yes/No/Conditional]` | `[TYPE]`      | `[Value/N/A]`      | `[Description of field]`                                              |
| `[CustomField2]`  | `[Yes/No]` | `[Yes/No/Conditional]` | `[TYPE]`      | `[Value/N/A]`      | `[Description of field]`                                              |
| OwnerNode         | No         | Yes                    | UINT64        | N/A                | Hint for which page this object appears on in the owner directory.    |
| PreviousTxnID     | No         | Yes                    | HASH256       | N/A                | Hash of the previous transaction that modified this object            |
| PreviousTxnLgrSeq | No         | Yes                    | UINT32        | N/A                | Ledger sequence of the previous transaction that modified this object |

_[Add more rows as needed for your specific fields. Remove example custom fields and replace with your actual fields.]_

**Field Details:** _[Include subsections below for any fields requiring detailed explanation]_

#### 2.2.1. `[FieldName]` _(If needed)_

_[Detailed explanation of field behavior, validation rules, etc.]_

### 2.3. Flags

\_[Describe any ledger entry-specific flags. The values must be powers of 2. If there are none, you can omit this section.]

| Flag Name        | Flag Value   | Description      |
| ---------------- | ------------ | ---------------- |
| `[lsfFlagName1]` | `0x[Value1]` | `[Description1]` |

### 2.4. Ownership

_[Specify which AccountRoot object owns this ledger entry and how the ownership relationship is established.]_

**Owner:** `[Account field name or "No owner" if this is a global object like FeeSettings]`

**Directory Registration:** `[Describe how this object is registered in the owner's directory, or specify if it's a special case]`

### 2.5. Reserves

**Reserve Requirement:** `[Standard/Custom/None]`

_[If Standard]: This ledger entry requires the standard owner reserve increment (currently 0.2 XRP, subject to Fee Voting changes)._

_[If Custom]: This ledger entry requires `[X]` reserve units because `[reason]`._

_[If None]: This ledger entry does not require additional reserves because `[reason]`._

### 2.6. Deletion

**Deletion Transactions:** `[List transaction types that can delete this object]`

**Deletion Conditions:**

- `[Condition 1, e.g., "Object balance must be zero"]`
- `[Condition 2, e.g., "No linked objects must exist"]`
- `[Additional conditions as needed]`

**Account Deletion Blocker:** `[Yes/No]`
_[If Yes]: This object must be deleted before its owner account can be deleted._
_[If No]: This object does not prevent its owner account from being deleted._

### 2.7. Pseudo-Account _(Optional)_

_[Only include this section if your ledger entry uses a pseudo-account. Otherwise, delete this subsection.]_

**Uses Pseudo-Account:** `[Yes/No]`

_[If Yes]:_

- **Purpose:** `[Describe why a pseudo-account is needed, e.g., "To hold assets on behalf of users"]`
- **AccountID Derivation:** `[Describe the algorithm for deriving the pseudo-account's AccountID]`
- **Capabilities:** `[List what the pseudo-account can/cannot do]`

### 2.8. Freeze/Lock _(Optional)_

_[Only include this section if your ledger entry holds assets that can be frozen/locked. Otherwise, delete this subsection.]_

**Freeze Support:** `[Yes/No]`
**Lock Support:** `[Yes/No]`

_[If applicable, describe how freeze/lock functionality is implemented for assets held by this object]_

### 2.9. Invariants

_[List logical statements that must always be true for this ledger entry. Use `<object>` for before-state and `<object>'` for after-state.]_

- `[Invariant 1, e.g., "<object>.Balance >= 0 AND <object>'.Balance >= 0"]`
- `[Invariant 2, e.g., "IF <object>.Status == 'Active' THEN <object>.Account != NULL"]`
- `[Additional invariants as needed]`

### 2.10. RPC Name

**RPC Type Name:** `[snake_case_name]`

_[This is the name used in `account_objects` and `ledger_data` RPC calls to filter for this object type]_

### 2.11. Example JSON

```json
{
  "LedgerEntryType": "[EntryTypeName]",
  "Flags": 0,
  "PreviousTxnID": "[32-byte hex hash]",
  "PreviousTxnLgrSeq": 12345678,
  "OwnerNode": "0000000000000000",
  "Account": "[r-address]",
  "[CustomField1]": "[example value]",
  "[CustomField2]": "[example value]"
}
```

## 3. Transaction: `[TransactionName]`

_[If your specification introduces new transactions, document each transaction in its own numbered section following this part of the template. Otherwise, delete this entire section.]_

_[If your specification introduces new transaction common fields, you can have a section called `Transaction: Common Fields` before listing out any specific transactions.]_

> **Naming Convention:** Transaction names should follow the pattern `<LedgerEntryName><Verb>` (e.g., `ExampleSet`, `ExampleDelete`). Most specifications will need at least:
>
> - `[Object]Set` or `[Object]Create`: Creates or updates the object
> - `[Object]Delete`: Deletes the object

### 3.1. Fields

| Field Name       | Required?              | JSON Type                      | Internal Type | Default Value       | Description                                          |
| ---------------- | ---------------------- | ------------------------------ | ------------- | ------------------- | ---------------------------------------------------- |
| TransactionType  | Yes                    | string                         | UINT16        | `[TransactionName]` | Identifies this as a `[TransactionName]` transaction |
| `[CustomField1]` | `[Yes/No/Conditional]` | `[string/number/object/array]` | `[TYPE]`      | `[Value/N/A]`       | `[Description of field]`                             |
| `[CustomField2]` | `[Yes/No/Conditional]` | `[string/number/object/array]` | `[TYPE]`      | `[Value/N/A]`       | `[Description of field]`                             |

_[Add more rows as needed for your specific fields. Remove example custom fields and replace with your actual fields. Common fields like Account, Fee, Sequence, Flags, SigningPubKey, TxnSignature are assumed.]_

**Field Details:** _[Include subsections below for any fields requiring detailed explanation]_

#### 3.1.1. `[FieldName]` _(If needed)_

_[Detailed explanation of field behavior, validation rules, etc.]_

### 3.2. Flags

\_[Describe any transaction-specific flags. The values must be powers of 2. If there are none, you can omit this section.]

| Flag Name       | Flag Value   | Description      |
| --------------- | ------------ | ---------------- |
| `[tfFlagName1]` | `0x[Value1]` | `[Description1]` |

### 3.3. Transaction Fee

**Fee Structure:** `[Standard/Custom]`

_[If Standard]: This transaction uses the standard transaction fee (currently 10 drops, subject to Fee Voting changes)._

_[If Custom]: This transaction requires `[X]` drops because `[reason]`._

### 3.4. Failure Conditions

_[List all conditions that cause the transaction to fail, with corresponding error codes]_

- `[Description of failure condition]` (`[ERROR_CODE]`)
- `[Description of failure condition]` (`[ERROR_CODE]`)
- `[Description of failure condition]` (`[ERROR_CODE]`)

_[For new error codes, provide justification for why existing codes are insufficient]_

### 3.5. State Changes

_[Describe the ledger state changes when the transaction executes successfully. Omit standard changes like fee processing and sequence increment.]_

**On Success (`tesSUCCESS`):**

- `[State change 1, e.g., "Create new [ObjectName] ledger entry"]`
- `[State change 2, e.g., "Update Account's OwnerCount"]`
- `[Additional changes as needed]`

### 3.6. Metadata Fields _(Optional)_

_[Only include this section if the transaction adds or modifies metadata fields. Otherwise, delete this subsection.]_

| Field Name     | Validated  | Always Present?        | Type                           | Description     |
| -------------- | ---------- | ---------------------- | ------------------------------ | --------------- |
| `[field_name]` | `[Yes/No]` | `[Yes/No/Conditional]` | `[string/number/object/array]` | `[Description]` |

### 3.7. Example JSON

```json
{
  "TransactionType": "[TransactionName]",
  "Account": "[r-address]",
  "Fee": "10",
  "Sequence": 12345,
  "[CustomField1]": "[example value]",
  "[CustomField2]": "[example value]"
}
```

## 4. Permission: `[PermissionName]`

_[If your specification introduces new permissions, document each permission in its own numbered section following this part of the template. Otherwise, do not include any sections with this title.]_

### 4.1. Transaction Types Affected

_[List transaction types that this permission applies to]_

### 4.2. Permission Scope

_[Describe what the granular permission controls]_

### 4.3. Permission Description

_[Describe how this permission interacts with existing permissions and what it allows/restricts]_

## 5. RPC: `[rpc_method_name]`

_[If your specification introduces new APIs or modifies existing ones, document each API in its own numbered section following this part of the template. Otherwise, do not include any sections with this title.]_

### 5.1. Request Fields

| Field Name     | Required?              | JSON Type                      | Description                   |
| -------------- | ---------------------- | ------------------------------ | ----------------------------- |
| command        | Yes                    | string                         | Must be `"[api_method_name]"` |
| `[field_name]` | `[Yes/No/Conditional]` | `[string/number/object/array]` | `[Description of field]`      |

### 5.2. Response Fields

| Field Name        | Always Present?        | JSON Type                      | Description                          |
| ----------------- | ---------------------- | ------------------------------ | ------------------------------------ |
| status            | Yes                    | string                         | `"success"` if the request succeeded |
| `[ResponseField]` | `[Yes/No/Conditional]` | `[string/number/object/array]` | `[Description of field]`             |

### 5.3. Failure Conditions

- `[Description of failure condition]` (`[ERROR_CODE]`)
- `[Description of failure condition]` (`[ERROR_CODE]`)
- `[Description of failure condition]` (`[ERROR_CODE]`)

### 5.4. Example Request

```json
{
  "command": "[api_method_name]",
  "[field_name]": "[example value]"
}
```

### 5.5. Example Response

```json
{
  "status": "success",
  "[ResponseField]": "[example value]"
}
```
