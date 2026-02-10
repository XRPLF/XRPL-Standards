<pre>
    xls: 24
    title: Metadata Structure for XLS-20
    description: Introduces a metadata standard for Non Fungible Tokens
    author: X-Tokenize (@x-Tokenize)
    proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/69
    created: 2022-02-16
    status: Final
    category: Ecosystem
</pre>

## Introduction

An NFT (Non Fungible Token) is a type of digital asset that uniquely represents ownership or the right to access to "something" that lives off chain. This "something" can take many different forms in the physical/digital realm such as works of art, real-estate, contractual agreements, tickets to events, derivative assets and much more.

The data which represents the underlying asset/rights are often described and then (in most cases) stored somewhere off-chain such as on a centralized server or a decentralized file system like InterPlantery File System ([IPFS](https://ipfs.io/)). This data is known as the metadata of the NFT and can take many different forms depending on what the NFT represents.

## Motivation

With the release of the [XLS-20](../XLS-0020-non-fungible-tokens/README.md) NFT dev network, there has been significant development of applications utilizing the proposed XLS-20 standard. The areas of interest utilizing NFTs are vast and thus requires a scalable standard for the representation of metadata to facilitate NFToken interoperability amongst applications.

## Advantages

- Increased interoperability amongst applications.
- Scalable data structure for new NFT use cases.
- Common fields shared with NFTs from other networks.

## Revision Changes (current:2)

- Removed [Metadata Standards Briefing](https://github.com/x-Tokenize/XLS-24D/blob/main/XLS24d-Revision0.md#metadata-standards-briefing)(removed in r1)
- Proposal (modified in r1)
- Removed Real estate [example](https://github.com/x-Tokenize/XLS-24D/blob/main/XLS24d-Revision1.md#real-estate-house-example) (r2)
- Added more information to the schema definition process. (r2)
- By popular demand, the xrart.v0 nftType has been renamed to art.v0 (r2)
- Modified and finalized the art.v0 nftType schema. (r2)
- Provided several live (nft-devnet) examples of the art.v0 nftType. (r2)

## Comments on Revision 2

Thank you to all the individuals that provided their feedback here and through other channels. All of your invaluable feedback has been taken into account in this second revision and we will definitely give credit where it's due!

The main goal of this revision was to expand on and provide additional guidance in the methodology assoicated with defining/advancing nftType schema definitions. Here we also provide a clear definition of the 'art.v0' nftType, have made changes to the art.v0 schema example in revision 1 and have provided additional examples to make it easier to follow along.

## Proposal

NFTs are versatile in nature and defining metadata requirements/expectations for all different use cases and implementations can lead to an astounding set of metadata definitions. The key elements of an NFT's metadata structure must be defined in such a way that they are concise and are easily expandable as use cases evolve and more complex systems are designed.

Identifying an appropriate base structure for NFT metadata will significantly create a more scalable and interoperable environment for application developers/creators building on the XRPL. It is also important for such a structure to be interoperable with standards being applied on other networks. Interoperability with other networks will provide other network participants a low-barrier to entry if they would like to bridge their NFTs to the XRPL.

Revision 1 introduced the concept of attaching a JSON schema file to the metadata of an NFT.

A JSON schema is used to describe your existing data format(s), provide human and machine readable documentation and can also be used to validate metadata of an NFT. Describing metadata format(s) provides applications with a detailed breakdown of types, requirements and structure of the metadata that it reads. Validation is not only great for determining if an NFT will work appropriately with your application but, can also be used for filtering out unwanted 'nftTypes'.

There are many existing schema validation libraries which makes integration into an application very trivial.

To learn more about JSON schemas, check out relevant resources here:

- [json-schema.org](https://json-schema.org/)
- [json-schema specification](https://json-schema.org/draft/2020-12/json-schema-core.html)
- [Getting Started](https://json-schema.org/learn/getting-started-step-by-step)
- [Understanding JSON schema](https://json-schema.org/understanding-json-schema/index.html)
- [Schema Generators and Validators](https://json-schema.org/implementations.html)
- [Schema.org](https://json-schema.org/understanding-json-schema/index.html)

Utilizing JSON schemas, we as a community can define and version our metadata as the XRPL NFT space evolves. For different nftTypes, we expect community leaders of those NFT types to contribute and derive a set of schema definitions for those use cases and implementations.

## Defining a schema for an nftType:

To create/update a schema for a specific nftType, it is important to consider the process as a set of building blocks;
If a schema for a specific nftType has not yet been defined, then it is up to it's creator to decide what are the absolute
bare minimum properties required for that nftType and should be an extension of the 'base.v0' nftType which can be found here:

### Base Metadata

```
{
    "schema":"URI://UriToBase.v0Schema",
    "nftType":"base.v0",
    "name":"Base NFT",
    "description":"An NFT using schemas."
}
```

### $Schema File

```
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type":"object",
    "required":[
        "schema",
        "nftType",
        "name",
        "description"
    ],
    "properties":{
        "schema":{
            "type":"string"
            "format":"uri"
        },
        "nftType":{
            "type":"string",
            "pattern":"(^[a-zA-Z]+.v[0-9]+$)"
        },
        "name":{
            "type":"string"
        },
        "description":{
            "type":"string"
        }
    }
}

```

Examining the 'base.v0' nftType, we can see that we include the schema, nftType, name and description which are all defined
as required properties within the schema file. These can be thought of as the foundational properties of everything in the sense
that everything has a 'name' and a can be described using a 'description'.

### Expanding to Different Use Cases

Defining the required metadata fields and schemas for different use cases and asset types is certainly not a trivial task. When deciding the properties that should or should not be included in the specification, it is important to perform extensive research into the industry that the nftType is associated with and follow industry best practices associated with what that nftType represents.

Versioning of nftTypes will allow for backwards compatability for legacy NFTs as new implementations and applications arise. Advancing an nftType should be backwards compatible with previous versions such that all prior required properties are included and required in the latter. These properties and schemas can be derived from definitions of the specific asset type found on [schema.org](https://schema.org/).

## Art/Collectible NFT Guidance:

Many of the pioneering projects in the XRPL NFT space fall under the art/collectible category; for this reason we deemed it important to derive the foundational 'art.v0' metadata format for projects and creators to adopt. After much discussion and debate on what the foundational art.v0 type should be, it became clear that the legacy 'art.v0' nftType should be a representation of other familiar standards which were previously mentioned in the original version of this proposal.

### art.v0:

The schema provided in revision 1 was meant to be an example and not a final version. Here you can find the final schema which can be used to validate nfts of the art.v0 nftType.

**Art and collectible projects that are following this guidance should note that the nftType and schema should remain constant as art.v0 and ipfs://QmNpi8rcXEkohca8iXu7zysKKSJYqCvBJn3xJwga8jXqWU respectively. The contributing marketplaces, minting and viewing applications will post an updated nftType (art.v1) and schema as the ecosystem evolves! Since versioned nftTypes are backwards compatible, there won't be any issues when nftTypes are updated. Since the content of the art.v0 schema doesn't change, uploading and pinning the schema to IPFS would result in an identical CID. If your project is utilizing IPFS, it is encouraged that you pin the schema to contribute to it availability and longevity.**

### Changes from the r1 example schema to the final art.v0 schema:

1. Removal of $id property.
   - In JSON-Schema Definitions, the $id property is used to reference a baseURL where "$ref" properties within the schema can retrieve additional schema definitions when validating an input. This definition does not refer to any external schemas and thus should not include the property. The removal of this property would also result in having an identical schema accross all issuers, an identical ipfs hash and ultimately more availability for the schema definition.
2. Fixed the regex pattern for the nftType.
   - There was a mistake in the pattern.
3. Removed contentMediaType from the asset properties.
   - Many marketplaces/viewing and consuming applications will support multiple file types for different properties. Thus this will be addressed in a seperate section.
4. Changed attribute.name to attribute.trait_type.
   - The usage of trait_type is more prominent on other networks.
5. Changed attribute.value types from ["string", "int", "float"] to ["string", "integer", "number"]
   - There was a mistake here in the nomenclature of the types.

### Schema File:

```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": [
    "schema",
    "nftType",
    "name",
    "description",
    "image"
  ],
  "properties": {
    "schema": {
      "type": "string",
      "format": "uri"
    },
    "nftType": {
      "type": "string",
      "pattern": "(^[a-zA-Z]+.v[0-9]+$)"
    },
    "name": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "image": {
      "type": "string",
      "format": "uri"
    },
    "animation": {
      "type": "string",
      "format": "uri"
    },
    "video": {
      "type": "string",
      "format": "uri"
    },
    "audio": {
      "type": "string",
      "format": "uri"
    },
    "file": {
      "type": "string",
      "format": "uri"
    },
    "collection": {
      "type": "object",
      "properties": {
        "name": {
          "type": "string"
        },
        "family": {
          "type": "string"
        }
      },
      "required": [
        "name"
      ]
    },
    "attributes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "trait_type": {
            "type": "string"
          },
          "value": {
            "type": [
              "string",
              "integer",
              "number"
            ]
          },
          "description": {
            "type": "string"
          }
        },
        "required": [
          "trait_type",
          "value"
        ]
      }
    }
  }
}
```

The art.v0 nftType defines schema, nftType, name, description and image as required properties to fall under the art.v0 category but, also provides validation support for additional properties found in other nft metadata standards such as animation, video, audio, file, collection and attributes.

This schema definition for art.v0 improves upon the one described in r1 as it no longer requires the nft creator to define their own schema because the variabilty has been stripped from the definition. A project that chooses to upload this schema to IPFS will notice that the resulting IPFS hash will be the identical.

If an NFT creator is using IPFS and following the art.v0 schema, it is encouraged to pin the following hash to ensure availability of the schema: QmNpi8rcXEkohca8iXu7zysKKSJYqCvBJn3xJwga8jXqWU

The contents of QmNpi8rcXEkohca8iXu7zysKKSJYqCvBJn3xJwga8jXqWUcan be found [here](https://x-tokenize.mypinata.cloud/ipfs/QmNpi8rcXEkohca8iXu7zysKKSJYqCvBJn3xJwga8jXqWU).

### Example 1) nftType: art.v0 with only required properties:

```
{
    "schema":"ipfs://QmNpi8rcXEkohca8iXu7zysKKSJYqCvBJn3xJwga8jXqWU",
    "nftType":"art.v0",
    "name":"ART NFT #0",
    "description":"An ART NFT with minimum properties!",
    "image":"ipfs://QmcCST9U9qwJwuBxZyTJ6ePvdJHrub7yPkAcNeCKZQ3trn"
}
```

Example 1 shows a valid art.v0 metadata file which includes the bare minimum required fields.

[Mint Tx](https://xls20.bithomp.com/explorer/D2B52B4C076F5E7C54EE6246AB094215A3E693FFAB1F9FA489EE02D742F0DC2A)
[IPFS Hash: QmPeitiHkxakhdqZsAFo4QdkkNUkCjSSzrXzCEw8sAnGAD](https://x-tokenize.mypinata.cloud/ipfs/QmPeitiHkxakhdqZsAFo4QdkkNUkCjSSzrXzCEw8sAnGAD)

### Example 2) nftType: art.v0 with all supported properties:

```
{
    "schema":"ipfs://QmNpi8rcXEkohca8iXu7zysKKSJYqCvBJn3xJwga8jXqWU",
    "nftType":"art.v0",
    "name":"ART NFT #0",
    "description":"An Art NFT with all properties supported by the art.v0 schema.",
    "image":"ipfs://QmcCST9U9qwJwuBxZyTJ6ePvdJHrub7yPkAcNeCKZQ3trn",
    "animation":"ipfs://QmfQGVwoxpqnAvDxFxW7bPsesivFas7FFjBcW9tVU5ymZQ",
    "video":"ipfs://QmWrLXyMFCB5XajAg9xRDkM9YtCvgMN7NqjmsgkoaV4k5k",
    "audio":"ipfs://QmQxMmXRrFZ8oMNtQjhaSnqosNTQFFzacT8F6kCoA4iSUd",
    "file":"ipfs://QmXVgDaHkXbyhnim8P9KmKG2khqLwnfT3fbZJRPBeVJDWY",
    "collection":
        {
            "name":"XLS-24D Examples",
            "family":"X-Tokenize Example NFTS"
        },
        "attributes":[
        {
            "trait_type":"Background",
            "description":"A dark background.",
            "value":"Black"
        },
        {
            "trait_type":"Text",
            "description":"A comforting message.",
            "value":"Hello XLS-24D"
        }
    ]
}
```

Example 2 shows a valid art.v0 metadata file which includes all of the supported fields that can be validated by the art.v0 schema definition.

[Mint Tx](https://xls20.bithomp.com/explorer/9033810BA9575F5922F0C84DEFA7C7D2840B290B734A1539661960B71E2C4E77)
[IPFS Hash: QmXA1nR96522ygY33KQoMk94LLHZLwfYkFhPU3c9jJ192o](https://x-tokenize.mypinata.cloud/ipfs/QmXA1nR96522ygY33KQoMk94LLHZLwfYkFhPU3c9jJ192o)

### Example 3) nftType: art.v0 with all supported properties and additional properties:

```
{
    "schema":"ipfs://QmNpi8rcXEkohca8iXu7zysKKSJYqCvBJn3xJwga8jXqWU",
    "nftType":"art.v0",
    "name":"ART NFT #0",
    "description":"An Art NFT with all properties supported by the art.v0 schema and additional information required by my own project!",
    "image":"ipfs://QmcCST9U9qwJwuBxZyTJ6ePvdJHrub7yPkAcNeCKZQ3trn",
    "animation":"ipfs://QmfQGVwoxpqnAvDxFxW7bPsesivFas7FFjBcW9tVU5ymZQ",
    "video":"ipfs://QmWrLXyMFCB5XajAg9xRDkM9YtCvgMN7NqjmsgkoaV4k5k",
    "audio":"ipfs://QmQxMmXRrFZ8oMNtQjhaSnqosNTQFFzacT8F6kCoA4iSUd",
    "file":"ipfs://QmXVgDaHkXbyhnim8P9KmKG2khqLwnfT3fbZJRPBeVJDWY",
    "collection":
        {
            "name":"XLS-24D Examples",
            "family":"X-Tokenize Example NFTS"
        },
    "attributes":[
        {
            "trait_type":"Background",
            "value":"Black"
        },
        {
            "trait_type":"Text",
            "value":"Hello XLS-24D",
            "someOtherInfo":"Some cool info needed here"
        }
    ],
    "additional":"Some really cool info!",
    "issuer":"rLE5f3mJwrXLzmvQbNfTcfdxMYTfrxVrgX",
    "network":"XLS20 Devnet"
    }
```

Example 3 shows a valid art.v0 metadata file which includes all of the supported fields as well as additional properties that an issuer might need for their application. Although XLS-24 enables you to add as much additional information as you'd like, it is up to the marketplace/viewing application to determine if they will handle and display that information.

[Mint Tx](https://xls20.bithomp.com/explorer/F4BBDC5FDC97833481E694FF37FC18BD822A3A22BA2B3C0E455CD6EEC6FBD43F)
[IPFS Hash: QmfYHzY8UwyobMqbQyCTbeUNfy9EJv2KvEvk6ouhUmdUj5](https://x-tokenize.mypinata.cloud/ipfs/QmfYHzY8UwyobMqbQyCTbeUNfy9EJv2KvEvk6ouhUmdUj5)

### Asset Property Media Types:

When declaring a "contentMediaType" for a property, JSON-Schema only allows for a single definition and is limiting. Marketplaces and viewing applications plan to support several media types for most of the asset properites (image, animation, video, audio, file). With this in mind below we have included a list of common media types for the different properties. These are not yet considered to be universally accepted. It is best to consult with your marketplace/viewing application of choice to determine their accepted content media types.

| Asset Property | Common Content Media Types     |
| -------------- | ------------------------------ |
| image          | .png, .jpg, .svg, .apng        |
| animation      | .gif, .mp4, .mpeg, .avi, .mov  |
| video          | .mp4, .mov, .wmv, .flv         |
| audio          | .mp4, .mp3, .wav, .m4a, .flac  |
| file           | .pdf, .doc, .docx, .xls, .html |

In the coming weeks, we will post a concise overview of known supported media types for all of the properties accross many of the popular NFT marketplaces and viewing applications.

### Conclusion

Defining a set metadata standards that applies to all NFTs is not possible because of the vast amount of use cases and asset types that an NFT can represent. It is important to emphasize that the goal here is not to provide a limiting standard but, to provide a scalable and interoperable methodology which can be applied to all nftTypes.

Although this revision includes guidance for the art.v0 nftType, it also shows that this approach enables creators to do what they do best and that's being creative. A creator can choose to add as much additional information within their metadata as they wish and it is encouraged to do so (assuming it doesn't interfere with the existing property definitions of that nftType). Adding information to your metadata, is what makes your project unique and can be used as a case study when determining revisions and additions to nftTypes (art.vX).

### Discord

To actively participate in the discussion join the [X-Tokenize Discord](https://discord.gg/mpd5msUSmf).
