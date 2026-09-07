import os
import wmill


SCHEMA_REGISTRY = {
    "phieu_thu": "f/information_extraction/schema_phieu_thu",
}


def get_schema(doc_type: str):
    path = SCHEMA_REGISTRY.get(doc_type)

    if not path:
        return None

    return wmill.get_resource(path)