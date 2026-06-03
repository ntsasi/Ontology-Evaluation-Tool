import json
import random

INPUT_FILE = "expanded_fuji_original_decomposed.json"
OUTPUT_FILE = "evaluation_dataset.json"

EXT_SAMPLE_SIZE = 100
NEW_NODE_SAMPLE_SIZE = 100


def load_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_nodes(obj):
    nodes = []

    if isinstance(obj, dict):
        if "nodeID" in obj or "name" in obj:
            nodes.append(obj)

        for v in obj.values():
            nodes.extend(extract_nodes(v))

    elif isinstance(obj, list):
        for item in obj:
            nodes.extend(extract_nodes(item))

    return nodes


def parse_names(node):
    names = node.get("EN_semanticNames", "")

    if isinstance(names, str):
        return [n.strip() for n in names.split(",") if n.strip()]
    elif isinstance(names, list):
        return names
    return []


def is_extension(node):
    meta = node.get("EN_semanticNamesMeta", {})
    if isinstance(meta, dict):
        return any(
            isinstance(v, dict) and v.get("type") == "extension"
            for v in meta.values()
        )
    return False


def classify(nodes):
    ext_cases = []
    new_cases = []

    for n in nodes:
        names = parse_names(n)

        if is_extension(n):
            ext_cases.append(n)

        # heuristic: single semantic name → new node
        if len(names) == 1:
            new_cases.append(n)

    return ext_cases, new_cases


def sample(ext, new):
    return (
        random.sample(ext, min(EXT_SAMPLE_SIZE, len(ext))),
        random.sample(new, min(NEW_NODE_SAMPLE_SIZE, len(new)))
    )


def main():
    data = load_data()
    nodes = extract_nodes(data)

    ext, new = classify(nodes)

    ext_s, new_s = sample(ext, new)

    dataset = {
        "extension_cases": ext_s,
        "new_node_cases": new_s
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print("Dataset created!")


if __name__ == "__main__":
    main()