#!/usr/bin/env python3
"""
Enhanced GEXF Generator for PyCATIA Knowledge Graph

This script reads the pycatia_knowledge_graph.json file and creates
a rich GEXF visualization file with proper relationships, attributes,
and structure for use with Gephi, Cytoscape, and D3.js.
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def load_knowledge_graph():
    """Load the knowledge graph JSON data"""
    json_file = Path(__file__).parent / 'pycatia_knowledge_graph.json'
    
    if not json_file.exists():
        raise FileNotFoundError(f"Knowledge graph not found: {json_file}")
    
    with open(json_file, 'r') as f:
        return json.load(f)


def create_enhanced_gexf():
    """Generate enhanced GEXF file with proper relationships and attributes"""
    
    print("🔍 Loading knowledge graph data...")
    kg_data = load_knowledge_graph()
    
    # Create GEXF root structure
    gexf = ET.Element("gexf")
    gexf.set("xmlns", "http://www.gexf.net/1.2draft")
    gexf.set("version", "1.2")
    
    # Meta information
    meta = ET.SubElement(gexf, "meta")
    meta.set("lastmodifieddate", datetime.now().strftime("%Y-%m-%d"))
    
    creator = ET.SubElement(meta, "creator")
    creator.text = "PyCATIA Knowledge Graph Generator"
    
    description = ET.SubElement(meta, "description")
    description.text = "Hierarchical knowledge graph of PyCATIA library methods and classes"
    
    # Graph element
    graph = ET.SubElement(gexf, "graph")
    graph.set("mode", "static")
    graph.set("defaultedgetype", "directed")
    
    # Attributes for nodes
    attributes = ET.SubElement(graph, "attributes")
    attributes.set("class", "node")
    
    attr_type = ET.SubElement(attributes, "attribute")
    attr_type.set("id", "0")
    attr_type.set("title", "node_type")
    attr_type.set("type", "string")
    
    attr_methods = ET.SubElement(attributes, "attribute")
    attr_methods.set("id", "1") 
    attr_methods.set("title", "method_count")
    attr_methods.set("type", "integer")
    
    attr_domain = ET.SubElement(attributes, "attribute")
    attr_domain.set("id", "2")
    attr_domain.set("title", "domain")
    attr_domain.set("type", "string")
    
    attr_docstring = ET.SubElement(attributes, "attribute")
    attr_docstring.set("id", "3")
    attr_docstring.set("title", "has_docstring")
    attr_docstring.set("type", "boolean")
    
    # Nodes and edges containers
    nodes = ET.SubElement(graph, "nodes")
    edges = ET.SubElement(graph, "edges")
    
    node_id = 0
    edge_id = 0
    node_map = {}  # class_name -> node_id
    
    print("🔍 Creating enhanced GEXF with relationships...")
    
    # Create class nodes
    classes_data = kg_data.get("classes", {})
    print(f"📚 Processing {len(classes_data)} classes...")
    
    for class_path, class_info in classes_data.items():
        # Create class node
        node = ET.SubElement(nodes, "node")
        node.set("id", str(node_id))
        node.set("label", class_path.split(".")[-1])  # Just class name for readability
        
        # Node attributes
        attvalues = ET.SubElement(node, "attvalues")
        
        att1 = ET.SubElement(attvalues, "attvalue")
        att1.set("for", "0")
        att1.set("value", "class")
        
        att2 = ET.SubElement(attvalues, "attvalue") 
        att2.set("for", "1")
        att2.set("value", str(len(class_info.get("methods", {}))))
        
        att3 = ET.SubElement(attvalues, "attvalue")
        att3.set("for", "2")
        domain = class_path.split(".")[1] if len(class_path.split(".")) > 1 else "unknown"
        att3.set("value", domain)
        
        att4 = ET.SubElement(attvalues, "attvalue")
        att4.set("for", "3")
        att4.set("value", "true")  # Classes generally have documentation
        
        node_map[class_path] = node_id
        node_id += 1
    
    # Create inheritance edges
    inheritance_count = 0
    print("🔗 Creating inheritance relationships...")
    
    for class_path, class_info in classes_data.items():
        if class_path in node_map:
            inheritance = class_info.get("inheritance", [])
            for parent_class in inheritance:
                # Find parent in our classes
                parent_full_path = None
                for cp in classes_data.keys():
                    if cp.endswith(f".{parent_class}") or cp.split(".")[-1] == parent_class:
                        parent_full_path = cp
                        break
                
                if parent_full_path and parent_full_path in node_map:
                    edge = ET.SubElement(edges, "edge")
                    edge.set("id", str(edge_id))
                    edge.set("source", str(node_map[parent_full_path]))
                    edge.set("target", str(node_map[class_path]))
                    edge.set("weight", "2.0")  # Higher weight for inheritance
                    edge.set("type", "inheritance")
                    edge_id += 1
                    inheritance_count += 1
    
    # Create method nodes and relationships (limited for visualization)
    method_nodes = 0
    method_relationships = 0
    print("🔧 Creating method nodes and relationships...")
    
    for class_path, class_info in classes_data.items():
        class_node_id = node_map.get(class_path)
        if class_node_id is None:
            continue
            
        methods = class_info.get("methods", {})
        
        # Create nodes for important methods (limit to avoid huge graph)
        important_methods = []
        for method_name, method_signature in list(methods.items())[:3]:  # Top 3 methods per class
            if any(keyword in method_name.lower() for keyword in ["add", "create", "new", "get", "set", "update"]):
                important_methods.append((method_name, method_signature))
        
        for method_name, method_signature in important_methods:
            # Create method node
            method_node = ET.SubElement(nodes, "node")
            method_node.set("id", str(node_id))
            method_node.set("label", method_name)
            
            # Method attributes
            method_attvalues = ET.SubElement(method_node, "attvalues")
            
            meth_att1 = ET.SubElement(method_attvalues, "attvalue")
            meth_att1.set("for", "0")
            meth_att1.set("value", "method")
            
            meth_att2 = ET.SubElement(method_attvalues, "attvalue")
            meth_att2.set("for", "1") 
            meth_att2.set("value", "1")
            
            meth_att3 = ET.SubElement(method_attvalues, "attvalue")
            meth_att3.set("for", "2")
            domain = class_path.split(".")[1] if len(class_path.split(".")) > 1 else "unknown"
            meth_att3.set("value", domain)
            
            meth_att4 = ET.SubElement(method_attvalues, "attvalue")
            meth_att4.set("for", "3")
            # For now, assume methods have documentation (we'll check actual docstrings later)
            meth_att4.set("value", "true")
            
            # Create edge from class to method
            edge = ET.SubElement(edges, "edge")
            edge.set("id", str(edge_id))
            edge.set("source", str(class_node_id))
            edge.set("target", str(node_id))
            edge.set("weight", "1.0")
            edge.set("type", "has_method")
            
            edge_id += 1
            node_id += 1
            method_nodes += 1
            method_relationships += 1
    
    # Create domain clusters (module-level relationships)
    print("🏗️ Creating domain cluster relationships...")
    domain_clusters = {}
    for class_path in classes_data.keys():
        parts = class_path.split(".")
        if len(parts) > 2:
            domain = parts[1]  # e.g., "hybrid_shape_interfaces"
            if domain not in domain_clusters:
                domain_clusters[domain] = []
            domain_clusters[domain].append(class_path)
    
    # Add domain cluster edges (classes in same domain are related)
    cluster_edges = 0
    for domain, class_paths in domain_clusters.items():
        if len(class_paths) > 1:
            # Create edges between classes in same domain (limited to avoid clutter)
            for i, class1 in enumerate(class_paths[:8]):  # Limit to avoid too many edges
                for class2 in class_paths[i+1:8]:
                    if class1 in node_map and class2 in node_map:
                        edge = ET.SubElement(edges, "edge")
                        edge.set("id", str(edge_id))
                        edge.set("source", str(node_map[class1]))
                        edge.set("target", str(node_map[class2]))
                        edge.set("weight", "0.3")  # Low weight for domain similarity
                        edge.set("type", "domain_cluster")
                        edge_id += 1
                        cluster_edges += 1
    
    # Write GEXF file
    tree = ET.ElementTree(gexf)
    ET.indent(tree, space="  ", level=0)
    
    output_path = Path(__file__).parent / "pycatia_mapping.gexf"
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    
    print(f"✅ Enhanced GEXF generated: {output_path}")
    print(f"📊 Graph Statistics:")
    print(f"  📋 Classes: {len(classes_data)}")
    print(f"  🔧 Method nodes: {method_nodes}")
    print(f"  🔗 Inheritance edges: {inheritance_count}")
    print(f"  🔗 Method relationships: {method_relationships}")
    print(f"  🔗 Domain cluster edges: {cluster_edges}")
    print(f"  📊 Total nodes: {node_id}")
    print(f"  📊 Total edges: {edge_id}")
    print(f"  🏗️ Domain clusters: {len(domain_clusters)}")
    
    return output_path


def create_gexf_from_knowledge_graph():
    """Wrapper function to maintain backward compatibility"""
    return create_enhanced_gexf()


if __name__ == "__main__":
    print("🌐 Generating GEXF Graph from Knowledge Graph")
    print("=" * 50)
    
    try:
        gexf_path = create_gexf_from_knowledge_graph()
        print(f"\n🎉 Generated: {gexf_path}")
        print("\nYou can now:")
        print("  • Open in Gephi for advanced visualization")
        print("  • Use with create_d3_graph.py for web visualization")
        
    except Exception as e:
        print(f"❌ Error: {e}")