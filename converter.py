"""
.NDM2 Converter to Django models.py

Step 1: Go through the schema and make a list of each:
    a. Entity Table
    b. attribute
    c. relationship
Step 2: Save the lists to a sqlite3 database (for now) each in thier own table
Step 3: write the models.py file(s) based on the sqlite3 database
Step 4: Migrate the database
Step 5: Add the relationships to the models.py file(s)
Step 6: Migrate the database
Step 7: Generate the forms.py file(s) based on the models.py file(s)
"""

"""
TODO: Support unique
TODO: Support null, blank ✔
TODO: Support OneToOneField ✔
TODO: Support Changes to the schema (Currently a nuclear option is used)
TODO: Generate the forms.py file(s) ✔
TODO: Support relationships with the forms.py file(s) ✔
TODO: Support other Input types in the forms.py file(s) ✔
TODO: Add class Meta, def save() & def __str__() to each of the models ✔
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
                        if field["name"] != "pk" and field["name"] != "id":
                            if obj["name"] not in attributes:
                                attributes[obj["name"]] = {}
                            attributes[obj["name"]][field["name"]] = {"type": field["type"]}
                            if field.get("length"):
                                attributes[obj["name"]][field["name"]]["length"] = field["length"]
                            if field.get("decimals") != -2147483648 and field.get("decimals") != 0:
                                attributes[obj["name"]][field["name"]]["decimal_places"] = field["decimals"]
                            if field.get("defaultValue"):
                                attributes[obj["name"]][field["name"]]["default_value"] = field["defaultValue"]
                            if field.get("IsNullable"):
                                attributes[obj["name"]][field["name"]]["IsNullable"] = field["IsNullable"] 
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
                        relationships[obj["name"]][foreign_key["name"]] = {"fields": foreign_key["fields"], "reference_table": foreign_key["referenceTable"], "reference_fields": foreign_key["referenceFields"], "cardinality": foreign_key["sourceCardinality"]}
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
    c.execute("CREATE TABLE attributes (id INTEGER PRIMARY KEY, table_id INTEGER, attribute_name TEXT, attribute_type TEXT, attribute_length INTEGER, attribute_decimal_places INTEGER, attribute_default_value TEXT, null_ TEXT, FOREIGN KEY(table_id) REFERENCES entity_tables(id))")
    c.execute("CREATE TABLE relationships (id INTEGER PRIMARY KEY, table_id INTEGER, relationship_name TEXT, relationship_fields TEXT, relationship_reference_table TEXT, relationship_reference_fields TEXT, relationship_cardinality TEXT, FOREIGN KEY(table_id) REFERENCES entity_tables(id))")

    # Insert the data
    for i, entity_table in enumerate(entity_tables):
        c.execute("INSERT INTO entity_tables VALUES (?, ?)", (i+1, entity_table))
    for table_name, table_attributes in attributes.items():
        for attribute_name, attribute_details in table_attributes.items():
            table_id = c.execute("SELECT id FROM entity_tables WHERE name=?", (table_name,)).fetchone()[0]
            c.execute("INSERT INTO attributes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (None, table_id, attribute_name, attribute_details["type"], attribute_details.get("length"), attribute_details.get("decimal_places"), attribute_details.get("default_value"), attribute_details.get("IsNullable")))
    for table_name, table_relationships in relationships.items():
        for relationship_name, relationship_details in table_relationships.items():
            table_id = c.execute("SELECT id FROM entity_tables WHERE name=?", (table_name,)).fetchone()[0]
            c.execute("INSERT INTO relationships VALUES (?, ?, ?, ?, ?, ?, ?)", (None, table_id, relationship_name, str(relationship_details["fields"]), relationship_details["reference_table"], str(relationship_details["reference_fields"]), relationship_details["cardinality"]))

    # Save the changes
    conn.commit()

    # Close the connection
    conn.close()

# Step 3: write the models.py file(s) based on the sqlite3 database
def write_models(relation=False, directory=""):
    TYPE_MAP = {
        "int": "IntegerField",
        "int4": "IntegerField",
        "int8": "IntegerField",
        "float": "FloatField",
        "str": "CharField",
        "varchar": "CharField",
        "date": "DateField",
        "datetime": "DateTimeField",
        "timestamptz": "DateTimeField",
        "bool": "BooleanField",
        "text": "TextField",
        "decimal": "DecimalField",
        "numeric": "DecimalField",
        "file": "FileField",
        "image": "ImageField",
    }
    MODEL_APP_MAP = {}
    header = """
