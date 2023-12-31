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
TODO: Sort the models based on dependencies ✔
TODO: Add created_at and updated_at to each model & ignore them in the forms.py file(s) ✔
TODO: If the attribute starts with a underscore, ignore it in the forms.py file(s)
TODO: If a table has a atrribute named _str=* then use what is in the * as the __str__ method
TODO: Auto Generate the views.py file(s) ✔
TODO: Add Gui using customtkinter to allow the user to have more control over the conversion ✔
TODO: Fix scrollbar
TODO: Add logic that removes url patterns that don't exist in the views.py file(s)
TODO: Auto generate the urls.py file(s) ✔
"""

import json
import sqlite3
import os
import sys
import customtkinter as tk
import tkinter
from toposort import get_dependency_order


class Converter(tk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("500x500")
        self.title("Navicat to Django Converter")
        
        self.outer_frame = tk.CTkFrame(self)
        self.outer_frame.pack(fill="both", expand=1)        

        # canvas
        self.my_canvas = tk.CTkCanvas(self.outer_frame)
        self.my_canvas.pack(side="left", fill="both", expand=1)      

        # scrollbar
        self.my_scrollbar = tk.CTkScrollbar(self.outer_frame, orientation="vertical", command=self.my_canvas.yview)
        self.my_scrollbar.pack(side="right", fill="y")       

        # configure the canvas
        self.my_canvas.configure(yscrollcommand=self.my_scrollbar.set)
        self.my_canvas.bind(
            '<Configure>', lambda e: self.my_canvas.configure(scrollregion=self.my_canvas.bbox("all"))
        )
        
        # bind the mousewheel event to the canvas
        self.my_canvas.bind_all("<MouseWheel>", self.on_mousewheel)

        self.main_frame = tk.CTkFrame(self.my_canvas, width = 1000, height = 100)

        self.my_canvas.create_window((0, 0), window=self.main_frame, anchor="nw") 

        self.startB = tk.CTkButton(self.main_frame, text="Convert", command=self.directory)
        self.startB.pack(padx=20, pady=20)

    def on_mousewheel(self, event):
        # scroll the canvas up or down based on the mousewheel direction
        if event.delta > 0:
            self.my_canvas.yview_scroll(-1, "units")
        elif event.delta < 0:
            self.my_canvas.yview_scroll(1, "units")
    
    def directory(self):
        """Main function"""
        
        # Remove startB
        self.startB.destroy()

        # Ask for the directory to save the files in
        self.directory_label = tk.CTkLabel(self.main_frame, text="Enter the directory to save the models.py files in (if empty will use current directory): ")
        self.directory_label.pack(padx=20, pady=20)
        self.directory_entry = tk.CTkEntry(self.main_frame)
        self.directory_entry.pack(padx=20, pady=20)

        def warning_message():
            warning = tkinter.messagebox.askquestion("Warning", "This will overwrite any existing models.py files in the directory. Continue?")
            if warning == "no":
                sys.exit()
            else:
                self.main()

        self.warning_button = tk.CTkButton(self.main_frame, text="Continue", command=warning_message)
        self.warning_button.pack(padx=20, pady=20)
    def main(self):
        directory = self.directory_entry.get()
        # Remove the directory label, entry, and button
        self.directory_label.destroy()
        self.directory_entry.destroy()
        self.warning_button.destroy()

        schema = self.get_schema()
        entity_tables = self.get_entity_tables(schema)
        attributes = self.get_attributes(schema)
        relationships = self.get_relationships(schema)
        self.save_to_database(entity_tables, attributes, relationships)

        self.generate_forms(directory)

        self.write_models(directory=directory)

        # Step 4:
        self.migrate_database(directory, entity_tables)

        # Step 5:
        self.write_models(relation=True, directory=directory)

        # Step 6:
        self.migrate_database(directory)

        self.generate_forms(directory, relation=True)

        # Step 7:
        self.views_gui(entity_tables, directory)

        # Step 8:
        self.generate_urls(directory)
    
    # Step 1: Go through the schema and make a list of each:
    #     a. Entity Table
    #     b. attribute
    #     c. relationship
    def get_schema(self):
        """Get the schema from the .ndm2 file"""
        with open("DatabaseSchema.ndm2", "r") as f:
            schema = json.load(f)
        return schema   

    def get_entity_tables(self, schema):
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

    def get_attributes(self, schema):
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
                            if field["name"] != "pk" and field["name"] != "id" and field["name"][-3:] != "_id" and field["name"] != "created_at" and field["name"] != "updated_at":
                                if obj["name"] not in attributes:
                                    attributes[obj["name"]] = {}
                                attributes[obj["name"]][field["name"]] = {"type": field["type"]}
                                if field.get("length"):
                                    attributes[obj["name"]][field["name"]]["length"] = field["length"]
                                if field.get("decimals") != -2147483648 and field.get("decimals") != 0:
                                    attributes[obj["name"]][field["name"]]["decimal_places"] = field["decimals"]
                                if field.get("defaultValue"):
                                    attributes[obj["name"]][field["name"]]["default_value"] = field["defaultValue"]
                                if field.get("isNullable"):
                                    attributes[obj["name"]][field["name"]]["isNullable"] = field["isNullable"] 
                for value in obj.values():
                    search_attributes(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_attributes(item)

        search_attributes(schema)
        return attributes

    def get_relationships(self, schema):
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

    def pretty_print_json(self, json_obj):
        """Pretty print a json object"""
        print(json.dumps(json_obj, indent=4, sort_keys=True))


    # Step 2: Save the lists to a sqlite3 database (for now) each in thier own table
    def save_to_database(self, entity_tables, attributes, relationships):
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
                c.execute("INSERT INTO attributes VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (None, table_id, attribute_name, attribute_details["type"], attribute_details.get("length"), attribute_details.get("decimal_places"), attribute_details.get("default_value"), attribute_details.get("isNullable")))
        for table_name, table_relationships in relationships.items():
            for relationship_name, relationship_details in table_relationships.items():
                table_id = c.execute("SELECT id FROM entity_tables WHERE name=?", (table_name,)).fetchone()[0]
                c.execute("INSERT INTO relationships VALUES (?, ?, ?, ?, ?, ?, ?)", (None, table_id, relationship_name, str(relationship_details["fields"]), relationship_details["reference_table"], str(relationship_details["reference_fields"]), relationship_details["cardinality"]))

        # Save the changes
        conn.commit()

        # Close the connection
        conn.close()

    # Step 3: write the models.py file(s) based on the sqlite3 database
    def write_models(self, relation=False, directory=""):
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

            if app_name not in DEPENDS:
                DEPENDS[app_name] = {}
            if class_name not in DEPENDS[app_name]:
                DEPENDS[app_name][class_name] = []

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
                    if TYPE_MAP[attribute_type] == "DecimalField":
                        class_string += f"max_digits={attribute_length}, "
                    elif TYPE_MAP[attribute_type] == "IntegerField":
                        pass
                    else:
                        class_string += f"max_length={attribute_length}, "
                    if attribute_decimal_places:
                        if class_string[-2:] == ", ":
                            class_string = class_string[:-2]
                        class_string += f", decimal_places={attribute_decimal_places}, "
                if attribute_default_value:
                    class_string += f"default={attribute_default_value}, "
                if attribute_null == '1':
                    class_string += "null=True, blank=True"
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

                    related_name = ', related_name="' + class_name + '"'

                    if relationship_reference_table.split("_", 1)[0] == app_name:
                        related_name = ', related_name="_' + class_name + '"'


                    class_string += f"    {relationship_field} = models.{relationship_cardinality}({relationship_reference_table.split('_', 1)[1]}, on_delete=models.CASCADE{related_name})\n"

            # Add created_at and updated_at to each model
            class_string += f"    created_at = models.DateTimeField(auto_now_add=True)\n"
            class_string += f"    updated_at = models.DateTimeField(default=auto_now=True)\n"

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

        def sort_model_app_map(model_app_map, depends):
            """
            The function to sort the MODEL_APP_MAP dictionary based on the dependencies.

            Args:
            model_app_map: The MODEL_APP_MAP dictionary to sort.
            depends: The DEPENDS dictionary representing dependencies.
            """

            # Get the dependency order
            dependency_order = get_dependency_order(depends)

            # Prepare a dictionary for quick access to class names.
            class_name_dict = {}
            for app, classes in model_app_map.items():
                for class_content in classes:
                    class_name = class_content.split("(")[0].split(" ")[1]
                    class_name_dict[class_name] = class_content

            # Prepare the sorted dictionary.
            sorted_dict = {}
            for class_name in dependency_order:
                if class_name in class_name_dict:
                    app_name = next(app for app, classes in model_app_map.items() if class_name_dict[class_name] in classes)
                    if app_name in sorted_dict:
                        sorted_dict[app_name].append(class_name_dict[class_name])
                    else:
                        sorted_dict[app_name] = [class_name_dict[class_name]]

            return sorted_dict

        if relation:
            MODEL_APP_MAP = sort_model_app_map(MODEL_APP_MAP, DEPENDS)
            # Reverse the order of the classes in each app
            MODEL_APP_MAP = {app: classes[::-1] for app, classes in MODEL_APP_MAP.items()}


        # Create the models.py files
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
    def migrate_database(self, directory, entity_tables=[]):
        # Get the name of all the apps
        apps = []
        for app in entity_tables:
            apps.append(app.split("_", 1)[0])
        apps = list(set(apps))
        app_string = ""
        for app in apps:
            app_string += f"{app} "

        # Use the django makemigrations and migrate commands
        # Use the directory specified by the user
        # If the directory does not contain a manage.py file,
        # Inform the user and exit
        if os.path.exists(os.path.join(directory, "manage.py")):
            os.system(f"python {os.path.join(directory, 'manage.py')} makemigrations " + app_string)
            os.system(f"python {os.path.join(directory, 'manage.py')} migrate")


    def generate_forms(self, directory, relation=False):
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

    def views_gui(self, entity_tables, directory=""):
        """Get the user input for the views to generate"""

        # Each app is going to get a label
        # Each model will get a label under the app label
        # And the user can select which views to generate for each model
        # The views will be generated in the views.py file in the app directory

        # Get a dictionary of the apps and models
        apps = {}
        for entity_table in entity_tables:
            app_name, class_name = entity_table.split("_", 1)
            if app_name not in apps:
                apps[app_name] = []
            apps[app_name].append(class_name)

        # Create the labels and text boxes
        """
        app1:
            model1: 
                list checkbox
                etc.
        """
        # Create the labels
        app_labels = {}
        self.app_checkboxes = {}
        row_num = 0
        for app in apps:
            self.app_checkboxes[app] = {}
            app_labels[app] = tk.CTkLabel(self.main_frame, text=app + ":", anchor="w")
            app_labels[app].grid(row=row_num, column=0, padx=20, pady=20, sticky="w")
            model_labels = {}
            for model in apps[app]:
                
                model_labels[model] = tk.CTkLabel(self.main_frame, text="\t" + model + ":", anchor="w")
                model_labels[model].grid(row=row_num, column=1, padx=20, pady=20, sticky="w")
                
                # Create the checkboxes
                
                
                self.app_checkboxes[app][model] = {}
                self.app_checkboxes[app][model]["list"] = tk.CTkCheckBox(self.main_frame, text="List")
                self.app_checkboxes[app][model]["list"].grid(row=row_num, column=2, padx=20, pady=20, sticky="w")
                self.app_checkboxes[app][model]["create"] = tk.CTkCheckBox(self.main_frame, text="Create")
                self.app_checkboxes[app][model]["create"].grid(row=row_num, column=3, padx=20, pady=20, sticky="w")
                self.app_checkboxes[app][model]["update"] = tk.CTkCheckBox(self.main_frame, text="Update")
                self.app_checkboxes[app][model]["update"].grid(row=row_num, column=4, padx=20, pady=20, sticky="w")
                self.app_checkboxes[app][model]["delete"] = tk.CTkCheckBox(self.main_frame, text="Delete")
                self.app_checkboxes[app][model]["delete"].grid(row=row_num, column=5, padx=20, pady=20, sticky="w")

                row_num += 1
            
        # add a continue button
        self.continue_button = tk.CTkButton(self.main_frame, text="Continue", command=lambda: self.generate_views(directory))
        self.continue_button.grid(row=row_num, column=0, padx=20, pady=20, sticky="w")
        
        # Set all of the checkboxes to selected
        for app in self.app_checkboxes:
            for model in self.app_checkboxes[app]:
                for checkbox in self.app_checkboxes[app][model]:
                    self.app_checkboxes[app][model][checkbox].select()

    # Step 7: Generate the views.py file(s) based on the models.py file(s)
    def generate_views(self, directory):
        """Gemerates all of the views for each of the models.
        Each model will can have a list, detail, create, update, and delete view.
        Which views are generated is determined by the user. and are stored in
        the dictionary self.app_checkboxes."""

        MODEL_APP_MAP = {}
        IMPORTS = {}

        HEADER = """
