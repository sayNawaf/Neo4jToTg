
from neo4j import GraphDatabase
import pyTigerGraph as tg
import json
from parserr import get_gsql_script
import io
from schema_generate import create_schema
from flask import send_file,Response

def Migrate(ConnectionsManager,TGconnection,NJconnection,trie):
    
        try:
            Uri,Username,password = ConnectionsManager.retrieve_connection_creds(NJconnection)
            tg_Uri,tg_Username,tg_password,graphname = ConnectionsManager.retrieve_connection_creds(TGconnection,getgraphname = True)
            
            graphdb = GraphDatabase.driver(uri=Uri, auth=(Username, password))
            session = graphdb.session()
            nodes = session.run("call apoc.meta.schema")
            
            for node in nodes: #converting Neo4j object containing schema to json
                for n in node:
                    a = json.dumps(n,indent=3)
            

            data = json.loads(a)
            
        except Exception as e:
            # Check if the error message contains "Unable to retrieve routing information"
            return {"status":False,"message":"error " + str(e) + " when loading the schema from Neo4j"}
        
        Vertex_code_graph,edge_code_graph,index_constraints = get_gsql_script(trie,data,graphname)
        schema = create_schema(Vertex_code_graph,edge_code_graph,index_constraints,graphname)
                #print(schema)
        schema = schema.replace("\n","")

        
            
            
        try:
            conn = tg.TigerGraphConnection(host=tg_Uri, username=tg_Username, password = tg_password)
            conn.gsql("ls")
        except Exception as e:
            return {"status":False,"message": "error" + str(e) + " when connecting to TigerGraph"}
        
        try:
            #print(schema)
            
            result=conn.gsql(schema)
            
            with open("log.txt", 'w') as file:
                    file.write(result)
                    
            if "successfully created schema change jobs:" not in result.lower():
                
                return  send_file("log.txt", as_attachment=True), 500
            
                
            return  send_file("log.txt", as_attachment=True), 200

        except Exception as e:
            return {"status":False,"message": "error" + str(e) + " when running the DDL on TigerGraph"}
    

    
