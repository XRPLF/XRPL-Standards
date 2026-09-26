<pre>
    xls: 17
    title: XFL Developer-friendly representation of XRPL balances
    description: Introduces developer-friendly representation of XRPL balances.
    author: RichardAH (@RichardAH)
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/39
    created: 2021-03-19
    status: Final
    category: System
</pre>

# Background

The XRP ledger allows for two types of balances on accounts:

- Native `xrp` balances
- IOU/Token `trustline` balances

Native balances are encoded and processed as signed 63bit integer values with an implicit decimal point at the 6th place from the right. A single unit is referred to as a drop. Thus the smallest possible value is `1 drop` represented logically as: `0.000001 xrp`.

Trustline balances are encoded and processed as a 63 bit decimal floating point number in the following format:
{`sign bit` `8 bits of exponent` `54 bits of mantissa`}
Note: This is not the IEEE floating point format (which is base 2.)

- The exponent is biased by 97. Thus an encoded exponent of `0b00000000` is `10^(-97)`.
- The mantissa is normalised between `10^15` and `10^16 - 1`
- The canonical zero of this format is all bits 0.

A 64th disambiguation bit is prepended (most significant bit) to both datatypes, which is `0` in the case of a native balance and `1` in the case of a trustline balance. [[1]](https://xrpl.org/serialization.html#amount-fields)

# Problem Definition

Performing computations between these two number formats can be difficult and error-prone for third party developers.

One existing partial solution is passing these amounts around as human-readable decimal numbers encoded as strings. This is computationally intensive and still does not allow numbers of one type to be mathematically operated on with numbers of the other type in a consistent and predictable way.

Internally the XRPL requires two independent types, however any xrp balance less than `10B` will translate without loss of precision into the trustline balance type. For amounts of xrp above `10B` (but less than `100B`) only 1 significant figure is lost from the least significant side. Thus in the worst possible case (moving >= `10B` XRP) `10` drops may be lost from an amount.

The benefits of representing xrp balances in the trustline balance format are:

- Much simpler developer experience (less mentally demanding, lower barrier to entry)
- Can compute exchange rates between trustline balances and xrp
- Can store all balance types in a single data type
- A unified singular set of safe math routines which are much less likely to be used wrongly by developers

# XFL Format

The XFL format is designed for ease of use and maximum compatibility across a wide variety of processors and platforms.

For maximum ease of passing and returning from (pure) functions all XFL numbers are encoded into an `enclosing number` which is always a signed 64 bit integer, as follows:

Note: bit 63 is the most significant bit

- bit 63: `enclosing sign bit` always 0 for a valid XFL
- bit 62: `internal sign bit` 0 = negative 1 = positive. note: this is not the int64_t's sign bit.
- bit 61 - 53: `exponent` biased such that `0b000000000` = -97
- bit 53 - 0: `mantissa` between `10^15` and `10^16 - 1`

Special case:

- Canonical zero: enclosing number = 0

Any XFL with a negative enclosing sign bit is `invalid`. This _DOES NOT_ refer to the internal sign bit inside the XFL format. It is definitely possible to have a negative value represented in an XFL, however these always exist with a _POSITIVE_ enclosing sign bit.

Invalid (negative enclosing sign bit) XFL values are reserved for propagation of error codes. If an invalid XFL is passed to an XFL processing function (for example `float_multiply`) it too should return an invalid XFL.

# Examples

| Number | Enclosing           | To String                     |
| ------ | ------------------- | ----------------------------- |
| -1     | 1478180677777522688 | -1000000000000000 \* 10^(-15) |
| 0      | 0000000000000000000 | [canonical zero]              |
| +1     | 6089866696204910592 | +1000000000000000 \* 10^(-15) |
| +PI    | 6092008288858500385 | +3141592653589793 \* 10^(-15) |
| -PI    | 1480322270431112481 | -3141592653589793 \* 10^(-15) |

# Reference Implementations

Javascript:

```js
const minMantissa = 1000000000000000n;
const maxMantissa = 9999999999999999n;
const minExponent = -96;
const maxExponent = 80;

function make_xfl(exponent, mantissa) {
  // convert types as needed
  if (typeof exponent != "bigint") exponent = BigInt(exponent);

  if (typeof mantissa != "bigint") mantissa = BigInt(mantissa);

  // canonical zero
  if (mantissa == 0n) return 0n;

  // normalize
  let is_negative = mantissa < 0;
  if (is_negative) mantissa *= -1n;

  while (mantissa > maxMantissa) {
    mantissa /= 10n;
    exponent++;
  }
  while (mantissa < minMantissa) {
    mantissa *= 10n;
    exponent--;
  }

  // canonical zero on mantissa underflow
  if (mantissa == 0) return 0n;

  // under and overflows
  if (exponent > maxExponent || exponent < minExponent) return -1; // note this is an "invalid" XFL used to propagate errors

  exponent += 97n;

  let xfl = !is_negative ? 1n : 0n;
  xfl <<= 8n;
  xfl |= BigInt(exponent);
  xfl <<= 54n;
  xfl |= BigInt(mantissa);

  return xfl;
}

function get_exponent(xfl) {
  if (xfl < 0n) throw "Invalid XFL";
  if (xfl == 0n) return 0n;
  return ((xfl >> 54n) & 0xffn) - 97n;
}

function get_mantissa(xfl) {
  if (xfl < 0n) throw "Invalid XFL";
  if (xfl == 0n) return 0n;
  return xfl - ((xfl >> 54n) << 54n);
}

function is_negative(xfl) {
  if (xfl < 0n) throw "Invalid XFL";
  if (xfl == 0n) return false;
  return ((xfl >> 62n) & 1n) == 0n;
}

function to_string(xfl) {
  if (xfl < 0n) throw "Invalid XFL";
  if (xfl == 0n) return "<zero>";
  return (
    (is_negative(xfl) ? "-" : "+") +
    get_mantissa(xfl) +
    " * 10^(" +
    get_exponent(xfl) +
    ")"
  );
}
```

C:

- See implementation in Hooks: [here](https://github.com/RichardAH/rippled-hooks/blob/6b132d6d1382e3ee61e6759cecad36f08b9e665f/src/ripple/app/tx/impl/applyHook.cpp#L86)