# THIS FILE IS AUTOGENERATED
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy\n
"""

        for app in self.app_checkboxes:
            for model in self.app_checkboxes[app]:
                for checkbox in self.app_checkboxes[app][model]:
                    if self.app_checkboxes[app][model][checkbox].get() == 1:
                        if app not in MODEL_APP_MAP:
                            MODEL_APP_MAP[app] = []
                        if app not in IMPORTS:
                            IMPORTS[app] = []
                        
                        # Add the import for the model and form
                        IMPORTS[app].append(f"from {app}.models import {model}\n")
                        IMPORTS[app].append(f"from {app}.forms import {model}Form\n")

                        model_caps = model.capitalize()

                        # Add the view to the MODEL_APP_MAP
                        if checkbox == "list":
                            formatted_patterns = f"{{'Details': '{model}:{model}_detail' ,'Update': '{model}:{model}_update', 'Delete': '{model}:{model}_delete'}}"

                            model_str = f"""
class {model}ListView(ListView):
    model = {model}
    template = "listview.html"
    # Set model_fields to the fields of the model
    model_fields = [field.name for field in {model}._meta.get_fields()]
    try: 
    # Remove any unwanted fields here
        pass
    except: pass
    
    # Set the url patterns for the dropdown menu under the action column
    patterns = {formatted_patterns}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_fields'] = self.model_fields
        context['patterns'] = (self.patterns)
        context['h1'] = '{model_caps} List'
        context['bpattern'] = '{model}:{model}_create'
        context['bname'] = 'Create {model_caps}'
        return context \n
