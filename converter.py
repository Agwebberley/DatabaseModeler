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

    def search_object_types(obj):
        """Search the schema for object types"""
        if isinstance(obj, dict):
            if obj.get("objectType") == "TableNormal_PGSQL":
                entity_tables.append(obj["name"])
            for value in obj.values():
                search_object_types(value)
        elif isinstance(obj, list):
            for item in obj:
                search_object_types(item)

    search_object_types(schema)
    return entity_tables

def get_attributes(schema):
    """Get the attributes from the schema"""
    attributes = {}

    def search_attributes(obj):
        """Search the schema for attributes"""
        # The attributes are objectTypes of "TableField_PGSQL"
        # They are in a list of "fields" in the "TableNormal_PGSQL" object
        # Save the name, type, (optional) length, (optional) decimal places, and (optional) default value
        # Ignore if the name is "id" or "pk"

        # Attributes are a dictionary of dictionaries
        # In the form of {table_name: {attribute_name: {attribute_type: type, attribute_length: length, attribute_decimal_places: decimal_places, attribute_default_value: default_value}}}
        if isinstance(obj, dict):
            if obj.get("objectType") == "TableNormal_PGSQL":
                for field in obj["fields"]:
                    if field["objectType"] == "TableField_PGSQL":
                        if field["name"] != "id" and field["name"] != "pk":
                            if obj["name"] not in attributes:
                                attributes[obj["name"]] = {}
                            attributes[obj["name"]][field["name"]] = {"type": field["type"]}
                            if field.get("length"):
                                attributes[obj["name"]][field["name"]]["length"] = field["length"]
                            if field.get("decimalPlaces"):
                                attributes[obj["name"]][field["name"]]["decimal_places"] = field["decimalPlaces"]
                            if field.get("defaultValue"):
                                attributes[obj["name"]][field["name"]]["default_value"] = field["defaultValue"]  
            for value in obj.values():
                search_attributes(value)
        elif isinstance(obj, list):
            for item in obj:
                search_attributes(item)

    search_attributes(schema)
    return attributes

def pretty_print_json(json_obj):
    """Pretty print a json object"""
    print(json.dumps(json_obj, indent=4, sort_keys=True))

def main():
    """Main function"""
    schema = get_schema()
    entity_tables = get_entity_tables(schema)
    attributes = get_attributes(schema)

main()