def create_schema(Vertex_code_graph,edge_code_graph,index_constraints,GraphName="ABC"):
    Query_Graph = f"""
    CREATE GRAPH {GraphName} ()
    USE GRAPH {GraphName}
    CREATE SCHEMA_CHANGE JOB schema_change_job_{GraphName} FOR GRAPH {GraphName} {{
        {Vertex_code_graph}
        {edge_code_graph}
    }}
    RUN SCHEMA_CHANGE JOB schema_change_job_{GraphName}
    DROP JOB schema_change_job_{GraphName}
    """

    if index_constraints:
        index_constraints = f"""
        USE GRAPH {GraphName}
        CREATE SCHEMA_CHANGE JOB indexschema_change_job_{GraphName} FOR GRAPH {GraphName} {{
            {index_constraints}
        }}
        RUN SCHEMA_CHANGE JOB indexschema_change_job_{GraphName}
        DROP JOB indexschema_change_job_{GraphName}
        """
    
    return Query_Graph + "\n" + index_constraints