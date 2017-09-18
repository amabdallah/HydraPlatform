# coding: utf-8


# This file builds a hydra template from the wamdam workbook.
# The file intends to export WaMDaM data that exist in the workbook
# into Hydra database

# The file reads WaMDaM workbook, then it maps each table in WaMDaM into the Hydra web-service
# Hydra API: http://umwrg.github.io/HydraPlatform/devdocs/HydraServer/index.html#api-functions

# steps
# Step 1: connect to the Hydra server
# Step 2: Import the WaMDaM workbook sheets
# Step 3: Define a project in Hydra. Add the template "dataset name", Object Types and Attribuets in Hydra
# Step 4: Import WaMDaM Network, Nodes, and links
# Step 5: Import Scenarios and Data Values of Attributes for Nodes and links



import pandas as pd
import os

import argparse as ap

# Python utility libraries.
from HydraLib.HydraException import HydraPluginError
from HydraLib.PluginLib import JsonConnection, \
    create_xml_response, \
    write_progress, \
    write_output

# General library for working with JSON objects
import json
# Used for working with files.
import os, sys, datetime

import logging

log = logging.getLogger(__name__)

# STEP 1: connect to the Hydra server
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# Connect to the Hydra server on the local machine
# More info: http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html#creating-a-client
url = "http://localhost:8080/"
conn = JsonConnection(url)
# connects by default to 'localhost:8080'
conn.login("root", "")

# STEP 2: Import the WaMDaM workbook sheets
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


# Load the excel file into pandas
wamdam_data = pd.read_excel('WEAP_June12.xlsm', sheetname=None)

# This returns an object, which is a dictionary of pandas 'dataframe'.
# The keys are sheet names and the dataframes are the sheets themselves.
wamdam_data.keys()

# Define the WaMDaM sheets to import
# Import the Datasets and Object Types
type_sheet = wamdam_data['2.1_Datasets&ObjectTypes']

# Import the attributes
attr_sheet = wamdam_data['2.2_Attributes']

# STEP 3: Define a project in Hydra. Add the template "dataset name", Object Types and Attributes in Hydra
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


# Use the 'get_projects' call to check for an existing project of this name by listing all available projects.
# The project concept does not exist in WaMDaM but it is needed in Hydra. We define it here
projects = conn.call('get_projects', {})
proj_id = 1
proj_name = "WaMDaM_%s"
# Identify the highest project ID number.
for p in projects:
    if p.name.find('WaMDaM_') == 0:
        try:
            proj_id = int(p.name.replace('WaMDaM_', ''))
        except:
            continue
# Add 1 to the hightest proj numner
log.info(proj_id)
log.info(proj_name)
proj_id = proj_id + 1
## Load the Project name to the Hydra db
my_new_project = conn.call('add_project', {'project': {'name': proj_name % proj_id}})

# Add the attribute:
# Attributes in Hydra are independent of ObjectTypes or templates types (they can be shared across object types)

# Look all the unique attributes in 2.2_Attributes sheet.  Get the AttributeUnit for each attribute.

# The "AttributeUnit" in WaMDaM is equivalent to "dimension" in Hydra
# my_new_attr_list = []
# my_new_attr = conn.call('add_attribute', {'attr': {'name': ['attr'], 'dimension': ['Volume']}})


all_attributes = conn.call('get_all_attributes', ({}))
all_attr_dict = {}
for a in all_attributes:
    all_attr_dict[a.name] = {'id': a.id, 'dimension': a.dimen}

# -------------------------

# Create a new template (dataset)
# This will fail second time around due to a unique naming restriction.
# You should call 'get_templates' first and update an existing one if one with the same name is already there.

# 2.1_Datasets&ObjectTypes sheet, look in the Datasets_table
# DatasetName which is cell A10 in 2.1_Datasets&ObjectTypes sheet

template = {'name': type_sheet.values[8][0], 'types': []}  # insert the value of the "DatasetName" from excel
# A template is equivalent to a dataset in wamdam

# my_templates lists available templates. A template equates to the 'Dataset' in WaMDaM.
# Go through this worksheet, building a hydra template
my_templates = conn.call('get_template_attributes', {})

# -----------------------------

# Go through the excel sheet and pull out the template type definitions...
# a template type in Hydra is equivalent to an Object Type in WaMDaM
# resource_type in Hydra is equivalent to an ObjectTypology in WaMDaM
# typeAttrs (the same as Template Type Attributes) links attributes to their template

