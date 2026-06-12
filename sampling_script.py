import json
import random

# =========================================================
# CONFIG
# =========================================================

INPUT_FILE = "expanded_fuji_original_decomposed.json"
OUTPUT_FILE = "evaluation_dataset.json"

EXT_SAMPLE_SIZE = 50
NEW_NODE_SAMPLE_SIZE = 50

RANDOM_SEED = 84

# =========================================================
# LOAD
# =========================================================

def load_data():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# =========================================================
# EXTRACT ALL NODES
# =========================================================

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

# =========================================================
# SEMANTIC NAMES
# =========================================================

def parse_names(node):
    names = node.get("EN_semanticNames", "")

    if isinstance(names, str):
        return [n.strip() for n in names.split(",") if n.strip()]

    elif isinstance(names, list):
        return names

    return []

# =========================================================
# FILTER (NEW)
# =========================================================

def has_valid_context(meta: dict) -> bool:
    """
    Returns True only if ALL semantic entries
    have a non-empty contextSentence.
    """
    if not isinstance(meta, dict):
        return False

    for v in meta.values():
        if isinstance(v, dict):
            sentence = v.get("contextSentence", "")
            if not isinstance(sentence, str) or not sentence.strip():
                return False

    return True

# =========================================================
# BUILD SEMANTIC-LEVEL CASES
# =========================================================

def build_semantic_cases(nodes):
    extension_cases = []
    new_node_cases = []

    for node in nodes:

        meta = node.get("EN_semanticNamesMeta", {})
        if not isinstance(meta, dict):
            continue

        names = parse_names(node)

        for idx, semantic_name in enumerate(names):

            semantic_name = semantic_name.strip()

            if semantic_name not in meta:
                continue

            semantic_info = meta[semantic_name]

            semantic_type = str(
                semantic_info.get("type", "")
            ).lower()

            case = dict(node)

            case["selected_semantic_name"] = semantic_name
            case["selected_semantic_index"] = idx
            case["selected_semantic_type"] = semantic_type

            if semantic_type == "extension":
                extension_cases.append(case)

            elif semantic_type == "creating new node":
                new_node_cases.append(case)

    return extension_cases, new_node_cases

# =========================================================
# SAMPLE
# =========================================================

def sample_cases(extension_cases, new_node_cases):

    random.seed(RANDOM_SEED)

    ext_sample = random.sample(
        extension_cases,
        min(EXT_SAMPLE_SIZE, len(extension_cases))
    )

    new_sample = random.sample(
        new_node_cases,
        min(NEW_NODE_SAMPLE_SIZE, len(new_node_cases))
    )

    return ext_sample, new_sample

# =========================================================
# MAIN
# =========================================================

def main():

    print("Loading ontology...")
    data = load_data()

    print("Extracting nodes...")
    nodes = extract_nodes(data)

    print(f"Nodes found: {len(nodes)}")

    extension_cases, new_node_cases = build_semantic_cases(nodes)

    print(f"Extension semantic terms available: {len(extension_cases)}")
    print(f"New-node semantic terms available: {len(new_node_cases)}")

    # =====================================================
    # 🔥 FILTER STEP (IMPORTANT ADDITION)
    # =====================================================

    extension_cases = [
        c for c in extension_cases
        if has_valid_context(c.get("EN_semanticNamesMeta", {}))
    ]

    new_node_cases = [
        c for c in new_node_cases
        if has_valid_context(c.get("EN_semanticNamesMeta", {}))
    ]

    print(f"After filtering:")
    print(f"  Extension cases: {len(extension_cases)}")
    print(f"  New-node cases: {len(new_node_cases)}")

    # =====================================================

    ext_sample, new_sample = sample_cases(extension_cases, new_node_cases)

    dataset = {
        "semantic_name_extension": ext_sample,
        "new_node_extension": new_sample
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print()
    print(f"Saved {len(ext_sample)} extension cases")
    print(f"Saved {len(new_sample)} new node cases")
    print(f"Random seed: {RANDOM_SEED}")
    print(f"Output file: {OUTPUT_FILE}")

# =========================================================

if __name__ == "__main__":
    main()