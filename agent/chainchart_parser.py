# agent/chainchart_parser.py

def parse_chainchart(diagram_json):
    """
    Parses the ChainChart diagram JSON into node/edge structures
    usable by the executor.
    """

    nodes = {node["id"]: node for node in diagram_json["nodes"]}

    edges = {}
    for edge in diagram_json["edges"]:
        edges.setdefault(edge["from"], []).append(edge["to"])

    return nodes, edges