# 2.1_Datasets&ObjectTypes sheet, look in the ObjectTypes_table

# iterate to get the object types and their attributes
for i in range(10):

    #  type_sheet.values[i + 16][0]--ObjectType
    #  type_sheet.values[i + 16][1]--ObjectTypology
    mytemplatetype = {'resource_type': type_sheet.values[i + 16][1].upper(), 'name': type_sheet.values[i + 16][0],
                      'typeattrs': []}
    #  insert the value of the ObjectTypology from excel. also insert the value of the ObjectType from excel

    # -------------------------------------
    for j in range(len(attr_sheet)):
        #  attr_sheet.values[j][0]--ObjectType of Attributes table
        #  attr_sheet.values[j][1]--AttributeName
        #  attr_sheet.values[j][3]--AttributeUnit
        if type_sheet.values[i + 16][0] == attr_sheet.values[j][0]:
            attr_name = attr_sheet.values[j][1]
            attr_dimension = attr_sheet.values[j][3]
            if all_attr_dict.get(attr_name) is None:
                attr_id = conn.call('add_attribute',
                                    {'attr': {'name': attr_sheet.values[j][1], 'dimen': attr_sheet.values[j][3]}})[
                    'id']
            else:
                attr_id = all_attr_dict[attr_name]['id']
            # connect the Template Type (ObjectType) with its Attributes
            mytemplatetype['typeattrs'].append({'type_id': i + 1, 'attr_id': attr_id})  # type_id for the template table

    # --------------------------------------------


    # Add some object types to the Template Type  (resource type can be NODE, LINK, GROUP, NETWORK)
    template['types'].append(mytemplatetype)

## Load the Template name and types to the Hydra db

tempDB = conn.call('get_templates', {})
flag_exist_template = False
for template_item in tempDB:
    if template_item['name'] == template['name']:
        flag_exist_template = True
        break
if not flag_exist_template:
    conn.call('add_template', {'tmpl': template})


# Build up a dict by attribute names to call them later.

for j in range(len(attr_sheet)):
    if j < 9: continue  # Avoid headers before line 9 in the nodes sheet
    name = attr_sheet.values[j][1]
    dimension = attr_sheet.values[j][3]

## Load the Attributes to the Hydra db
    if all_attr_dict.get(name) is None:
        id = \
        conn.call('add_attribute', {'attr': {'name': attr_sheet.values[j][1], 'dimen': attr_sheet.values[j][3]}})[
            'id']
        all_attr_dict[name] = {'id': id, 'dimension': dimension}

# STEP 4: Import WaMDaM Network, Nodes, and links
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


# Follow the instructions here
# http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html

# add_network
network_sheet = wamdam_data['3.1_Networks&Scenarios']

network_template = {'name': network_sheet.values[8][0], 'description': network_sheet.values[8][4],
                    'project_id': proj_id}


# add_nodes
nodes_sheet = wamdam_data['3.2_Nodes']

list_node = []

node_lookup = {}

resource_attr_lookup = {}

type_id = None
# Iterate over the node instances and assign the parent Object Attributes to each node instance = ResourceAttribute (as in Hydra)
for i in range(len(nodes_sheet)):
    if i < 9: continue  # Avoid headers before line 9 in the nodes sheet

    # Look up the type_id in Hydra for each type
    for templateType in template['types']:
        if nodes_sheet.values[i][1] == templateType['name']:
            type_id = template['typeattrs'][0]['type_id']
            break

    if type_id is None:
        raise Exception("Unable to find a type in the template for %s" % nodes_sheet.values[i][1])

    flag = False
    for node_item in list_node:
        if node_item['name'] == nodes_sheet.values[i][1]:
            flag = True
    if flag: continue

    node = {'id': i * -1,
            'name': nodes_sheet.values[i][1],
            'description': nodes_sheet.values[i][9],
            'x': str(nodes_sheet.values[i][7]),
            'y': str(nodes_sheet.values[i][8]),
            'types': [{'type_id': type_id}]
            }

    list_res_attr = []
    for j in range(len(attr_sheet)):
        if nodes_sheet.values[i][0] == attr_sheet.values[j][0]:
            name = attr_sheet.values[j][1]
            dimension = attr_sheet.values[j][3]

            res_id = (len(list_res_attr) + 1) * -1
            # When you need to refer to resource attributes from scenarios before sending them to Hydra, use NEGATIVE ID numbers.

            res_attr = {
                'ref_key': 'NODE',
                'attr_id': all_attr_dict[name]['id'],
                'id': res_id
            }

            resource_attr_lookup[('NODE', res_id)] = res_attr

            list_res_attr.append(res_attr)

    node['attributes'] = list_res_attr
    list_node.append(node)
    node_lookup[node['name']] = node