from django.db import models
from django.urls import reverse
from django.utils import timezone\n\n
"""
    IMPORTS = {}

    # DEPENDS is a dictionary that keeps track of the dependencies between the models that are in the same app
    # Since parent models need to be created before child models
    DEPENDS = {}

    conn = sqlite3.connect("ndm2.db")
    c = conn.cursor()

    # Get the entity tables
    entity_tables = c.execute("SELECT * FROM entity_tables").fetchall()

    # Create each model class
    for entity_table in entity_tables:
        # Seperate the class and app name
        # The format is appName_className
        # Each app will have its own models.py file
        # Split the string at the first underscore, ignore the any other underscores
        app_name, class_name = entity_table[1].split("_", 1)
        # Create the class
        class_string = f"class {class_name}(models.Model):\n"
        # Get the attributes for the class
        attributes = c.execute("SELECT * FROM attributes WHERE table_id=?", (entity_table[0],)).fetchall()
        # Get the relationships for the class
        relationships = c.execute("SELECT * FROM relationships WHERE table_id=?", (entity_table[0],)).fetchall()

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
            # Get the attribute null
            attribute_null = attribute[7]
            # Add the attribute to the class string
            class_string += f"    {attribute_name} = models.{TYPE_MAP[attribute_type]}("
            if attribute_length:
                class_string += f"max_length={attribute_length}"
                if attribute_decimal_places:
                    class_string += f", decimal_places={attribute_decimal_places}"
                class_string += ", "
            if attribute_default_value:
                class_string += f"default={attribute_default_value}, "
            if attribute_null == "true":
                class_string += "null=true, blank=true"
            class_string += ")\n"
        if relation:
            for relationship in relationships:
                # Get the relationship name
                relationship_name = relationship[2]
                # Get the relationship fields
                relationship_fields = relationship[3]
                
                # Get the relationship reference table
                relationship_reference_table = relationship[4]
                relationship_field = relationship_reference_table.split("_", 1)[1]
                # If the relationship reference table is in the same app, add it to the depends dictionary
                if relationship_reference_table.split("_", 1)[0] == app_name:
                    if app_name not in DEPENDS:
                        DEPENDS[app_name] = []
                    if class_name not in DEPENDS[app_name]:
                        DEPENDS[app_name].append({class_name: []})
                    DEPENDS[app_name][class_name].append(relationship_reference_table.split("_", 1)[1])
                # Get the relationship reference fields
                relationship_reference_fields = relationship[5]
                
                # Get the cardinality of the relationship
                relationship_cardinality = relationship[6]

                if relationship_cardinality == "ZeroOrOneRelationship":
                    relationship_cardinality = "OneToOneField"
                else:
                    relationship_cardinality = "ForeignKey"

                # Add the relationship to the class string
                # Import the model if it is not in the same app
                
                class_string += f"    {relationship_field} = models.{relationship_cardinality}({relationship_reference_table.split('_', 1)[1]}, on_delete=models.CASCADE, related_name='{relationship_field}')\n"
        
        # Add the Meta class to the class string
        class_string += f"\n    class Meta:\n        app_label = '{app_name}'\n\n"

        # Add the __str__ method to the class string
        class_string += f"    def __str__(self):\n        return str(self.pk)\n\n"

        # add the save method to the class string
        class_string += f"    def save(self, *args, **kwargs):\n        super().save(*args, **kwargs)\n\n"

        class_string += "\n\n"
        
        # Put the class in the MODEL_APP_MAP
        if app_name not in MODEL_APP_MAP:
            MODEL_APP_MAP[app_name] = []
        MODEL_APP_MAP[app_name].append(class_string)

        if relation:
            if app_name not in IMPORTS:
                IMPORTS[app_name] = []
            for relationship in relationships:
                if relationship[4].split('_', 1)[0] != app_name:
                    import_str = f"from {relationship[4].split('_', 1)[0]}.models import {relationship[4].split('_', 1)[1]}\n"
                    if import_str not in IMPORTS[app_name]:
                        IMPORTS[app_name].append(import_str)

    
    # Create the models.py files

    # If the directory is empty, use the current directory
    if not directory:
        directory = os.getcwd()
    # Create the models.py files

    if relation:
        # Rearrange the MODEL_APP_MAP so that the parent models are created first
        # This is done by using the DEPENDS dictionary
        for app_name, depends_list in DEPENDS.items():
            # Create a dictionary to hold the new order of the classes
            new_order = {}
            # Create a list to hold the classes that have dependencies
            dependent_classes = []
            # Loop through the depends_list and add the classes to the new_order dictionary
            for depends_dict in depends_list:
                for class_name, dependencies in depends_dict.items():
                    # If the class has no dependencies, add it to the new_order dictionary
                    if not dependencies:
                        new_order[class_name] = MODEL_APP_MAP[app_name].pop(MODEL_APP_MAP[app_name].index(next(filter(lambda x: x.startswith(f"class {class_name}"), MODEL_APP_MAP[app_name]))))
                    # If the class has dependencies, add it to the dependent_classes list
                    else:
                        dependent_classes.append(class_name)
            # Loop through the dependent_classes list and add the classes to the new_order dictionary
            while dependent_classes:
                for class_name in dependent_classes:
                    dependencies = next(filter(lambda x: x.startswith(f"class {class_name}"), MODEL_APP_MAP[app_name])).split("(")[1].split(")")[0].split(", ")
                    # If all of the dependencies are in the new_order dictionary, add the class to the new_order dictionary
                    if all(dependency in new_order for dependency in dependencies):
                        new_order[class_name] = MODEL_APP_MAP[app_name].pop(MODEL_APP_MAP[app_name].index(next(filter(lambda x: x.startswith(f"class {class_name}"), MODEL_APP_MAP[app_name]))))
                        dependent_classes.remove(class_name)
            # Add the classes in the new order to the MODEL_APP_MAP
            MODEL_APP_MAP[app_name] = list(new_order.values()) + MODEL_APP_MAP[app_name]

    for app_name, classes in MODEL_APP_MAP.items():
        # Create the files
        # Each app will have its own models.py file in a directory named after the app
        # The directory will be in the directory specified by the user
        # If the app directory does not exist, create it
        # If there already is a models.py in the app directory, overwrite it
        if not os.path.exists(os.path.join(directory, app_name)):
            os.makedirs(os.path.join(directory, app_name))
        with open(os.path.abspath(os.path.join(directory, app_name, "models.py")), "w") as f:
            f.write(header)
            if app_name in IMPORTS:
                for import_string in IMPORTS[app_name]:
                    f.write(import_string)
            for class_string in classes:
                f.write(class_string)
    


# Step 4 & 6: Migrate the database
def migrate_database(directory):
    # Use the django makemigrations and migrate commands
    # Use the directory specified by the user
    # If the directory does not contain a manage.py file,
    # Inform the user and exit
    if os.path.exists(os.path.join(directory, "manage.py")):
        os.system(f"python {os.path.join(directory, 'manage.py')} makemigrations")
        os.system(f"python {os.path.join(directory, 'manage.py')} migrate")


def generate_forms(directory, relation=False):
    """
