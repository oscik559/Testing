import xml.etree.ElementTree as ET
import json
from pathlib import Path

def main():
    print("Creating simple D3 visualization...")
    
    gexf_file = "pycatia_mapping.gexf"
    if not Path(gexf_file).exists():
        print(f"GEXF file not found: {gexf_file}")
        return
    
    # Parse GEXF
    tree = ET.parse(gexf_file)
    root = tree.getroot()
    
    # Simple namespace handling
    ns = {"": "http://www.gexf.net/1.2draft"}
    if root.tag.startswith("{"):
        ns[""] = root.tag.split("}")[0][1:]
    
    # Extract nodes (limit for demo)
    nodes = []
    for i, node in enumerate(root.findall(".//node", ns)):
        if i >= 100: break  # Limit nodes
        node_id = node.get("id", "")
        label = node.get("label", node_id)
        nodes.append({"id": node_id, "label": label, "group": i % 10})
    
    # Extract edges (limit for demo)  
    edges = []
    for i, edge in enumerate(root.findall(".//edge", ns)):
        if i >= 200: break  # Limit edges
        source = edge.get("source", "")
        target = edge.get("target", "")
        if source and target:
            edges.append({"source": source, "target": target})
    
    print(f"Loaded {len(nodes)} nodes and {len(edges)} edges")
    
    # Create simple HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PyCATIA Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: Arial; margin: 20px; }}
        #graph {{ width: 800px; height: 600px; border: 1px solid #ccc; }}
        .node {{ fill: steelblue; stroke: white; stroke-width: 2px; }}
        .link {{ stroke: #999; stroke-width: 1px; }}
    </style>
</head>
<body>
    <h1>PyCATIA Knowledge Graph</h1>
    <p>{len(nodes)} nodes, {len(edges)} edges</p>
    <svg id="graph"></svg>
    
    <script>
        const data = {json.dumps({"nodes": nodes, "links": edges})};
        
        const svg = d3.select("#graph").attr("width", 800).attr("height", 600);
        
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-100))
            .force("center", d3.forceCenter(400, 300));
        
        const link = svg.append("g")
            .selectAll(".link")
            .data(data.links)
            .enter().append("line")
            .attr("class", "link");
        
        const node = svg.append("g")
            .selectAll(".node")
            .data(data.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", 5);
        
        simulation.on("tick", () => {{
            link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            node.attr("cx", d => d.x).attr("cy", d => d.y);
        }});
    </script>
</body>
</html>"""
    
    # Save HTML
    with open("pycatia_graph_d3.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("Created: pycatia_graph_d3.html")

if __name__ == "__main__":
    main()
