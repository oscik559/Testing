#!/usr/bin/env python3
"""
Enhanced    # Sort classes by method count - USE ALL CLASSES
    class_method_counts.sort(key=lambda x: x[1], reverse=True)
    selected_classes = class_method_counts  # ALL classes, sorted by importance
    
    print(f"📋 Processing ALL {len(selected_classes)} classes")TIA Knowledge Graph Visualizer

Creates an interactive D3 visualization that properly handles the class-method relationship structure.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


def create_interactive_d3_from_json():
    """Create interactive D3 visualization directly from JSON (better approach)"""
    
    print("🧠 Creating Interactive D3 from Knowledge Graph JSON")
    print("=" * 50)
    
    # Load JSON data
    with open("pycatia_knowledge_graph.json", "r") as f:
        kg_data = json.load(f)
    
    classes = kg_data.get("classes", {})
    
    print(f"📊 Processing {len(classes)} classes...")
    
    # Create nodes with proper data
    nodes = []
    node_map = {}
    
    # Sort classes by method count to get most important ones
    class_method_counts = []
    for class_name, class_info in classes.items():
        method_count = len(class_info.get("methods", {}))
        class_method_counts.append((class_name, method_count, class_info))
    
    # Sort by method count - USE ALL CLASSES
    class_method_counts.sort(key=lambda x: x[1], reverse=True)
    selected_classes = class_method_counts  # ALL classes, sorted by importance
    
    print(f"📋 Selected top {len(selected_classes)} classes")
    
    # Create nodes
    for i, (class_name, method_count, class_info) in enumerate(selected_classes):
        domain = class_info.get('domain', 'unknown')
        nodes.append({
            'id': str(i),
            'name': class_name,
            'label': class_name,
            'group': hash(domain) % 12,
            'method_count': method_count,
            'domain': domain,
            'is_factory': class_info.get('is_factory', False),
            'is_collection': class_info.get('is_collection', False),
            'full_name': class_info.get('full_name', class_name),
            'docstring': (class_info.get('docstring', '')[:200] + '...') if class_info.get('docstring', '') else 'No documentation'
        })
        node_map[class_name] = i
    
    # Create edges based on inheritance and domain relationships
    edges = []
    
    # Inheritance edges
    for i, (class_name, _, class_info) in enumerate(selected_classes):
        parent_classes = class_info.get('parent_classes', [])
        for parent in parent_classes:
            if parent in node_map:
                edges.append({
                    'source': str(i),
                    'target': str(node_map[parent]),
                    'type': 'inheritance',
                    'strength': 1.5
                })
    
    # Domain clustering edges (connect classes in same domain)
    domain_groups = defaultdict(list)
    for i, (class_name, _, class_info) in enumerate(selected_classes):
        domain = class_info.get('domain', 'unknown')
        domain_groups[domain].append(i)
    
    # Create loose connections within domains
    for domain, class_indices in domain_groups.items():
        if len(class_indices) > 1:
            # Connect each class to a few others in same domain
            for i, class_idx in enumerate(class_indices[:5]):  # Limit connections
                for j in range(1, min(3, len(class_indices) - i)):
                    target_idx = class_indices[(i + j) % len(class_indices)]
                    edges.append({
                        'source': str(class_idx),
                        'target': str(target_idx),
                        'type': 'domain',
                        'strength': 0.5
                    })
    
    graph_data = {'nodes': nodes, 'links': edges}
    
    print(f"✅ Graph created: {len(nodes)} nodes, {len(edges)} edges")
    
    # Create enhanced HTML
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>🧠 PyCATIA Knowledge Graph - Interactive Explorer</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            overflow: hidden;
        }}
        
        .header {{
            padding: 15px 20px;
            background: rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .title {{
            font-size: 1.8em;
            font-weight: 600;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .stats {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .controls {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        
        button {{
            padding: 8px 16px;
            background: rgba(255,255,255,0.15);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.3s ease;
            backdrop-filter: blur(5px);
        }}
        
        button:hover {{
            background: rgba(255,255,255,0.25);
            transform: translateY(-1px);
        }}
        
        #graph {{
            width: 100vw;
            height: calc(100vh - 80px);
        }}
        
        .node {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 1.5px;
            transition: all 0.3s ease;
        }}
        
        .node:hover {{
            stroke-width: 3px;
        }}
        
        .node.factory {{
            stroke: #ffd700;
            stroke-width: 2.5px;
        }}
        
        .node.collection {{
            stroke: #ff6b6b;
            stroke-width: 2.5px;
        }}
        
        .link {{
            stroke-opacity: 0.4;
            fill: none;
        }}
        
        .link.inheritance {{
            stroke: #4ecdc4;
            stroke-width: 2px;
            stroke-opacity: 0.8;
        }}
        
        .link.domain {{
            stroke: #95a5a6;
            stroke-width: 1px;
            stroke-opacity: 0.3;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 15px;
            background: rgba(0, 0, 0, 0.95);
            color: white;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            pointer-events: none;
            font-size: 13px;
            max-width: 350px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            backdrop-filter: blur(10px);
            z-index: 1000;
        }}
        
        .tooltip .class-name {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #4ecdc4;
        }}
        
        .tooltip .info-row {{
            margin: 4px 0;
        }}
        
        .tooltip .label {{
            font-weight: 600;
            color: #bdc3c7;
        }}
        
        .search-box {{
            padding: 6px 12px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 15px;
            color: white;
            font-size: 12px;
            width: 200px;
        }}
        
        .search-box::placeholder {{
            color: rgba(255,255,255,0.6);
        }}
        
        .node-label {{
            font-size: 10px;
            fill: white;
            text-anchor: middle;
            pointer-events: none;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🧠 PyCATIA Knowledge Graph Explorer</div>
                .stats">{len(nodes)} classes • {len(edges)} relationships • Complete PyCATIA Library</div>
        <div class="controls">
            <input type="text" class="search-box" placeholder="Search classes..." id="searchBox">
            <button onclick="resetView()">🔄 Reset</button>
            <button onclick="zoomToFit()">🔍 Fit</button>
            <button onclick="toggleFactories()">🏭 Factories</button>
            <button onclick="toggleCollections()">📦 Collections</button>
            <button onclick="toggleLabels()">🏷️ Labels</button>
        </div>
    </div>
    
    <svg id="graph"></svg>
    
    <script>
        const data = {json.dumps(graph_data, indent=2)};
        
        // Set up SVG
        const svg = d3.select("#graph");
        const width = window.innerWidth;
        const height = window.innerHeight - 80;
        
        svg.attr("width", width).attr("height", height);
        
        const g = svg.append("g");
        
        // Color scale
        const color = d3.scaleOrdinal(d3.schemeSet3);
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .on("zoom", (event) => g.attr("transform", event.transform));
        
        svg.call(zoom);
        
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        // Force simulation
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links)
                .id(d => d.id)
                .distance(d => d.type === 'inheritance' ? 80 : 120)
                .strength(d => d.strength || 0.5))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => Math.max(8, Math.sqrt(d.method_count) * 2)));
        
        // Create links
        const link = g.append("g")
            .selectAll(".link")
            .data(data.links)
            .enter().append("line")
            .attr("class", d => `link ${{d.type}}`);
        
        // Create nodes
        const node = g.append("g")
            .selectAll(".node")
            .data(data.nodes)
            .enter().append("circle")
            .attr("class", d => {{
                let classes = "node";
                if (d.is_factory) classes += " factory";
                if (d.is_collection) classes += " collection";
                return classes;
            }})
            .attr("r", d => Math.max(6, Math.min(20, Math.sqrt(d.method_count) * 1.5)))
            .attr("fill", d => color(d.group))
            .on("mouseover", function(event, d) {{
                // Highlight connections
                const connectedNodes = new Set([d.id]);
                const connectedLinks = new Set();
                
                link.each(function(l) {{
                    if (l.source.id === d.id || l.target.id === d.id) {{
                        connectedNodes.add(l.source.id);
                        connectedNodes.add(l.target.id);
                        connectedLinks.add(l);
                    }}
                }});
                
                node.style("opacity", n => connectedNodes.has(n.id) ? 1 : 0.2);
                link.style("opacity", l => connectedLinks.has(l) ? 0.8 : 0.1);
                
                // Show tooltip
                tooltip.transition().duration(200).style("opacity", 1);
                tooltip.html(`
                    <div class="class-name">${{d.name}}</div>
                    <div class="info-row"><span class="label">Methods:</span> ${{d.method_count}}</div>
                    <div class="info-row"><span class="label">Domain:</span> ${{d.domain}}</div>
                    <div class="info-row"><span class="label">Type:</span> ${{d.is_factory ? 'Factory' : (d.is_collection ? 'Collection' : 'Class')}}</div>
                    <div class="info-row"><span class="label">Full Name:</span> ${{d.full_name}}</div>
                    <div class="info-row" style="margin-top: 8px; font-size: 11px; opacity: 0.8;">
                        ${{d.docstring}}
                    </div>
                `)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                node.style("opacity", 1);
                link.style("opacity", d => d.type === 'inheritance' ? 0.8 : 0.4);
                tooltip.transition().duration(300).style("opacity", 0);
            }})
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Labels (initially hidden)
        const labels = g.append("g")
            .selectAll(".node-label")
            .data(data.nodes.filter(d => d.method_count > 100))
            .enter().append("text")
            .attr("class", "node-label")
            .text(d => d.name.length > 15 ? d.name.substring(0, 15) + "..." : d.name)
            .style("opacity", 0);
        
        // Update positions
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
                .attr("y", d => d.y + 3);
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
        let labelsVisible = false;
        
        function resetView() {{
            simulation.alpha(1).restart();
            node.style("opacity", 1);
            link.style("opacity", d => d.type === 'inheritance' ? 0.8 : 0.4);
        }}
        
        function zoomToFit() {{
            const bounds = g.node().getBBox();
            if (bounds.width === 0 || bounds.height === 0) return;
            
            const scale = Math.min(width / bounds.width, height / bounds.height) * 0.85;
            const translate = [
                width / 2 - scale * (bounds.x + bounds.width / 2),
                height / 2 - scale * (bounds.y + bounds.height / 2)
            ];
            
            svg.transition().duration(750)
                .call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        }}
        
        function toggleFactories() {{
            const factoryNodes = data.nodes.filter(d => d.is_factory);
            if (factoryNodes.length > 0) {{
                node.style("opacity", d => d.is_factory ? 1 : 0.1);
                link.style("opacity", 0.05);
            }}
        }}
        
        function toggleCollections() {{
            const collectionNodes = data.nodes.filter(d => d.is_collection);
            if (collectionNodes.length > 0) {{
                node.style("opacity", d => d.is_collection ? 1 : 0.1);
                link.style("opacity", 0.05);
            }}
        }}
        
        function toggleLabels() {{
            labelsVisible = !labelsVisible;
            labels.style("opacity", labelsVisible ? 1 : 0);
        }}
        
        // Search functionality
        document.getElementById('searchBox').addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();
            if (searchTerm) {{
                node.style("opacity", d => 
                    d.name.toLowerCase().includes(searchTerm) || 
                    d.domain.toLowerCase().includes(searchTerm) ? 1 : 0.1
                );
                link.style("opacity", 0.05);
            }} else {{
                resetView();
            }}
        }});
        
        // Initial zoom to fit
        setTimeout(zoomToFit, 1000);
    </script>
</body>
</html>'''
    
    # Save the interactive HTML
    output_path = Path("pycatia_graph_d3.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Interactive explorer created: {output_path}")
    return output_path


def main():
    """Create the interactive visualization"""
    html_file = create_interactive_d3_from_json()
    
    print(f"\n🎉 Interactive PyCATIA Knowledge Graph Explorer Created!")
    print(f"📁 File: {html_file}")
    print(f"\n🚀 Features:")
    print(f"   • 🔍 Search classes by name or domain")
    print(f"   • 🏭 Highlight factory classes (create objects)")
    print(f"   • 📦 Highlight collection classes (manage groups)")
    print(f"   • 🔗 Show inheritance relationships")
    print(f"   • 📊 Node size = number of methods")
    print(f"   • 🎨 Colors = different domains")
    print(f"   • 💡 Hover for detailed tooltips")
    print(f"\n💻 Open {html_file} in your web browser to explore!")


if __name__ == "__main__":
    main()