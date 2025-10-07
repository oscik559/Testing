#!/usr/bin/env python3
"""
Simple PyCATIA Class-Only Knowledge Graph Visualizer

Creates a clean D3 visualization showing only classes and their inheritance relationships.
No method clutter - just clean class hierarchy visualization.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


def create_interactive_d3_from_json():
    """Create clean class-only interactive D3 visualization with inheritance relationships"""
    
    print("🧠 Creating Class-Only Interactive D3 Visualization")
    print("=" * 50)
    
    # Handle path properly - look for JSON file relative to script location
    script_dir = Path(__file__).parent
    json_file = script_dir / "pycatia_knowledge_graph.json"
    
    if not json_file.exists():
        # Try alternative paths
        alt_paths = [
            Path("pycatia_knowledge_graph.json"),  # Current directory
            Path("knowledge_graph/pycatia_knowledge_graph.json")  # From root
        ]
        
        for alt_path in alt_paths:
            if alt_path.exists():
                json_file = alt_path
                break
        else:
            print(f"❌ JSON file not found. Tried:")
            print(f"  - {script_dir / 'pycatia_knowledge_graph.json'}")
            for alt_path in alt_paths:
                print(f"  - {alt_path}")
            return None
    
    print(f"📁 Loading: {json_file}")
    
    # Load JSON data
    with open(json_file, "r") as f:
        kg_data = json.load(f)
    
    classes = kg_data.get("classes", {})
    
    print(f"📊 Processing {len(classes)} classes...")
    
    # Create nodes - CLASSES ONLY (simple and clean)
    nodes = []
    node_map = {}
    
    # Sort classes by method count and importance
    class_method_counts = []
    for class_name, class_info in classes.items():
        method_count = len(class_info.get("methods", {}))
        class_method_counts.append((class_name, method_count, class_info))
    
    # Use all classes for complete inheritance visualization
    class_method_counts.sort(key=lambda x: x[1], reverse=True)
    selected_classes = class_method_counts  # ALL classes
    
    print(f"📋 Processing {len(selected_classes)} classes (class-only visualization)")
    
    # Create CLASS nodes only
    for i, (class_name, method_count, class_info) in enumerate(selected_classes):
        domain = class_info.get('domain', 'unknown')
        
        nodes.append({
            'id': str(i),
            'name': class_name,
            'label': class_name,
            'type': 'class',
            'group': hash(domain) % 15,
            'method_count': method_count,
            'domain': domain,
            'is_factory': class_info.get('is_factory', False),
            'is_collection': class_info.get('is_collection', False),
            'full_name': class_info.get('full_name', class_name),
            'docstring': (class_info.get('docstring', '')[:200] + '...') if class_info.get('docstring', '') else 'No documentation',
            'parent_classes': class_info.get('parent_classes', []),
            'mro': class_info.get('mro', [])
        })
        node_map[class_name] = i
    
    print(f"📋 Created {len(nodes)} class nodes (clean design)")

    # Create edges - INHERITANCE ONLY (class-method edges added on click)
    edges = []
    
    # INHERITANCE edges (class to class) - FIXED to show proper connections
    inheritance_count = 0
    missing_parents = set()
    
    for node in nodes:
        if node['type'] == 'class':
            class_name = node['name']
            parent_classes = node.get('parent_classes', [])
            
            for parent in parent_classes:
                if parent in node_map:
                    # Found parent in our dataset
                    edges.append({
                        'source': node['id'],           # Child class
                        'target': str(node_map[parent]), # Parent class
                        'type': 'inheritance',
                        'strength': 1.5
                    })
                    inheritance_count += 1
                else:
                    missing_parents.add(parent)
    
    print(f"📋 Created {inheritance_count} inheritance relationships")
    if missing_parents:
        print(f"⚠️  Missing parent classes: {len(missing_parents)} (e.g., {list(missing_parents)[:5]})")
    
    # DOMAIN clustering edges (minimal, for loose grouping)
    domain_groups = defaultdict(list)
    for node in nodes:
        if node['type'] == 'class':
            domain = node.get('domain', 'unknown')
            domain_groups[domain].append(node['id'])
    
    # Very minimal domain connections
    domain_edges = 0
    for domain, class_ids in domain_groups.items():
        if len(class_ids) > 1 and len(class_ids) < 20:  # Only small domains
            # Connect just first to second
            edges.append({
                'source': class_ids[0],
                'target': class_ids[1],
                'type': 'domain',
                'strength': 0.2
            })
            domain_edges += 1
    
    print(f"📋 Added {domain_edges} domain clustering edges")

    # Prepare data for JavaScript (simple class-only data)
    graph_data = {
        'nodes': nodes, 
        'links': edges
    }
    
    print(f"✅ Graph created: {len(nodes)} class nodes, {len(edges)} relationships")
    
    # Create enhanced HTML
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>🧠 PyCATIA Class Inheritance Graph</title>
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
            stroke-width: 1.5px;
            transition: all 0.3s ease;
        }}
        
        .node:hover {{
            stroke-width: 3px;
        }}
        
        .node.class {{
            stroke: #2c3e50;
            stroke-width: 3px;
        }}
        
        .node.factory {{
            stroke: #f39c12;
            stroke-width: 4px;
            filter: drop-shadow(0 0 8px #f39c12);
        }}
        
        .node.collection {{
            stroke: #e74c3c;
            stroke-width: 4px;
            filter: drop-shadow(0 0 8px #e74c3c);
        }}
        
        .link {{
            fill: none;
        }}
        
        .link.inheritance {{
            stroke: #2c3e50;
            stroke-width: 2px;
            stroke-opacity: 0.8;
            stroke-dasharray: 4,4;
        }}
        
        .link.domain {{
            stroke: #7f8c8d;
            stroke-width: 1.5px;
            stroke-opacity: 0.4;
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
            max-width: 400px;
            max-height: 500px;
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            backdrop-filter: blur(10px);
            z-index: 1000;
        }}
        
        .methods-panel {{
            position: absolute;
            padding: 20px;
            background: rgba(0, 0, 0, 0.95);
            color: white;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            font-size: 12px;
            max-width: 450px;
            max-height: 600px;
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            backdrop-filter: blur(10px);
            z-index: 1001;
            display: none;
        }}
        
        .method-item {{
            margin: 3px 0;
            padding: 2px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-family: 'Courier New', monospace;
            font-size: 11px;
        }}
        
        .close-btn {{
            position: absolute;
            top: 5px;
            right: 10px;
            background: none;
            border: none;
            color: #ff6b6b;
            font-size: 16px;
            cursor: pointer;
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
        <div class="title">🧠 PyCATIA Class Inheritance Graph</div>
        <div class="stats">{len(nodes)} classes • {len(edges)} inheritance links • Class-only view</div>
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
    
    <div id="methodsPanel" class="methods-panel">
        <button class="close-btn" onclick="closeMethods()">×</button>
        <div id="methodsContent"></div>
    </div>
    
    <div class="legend" style="position: absolute; top: 100px; left: 20px; background: rgba(0,0,0,0.9); padding: 15px; border-radius: 10px; font-size: 12px; max-width: 250px; border: 1px solid rgba(255,255,255,0.2);">
        <div style="color: #4ecdc4; font-weight: bold; margin-bottom: 10px;">🗺️ Class Inheritance Graph</div>
        <div style="margin: 5px 0;"><span style="color: #e74c3c;">●</span> Classes (size = method count)</div>
        <div style="margin: 5px 0;"><span style="color: #f39c12;">●</span> Factory Classes (golden outline)</div>
        <div style="margin: 5px 0;"><span style="color: #e74c3c;">●</span> Collection Classes (red outline)</div>
        <hr style="border: 0.5px solid rgba(255,255,255,0.3); margin: 8px 0;">
        <div style="margin: 5px 0;"><span style="color: #2c3e50;">- -</span> Inheritance (child → parent)</div>
        <div style="margin: 5px 0;"><span style="color: #7f8c8d;">—</span> Domain clustering</div>
        <hr style="border: 0.5px solid rgba(255,255,255,0.3); margin: 8px 0;">
        <div style="margin: 5px 0; font-size: 11px; opacity: 0.8;">💡 Hover for class details</div>
        <div style="margin: 5px 0; font-size: 11px; opacity: 0.8;">🔍 Search by name/domain/parent</div>
        <div style="margin: 5px 0; font-size: 11px; opacity: 0.8;">🖱️ Click class to see methods</div>
    </div>
    
    <script>
        const data = {json.dumps(graph_data, indent=2)};
        const classData = {json.dumps({name: {'methods': dict(list(class_info.get('methods', {}).items())[:])} for name, class_info in classes.items()}, indent=2)};
        
        // Set up SVG
        const svg = d3.select("#graph");
        const width = window.innerWidth;
        const height = window.innerHeight - 80;
        
        svg.attr("width", width).attr("height", height);
        
        const g = svg.append("g");
        
        // Methods panel
        const methodsPanel = d3.select("#methodsPanel");
        const methodsContent = d3.select("#methodsContent");
        
        // Enhanced color palette for classes
        const classColors = [
            '#e74c3c', '#9b59b6', '#3498db', '#1abc9c', '#f1c40f',
            '#e67e22', '#95a5a6', '#34495e', '#ff6b9d', '#c44569',
            '#f8b500', '#6a89cc', '#82ccdd', '#60a3bc', '#786fa6'
        ];
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 5])
            .on("zoom", (event) => g.attr("transform", event.transform));
        
        svg.call(zoom);
        
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        // Force simulation - improved centering and domain clustering
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links)
                .id(d => d.id)
                .distance(d => {{
                    if (d.type === 'inheritance') return 120;     // Inheritance relationships - closer
                    return 180;                                    // Domain connections - closer to center
                }})
                .strength(d => d.strength || 0.8))
            .force("charge", d3.forceManyBody().strength(-500))   // Less repulsion
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("x", d3.forceX(width / 2).strength(0.1))      // Pull towards horizontal center
            .force("y", d3.forceY(height / 2).strength(0.1))     // Pull towards vertical center
            .force("collision", d3.forceCollide().radius(d => {{
                return Math.max(12, Math.sqrt(d.method_count || 1) * 2.5);
            }}));

        // Create links
        const link = g.append("g")
            .selectAll(".link")
            .data(data.links)
            .enter().append("line")
            .attr("class", d => `link ${{d.type}}`);
        
        // Create nodes - classes only
        const node = g.append("g")
            .selectAll(".node")
            .data(data.nodes)
            .enter().append("circle")
            .attr("class", d => {{
                let classes = `node ${{d.type}}`;
                if (d.is_factory) classes += " factory";
                if (d.is_collection) classes += " collection";
                return classes;
            }})
            .attr("r", d => {{
                return Math.max(8, Math.min(35, Math.sqrt(d.method_count || 1) * 2.5));
            }})
            .attr("fill", d => {{
                return classColors[d.group % classColors.length];
            }})
            .on("click", function(event, d) {{
                showMethods(d, event);
            }})
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
                link.style("opacity", l => connectedLinks.has(l) ? 1 : 0.1);
                
                // Show tooltip
                tooltip.transition().duration(200).style("opacity", 1);
                tooltip.html(`
                    <div class="class-name">🏗️ ${{d.name}}</div>
                    <div class="info-row"><span class="label">Type:</span> Class</div>
                    <div class="info-row"><span class="label">Methods:</span> ${{d.method_count}}</div>
                    <div class="info-row"><span class="label">Parents:</span> ${{d.parent_classes?.join(', ') || 'None'}}</div>
                    <div class="info-row"><span class="label">Domain:</span> ${{d.domain}}</div>
                    <div class="info-row"><span class="label">Category:</span> ${{d.is_factory ? 'Factory' : (d.is_collection ? 'Collection' : 'Standard')}}</div>
                    <div class="info-row" style="margin-top: 8px; font-size: 11px; opacity: 0.8;">
                        ${{d.docstring}}
                    </div>
                `)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                node.style("opacity", 1);
                link.style("opacity", d => {{
                    if (d.type === 'inheritance') return 0.8;
                    return 0.4;
                }});
                tooltip.transition().duration(300).style("opacity", 0);
            }})
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Labels for major classes
        const labels = g.append("g")
            .selectAll(".node-label")
            .data(data.nodes.filter(d => d.method_count > 50))
            .enter().append("text")
            .attr("class", "node-label")
            .text(d => d.name.length > 15 ? d.name.substring(0, 15) + "..." : d.name)
            .style("opacity", 0)
            .style("font-size", "11px");

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
            link.style("opacity", d => {{
                if (d.type === 'inheritance') return 0.8;
                return 0.4;
            }});
        }}
        
        function showMethods(classNode, event) {{
            const className = classNode.name;
            const classInfo = classData[className];
            
            if (!classInfo || !classInfo.methods) {{
                methodsContent.html(`
                    <h3 style="color: #4ecdc4; margin-bottom: 15px;">⚙️ ${{className}}</h3>
                    <p style="opacity: 0.8;">No method information available.</p>
                `);
            }} else {{
                const methods = Object.entries(classInfo.methods);
                const methodsList = methods.map(([name, signature]) => `
                    <div class="method-item">
                        <strong style="color: #3498db;">${{name}}</strong><br>
                        <span style="opacity: 0.7; font-size: 10px;">${{signature}}</span>
                    </div>
                `).join('');
                
                methodsContent.html(`
                    <h3 style="color: #4ecdc4; margin-bottom: 15px;">⚙️ ${{className}} Methods</h3>
                    <div style="margin-bottom: 10px; font-size: 11px; opacity: 0.8;">
                        ${{methods.length}} methods • Domain: ${{classNode.domain}}
                    </div>
                    ${{methodsList}}
                `);
            }}
            
            // Position panel near click but keep it visible
            const panelWidth = 450;
            const panelHeight = 600;
            const x = Math.min(event.pageX + 20, window.innerWidth - panelWidth - 20);
            const y = Math.min(event.pageY - 50, window.innerHeight - panelHeight - 20);
            
            methodsPanel
                .style("left", x + "px")
                .style("top", y + "px")
                .style("display", "block");
        }}
        
        function closeMethods() {{
            methodsPanel.style("display", "none");
        }}
        
        // Close methods panel when clicking elsewhere
        document.addEventListener('click', function(event) {{
            if (!event.target.closest('.methods-panel') && !event.target.closest('circle')) {{
                closeMethods();
            }}
        }});
        
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
        
        // Search functionality - classes only
        document.getElementById('searchBox').addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();
            if (searchTerm) {{
                node.style("opacity", d => {{
                    const nameMatch = d.name.toLowerCase().includes(searchTerm);
                    const domainMatch = d.domain.toLowerCase().includes(searchTerm);
                    const parentMatch = d.parent_classes && d.parent_classes.some(p => p.toLowerCase().includes(searchTerm));
                    
                    return nameMatch || domainMatch || parentMatch ? 1 : 0.1;
                }});
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
    
    # Save the interactive HTML in the same directory as the script
    output_path = script_dir / "pycatia_graph_d3.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Interactive class graph created: {output_path}")
    return output_path


def main():
    """Create the class-only visualization"""
    html_file = create_interactive_d3_from_json()
    
    print(f"\n🎉 PyCATIA Class Inheritance Graph Created!")
    print(f"📁 File: {html_file}")
    print(f"\n🚀 Features:")
    print(f"   • 🏗️ CLASS-ONLY: Clean visualization without method clutter")
    print(f"   • 🔗 INHERITANCE: Red dashed lines show parent-child relationships")
    print(f"   • 📊 NODE SIZE: Larger circles = more methods in class")
    print(f"   • 🎨 COLORS: 15 distinct colors for different domains")
    print(f"   • 🔍 SEARCH: Find classes by name, domain, or parent class")
    print(f"   • 🏭 FACTORIES: Golden outline (create objects)")
    print(f"   • 📦 COLLECTIONS: Red outline (manage groups)")
    print(f"   • 💡 TOOLTIPS: Hover for class details and inheritance info")
    print(f"\n💻 Open {html_file} in your web browser to explore!")


if __name__ == "__main__":
    main()