network_template['nodes'] = list_node

link_lookup = {}
links_sheet = wamdam_data['3.3_Links']
list_link = []
for i in range(len(links_sheet)):
    if i < 9: continue  # Avoid headers before line 9 in the links sheet
    link = {
        'id': i * -1,
        'name': links_sheet.values[i][1],
        'description': links_sheet.values[i][9]}
    node_a = node_lookup.get(links_sheet.values[i][6])
    if node_a is None:
        raise Exception("Node %s could not be found" % (links_sheet.values[i][6]))
    link['node_1_id'] = node_a['id']
    node_b = node_lookup.get(links_sheet.values[i][7])
    if node_b is None:
        raise Exception("Node %s could not be found" % (links_sheet.values[i][6]))
    link['node_2_id'] = node_b['id']

    list_link.append(link)
    link_lookup[link['name']] = link

network_template['links'] = list_link

## Load the Network, its nodes, and links to the Hydra db

# http://umwrg.github.io/HydraPlatform/tutorials/plug-in/tutorial_json.html#scenarios-and-data

network = conn.call('add_network', {'net':network_template})


# STEP 5: Import Scenarios and Data Values of Attributes for Nodes and links
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# 5.1 add the scenario
list_scenario = []
for i in range(len(network_sheet)):
    if i < 9: continue  # Avoid headers before line 9 in the 4_NumericValues sheet

    if network_sheet.values[i][0] == None or network_sheet.values[i][0] == "":
        # If there is no value in network sheet, stop loop.
        break

    scenario = {'name': network_sheet.values[i][0], 'description': network_sheet.values[i][8], 'resourcescenarios': []}
    list_rs = []

    # Working with Datasets in Hydra which are equivalent to DataValues tables in WaMDaM
    # http://umwrg.github.io/HydraPlatform/tutorials/webservice/datasets.html?highlight=datasets

    # **************************************************
    # 5.2 Numeric Values

    numerical_sheet = wamdam_data['4_NumericValues']

    # Iterate over the rows in the Numeric Values sheet [scalars dataset] and associate the value with resource attribute (node instance and attribute)
    for j in range(8, len(numerical_sheet)):  # //8: reall value row in sheet
        if network_sheet.values[i][0] == numerical_sheet.values[j][2]:
            attr_name = numerical_sheet.values[j][3]
            dimension = all_attr_dict[attr_name]['dimension']
            rs = {'resource_attr_id': all_attr_dict[numerical_sheet.values[j][3]]['id']}

            dataset = {'type': 'scalar', 'name': attr_name, 'unit': dimension, 'dimension': dimension,
                       'hidden': 'N', 'value': str(numerical_sheet.values[j][6])}
            # The provided dimension here must match the attribute as defined earlier.

            rs['value'] = dataset
            list_rs.append(rs)
    # associate the values, resources attributes to their scenario
    scenario['resourcescenarios'] = list_rs
    list_scenario.append(scenario)

network_template['scenarios'] = list_scenario

# network = conn.call('add_network', {'net':network_template})

# ****************************************************
# 5.3 Descriptor Values (4_DescriptorValues )
# Iterate over the rows in the 4_DescriptorValuess sheet and associate the value with its scenario, and resource attribute
Descriptor_sheet = wamdam_data['4_DescriptorValues']

# add the scenario
list_scenario = []
for i in range(len(network_sheet)):
    if i < 9: continue  # Avoid headers before line 9 in the 4_DescriptorValues sheet

    if network_sheet.values[i][0] == None or network_sheet.values[i][0] == "":
        # If there is no value in network sheet, stop loop.
        break

    scenario = {'name': network_sheet.values[i][0], 'description': network_sheet.values[i][8], 'resourcescenarios': []}
    list_rs = []

    # Iterate over the rows in the Numeric Values sheet [scalars dataset] and associate the value with resource attribute (node instance and attribute)
    for j in range(8, len(Descriptor_sheet)):
        if network_sheet.values[i][0] == Descriptor_sheet.values[j][2]:
            attr_name = Descriptor_sheet.values[j][3]
            dimension = all_attr_dict[Descriptor_sheet.values[j][3]]['dimension']

            rs = {'resource_attr_id': all_attr_dict[Descriptor_sheet.values[j][3]]['id']}

            dataset = {'type': 'descriptor', 'name': attr_name, 'unit': dimension, 'dimension': dimension,
                       'hidden': 'N', 'value': Descriptor_sheet.values[j][6]}
            # The provided dimension here must match the attribute as defined earlier.

            rs['value'] = dataset
            list_rs.append(rs)
    # associate the values, resources attributes to their scenario
    scenario['resourcescenarios'] = list_rs
    list_scenario.append(scenario)