"""
                            MODEL_APP_MAP[app].append(model_str)
                        elif checkbox == "create":
                            model_str = f"""
class {model}CreateView(CreateView):
    model = {model}
    form_class = {model}Form
    template = "form.html"
    success_url = reverse_lazy('{model}:{model}_list') \n
    """
                            MODEL_APP_MAP[app].append(model_str)
                        elif checkbox == "update":
                            model_str = f"""
class {model}UpdateView(UpdateView):
    model = {model}
    form_class = {model}Form
    template = "form.html"
    success_url = reverse_lazy('{model}:{model}_list') \n
    """
                            MODEL_APP_MAP[app].append(model_str)
                        elif checkbox == "delete":
                            model_str = f"""
class {model}DeleteView(DeleteView):
    model = {model}
    template = "delete.html"
    success_url = reverse_lazy('{model}:{model}_list') \n
    """
                            MODEL_APP_MAP[app].append(model_str)
                        
        # Create the views.py files
        # Use the directory specified by the user

        for app in MODEL_APP_MAP:
            # Create the files
            # Each app will have its own views.py file in a directory named after the app
            # The directory will be in the directory specified by the user
            # If the app directory does not exist, create it
            # If there already is a views.py in the app directory, overwrite it
            if not os.path.exists(os.path.join(directory, app)):
                os.makedirs(os.path.join(directory, app))
            with open(os.path.join(directory, app, "views.py"), "w") as f:
                f.write(HEADER)
                IMPORTS = list(set(IMPORTS[app]))
                for import_string in IMPORTS[app]:
                    f.write(import_string)
                for model_string in MODEL_APP_MAP[app]:
                    f.write(model_string)
    
    def generate_urls(self, directory):
        """Generates the urls.py file(s) based on the views.py file(s)"""

        MODEL_APP_MAP = {}
        HEADER = """
