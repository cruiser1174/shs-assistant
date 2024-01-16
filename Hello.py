# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Import packages
import streamlit as st
import json
from openai import AzureOpenAI

# import custom functions
from functions import query_data, get_sql_query_json, apply_query, format_data, describe_df, chart_data

# Load config values
with open(r'config.json') as config_file:
    config_details = json.load(config_file)

# Define deployment
deployment_name = config_details['DEPLOYMENT_NAME'] 

# Establish OpenAI Client
client = AzureOpenAI(
        api_key=config_details["OPENAI_API_KEY"],  
        api_version=config_details['OPENAI_API_VERSION'],
        azure_endpoint = config_details['OPENAI_API_BASE']
        )

# Load Siemens logo and set title for page
st.image("https://upload.wikimedia.org/wikipedia/commons/7/79/Siemens_Healthineers_logo.svg", width=300)
st.title("Siemens Healthineers Audit Assistant") 

# Check if there is message history in session, if not, establish 
# a messages list and add the opening assistant prompt
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi there! I'm here to assist you with querying and visualizing data about actions and their costs at Siemens Healthineers. Ask me anything! For example: 'What are the 5 most expensive actions to date?'"}]

# For each message, write this to the UI, this will start with just adding the system welcome prompt
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# The main page prompt flow, called if the user inputs a prompt in the chat box
if prompt := st.chat_input():
    # Add the message to the end of the history of user messages
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Write the users message to the screen for them to read
    st.chat_message("user").write(prompt)
    # Generate a query or simple answer based on the user message
    query_dt = query_data(st.session_state.messages, client)

    # If the function to generate a query called, and an sql query was returned, 
    # proceed to execute query and generate results, otherwise return simple openai response
    if query_dt.function_call:
        # extract the json query from the openai api response
        query = get_sql_query_json(query_dt)
        # apply the query to the data tables to get the final pandas dataframe
        data = apply_query(query)

        # combine the query with the initial user message to input into a following 
        # openai call to decide whether or not to plot data
        format_input = st.session_state.messages[-1]["content"] + ", " + json.loads(query)["query"]
        # make the openai call to determine whether or not to plot data
        format_dt = format_data(format_input, client)

        # Make an openai call to generate an easy to read description 
        # of the resultant dataframe based on the initial user input
        msg = describe_df(data, prompt, client)
        # add the messge to the chat history
        st.session_state.messages.append({"role": msg.role, "content": msg.content})
        # write the message to the user
        st.chat_message("assistant").write(msg.content)

        # if the format_data plot function was called, proceed to plot data, 
        # otherwise return just the data
        if format_dt.function_call:
            # retrieve the plot format data from the json output
            format_json = get_sql_query_json(format_dt)
            # Try to plot the data based on the json output
            try:
                format_to_use = json.loads(format_json)
                if data.shape[0] > 0:
                  st.write("Here is a chart describing the data:")
                  chart_data(data, format_to_use)
            # if unable to plot data, simply return data in addition to text description
            except:
                st.write("Couldn't plot data")
        
        # Log the raw data to the screen in a dataframe format if it is not empty
        if data.shape[0] > 0:
            st.write("Here is the raw data in a table that you can search through or download:", data) 
    
    # Return simple response from open ai, as it determined the data did not need to be queried        
    else:
        st.session_state.messages.append({"role": query_dt.role, "content": query_dt.content})
        st.chat_message("assistant").write(query_dt.content)