network_template['scenarios'] = list_scenario

# ******************************************************************************************************************

# 5.4 Descriptor Values (4_DualValues) (does the same like 2.1 but for another sheet)
# Iterate over the rows in the 4_DualValues sheet and associate the value with its scenario, and resource attribute
#  (dual Value here is like DescriptorValue)
Descriptor_sheet = wamdam_data['4_DualValues']

# add the scenario
list_scenario = []
for i in range(len(network_sheet)):
    if i < 9: continue  # Avoid headers before line 9 in the 4_DualValues sheet

    if network_sheet.values[i][0] == None or network_sheet.values[i][0] == "":
        # If there is no value in network sheet, stop loop.
        break

    scenario = {'name': network_sheet.values[i][0], 'description': network_sheet.values[i][8], 'resourcescenarios': []}
    list_rs = []

    # Iterate over the rows in the Numeric Values sheet [scalars dataset] and associate the value with resource attribute
    # (node instance and attribute)
    for j in range(8, len(Descriptor_sheet)):
        if network_sheet.values[i][0] == Descriptor_sheet.values[j][2]:
            attr_name = Descriptor_sheet.values[j][3]
            dimension = all_attr_dict[Descriptor_sheet.values[j][3]]['dimension']
            rs = {'resource_attr_id': all_attr_dict[Descriptor_sheet.values[j][3]]['id']}

            dataset = {'type': 'descriptor', 'name': attr_name, 'unit': dimension, 'dimension': dimension,
                       'hidden': 'N', 'value': Descriptor_sheet.values[j][6]}
            # The provided dimension here must match the attribute as defined earlier.

            rs['value'] = dataset
            list_rs.append(rs)
    # associate the values, resources attributes to their scenario
    scenario['resourcescenarios'] = list_rs
    list_scenario.append(scenario)

network_template['scenarios'] = list_scenario

# ********************************************************
# 5.5 Time Series
# Iterate over the rows in the 4_TimeSeriesValues sheet and associate the value with its scenario, and resource attribute
# Reference for time series in Hydra: follow this logic
# http://umwrg.github.io/HydraPlatform/devdocs/techdocs/timeseries.html#an-example-in-python

TimeSeriesValues_sheet = wamdam_data['4_TimeSeriesValues']

# add the scenario
list_scenario = []
for i in range(len(network_sheet)):
    if i < 9: continue  # Avoid headers before line 9 in the 4_TimeSeriesValues sheet
    if network_sheet.values[i][0] == None or network_sheet.values[i][0] == "":
        # If there is no value in network sheet, stop loop.
        break

    scenario = {'name': network_sheet.values[i][0], 'description': network_sheet.values[i][8], 'resourcescenarios': []}
    list_rs = []

    # Iterate over the rows in the TimeSeriesValues sheet [scalars dataset] and associate the value with resource attribute
    # (node instance and attribute)
    timeseries_list = {}
    for j in range(8, len(TimeSeriesValues_sheet)):  # //8: reall value row in sheet
        if network_sheet.values[i][0] == TimeSeriesValues_sheet.values[j][2]:
            attr_name = TimeSeriesValues_sheet.values[j][3]
            if attr_name in timeseries_list.keys():
                timeseries_list[attr_name].append(
                    (TimeSeriesValues_sheet.values[j][4], TimeSeriesValues_sheet.values[j][5]))
            else:
                values = []
                values.append((TimeSeriesValues_sheet.values[j][4], TimeSeriesValues_sheet.values[j][5]))
                timeseries_list[attr_name] = values

    for key in timeseries_list.keys():
        timeseries = {"Header": {}, "0": {}}
        for time, value in timeseries_list[key]:
            t = str(time)
            timeseries["0"][t] = value

        timeseries['ts_values'] = json.dumps(timeseries)

        attr_name = key
        dimension = all_attr_dict[attr_name]['dimension']
        rs = {'resource_attr_id': all_attr_dict[attr_name]['id']}

        dataset = {'type': 'timeseries', 'name': attr_name, 'unit': dimension, 'dimension': dimension,
                   'hidden': 'N', 'value': timeseries}
        # The provided dimension here must match the attribute as defined earlier.

    rs['value'] = dataset
    list_rs.append(rs)
    # associate the values, resources attributes to their scenario
    scenario['resourcescenarios'] = list_rs
    list_scenario.append(scenario)

