import streamlit as st
import json
import re
from collections import Counter
from streamlit.components.v1 import html

if "results" not in st.session_state:
    st.session_state.results = []

# remember position independently for each case type
if "extension_index" not in st.session_state:
    st.session_state.extension_index = 0

if "new_node_index" not in st.session_state:
    st.session_state.new_node_index = 0

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Ontology Evaluation Tool",
    layout="wide"
)

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<h1 style='text-align:center;'>
<br>
Ontology Evaluation Tool
</h1>
""", unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# INTRODUCTION DROPDOWN
# =========================================================

with st.expander(
    "Project Introduction & Evaluation Instructions",
    expanded=False
):

    st.markdown("""
    <div style="
        background:white;
        padding:24px;
        border-radius:12px;
        line-height:1.9;
        font-size:16px;
        box-shadow:0 1px 6px rgba(0,0,0,0.08);
    ">

    The purpose of this user interface (UI) is to evaluate automatically generated extensions of an ontology in the manufacturing domain, based on source material derived from manufacturing manuals. An ontology refers to a hierarchical knowledge structure that organizes concepts. Within this structure, nodes are distinct points that represent a specific concept and each node is described by one or more semantic names. Two types of ontology extensions are evaluated in this study. 1) semantic_name_extension_cases: This first type extends the description of a leaf node (which sits at the end of a branch in the hierarchy) in the ontology by adding a new "semantic name" & 2) new_node_extension_cases: This second type adds a new node under an existing leaf node of the ontology, along with its semantic name(s).
    <br>    
    This UI was created to provide an efficient tool to allow human evaluators to organize and assess whether randomly selected test cases within the ontology are semantically correct, contextually meaningful, and properly positioned within the hierarchy, based on a given dataset. Consisting of two modes (semantic_name_extension & new_node_extension), users can switch through relevant datasets for evaluation using the “Case Type” dropdown menu. Once users have selected the set they wish to evaluate, they can proceed to the next case using the “Case Index” bar. There are 50 cases to evaluate per set (indexed from 0-49) and users must evaluate cases sequentially in the order in which they appear. Users can revisit previous cases by toggling through the “Case Index” bar and updating their evaluation score. Once saved, the most recent result will be recorded. *To download saved results to a JSON file for later analysis, please ensure to select the “Download” button once you have completed a session and before closing this app, as unsaved exports will not be retained.
    

    This UI tool consists of three panels. The “Source Context” panel displays contextual evidence retrieved from the metadata associated with the semantic names of the selected node. The “Ontology Tree Visualization” panel displays the node’s hierarchical path, local neighborhood (most relevant branches of the tree), and full expandable ontology tree. The “Evaluation” panel contains the node’s name and ID, semantic names, a redundancy check to determine whether a semantic name already exists elsewhere in the ontology, and Likert-scale sliders (scores 1-5) to determine Semantic Appropriateness, Context Consistency, and Hierarchy Appropriateness. A corresponding scoring guide for each case type is located below. 
    <br>
    <h6>Designed by: Nicolas Tsasis</h6>

    </div>
    """, unsafe_allow_html=True)


# =========================================================
# EXTENSION CASE SCORING GUIDE
# =========================================================

with st.expander(
    "Semantic Name Extension Case Scoring Guide",
    expanded=False
):

    st.markdown("""
    <div style="
        background:white;
        padding:20px;
        border-radius:12px;
        line-height:1.8;
        font-size:15px;
        box-shadow:0 1px 6px rgba(0,0,0,0.08);
    ">

    <h4 style="text-align:center;">Semantic Name Extension Case Scoring Guide</h4>
    <br>
    Semantic name extension cases occur when a new semantic term is added to an existing node. For example, if the ontology hierarchy already contains a node called "LiquidTank", the system can propose that additional semantic names such as "liquid reservoir" be added. In this case, an evaluator would assess whether the semantic name appropriately represents the node concept, is supported by the source context, and whether the node is correctly located within the ontology.
    <br>
    <br>
    <b>1. Completely Incorrect</b><br>
    • Semantic name does not belong to node<br>
    • No meaningful relationship<br><br>

    <b>2. Mostly Incorrect</b><br>
    • Weak or unclear connection<br>
    • Poor alignment with ontology structure<br><br>

    <b>3. Partially Correct</b><br>
    • Some relevance but ambiguous<br>
    • Could belong elsewhere<br><br>

    <b>4. Mostly Correct</b><br>
    • Good fit with minor issues<br>
    • Slight redundancy or phrasing issues<br><br>

    <b>5. Fully Correct</b><br>
    • Perfect semantic fit<br>
    • Clearly belongs in this node

    </div>
    """, unsafe_allow_html=True)


# =========================================================
# NEW NODE CASE SCORING GUIDE
# =========================================================

with st.expander(
    "New Node Extension Scoring Guide",
    expanded=False
):

    st.markdown("""
    <div style="
        background:white;
        padding:20px;
        border-radius:12px;
        line-height:1.8;
        font-size:15px;
        box-shadow:0 1px 6px rgba(0,0,0,0.08);
    ">

    <h4 style="text-align:center;">New Node Case Scoring Guide</h4>
    <br>
    New node cases occur when the system determines an existing node is insufficient and creates a new node within the ontology. For example, under the existing hierarchy "Building → Garage → Door", the system can create a new node (i.e. "FrontDoor"). In this case, an evaluator would assess both the relevant semantic name (same process as above) and newly created node, including whether the node concept is meaningful and non-redundant, the node name is appropriate, and whether the node is correctly located within the ontology.
    <br>
    <br>
    <b>1. Completely Incorrect</b><br>
    • Node name unclear or invalid<br>
    • Wrong or meaningless placement<br><br>

    <b>2. Mostly Incorrect</b><br>
    • Weak concept or poor placement<br>
    • Structural mismatch in ontology<br><br>

    <b>3. Partially Correct</b><br>
    • Reasonable concept but debatable placement<br>
    • Naming unclear or not generalizable<br><br>

    <b>4. Mostly Correct</b><br>
    • Good conceptual fit<br>
    • Minor naming or structure issues<br><br>

    <b>5. Fully Correct</b><br>
    • Clear, meaningful, and well-placed node<br>
    • Consistent with ontology design

    </div>
    """, unsafe_allow_html=True)

# =========================================================
# CONFIG
# =========================================================

DATA_FILE = "evaluation_dataset.json"
RESULTS_FILE = "results.json"

# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

.panel-title {
    margin-top: 0;
    margin-bottom: 18px;
    font-size: 28px;
    font-weight: 700;
}

.section-title {
    font-size: 20px;
    margin-top: 22px;
    margin-bottom: 12px;
    font-weight: 700;
}

.context-card {
    background: white;
    padding: 14px;
    margin-bottom: 12px;
    border-left: 6px solid #2563eb;
    border-radius: 10px;
    line-height: 1.7;
    font-size: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.info-box {
    background: white;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.path-box {
    background: white;
    border-radius: 8px;
    padding: 10px;
    border: 1px solid #d1d5db;
    font-family: monospace;
    margin-bottom: 10px;
}

.neighbor-item {
    background: white;
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 6px;
    border-left: 4px solid #059669;
    font-size: 14px;
}

.selected-neighbor {
    background: #d1fae5;
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 6px;
    border-left: 4px solid #065f46;
    font-weight: 700;
    font-size: 14px;
}

.semantic-item {
    background: white;
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 6px;
    border-left: 4px solid #dc2626;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# =========================================================
# VALIDATE
# =========================================================

if (
    "semantic_name_extension" not in data
    or "new_node_extension" not in data
):
    st.error(
        "Dataset format invalid.\n"
        "Missing semantic_name_extension or new_node_extension."
    )
    st.stop()

# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text_spacing(text):

    if not text:
        return text

    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    text = re.sub(
        r'([.,;:!?()])([A-Za-z])',
        r'\1 \2',
        text
    )

    text = re.sub(r'\s+', ' ', text)

    return text.strip()

# =========================================================
# HELPERS
# =========================================================

def parse_semantic_names(node):

    names = node.get("EN_semanticNames", "")

    if isinstance(names, str):

        return [
            n.strip()
            for n in names.split(",")
            if n.strip()
        ]

    elif isinstance(names, list):

        return names

    return []

def redundancy_check(names):

    counts = Counter(names)

    return {
        k: v
        for k, v in counts.items()
        if v > 1
    }

# =========================================================
# BUILD TREE STRUCTURE
# =========================================================

def build_tree(paths):

    tree = {}

    for path in paths:

        parts = path.split("-")

        current = tree

        for p in parts:

            current = current.setdefault(p, {})

    return tree

# =========================================================
# CONVERT TREE TO D3 FORMAT
# =========================================================

def tree_to_d3(name, subtree):

    return {
        "name": name,
        "children": [
            tree_to_d3(k, v)
            for k, v in subtree.items()
        ]
    }

# =========================================================
# LOCAL NEIGHBORS
# =========================================================

def get_local_neighbors(
    current_path,
    all_paths
):

    current_parts = current_path.split("-")

    neighbors = []

    for path in all_paths:

        parts = path.split("-")

        overlap = 0

        for a, b in zip(
            current_parts,
            parts
        ):

            if a == b:
                overlap += 1
            else:
                break

        if overlap >= max(
            1,
            len(current_parts) - 2
        ):

            neighbors.append(path)

    return neighbors[:15]

# =========================================================
# BUILD TREE
# =========================================================

all_cases = (
    data["semantic_name_extension"]
    + data["new_node_extension"]
)

all_paths = sorted(list(set([
    c.get("value", "")
    for c in all_cases
    if c.get("value")
])))

tree = build_tree(all_paths)

d3_tree = {
    "name": "ROOT",
    "children": [
        tree_to_d3(k, v)
        for k, v in tree.items()
    ]
}

# =========================================================
# TOP CONTROLS
# =========================================================

top1, top2 = st.columns([1, 1])

with top1:

    case_type = st.selectbox(
        "Case Type",
        [
            "semantic_name_extension",
            "new_node_extension"
        ]
    )

cases = data[case_type]

# choose the correct stored index
if case_type == "semantic_name_extension":
    current_index = st.session_state.extension_index
else:
    current_index = st.session_state.new_node_index

with top2:

    case_index = st.number_input(
        "Case Index (50 cases, 0-49)",
        min_value=0,
        max_value=len(cases) - 1,
        value=current_index,
        step=1
    )

# save current position back to session state
if case_type == "semantic_name_extension":
    st.session_state.extension_index = case_index
else:
    st.session_state.new_node_index = case_index

case = cases[case_index]

# =========================================================
# CURRENT NODE
# =========================================================

semantic_names = parse_semantic_names(case)

meta = case.get(
    "EN_semanticNamesMeta",
    {}
)

# =========================================================
# SEMANTIC TERM INDEX
# =========================================================

semantic_index = case.get(
    "selected_semantic_index",
    0
)

selected_semantic_name = case.get(
    "selected_semantic_name",
    semantic_names[semantic_index]
)

target_context = ""

target_meta = {}

if (
    isinstance(meta, dict)
    and selected_semantic_name in meta
):

    target_meta = meta[selected_semantic_name]

    target_context = clean_text_spacing(
        target_meta.get(
            "contextSentence",
            ""
        )
    )

duplicates = redundancy_check(
    semantic_names
)

path = case.get("value", "N/A")

neighbors = get_local_neighbors(
    path,
    all_paths
)

# =========================================================
# MAIN LAYOUT
# =========================================================

left, middle, right = st.columns(
    [1.2, 2.2, 1.2]
)

# =========================================================
# LEFT PANEL
# =========================================================

with left:

    st.markdown("""
    <div class="panel-title">
    Source Context Panel
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-title">
    Added Semantic Name
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
    <b>{selected_semantic_name}</b>
    </div>
    """, unsafe_allow_html=True)

    semantic_type = target_meta.get(
        "type",
        "unknown"
    )

    st.markdown(f"""
    <div class="info-box">
    <b>Metadata Type:</b> {semantic_type}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-title">
    Source Context
    </div>
    """, unsafe_allow_html=True)

    if target_context:

        st.markdown(f"""
        <div class="context-card">
        {target_context}
        </div>
        """, unsafe_allow_html=True)

    else:

        st.info(
            "No source context available for this semantic term."
        )

# =========================================================
# MIDDLE PANEL
# =========================================================

with middle:

    st.markdown("""
    <div class="panel-title">
    Ontology Tree Visualization Panel
    </div>
    """, unsafe_allow_html=True)

    path_title = (
    "A tree path containing the extended node"
    if case_type == "semantic_name_extension"
    else "A tree path containing the new node"
    )

    st.markdown(f"""
    <div class="section-title">
    {path_title}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="path-box">
        {path}
        </div>
        """,
        unsafe_allow_html=True
    )

    path_title = (
    "Paths of the sibling nodes of the extended nodes"
    if case_type == "semantic_name_extension"
    else "Paths of the sibling nodes of the new nodes"
    )

    st.markdown(f"""
    <div class="section-title">
    {path_title}
    </div>
    """, unsafe_allow_html=True)

    for n in neighbors:

        if n == path:

            st.markdown(
                f"""
                <div class="selected-neighbor">
                {n}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"""
                <div class="neighbor-item">
                {n}
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("""
    <div class="section-title">
    Interactive Zoomable Ontology Tree
    </div>
    """, unsafe_allow_html=True)

    tree_json = json.dumps(d3_tree)

    current_leaf = path.split("-")[-1]

    d3_html = f"""
    <!DOCTYPE html>
    <html>
    <head>

        <script src="https://d3js.org/d3.v7.min.js"></script>

        <style>

            body {{
                margin: 0;
                overflow: hidden;
                font-family: Arial;
            }}

            .node circle {{
                stroke-width: 2px;
                cursor: pointer;
            }}

            .node text {{
                font-size: 12px;
                user-select: none;
            }}

            .link {{
                fill: none;
                stroke: #999;
                stroke-opacity: 0.6;
                stroke-width: 1.5px;
            }}

        </style>

    </head>

    <body>

    <svg width="100%" height="1400"></svg>

    <script>

    const data = {tree_json};

    const width = 2200;
    const height = 1400;

    const svg = d3.select("svg")
        .attr("viewBox", [0, 0, width, height]);

    const g = svg.append("g");

    svg.call(
        d3.zoom()
            .scaleExtent([0.1, 6])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }})
    );

    const root = d3.hierarchy(data);

    root.x0 = height / 2;
    root.y0 = 0;

    root.children.forEach(collapse);

    function collapse(d) {{
        if (d.children) {{
            d._children = d.children;
            d._children.forEach(collapse);
            d.children = null;
        }}
    }}

    expandToTarget(root, "{current_leaf}");

    function expandToTarget(node, target) {{

        if (node.data.name === target) {{
            return true;
        }}

        let children = node._children || node.children;

        if (children) {{

            for (let child of children) {{

                if (expandToTarget(child, target)) {{

                    if (node._children) {{
                        node.children = node._children;
                        node._children = null;
                    }}

                    return true;
                }}
            }}
        }}

        return false;
    }}

    const treeLayout = d3.tree()
        .nodeSize([35, 240]);

    update(root);

    function update(source) {{

        treeLayout(root);

        const nodes = root.descendants();
        const links = root.links();

        const link = g.selectAll(".link")
            .data(links, d => d.target.id || (d.target.id = Math.random()));

        link.enter()
            .append("path")
            .attr("class", "link")
            .merge(link)
            .attr("d", d3.linkHorizontal()
                .x(d => d.y + 100)
                .y(d => d.x + 50)
            );

        link.exit().remove();

        const node = g.selectAll(".node")
            .data(nodes, d => d.id || (d.id = Math.random()));

        const nodeEnter = node.enter()
            .append("g")
            .attr("class", "node")
            .attr(
                "transform",
                d => `translate(${{source.y0 + 100}},${{source.x0 + 50}})`
            )
            .on("click", click);

        nodeEnter.append("circle")
            .attr("r", 1e-6)
            .attr("fill", d => {{

                if (d.data.name === "{current_leaf}") {{
                    return "#16a34a";
                }}

                return d._children
                    ? "#2563eb"
                    : "#60a5fa";
            }})
            .attr("stroke", d => {{

                if (d.data.name === "{current_leaf}") {{
                    return "#065f46";
                }}

                return "#1e3a8a";
            }});

        nodeEnter.append("text")
            .attr("dy", 4)
            .attr("x", d => d._children ? -14 : 14)
            .style("text-anchor", d => d._children ? "end" : "start")
            .text(d => d.data.name)
            .style("fill-opacity", 1e-6);

        const nodeUpdate = nodeEnter.merge(node);

        nodeUpdate.transition()
            .duration(350)
            .attr(
                "transform",
                d => `translate(${{d.y + 100}},${{d.x + 50}})`
            );

        nodeUpdate.select("circle")
            .transition()
            .duration(350)
            .attr("r", 7)
            .attr("fill", d => {{

                if (d.data.name === "{current_leaf}") {{
                    return "#16a34a";
                }}

                return d._children
                    ? "#2563eb"
                    : "#60a5fa";
            }});

        nodeUpdate.select("text")
            .transition()
            .duration(350)
            .style("fill-opacity", 1);

        const nodeExit = node.exit()
            .transition()
            .duration(350)
            .attr(
                "transform",
                d => `translate(${{source.y + 100}},${{source.x + 50}})`
            )
            .remove();

        nodeExit.select("circle")
            .attr("r", 1e-6);

        nodeExit.select("text")
            .style("fill-opacity", 1e-6);

        nodes.forEach(d => {{
            d.x0 = d.x;
            d.y0 = d.y;
        }});
    }}

    function click(event, d) {{

        if (d.children) {{

            d._children = d.children;
            d.children = null;

        }} else {{

            d.children = d._children;
            d._children = null;
        }}

        update(d);
    }}

    </script>

    </body>
    </html>
    """

    html(
        d3_html,
        height=1400,
        scrolling=True
    )

# =========================================================
# RIGHT PANEL
# =========================================================

with right:

    st.markdown("""
    <div class="panel-title">
    Evaluation Panel
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-title">
    Added Node Information
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
    <b>Name:</b> {case.get('name', 'N/A')}<br><br>
    <b>NodeID:</b> {case.get('nodeID', 'N/A')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-title">
    Added Semantic Name
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="semantic-item">
        <b>{selected_semantic_name}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="section-title">
    Redundancy Check
    </div>
    """, unsafe_allow_html=True)

    if duplicates:

        for word, count in duplicates.items():

            st.warning(
                f"'{word}' appears {count} times"
            )

    else:

        st.success(
            "No exact duplicates found"
        )

    is_extension = False

    if isinstance(meta, dict):

        is_extension = any(
            isinstance(v, dict)
            and v.get("type") == "extension"
            for v in meta.values()
        )

    st.markdown(
        f"""
        <div class="info-box">
        <b>Contains Extension:</b> {is_extension}
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # TERM-LEVEL EVALUATION
    # =====================================================

    st.markdown("""
    <div class="section-title">
    Semantic Term Evaluation
    </div>
    """, unsafe_allow_html=True)
    
    confused_no_context = st.checkbox(
    "Insufficient source context / Unable to evaluate"
    )

    score1 = st.slider(
        "Semantic Meaning Alignment with Node Concept",
        1,
        5,
        1
    )

    score2 = st.slider(
        "Context Consistency",
        1,
        5,
        1
    )

    score3 = st.slider(
        "Appropriateness of Placement in Current Node",
        1,
        5,
        1
    )

    # =====================================================
    # NEW NODE DETECTION
    # =====================================================
    selected_type = case.get(
        "selected_semantic_type",
        ""
    ).lower()

    contains_new_node = (
        selected_type == "creating new node"
    )
    # =====================================================
    # NODE-LEVEL EVALUATION
    # =====================================================

    if contains_new_node:

        st.markdown("---")

        st.markdown("""
        <div class="section-title">
        Additional New Node Evaluation
        </div>
        """, unsafe_allow_html=True)

        st.info(
            "This node contains semantic entries labeled "
            "'creating new node'. "
            "Please also evaluate the node itself using the following criteria."
        )

        node_score1 = st.slider(
            "New Node Semantic Correctness",
            1,
            5,
            1
        )

        node_score2 = st.slider(
            "Node Naming Quality",
            1,
            5,
            1
        )

        node_score3 = st.slider(
            "Hierarchy Placement Correctness",
            1,
            5,
            1
        )

        node_score4 = st.slider(
            "Node Necessity / Non-Redundancy",
            1,
            5,
            1
        )

    else:

        node_score1 = None
        node_score2 = None
        node_score3 = None
        node_score4 = None


    # =====================================================
    # SAVE
    # =====================================================
    if st.button(
        "Save",
        key=f"{case_type}_{case_index}_{semantic_index}"
    ):

    # =====================================================
    # PREVENT DUPLICATES (overwrite behavior)
    # =====================================================

        st.session_state.results = [
            r for r in st.session_state.results
            if not (
                r["case_type"] == case_type and
                r["nodeID"] == case.get("nodeID") and
                r["semantic_index"] == semantic_index
            )
        ]

# =====================================================
# FORCE ZERO IF USER MARKED CONFUSED
# =====================================================

        if confused_no_context:
            score1 = 0
            score2 = 0
            score3 = 0

            if contains_new_node:
                node_score1 = 0
                node_score2 = 0
                node_score3 = 0
                node_score4 = 0

    # =====================================================
    # BUILD RESULT
    # =====================================================

        result = {
            "case_type": case_type,
            "nodeID": case.get("nodeID"),
            "name": case.get("name"),
            "path": path,
            "semantic_index": semantic_index,
            "target_semantic_name": selected_semantic_name,
            "target_semantic_type": semantic_type,
            "target_context": target_context,
            "contains_extension": is_extension,
            "semantic_alignment_score": score1,
            "context_consistency_score": score2,
            "placement_appropriateness_score": score3,
            "confused_no_context": confused_no_context,
            "contains_creating_new_node": contains_new_node,
            "new_node_semantic_correctness": node_score1,
            "new_node_naming_quality": node_score2,
            "new_node_hierarchy_correctness": node_score3,
            "new_node_nonredundancy": node_score4
        }

    # append updated result
        st.session_state.results.append(result)

        st.success("Evaluation saved")

        st.download_button(
            "Download All Results (JSON)",
            data=json.dumps(st.session_state.results, indent=2),
            file_name="results.json",
            mime="application/json"
        )