# coding: utf-8


# This file builds a hydra template from the wamdam worksheet.
# The file intends to export WaMDaM data that exist in the workbook
# into Hydra database

# The file reads WaMDaM workbook, then it maps each table in WaMDaM into Hydra web-service
# Hydra API: http://umwrg.github.io/HydraPlatform/devdocs/HydraServer/index.html#api-functions


import pandas as pd
import  os

import argparse as ap

#Python utility libraries.
from HydraLib.HydraException import HydraPluginError
from HydraLib.PluginLib import JsonConnection,\
                              create_xml_response,\
                              write_progress,\
                              write_output

#General library for working with JSON objects
import json
#Used for working with files.
import os, sys, datetime

#Load the excel file into pandas

wamdam_data = pd.read_excel('WEAP_June12.xlsm', sheetname=None)

#This returns an object, which is a dictionary of pandas 'dataframe'.
#The keys are sheet names and thrun e dataframes are the sheets themselves.
wamdam_data.keys()

# Define the WaMDaM sheets to import
type_sheet = wamdam_data['2.1_Datasets&ObjectTypes']

attr_sheet = wamdam_data['2.2_Attributes']

# More info: http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html#creating-a-client
url = "http://localhost:8080/"
conn = JsonConnection(url)
#connects by default to 'localhost:8080'
conn.login("root", "")

#You would need to check for an existing project of this name by listing all available projects. Do this using the 'get_projects' call.
projects = conn.call('get_projects', {})
proj_id = 1
proj_name = "proj_%s"
#Identify the highest project ID number.
for p in projects:
    if p.name.find('proj_') == 0:
        try:
            proj_id = int(p.name.replace('proj_', ''))
        except:
            continue
#Add 1 to the hightest proj numner
proj_id = proj_id + 1
my_new_project = conn.call('add_project', {'project': {'name': proj_name%(proj_id,)}})


my_templates = conn.call('get_template_attributes', {})


#my_templates lists available templates. A template equates to the 'object types' worksheet.
#Go through this worksheet, building a hydra template
#--------------------------------------------------------------------------------------------------------

#Steps

# Add the attribute:
# Attributes in Hydra are independent of ObjectTypes or templates (they can be shared across object types)

# Look all the unique attributes in 2.2_Attributes sheet.  Get the AttributeUnit for each attribute.

# The "AttributeUnit" in WaMDaM is equivelant to "dimension" in Hydra
# my_new_attr_list = []
# my_new_attr = conn.call('add_attribute', {'attr': {'name': ['attr'], 'dimension': ['Volume']}})


#--------------------------------------------------------------------------------------------------------

#Create a new template (dataset)
#This will fail second time around due to a unique naming restriction.
#You should call 'get_templates' first and update an existing one if one with the same name is already there.

# 2.1_Datasets&ObjectTypes sheet, look in the Datasets_table
# DatasetName which is cell A10 in 2.1_Datasets&ObjectTypes sheet

template = {'name': type_sheet.values[8][0], 'types': []}  # insert the value of the "DatasetName" from excel
# A template is equivelant to a dataset in wamdam


#--------------------------------------------------------------------------------------------------------

#Go through the excel sheet and pull out the template type definitions...
# a template type in Hydra is equivelant to an Object Type in wamdam
# resource_type in Hydra is equivelant to an ObjectTypology in wamdam
# typeAttrs (the same as Template Type Attributes) links attributes to their template

# 2.1_Datasets&ObjectTypes sheet, look in the ObjectTypes_table

# iterate to get the object types and their attributes
for i in range(10):

    #  type_sheet.values[i + 16][0]--ObjectType
    #  type_sheet.values[i + 16][1]--ObjectTypology
    mytemplatetype = {'resource_type': type_sheet.values[i + 16][1].upper(), 'name': type_sheet.values[i + 16][0], 'typeattrs': []}
    #  insert the value of the ObjectTypology from excel. also insert the value of the ObjectType from excel

    #--------------------------------------------------------------------------------------------------------
    for j in range(attr_sheet.__len__()):
        #  attr_sheet.values[j][0]--ObjectType of Attributes table
        #  attr_sheet.values[j][1]--AttributeName
        #  attr_sheet.values[j][3]--AttributeUnit
        if type_sheet.values[i + 16][0] == attr_sheet.values[j][0]:
            my_new_attr_id = conn.call('add_attribute', {'attr': {'name': attr_sheet.values[j][1], 'dimension': attr_sheet.values[j][3]}})['id']
            # connect the Template Type (ObjectType) with its Attribites
            mytemplatetype['typeattrs'].append({'type_id': i + 1, 'attr_id':  my_new_attr_id})  #type_id for the template table

    #--------------------------------------------------------------------------------------------------------


    #Add some object types to the Template Type  (resource type can be NODE, LINK, GROUP, NETWORK)
    template['types'].append(mytemplatetype)

conn.call('add_template', {'tmpl': template})



#######################################################################################################################

# Import WaMDaM Network, Scenarios, Nodes, and links



# add_network





# add_scenario



# add_nodes






# add_links






