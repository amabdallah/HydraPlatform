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

wamdam_data = pd.read_excel('WEAP_small.xlsm', sheetname=None)

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

# conn.call('add_template', {'tmpl': template})



#######################################################################################################################

# Import WaMDaM Network, Scenarios, Nodes, and links

# Follow the instructions here
# http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html

# add_network
#SK:: This should be inside a function called something like 'create network', called from the __main__ function.
network_sheet = wamdam_data['3.1_Networks&Scenarios']

network_template = {'name': network_sheet.values[8][0], 'description': network_sheet.values[8][4], 'project_id': proj_id}


#SK:: You should call get_all_attributes here, and build up a dict by their name. That way you can avoid calling get_attribute a million times.


# add_nodes
nodes_sheet = wamdam_data['3.2_Nodes']

list_node = []#SK:: Use a dictionary here instead of a list. I usually call it 'node_lookup' or something. Key = node name, value = node object. THen you can easily access the node you want later.

node_lookup = {} #SK:: Added this.
resource_attr_lookup = {} #SK:: ADDed this

# Iterate over the node instances and assign the parent Object Attributes to each node instance = ResourceAttribute
for i in range(nodes_sheet.__len__()): #SK:: WHy are you using __len__() instead of len(nodes_sheet)?
    
    if i < 9: continue #SK:: Why is this here?

    #SK:: good formatting never hurt anyone
    node = {'id':i*-1, #SK:: Use a negative ID here. THis will be replaced by a positive ID in Hydra.
            'name': nodes_sheet.values[i][1],
            'description':nodes_sheet.values[i][9],
            'x': str(nodes_sheet.values[i][7]), #SK:: Added str
            'y': str(nodes_sheet.values[i][8]),#SK:: Added str
            'types': []#SK:: You should put a dict in here with {'type_id': XXX} to tell Hydra what type of node this is. Same for links below, and the network. A netework must have a type.
           }

    list_res_attr = []
    for j in range(attr_sheet.__len__()):
        if nodes_sheet.values[i][0] == attr_sheet.values[j][0]:
            name = attr_sheet.values[j][1]
            dimension = attr_sheet.values[j][3]

            attr = conn.call('get_attribute', ({'name':name, 'dimension':dimension}))
            if attr.__len__() < 1 :
                attr = {'name': name, 'dimen': dimension}
                attr = conn.call('get_attribute', ({'attr':attr}))#SK:: WHy are you calling get_attribute twice?

            id = None #SK:: Never use such general variable names. In 10 lines time, you'll forget what 'id' refers to. Use attribute_id or similar
            if attr.__len__() < 1:
                id = conn.call('add_attribute', {'attr': {'name': attr_sheet.values[j][1], 'dimension': attr_sheet.values[j][3]}})['id']
            else:
                id = attr.id

            res_id = (len(list_res_attr) + 1) * -1 #SK:: Hydra automatically assigns IDS. When you need to refer to resource attributes from scenarios before sending them to Hydra, use NEGATIVE ID numbers.

            #SK::


            res_attr = { #SK:: Formatting
                        'ref_key': 'NODE',
                        'attr_id': id,
                        'id': res_id
                       }

            resource_attr_lookup[('NODE', res_id)] = res_attr #SK:: Now you can look up the negative resource_attr_id when processing the scenario by using the resource type (NODE, LINK) and the ID of the resource. You could use any other key you want,d epending on what data you have available to you when processing the scenario data. Doesn't have to be this key. Just an example..

            list_res_attr.append(res_attr)

    node['attributes'] = list_res_attr
    list_node.append(node)
    node_lookup[node['name']] = node #SK:: Added this
network_template['nodes'] = list_node

# add_links
# Iterate over the link instances and assign the parent Object Attributes to each link instance = Resource Attribute
link_lookup = {}#SK:: Added this. It may be necessary later. 
links_sheet = wamdam_data['3.3_Links']
list_link = []
for i in range(links_sheet.__len__()):
    if i < 9: continue
    link = {
        'id': i*-1,#SK:: Added this
        'name': links_sheet.values[i][1],
        'description':links_sheet.values[i][9]}
    node_a = node_lookup.get(links_sheet.values[i][6])
    if node_a is None:
        raise Exception("Node %s could not be found"%(links_sheet.values[i][6]))
    link['node_1_id'] = node_a['id']
    node_b = node_lookup.get(links_sheet.values[i][7])
    if node_b is None:
        raise Exception("Node %s could not be found"%(links_sheet.values[i][6]))
    link['node_2_id'] = node_b['id']

    list_link.append(link)
    link_lookup[link['name']] = link

#SK:: Should there be link attributes too?
network_template['links'] = list_link

# add_scenario and data

numerical_sheet = wamdam_data['4_NumericValues']

# add the scenario
list_scenario = []
for i in range(network_sheet.__len__()):
    if i < 18: continue #SK:: Again, what is this? Needs to be commented to explain or removed.

    if network_sheet.values[i][0] == None or network_sheet.values[i][0] == "":
        break #SK:: A log line here to explain why there's no data coming would be useful here.

    scenario = {'name': network_sheet.values[i][0], 'description': network_sheet.values[i][8], 'resourcescenarios': []}
    list_rs = []

    # Iterrate over the rows in the Numeric Values sheet [scalars dataset] and associate the value with resource attribute (node instance and attribute)
    for j in range(numerical_sheet.__len__()):
        if network_sheet.values[i ][0] == numerical_sheet.values[j][2]:
            attr_name = ''
            dimension = ''
            for k in range(attr_sheet.__len__()):
                if numerical_sheet.values[j][3] == attr_sheet.values[k][1]:
                    attr_name = attr_sheet.values[k][1]
                    dimension = attr_sheet.values[k][3]
                    # attr_unit = attr_sheet.values[k][3]
                    attr = conn.call('get_attribute', ({'name':attr_name, 'dimension':dimension})) #SK:: This is the second time this code has appeared. Put it into a common function, and remove the dupliate get_attribute.
                    if attr.__len__() < 1:
                        attr = {'name': attr_name, 'dimen': dimension}
                        attr = conn.call('get_attribute', ({'attr':attr}))

                    id = None
                    if attr.__len__() < 1:
                        id = conn.call('add_attribute', {'attr': {'name': attr_sheet.values[j][1], 'dimension': attr_sheet.values[j][3]}})['id']
                    else:
                        id = attr.id

                    rs = {'resource_attr_id': id} #SK:: the id variable here is an attribute ID, not a resource attr id. You need to get the resource_attr ID from a lookup dict, created above and populated as you're adding attributes to the nodes.

                    break

            dataset = {'type':'scalar','name': attr_name, 'unit': dimension,'dimension': dimension, # THis must match the dimension of the attribute.
                       'hidden' :'N', 'value': str(numerical_sheet.values[j][6])} 

            rs['value'] = dataset
            list_rs.append(rs)
    # associate the values, resources attributes to their scenario
    scenario['resourcescenarios'] = list_rs
    list_scenario.append(scenario)

network_template['scenarios'] = list_scenario


network = conn.call('add_network', {'net':network_template})

# Iterrate over the rows in the 4_DescriptorValuess [timeseries datasets] sheet and associate the value with its scenario, and resource attribute


# http://umwrg.github.io/HydraPlatform/devdocs/techdocs/timeseries.html
# Iterrate over the rows in the 4_TimeSeries [descriptor  dataset] sheet and associate the value with its scenario, and resource attribute


