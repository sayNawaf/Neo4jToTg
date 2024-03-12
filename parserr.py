from neo4j_tg_datatype_mapper import type_mapper
import re
import json

    
def replace_special_characters(input_string):
    # Use a regular expression to replace all non-alphanumeric characters with underscores
    return re.sub(r'[^a-zA-Z0-9]', '_', input_string)

def check_if_used(used_identifiers,identifier):
    if identifier in used_identifiers:
        return check_if_used(used_identifiers,identifier + "_")
    
    return identifier

def get_gsql_script(trie,data,graphname):
    
    Vertex_code_graph = ""
    edge_code_graph = ""
    used_vertex = []
    used_edge = []
    used_vertex_attributes = []
    used_edge_attributes = []
    
    primary_id_map = {}
    edgeNameDirection = {}
    EdgeNameAttributes = {}
    index_constraints = ""
    type_allowed_for_index_TG = ['INT', 'STRING', 'DATETIME'] #datatypes which TG permits to be indexed
    type_allowed_for_index_Neo4j = [key for key, value in type_mapper.items() if value in type_allowed_for_index_TG]#datatypes in neo4j which TG permits to be indexed
    with open("neo4j_schema.txt", "w") as file:
        json.dump(data, file)
    
    for Node, value in data.items():
        attributes = ""
        
        if value["type"] == 'node':
            Node = replace_special_characters(Node)
            if trie.search(Node.upper()) or Node == graphname:
                Node += '_'
            Node = check_if_used(used_vertex + used_vertex_attributes,Node)
            used_vertex.append(Node)
            Vertex_code_graph += f"""\n ADD VERTEX {Node}("""
            primary_id = None

            for attributeName, prop in value['properties'].items():
                attributeName = replace_special_characters(attributeName)
                if trie.search(attributeName.upper()) or attributeName == graphname:
                    attributeName += '_'
                attributeName = check_if_used(used_vertex,attributeName)
                used_vertex_attributes.append(attributeName)
                if prop.get("unique"):
                    if prop['unique'] == True and not primary_id:
                        Primary_id_code = f"PRIMARY_ID {attributeName} {type_mapper[prop['type']]}"
                        primary_id = attributeName
                    else:
                        attributes += f",{attributeName} {type_mapper[prop['type']]}"
                else:
                    attributes += f",{attributeName} {type_mapper[prop['type']]}"

                if prop.get("indexed"):
                    if prop['indexed'] == True and prop['unique'] == False and prop['type'] in type_allowed_for_index_Neo4j:
                        index_constraints += f"ALTER VERTEX {Node} ADD INDEX {Node}_{attributeName} ON ({attributeName});"

            if not primary_id:
                Primary_id_code = "PRIMARY_ID id string"
                primary_id = "id"

            
            attributes += """) WITH primary_id_as_attribute = "true" """
            Vertex_code_graph += Primary_id_code + attributes + ";"
            attributes = ""
            
            for edgeName, EdgeValue in value["relationships"].items(): #itterate thorugh every item of type relationship which is edge
                
                
                if EdgeValue["direction"] == "out":
                    
                    edgeName = replace_special_characters(edgeName)
                    if trie.search(edgeName.upper()) or edgeName == graphname:  #check if edge name is a reserve word
                            edgeName += '_'
                    edgeName = check_if_used(used_vertex + used_vertex_attributes + used_edge_attributes + used_edge,edgeName)
                    used_edge.append(edgeName)
                    for label in  EdgeValue['labels']:
                        
                        label = replace_special_characters(label)
                        if trie.search(label.upper()) or label == graphname:  #check if edge name is a reserve word
                            label += '_'
                        
                        if edgeNameDirection.get(edgeName) and f"From {Node},To {label}" in edgeNameDirection[edgeName]:
                            #if f"From {Node},To {label}" in edgeNameDirection[edgeName]:
                            continue                                     #to prevent coming accros same edge again  only consider out direction 
                        #label = EdgeValue['labels'][0]  #label denotes the target vertex of the edge
                        
                        edge_direction = f"From {Node},To {label}"  #node beign the source vertex and label being the target vertex
                        if edgeNameDirection.get(edgeName):  #check if the edge name has been previously used
                            edgeNameDirection[edgeName] += f"|{edge_direction}"
                            if not EdgeNameAttributes.get(edgeName) and 'properties' in EdgeValue and any(EdgeValue['properties']):
                                EdgeNameAttributes[edgeName] = "" 
                                #if yes then append the new edge direction using "|" to already existing edge name
                            for attributeName, prop in EdgeValue['properties'].items():
                                attributeName = replace_special_characters(attributeName)
                                
                                if trie.search(attributeName.upper()) or attributeName == graphname:  #check if edge name is a reserve word
                                    attributeName += '_' #iterate through the attributes of the edge
                                attributeName = check_if_used(used_vertex + used_edge,attributeName)
                                used_edge_attributes.append(attributeName)
                                if f",{attributeName} {type_mapper[prop['type']]}" not in EdgeNameAttributes[edgeName]: #append the attribute only if the attribute has not been saved before to the already existing edge name  
                                    EdgeNameAttributes[edgeName] += f",{attributeName} {type_mapper[prop['type']]}"
                        else:
                            
                            edgeNameDirection[edgeName] = edge_direction
                            
                            if 'properties' in EdgeValue and any(EdgeValue['properties']):
                                EdgeNameAttributes[edgeName] = ""            #if the edge name has not been used before initialize it 
                                for attributeName, prop in EdgeValue['properties'].items():
                                    attributeName = replace_special_characters(attributeName)
                                    if trie.search(attributeName.upper()) or attributeName == graphname:  #check if edge name is a reserve word
                                        attributeName += '_'
                                    attributeName = check_if_used(used_vertex + used_edge,attributeName)
                                    used_edge_attributes.append(attributeName)
                                    EdgeNameAttributes[edgeName] += f",{attributeName} {type_mapper[prop['type']]}"


    for edgeName in edgeNameDirection.keys():
        if trie.search(edgeName.upper()):
            edgeName += '_'
        edge_code_graph += f"""\n ADD DIRECTED EDGE {edgeName}("""
        edge_code_graph += edgeNameDirection[edgeName]

        if EdgeNameAttributes.get(edgeName):
            edge_code_graph += EdgeNameAttributes[edgeName] + ")" + ";"
        else:
            edge_code_graph += ")" + ";"
    
    
    #yield {"status":True,"message":Vertex_code_graph + edge_code_graph + index_constraints}
    
    return Vertex_code_graph,edge_code_graph,index_constraints


