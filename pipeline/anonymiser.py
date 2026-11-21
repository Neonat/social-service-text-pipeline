from collections import defaultdict

from pipeline.models import RedactedText


def anonymise(redacted: RedactedText) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}
    type_counter: dict[str, int] = defaultdict(int)
    result = redacted.redacted

    for entity in sorted(redacted.entities, key=lambda entity: entity.start):
        type_counter[entity.entity_type] += 1
        placeholder = f"[{entity.entity_type}_{type_counter[entity.entity_type]}]"
        mapping[placeholder] = entity.original
        result = result.replace(entity.placeholder, placeholder, 1)

    return result, mapping


def restore(text: str, mapping: dict[str, str]) -> str:
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text
