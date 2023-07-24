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
                            if field.get("decimals") != -2147483648 and field.get("decimals") != 0:
                                attributes[obj["name"]][field["name"]]["decimal_places"] = field["decimals"]
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
    
    # Clear the database
    c.execute("DROP TABLE IF EXISTS entity_tables")
    c.execute("DROP TABLE IF EXISTS attributes")
    c.execute("DROP TABLE IF EXISTS relationships")

    # Create the tables
    c.execute("CREATE TABLE entity_tables (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("CREATE TABLE attributes (id INTEGER PRIMARY KEY, table_id INTEGER, attribute_name TEXT, attribute_type TEXT, attribute_length INTEGER, attribute_decimal_places INTEGER, attribute_default_value TEXT, FOREIGN KEY(table_id) REFERENCES entity_tables(id))")
    c.execute("CREATE TABLE relationships (id INTEGER PRIMARY KEY, table_id INTEGER, relationship_name TEXT, relationship_fields TEXT, relationship_reference_table TEXT, relationship_reference_fields TEXT, FOREIGN KEY(table_id) REFERENCES entity_tables(id))")

    # Insert the data
    for i, entity_table in enumerate(entity_tables):
        c.execute("INSERT INTO entity_tables VALUES (?, ?)", (i+1, entity_table))
    for table_name, table_attributes in attributes.items():
        for attribute_name, attribute_details in table_attributes.items():
            table_id = c.execute("SELECT id FROM entity_tables WHERE name=?", (table_name,)).fetchone()[0]
            c.execute("INSERT INTO attributes VALUES (?, ?, ?, ?, ?, ?, ?)", (None, table_id, attribute_name, attribute_details["type"], attribute_details.get("length"), attribute_details.get("decimal_places"), attribute_details.get("default_value"),))
    for table_name, table_relationships in relationships.items():
        for relationship_name, relationship_details in table_relationships.items():
            table_id = c.execute("SELECT id FROM entity_tables WHERE name=?", (table_name,)).fetchone()[0]
            c.execute("INSERT INTO relationships VALUES (?, ?, ?, ?, ?, ?)", (None, table_id, relationship_name, str(relationship_details["fields"]), relationship_details["reference_table"], str(relationship_details["reference_fields"]),))

    # Save the changes
    conn.commit()

    # Close the connection
    conn.close()

# Step 3: write the models.py file(s) based on the sqlite3 database
def write_models():
    TYPE_MAP = {
        "int": "IntegerField",
        "float": "FloatField",
        "str": "CharField",
        "date": "DateField",
        "datetime": "DateTimeField",
        "bool": "BooleanField",
        "text": "TextField",
        "decimal": "DecimalField",
        "file": "FileField",
        "image": "ImageField",
    }
    MODEL_APP_MAP = {}
    header = """
    from django.db import models
    from django.urls import reverse
    from django.utils import timezone
    """

    conn = sqlite3.connect("ndm2.db")
    c = conn.cursor()

    # Get the entity tables
    entity_tables = c.execute("SELECT * FROM entity_tables").fetchall()

    # Create each model class
    for entity_table in entity_tables:
        # Seperate the class and app name
        # The format is appName_className
        # Each app will have its own models.py file
        app_name, class_name = entity_table[1].split("_")
        # Create the class
        class_string = f"class {class_name}(models.Model):\n"
        # Get the attributes for the class
        attributes = c.execute("SELECT * FROM attributes WHERE table_id=?", (entity_table[0],)).fetchall()
        for attribute in attributes:
            # Get the attribute name
            attribute_name = attribute[2]
            # Get the attribute type
            attribute_type = attribute[3]
            # Get the attribute length
            attribute_length = attribute[4]
            # Get the attribute decimal places
            attribute_decimal_places = attribute[5]
            # Get the attribute default value
            attribute_default_value = attribute[6]
            # Add the attribute to the class string
            class_string += f"    {attribute_name} = models.{TYPE_MAP[attribute_type]}("
            if attribute_length:
                class_string += f"{attribute_length}"
                if attribute_decimal_places:
                    class_string += f", {attribute_decimal_places}"
                class_string += ", "
            if attribute_default_value:
                class_string += f"{attribute_default_value}"
            class_string += ")\n"
        class_string += "\n\n"
        
        # Put the class in the MODEL_APP_MAP
        if app_name not in MODEL_APP_MAP:
            MODEL_APP_MAP[app_name] = []
        MODEL_APP_MAP[app_name].append(class_string)
    
    # Create the models.py files
    # Ask for the directory to save the files in
    directory = input("Enter the directory to save the models.py files in: ")
    warning = input("WARNING: This will overwrite any existing models.py files in the directory. Continue? (y/n): ")

    if warning.lower() == "y":
        # Create the models.py files
        for app_name, classes in MODEL_APP_MAP.items():
            # Create the file
            with open(os.path.join(directory, "models.py"), "w") as f:
                # Write the header
                f.write(header)
                # Write the classes
                for class_string in classes:
                    f.write(class_string)
    else:
        print("Aborting...")
        sys.exit(0)






def main():
    """Main function"""
    schema = get_schema()
    entity_tables = get_entity_tables(schema)
    attributes = get_attributes(schema)
    relationships = get_relationships(schema)
    save_to_database(entity_tables, attributes, relationships)

main()