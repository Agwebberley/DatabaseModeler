"""
.NDM2 Converter to Django models.py

Step 1: Go through the schema and make a list of each:
    a. Entity Table
    b. attribute
    c. relationship
Step 2: Save the lists to a sqlite3 database (for now) each in thier own table
Step 3: write the models.py file(s) based on the sqlite3 database
"""
import json
import sqlite3
import os
import sys


# Step 1: Go through the schema and make a list of each:
#     a. Entity Table
#     b. attribute
#     c. relationship
def get_schema():
    """Get the schema from the .ndm2 file"""
    with open("DatabaseSchema.ndm2", "r") as f:
        schema = json.load(f)
    return schema

def get_entity_tables(schema):
    """Get the entity tables from the schema"""
    entity_tables = []

    def search_object_types(obj,  ):
        """Search the schema for object types"""
        if isinstance(obj, dict):
            if obj.get("objectType") == "TableNormal_PGSQL":
                entity_tables.append(obj["name"])
            for value in obj.values():
                search_object_types(value)
        elif isinstance(obj, list):
            for item in obj:
                search_object_types(item)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                search_object_types(value)
        

    search_object_types(schema)
    return entity_tables



def main():
    """Main function"""
    schema = get_schema()
    entity_tables = get_entity_tables(schema)
    print(entity_tables)

main()