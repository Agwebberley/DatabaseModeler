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
        # Ignore if the name is "pk"

        # Attributes are a dictionary of dictionaries
        # In the form of {table_name: {attribute_name: {attribute_type: type, attribute_length: length, attribute_decimal_places: decimal_places, attribute_default_value: default_value}}}
        if isinstance(obj, dict):
            if obj.get("objectType") == "TableNormal_PGSQL":
                for field in obj["fields"]:
                    if field["objectType"] == "TableField_PGSQL":
                        if field["name"] != "pk":
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

def get_relationships(schema):
    """Get the relationships from the schema"""
    relationships = {}

    def search_relationships(obj):
        """Search the schema for relationships"""
        # The relationships are objectTypes of "ForeignKey_PGSQL"
        # They are in a list of "foreignKeys" in the "TableNormal_PGSQL" object
        # Save the name, fields (list), referenceTable, referenceFields (List)

        # foreignKeys are a list of dictionaries
        # In the form of {table_name: {name: {fields: [field1, field2, ...], reference_table: reference_table, reference_fields: [reference_field1, reference_field2, ...]}}
        if isinstance(obj, dict):
            if obj.get("objectType") == "TableNormal_PGSQL":
                for foreign_key in obj["foreignKeys"]:
                    if foreign_key["objectType"] == "ForeignKey_PGSQL":
                        if obj["name"] not in relationships:
                            relationships[obj["name"]] = {}
                        relationships[obj["name"]][foreign_key["name"]] = {"fields": foreign_key["fields"], "reference_table": foreign_key["referenceTable"], "reference_fields": foreign_key["referenceFields"]}
            for value in obj.values():
                search_relationships(value)
        elif isinstance(obj, list):
            for item in obj:
                search_relationships(item)

    search_relationships(schema)
    return relationships

def pretty_print_json(json_obj):
    """Pretty print a json object"""
    print(json.dumps(json_obj, indent=4, sort_keys=True))


# Step 2: Save the lists to a sqlite3 database (for now) each in thier own table
def save_to_database(entity_tables, attributes, relationships):
    """Save the lists to a sqlite3 database (for now) each in thier own table"""
    # Create the database
    conn = sqlite3.connect("ndm2.db")
    c = conn.cursor()

    # Create the tables
    c.execute("CREATE TABLE entity_tables (name text)")
    c.execute("CREATE TABLE attributes (table_name text, attribute_name text, attribute_type text, attribute_length integer, attribute_decimal_places integer, attribute_default_value text)")
    c.execute("CREATE TABLE relationships (table_name text, relationship_name text, relationship_fields text, relationship_reference_table text, relationship_reference_fields text)")

    # Insert the data
    for entity_table in entity_tables:
        c.execute("INSERT INTO entity_tables VALUES (?)", (entity_table,))
    for table_name, table_attributes in attributes.items():
        for attribute_name, attribute_details in table_attributes.items():
            c.execute("INSERT INTO attributes VALUES (?, ?, ?, ?, ?, ?)", (table_name, attribute_name, attribute_details["type"], attribute_details.get("length"), attribute_details.get("decimal_places"), attribute_details.get("default_value")))
    for table_name, table_relationships in relationships.items():
        for relationship_name, relationship_details in table_relationships.items():
            c.execute("INSERT INTO relationships VALUES (?, ?, ?, ?, ?)", (table_name, relationship_name, relationship_details["fields"], relationship_details["reference_table"], relationship_details["reference_fields"]))

    # Save the changes
    conn.commit()

    # Close the connection
    conn.close()



def main():
    """Main function"""
    schema = get_schema()
    entity_tables = get_entity_tables(schema)
    attributes = get_attributes(schema)
    relationships = get_relationships(schema)
    pretty_print_json(relationships)

main()