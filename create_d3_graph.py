#!/usr/bin/env python3
"""
Simple Gephi GEXF Graph Visualizer

Creates a basic web visualization for the existing GEXF graph file.
"""

import xml.etree.ElementTree as ET
import json


def gexf_to_json(gexf_file: str = 'knowledge_graph/pycatia_mapping.gexf'):
    """Convert GEXF to JSON for web visualization"""
    
    try:
        tree = ET.parse(gexf_file)
        root = tree.getroot()
        
        # Find namespace
        ns = {'': 'http://www.gexf.net/1.2draft'}
        if root.tag.startswith('{'):
            ns[''] = root.tag.split('}')[0][1:]
        
        # Extract nodes
        nodes = []
        node_elements = root.findall('.//node', ns)
        print(f"Found {len(node_elements)} nodes")
        
        for node in node_elements[:100]:  # Limit for web visualization
            node_id = node.get('id', '')
            label = node.get('label', node_id)
            nodes.append({
                'id': node_id,
                'label': label,
                'group': hash(label.split('.')[0]) % 10  # Color by domain
            })
        
        # Extract edges
        edges = []
        edge_elements = root.findall('.//edge', ns)
        print(f"Found {len(edge_elements)} edges")
        
        for edge in edge_elements[:200]:  # Limit for web visualization
            source = edge.get('source', '')
            target = edge.get('target', '')
            if source and target:
                edges.append({
                    'source': source,
                    'target': target
                })
        
        return {
            'nodes': nodes,
            'links': edges
        }
        
    except Exception as e:
        print(f"Error reading GEXF: {e}")
        return None


def create_d3_visualization():
    """Create D3.js web visualization"""
    
    graph_data = gexf_to_json()
    if not graph_data:
        print("❌ Could not load GEXF graph data")
        return
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PyCATIA Knowledge Graph - D3 Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        
        #graph {{
            width: 100%;
            height: 80vh;
            border: 1px solid #ddd;
            background: white;
        }}
        
        .node {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 1px;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 5px;
            pointer-events: none;
            font-size: 12px;
        }}
        
        .controls {{
            margin-bottom: 10px;
        }}
        
        button {{
            margin-right: 10px;
            padding: 8px 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        
        button:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <h1>🧠 PyCATIA Knowledge Graph Visualization</h1>
    <p>Interactive visualization of {len(graph_data['nodes'])} classes and {len(graph_data['links'])} relationships</p>
    
    <div class="controls">
        <button onclick="resetSimulation()">Reset Layout</button>
        <button onclick="toggleLinks()">Toggle Links</button>
        <button onclick="zoomToFit()">Zoom to Fit</button>
    </div>
    
    <svg id="graph"></svg>
    
    <script>
        const graphData = {json.dumps(graph_data, indent=2)};
        
        const width = window.innerWidth - 40;
        const height = window.innerHeight * 0.8;
        
        const color = d3.scaleOrdinal(d3.schemeCategory10);
        
        const svg = d3.select("#graph")
            .attr("width", width)
            .attr("height", height);
        
        const g = svg.append("g");
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        // Create tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        // Create simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(50))
            .force("charge", d3.forceManyBody().strength(-100))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(20));
        
        // Create links
        const link = g.append("g")
            .selectAll(".link")
            .data(graphData.links)
            .enter().append("line")
            .attr("class", "link");
        
        // Create nodes
        const node = g.append("g")
            .selectAll(".node")
            .data(graphData.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", 8)
            .attr("fill", d => color(d.group))
            .on("mouseover", function(event, d) {{
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                tooltip.html(`<strong>${{d.label}}</strong><br/>ID: ${{d.id}}<br/>Group: ${{d.group}}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", function(d) {{
                tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);
            }})
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Add labels to nodes
        const labels = g.append("g")
            .selectAll(".label")
            .data(graphData.nodes)
            .enter().append("text")
            .attr("class", "label")
            .attr("text-anchor", "middle")
            .attr("dy", ".35em")
            .style("font-size", "10px")
            .style("pointer-events", "none")
            .text(d => d.label.split('.').pop()); // Show only class name
        
        // Update positions on tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});
        
        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        // Control functions
        let linksVisible = true;
        
        function resetSimulation() {{
            simulation.alpha(1).restart();
        }}
        
        function toggleLinks() {{
            linksVisible = !linksVisible;
            link.style("opacity", linksVisible ? 1 : 0);
        }}
        
        function zoomToFit() {{
            const bounds = g.node().getBBox();
            const fullWidth = width;
            const fullHeight = height;
            const midX = bounds.x + bounds.width / 2;
            const midY = bounds.y + bounds.height / 2;
            
            if (bounds.width == 0 || bounds.height == 0) return;
            
            const scale = Math.min(fullWidth / bounds.width, fullHeight / bounds.height) * 0.8;
            const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];
            
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        }}
        
        // Initial zoom to fit
        setTimeout(zoomToFit, 1000);
    </script>
</body>
</html>
"""
    
    with open('pycatia_graph_d3.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Created: pycatia_graph_d3.html")


if __name__ == "__main__":
    print("🌐 Creating D3.js Graph Visualization")
    print("=" * 40)
    create_d3_visualization()