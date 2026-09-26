<pre>
  xls: 22
  title: rippled API Versioning
  description: The API version number allows for evolving the `rippled` API while maintaining backward compatibility
  author: Elliot Lee (@intelliot), Peng Wang (@pwang200)
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/54
  status: Final
  category: System
  created: 2021-08-11
</pre>

# rippled API Versioning

rippled offers an API (application programming interface) that apps use to integrate with the XRP Ledger. In order to evolve and improve this API over time, while providing consistency and ensuring backward compatibility for clients, the API shall be versioned with an `API version number`.

For JSON-RPC and WebSocket (the most commonly-used interfaces), the API version number field is called `"api_version"`.

### JSON-RPC

```json
{
  "method": "...",
  "params": [
    {
      "api_version": 1,
      "...": "..."
    }
  ]
}
```

Notice that "api_version" is [not a top-level field](https://github.com/ripple/rippled/issues/3065).

### WebSocket

```json
{
  "api_version": 1,
  "id": 4,
  "command": "...",
  "...": "..."
}
```

Following the [WebSocket request format](https://xrpl.org/request-formatting.html), it is placed at the top level.

### rippled command line

The RPC command and its parameters are parsed first. Then, a JSON-RPC request is created. rippled shall not support multiple versions of the command-parameter parsers, so the JSON-RPC requests will have one API version number. The latest API version number shall be used. Under the hood, rippled shall insert the `"api_version"` field internally.

### gRPC

The version number for gRPC is specified as part of the package name of the gRPC service definition (in .proto files). The .proto files of different versions shall be placed in version-specific folders.

Multiple versions of the API are created by constructing multiple services, located in different namespaces. From gRPC's perspective, they are simply different services. All of the services can be registered to a single gRPC server.

## Specification

**The API version number shall be a single unsigned integer.** This is simpler than the major.minor.patch format, which is already used for versions of rippled itself. When it comes to API versions, there is no need for additional complexity beyond a single integer.

**The API version number shall be increased if, and only if, we introduce one or more breaking changes to the API.** When the version number is increased, it is increased by one.

**The lowest valid version number shall be 1.** The version number 0 is invalid.

**rippled shall support a range of versions with consecutive version numbers.** At the moment, the range is [1, 1].

**Client requests targeting an API version that is out of the supported version range shall be rejected.** For safety and ease of understanding, we do not allow "forward compatibility" where, if a version number in the request is higher than the supported range, we would lower its version number to the highest supported version number. Most clients know in advance which rippled servers they are connecting to (indeed, this is required for the XRPL security model). So it is unlikely that they will "mistakenly" make a request to a server that does not support the API version that they require. And if they do, it is better to respond with an error: the client can then choose to handle the error in a way that is appropriate for its use case.

**Client targeting APIs with versions 2 and above shall specify the version number in their requests.** The WebSocket and JSON-RPC (HTTP) requests shall include the version number in the request payloads.

**Requests without a version number shall be handled as version 1 requests.** This provides backward compatibility to the time when API version numbers did not yet exist.

**Responses do not need to include the API version number.** This saves some bandwidth and encourages the "best practice" of having the client track its requests with the `id` field.

**When a client sends multiple requests over a persistent connection (e.g. WebSockets), each request may use a different API version number.** This gives clients flexibility, with the ability to "progressively" update to new API versions in specific requests, without changing their entire integration.

**When using the rippled command line interface, the latest API version shall be used.** The command line interface is typically used for development, debugging, and one-off requests. For simplicity and to ensure that developers always pay attention to the evolution of the API, these requests shall use the latest API version.

**An API version that available in a stable release of rippled is considered "ready".** From the client's perspective, alpha/beta API versions generally should not exist.

## Implementation Details

There are four (4) RPC interfaces:

1. JSON-RPC (HTTP)
2. WebSocket
3. rippled command line
4. gRPC

The API version number is a single 32-bit unsigned integer. A range of consecutive API versions are supported by rippled. The lower and upper bounds of the range shall be hardcoded. Different rippled software versions may support different API version ranges.

For JSON-RPC and WebSocket, when a client requests an API version that is out of the supported range, the returned error message shall include the string "Unsupported API version", the version number targeted by the request, and the lower and upper bounds of the supported range.

## What is considered a breaking change?

- Deleting (removing), renaming, changing the type of, or changing the meaning of a field of a request or a response.
- Changing the order of position-based parameters, or inserting a new field in front of existing position-based parameters.
- Deleting or renaming an API method (function).
- Changing the behavior of an API method in a way that is visible to existing clients.
- Changing HTTP status codes[^1].

gRPC only:

- Changing a proto field number.
- Deleting or renaming an enum or enum value.
- Moving fields into or out of a oneof, split, or merge oneof.
- Changing the label of a message field, i.e. optional, repeated, required.
- Changing the stream value of a method request or response.
- Deleting or renaming a package or service.

## What is not a breaking change?

- Adding a new field to a request or response message, if it is not a position-based parameter.
- Adding a new API method (function).

## References

- [Documentation: API Versioning](https://xrpl.org/request-formatting.html#api-versioning)
- [API versioning #3155 (rippled PR)](https://github.com/ripple/rippled/pull/3155): Merged and released in [rippled v1.5.0](https://github.com/ripple/rippled/releases/tag/1.5.0)
- [Original Requirements](https://github.com/pwang200/RippledRPCDesign/blob/API_versioning/requirement/requirements.md)
- [Original Design Document](https://github.com/pwang200/RippledRPCDesign/blob/API_versioning/design/design.md)

[^1]:
    Changes to response status codes. For example, this is a breaking change:
    **Before:** POST /values returns 400 for missing property
    **After:** POST /values returns 409 for missing property
    [Reference](https://community.blackbaud.com/blogs/69/3219)