# THIS FILE IS AUTOGENERATED
from django.urls import path
from .views import *

"""

        for app in self.app_checkboxes:
            if app not in MODEL_APP_MAP:
                MODEL_APP_MAP[app] = []
            for model in self.app_checkboxes[app]:
                for checkbox in self.app_checkboxes[app][model]:
                    if self.app_checkboxes[app][model][checkbox].get() == 1:
                        model_caps = model.capitalize()
                        if checkbox == "list":
                            model_str = f"path('{model}/', {model}ListView.as_view(), name='{model}_list'),\n"
                            MODEL_APP_MAP[app].append(model_str)
                        elif checkbox == "create":
                            model_str = f"path('{model}/create/', {model}CreateView.as_view(), name='{model}_create'),\n"
                            MODEL_APP_MAP[app].append(model_str)
                        elif checkbox == "update":
                            model_str = f"path('{model}/<int:pk>/update/', {model}UpdateView.as_view(), name='{model}_update'),\n"
                            MODEL_APP_MAP[app].append(model_str)
                        elif checkbox == "delete":
                            model_str = f"path('{model}/<int:pk>/delete/', {model}DeleteView.as_view(), name='{model}_delete'),\n"
                            MODEL_APP_MAP[app].append(model_str)
        
        # Create the urls.py files

        for app in MODEL_APP_MAP:
            # Create the files
            # Each app will have its own urls.py file in a directory named after the app
            # The directory will be in the directory specified by the user
            # If the app directory does not exist, create it
            # If there already is a urls.py in the app directory, overwrite it
            if not os.path.exists(os.path.join(directory, app)):
                os.makedirs(os.path.join(directory, app))
            with open(os.path.join(directory, app, "urls.py"), "w") as f:
                f.write(HEADER)
                f.write("\n app_name='" + app + "'\n\n")
                f.write("urlpatterns = [\n")
                for model_string in MODEL_APP_MAP[app]:
                    f.write(model_string)
                f.write("]\n")


if __name__ == "__main__":
    app = Converter()
    app.mainloop()