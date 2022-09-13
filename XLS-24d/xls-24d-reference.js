{
    "$id": "https://<TBD>/nft.schema.json",
    "$schema": "https://<TBD>/schema/xrpl/v1.0/nft.schema.json",
    "description": "XRPL NFT schema version 1.0",
    "$defs": {
        "attribute": {
            "type": "object",
            "required": [
                "trait_type",
                "value"
            ],
            "properties": {
                "value": {
                    "type": "string"
                },
                "trait_type": {
                    "type": "string"
                }
            }
        }
    },
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
            "type": "string"
        },
        "nftType": {
            "type": "string",
            "enum": [
                "image",
                "animation",
                "video",
                "audio",
                "document",
                "other"
            ]
        },
        "nftTypeVersion": {
            "type": "string"
        },
        "name": {
            "type": "string"
        },
        "creator": {
            "type": "string"
        },
        "description": {
            "type": "string"
        },
        "image": {
            "type": "string"
        },
        "animation_url": {
            "type": "string",
            "contentMediaType": "video/mp4",
            "format": "uri"
        },
        "video": {
            "type": "string",
            "contentMediaType": "video/mp4",
            "format": "uri"
        },
        "audio": {
            "type": "string",
            "contentMediaType": "audio/mpeg",
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
            }
        },
        "attributes": {
            "type": "array",
            "items": {
                "$ref": "#/$defs/attribute"
            }
        },
        "external_url": {
            "type": "string"
        },
        "is_explicit": {
            "type": "boolean"
        }
    }
}