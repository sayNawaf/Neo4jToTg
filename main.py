from flask import Flask, request, render_template_string,send_file,jsonify,Response
from flask_cors import CORS, cross_origin
from reserve_word_searcher import Trie
from reserve_words import reserved_words
from parserr import get_gsql_script
from connection_db import ConnectionsCollection
from schema_generate import create_schema
import json
from datetime import datetime
from neo4j import GraphDatabase
import pyTigerGraph as tg
from schema_migration import Migrate
from flask_cors import cross_origin
import re
from config import Config


app = Flask(__name__)
CORS(app)
#app.config.from_object(Config)
trie = Trie()
for word in reserved_words:
        trie.insert(word)

connection_string = Config.connection_string
database_name = Config.database_name
collection_name = Config.collection_name

# Create an instance of the MongoDBManager class
Connections_manager = ConnectionsCollection(connection_string, database_name, collection_name)

#,provide_automatic_options = True
@app.route('/SaveConnection',methods = ['POST','OPTIONS'])
def CreateConnection():

    
    
    #     # Handle CORS preflight request
    #     response = jsonify({"message": "CORS preflight request successful"})
    #     response.headers.add("Access-Control-Allow-Origin", "*")
    #     response.headers.add("Access-Control-Allow-Headers", "*")
    #     response.headers.add("Access-Control-Allow-Methods", "*")
    #     return response
    
        print(request.form)

        if not request.form.get("id"):
            
            document = {
            "ConnectionName": request.form.get("ConnectionName"),
            "URL": request.form.get("URL"),
            "Username": request.form.get("Username"),
            "Password": request.form.get("Password"),
            "IsActive": True,
            "Type" : request.form.get("Type"),
            "Version": "4.0",
            }
            print(document)
            return  Connections_manager.insert_document(document)

        
        else:
            return Connections_manager.update_document(request.form.get("id"),request.form.to_dict())

    
    


   

@app.route('/GetConnectionNames',methods = ['GET'])
def ConnectionNames():

    cursor = Connections_manager.retrieve_all()
    
    connection_dict = {}
  
    for document in cursor:
        if document and document.get("ConnectionName") and document.get("Type"):
            
            connection_type = document.get("Type")
            connection_name = document.get("ConnectionName")
            
            # If the Type is not already in the dictionary, add it with an empty list
            if connection_type not in connection_dict:
                connection_dict[connection_type] = []

            # Append the ConnectionName to the list
            connection_dict[connection_type].append(connection_name)

    return connection_dict
    
@app.route('/checkConnectionNeo4j/<connectionName>',methods = ['GET'])
def CheckConnectionNJ(connectionName):
    
    try:
        Uri,Username,password = Connections_manager.retrieve_connection_creds(connectionName)
        
        graphdb = GraphDatabase.driver(uri=Uri, auth=(Username, password))
        session = graphdb.session()
        session.run("call apoc.meta.schema ")
        return jsonify({"status": True,"message":"successfully established connection"})
    except Exception as e:
        # Check if the error message contains "Unable to retrieve routing information"
        if "Unable to retrieve routing information" in str(e):
            # Replace +s with +ssc in the URI and try again
            modified_uri = Uri.replace("+s", "+ssc")
            try:
                graphdb = GraphDatabase.driver(uri=modified_uri, auth=(Username, password))
                session = graphdb.session()
                session.run("call apoc.meta.schema ")
                Connections_manager.update_document_newkey(connectionName,"URL",modified_uri)
                return jsonify({"status": True,"message":"successfully established connection"})
            except Exception as modified_error:
                return jsonify({"status": True, "message": str(modified_error)})
        else:
            return jsonify({"status": False, "messagee": str(e)})
    
@app.route('/checkConnectionTigerGraph/<connectionName>',methods = ['GET'])
def CheckConnectionTG(connectionName):
    try:
       
            #Uri,Username,password,_ = Connections_manager.retrieve_connection_creds(request.form.get('TGconnection'))
            Uri,Username,password = Connections_manager.retrieve_connection_creds(connectionName)
           
            conn = tg.TigerGraphConnection(host=Uri, username=Username, password = password)
        
            conn.gsql('ls')
            return jsonify({"status": True,"message":"successfully established connection"})
    except Exception as e:
        print("here222")
        return jsonify({"status": False, "message": str(e)})
    

@app.route('/CheckTigerGraphName/',methods = ['GET'])
def CheckTGraphName():
    try:
        #graphName = request.form.get('GraphName')
        graphName = request.args.get('graphName')
        connectionName = request.args.get('ConnectionName')
        
        if trie.search(graphName):
            return jsonify({"status": False,"message":"GraphName Entered is a TigerGraph Keyword"})
        print(graphName)
        if contains_special_characters(graphName):
            return jsonify({"status": False,"message":"GraphName Entered contains special character"})
        Uri,Username,password = Connections_manager.retrieve_connection_creds(connectionName,getgraphname = False)
        conn = tg.TigerGraphConnection(host=Uri, username=Username, password = password)
        result = conn.gsql('ls')
        if graphName in result:
            return {"status": False,"message":"GraphName Entered is already existing in cluster as graph,vertex or edge name"}
        res = Connections_manager.update_document_newkey(connectionName,"GraphName",graphName)
        print(res)
            
        return {"status": True,"message":"GraphName Entered is acceptable"}
    except Exception as e:
        return {"status": False, "message": str(e)}
    
@app.route('/Migrate',methods = ['GET'])
def Migrattion():
    if request.method == 'GET':
        tg_connection = request.args.get('TGconnection')
        nj_connection = request.args.get('NJconnection')
        return Migrate(Connections_manager,tg_connection,nj_connection,trie)

@app.route('/ConnectionDetails',methods = ['GET'])
def ConnectionDetails():
    cursor = Connections_manager.retrieve_all_document()
    document_list = list(cursor)
    document_dict = {}
    try:
        document_dict["message"] = [
            {
                "ConnectionName": document.get("ConnectionName"),
                "URL": document.get("URL"),
                "Username": document.get("Username"),
                "Password": document.get("Password"),
                "Type": document.get("Type"),
                "id": str(document.get("_id")),
            }
            for document in document_list
            if document.get("ConnectionName") is not None
        ]
        document_dict["status"] = True
    except Exception as e:
        document_dict["status"] = False
        document_dict["message"] = str(e)
    #print(dict(cursor))
    return document_dict

@app.route("/DeleteConnection",methods = ["GET"])
def DeleteConnection():
    print(request.args.get('objectID'))
    return Connections_manager.delete_document(request.args.get('objectID'))

def contains_special_characters(input_string):
    # Define a regular expression for special characters
    special_char_regex = re.compile(r'[@_!#$%^&*()<>?/\|}{~:]')

    # Search for special characters in the input string
    match = re.search(special_char_regex, input_string)

    # Return True if special characters are found, False otherwise
    return bool(match)

    
if __name__ == '__main__':
    
    app.run(debug=True)