network_template['scenarios'] = list_scenario



# ********************************************************
# 5.6 Arrays
# Iterate over the rows in the MultiColumns Series sheet and associate the value with its scenario, and resource attribute

# Reference for arrays in Hydra (not clear to me yet, an example would help)
#	http://umwrg.github.io/HydraPlatform/tutorials/webservice/datasets.html?highlight=arrays#array-format


# Will add the array values for each attribute
# Here Column D in excel starting row 19 has the attribute name that for the whole array (its just like the attribute for the descriptor)
# Columns G, H,....L, etc starting row 4 in excel have the names of the Array "items" or sub-attributes
# so each value belongs to an Attribute (array name) and a sub-attribute (array item) under an ObjectType and Instance name

multiAttr_sheet = wamdam_data['4_MultiAttributeSeries']
#get attribut field count
con_attributes = {}
for i in range(3, 12):
    if multiAttr_sheet.values[i][5] == None or multiAttr_sheet.values[i][5] == "":
        # If there is no value in network sheet, stop loop.
        break
    con_attributes[multiAttr_sheet.values[i][5]] = 0
    for j in range(6, 11):

        if str(multiAttr_sheet.values[i][j]) == 'nan' or multiAttr_sheet.values[i][j] == "":
        # If there is no value in network sheet, stop loop.
            break
        con_attributes[multiAttr_sheet.values[i][5]] = con_attributes[multiAttr_sheet.values[i][5]] + 1


# add the scenario
list_scenario = []
for i in range(18, len(network_sheet)):
    # if i < 9: continue  # Avoid headers before line 9 in the 4_DescriptorValues sheet

    if network_sheet.values[i][0] == None or str(network_sheet.values[i][0]) == "nan":
        # If there is no value in network sheet, stop loop.
        break

    scenario = {'name': network_sheet.values[i][0], 'description': network_sheet.values[i][8], 'resourcescenarios': []}
    list_rs = []

    # Iterate over the rows in the Numeric Values sheet [scalars dataset] and associate the value with resource attribute (node instance and attribute)
    name = '' #multiarray instance name
    array_value = []
    for j in range(17, len(multiAttr_sheet)):
        if network_sheet.values[i][0] == multiAttr_sheet.values[j][2]:
            if name != multiAttr_sheet.values[j][1]:
                if len(array_value) > 0:
                    dimension = all_attr_dict[multiAttr_sheet.values[j][3]]['dimension']
                    rs = {'resource_attr_id': all_attr_dict[multiAttr_sheet.values[j][3]]['id']}

                    dataset = {'type': 'array', 'name': name, 'unit': dimension, 'dimension': dimension, 'hidden': 'N'}
                    dataset['value'] = {'arr_data': array_value}
                    print dataset
                    dataset['metadata'] = [
                        { 'name' : 'ObjectType', 'value' : multiAttr_sheet.values[j-1][0]},
                        { 'name' : 'ScenarioName', 'value' : multiAttr_sheet.values[j-1][2]},
                        { 'name' : 'SourceName', 'value' : multiAttr_sheet.values[j-1][4]},
                        { 'name' : 'MethodName', 'value' : multiAttr_sheet.values[j-1][5]}
                    ]

                    rs['value'] = dataset
                    list_rs.append(rs)

                name = multiAttr_sheet.values[j][1] # new instance name of multiarray
                array_value = []
                for kk in range(1, con_attributes[multiAttr_sheet.values[j][3]] + 1):
                    templist = []
                    templist.append(multiAttr_sheet.values[j][5 + kk])
                    array_value.append(templist)


            else:
                for kk in range(1, con_attributes[multiAttr_sheet.values[j][3]] + 1):
                    array_value[kk - 1].append(multiAttr_sheet.values[j][5 + kk])

            # The provided dimension here must match the attribute as defined earlier.

            # rs['value'] = dataset
            # list_rs.append(rs)
    # associate the values, resources attributes to their scenario
    scenario['resourcescenarios'] = list_rs
    list_scenario.append(scenario)

network_template['scenarios'] = list_scenario