from django import forms
from .models import Customers

class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-half px-3 py-2 mb-4 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none sm:text-sm text-black'

class CustomerForm(BaseForm):
    class Meta:
        model = Customers
        fields = ('name', 'billing_address', 'shipping_address', 'phone', 'email')


    """
    HEADER = """
from django import forms\n
class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'w-half px-3 py-2 mb-4 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none sm:text-sm text-black'
\n
"""
    MODEL_APP_MAP = {}
    
    # For every model, create a form inside the forms.py file in the app directory
    # The form will be named ModelNameForm
    # The form will have a Meta class with the model and fields

    c = sqlite3.connect("ndm2.db").cursor()
    entity_tables = c.execute("SELECT * FROM entity_tables").fetchall()

    for entity_table in entity_tables:
        # Seperate the class and app name
        # The format is appName_className
        # Each app will have its own models.py file
        # Split the string at the first underscore, ignore the any other underscores
        app_name, class_name = entity_table[1].split("_", 1)
        # Create the form
        form_string = f"class {class_name}Form(forms.ModelForm):\n"
        # Get the attributes for the class
        attributes = c.execute("SELECT * FROM attributes WHERE table_id=?", (entity_table[0],)).fetchall()
        # Get the relationships for the class
        relationships = c.execute("SELECT * FROM relationships WHERE table_id=?", (entity_table[0],)).fetchall()

        form_string += "    class Meta:\n"
        # Import the model
        form_string += f"        from .models import {class_name}\n"
        form_string += f"        model = {class_name}\n"
        form_string += "        fields = ("
        for attribute in attributes:
            form_string += f"'{attribute[2]}', "
        if relation:
            for relationship in relationships:
                # Get the relationship reference table
                relationship_reference_table = relationship[4]
                relationship_field = relationship_reference_table.split("_", 1)[1]
                form_string += f"'{relationship_field}', "
        form_string = form_string[:-2]
        form_string += ")\n\n"
        
        # Put the form in the MODEL_APP_MAP
        if app_name not in MODEL_APP_MAP:
            MODEL_APP_MAP[app_name] = []
        MODEL_APP_MAP[app_name].append(form_string)

    # Create the forms.py files
    # Use the directory specified by the user
    # If the directory is empty, use the current directory

    for app in MODEL_APP_MAP:
        # Create the files
        # Each app will have its own forms.py file in a directory named after the app
        # The directory will be in the directory specified by the user
        # If the app directory does not exist, create it
        # If there already is a forms.py in the app directory, overwrite it
        if not os.path.exists(os.path.join(directory, app)):
            os.makedirs(os.path.join(directory, app))
        with open(os.path.join(directory, app, "forms.py"), "w") as f:
            f.write(HEADER)
            for form_string in MODEL_APP_MAP[app]:
                f.write(form_string)
        

def main():
    """Main function"""

    # Ask for the directory to save the files in
    directory = input("Enter the directory to save the models.py files in (if empty will use current directory): ")
    warning = input("WARNING: This will overwrite any existing models.py files in the directory. Continue? (y/n): ")
    if warning.lower() != "y":
        sys.exit()
    
    schema = get_schema()
    entity_tables = get_entity_tables(schema)
    attributes = get_attributes(schema)
    relationships = get_relationships(schema)
    save_to_database(entity_tables, attributes, relationships)

    generate_forms(directory)

    write_models(directory=directory)

    # Step 4:
    migrate_database(directory)

    

    # Step 5:
    write_models(relation=True, directory=directory)

    # Step 6:
    migrate_database(directory)

    generate_forms(directory, relation=True)

main()