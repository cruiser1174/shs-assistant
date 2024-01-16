import streamlit as st
import pandasql as ps
import json
import pandas as pd

# Import raw data tables
Data=pd.read_excel('use_case_resources/OPW_AI_Input_P12_FY23.xlsx')

# Function to generate sql queries to the data tables if necessary, 
# or to return a simple answer to the most recent user question
def query_data(messages, client):
    # The system prompt, telling the model who it is, and providing information 
    # about the data tables available, and each feature within these tables. This 
    # allows the model to write queries joining the tables to best answer the user's 
    # questions
    system_prompt = """
                You are a query machine, the user will ask for information 
                about data from a table, and you will write sql queries to 
                retrieve this information. Here is some information about the data tables:

                Here is a description of the table Data: <Insert description here> 

                Please answer the user's questions assuming the data is in one dataframe. Below is the data structure of the dataframe. Separated by semi-colons, each line in this data structure tells you the name of the dataframe, column names in each dataset, a description of each column, and the data type of each column.
                Data,Action Id,Unique ID for employee,integer
                Data,Organizational Unit,Organization ,string
                Data,Level1,Sub-organization ,string
                Data,Level2,TBD,string
                Data,Level3,Location of work,string
                Data,Level4,Location of experiment,string
                Data,Level5,Department,string
                Data,Level6,Team,string
                Data,Level7,TBD,string
                Data,Level8,TBD,string
                Data,Level9,TBD,string
                Data,Level10,TBD,string
                Data,Level11,TBD,string
                Data,Level12,TBD,string
                Data,Level13,TBD,string
                Data,Level14,TBD,string
                Data,Title,Project title ,string
                Data,Action Responsible,Responsible person ,
                Data,Implementation Responsible,TBD,string
                Data,Action Type,Reason ,string
                Data,Impact Type,Time effect ,string
                Data,Lever,TBD,string
                Data,DI,TBD,integer
                Data,Last change,Date ,date
                Data,Modified by,Who modified this entry ,string
                Data,Next DI Date,TBD,date
                Data,DI 5 Date,TBD,date
                Data,Is Overdue,Is action overdue,string
                Data,Total FC,Total budgeted financial cost for action,float
                Data,Total Actual,Total actual financial cost for action,float
                Data,Actual 2023,Actual financial cost for action in 2023,float
                Data,FC 2023,Budgeted financial cost for action in 2023,float
                Data,FC 2024,Budgeted financial cost for action in 2024,float
                Data,FC 2025,Budgeted financial cost for action in 2025,float
                Data,FC 2026,Budgeted financial cost for action in 2026,float
                Data,FC 2027,Budgeted financial cost for action in 2027,float
                Data,FC 2028,Budgeted financial cost for action in 2028,float
                Data,One-Time Expenses 2023: Plan,Budgeted one time expenses for action in 2023,float
                Data,One-Time Expenses 2023: Actual,Actual one time expenses for action in 2023,float
                Data,One-Time Expenses 2024: Plan,Budgeted one time expenses for action in 2024,float
                Data,One-Time Expenses 2024: Actual,Actual one time expenses for action in 2024,float
                Data,One-Time Expenses 2025: Plan,Budgeted one time expenses for action in 2025,float
                Data,One-Time Expenses 2025: Actual,Actual one time expenses for action in 2025,float
                Data,One-Time Expenses 2026: Plan,Budgeted one time expenses for action in 2026,float
                Data,One-Time Expenses 2026: Actual,Actual one time expenses for action in 2026,float
                Data,One-Time Expenses 2027: Plan,Budgeted one time expenses for action in 2027,float
                Data,One-Time Expenses 2027: Actual,Actual one time expenses for action in 2027,float
                Data,One-Time Expenses 2028: Plan,Budgeted one time expenses for action in 2028,float
                Data,One-Time Expenses 2028: Actual,Actual one time expenses for action in 2028,float
                Data,Origin Action Currency,Currency ,string
                Data,Status,TBD,string
                Data,Consolidation Level,TBD,string
                Data,Consolidation of Allocation,TBD,string
                Data,Attachment,TBD,string
                Data,Description,TBD,string
                Data,Additional Remark,TBD,string
                Data,Explanation of impact calculation,TBD,string
                Data,Allocation Target OrgUnit,TBD,string
                Data,All. Level1,TBD,string
                Data,All. Level2,TBD,string
                Data,All. Level3,TBD,string
                Data,All. Level4,TBD,string
                Data,All. Level5,TBD,string
                Data,All. Level6,TBD,string
                Data,All. Level7,TBD,string
                Data,All. Level8,TBD,string
                Data,All. Level9,TBD,string
                Data,All. Level10,TBD,string
                Data,All. Level11,TBD,string
                Data,All. Level12,TBD,string
                Data,All. Level13,TBD,string
                Data,All. Level14,TBD,string
                Data,Remote system,TBD,string
                Data,Remote system ID,TBD,string
                Data,Depth Structure (Source),TBD,string
                Data,Depth Structure (Allocation),TBD,string
                Data,Created at,Activity creation timestamp ,date
                Data,Created by,Created by ARN ID ,string
                Data,DX Transformation,TBD,string
                Data,DX Verticalization,TBD,string
                Data,LD Franchise,TBD,string
                Data,LD Initiative,TBD,string
                Data,LD SCORE,TBD,string
                Data,LD Service 4.0,TBD,string
                Data,RSC,TBD,string
            """

    # Define messages that model concerns: the system prompt and the history of messages in 
    # the user chat. The most recent user question is appended to messages before calling the 
    # function
    messages_instruction= [{"role": "system", "content": system_prompt}] + messages

    # Define an openai function to generate sql queries to query a database of pandas dataframe tables. 
    # It is important that the queries are compatible with sqlite3. Name columns are included so that a 
    # more readable representation can be given in the final result prompt given to the user
    functions= [
            {
                "name": "data_sql_query",
                "description": "Write an sql query to the data table to retrieve the desired data fields, make sure the query is compatible with sqlite 3. When selecting id columns, also select the corresponding name column",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "an sql query to the data table to extract data based on the user's input"
                        }
                    }
                },
                "required": [
                    "query"
                ]
            }
        ]

    # Get the response of the openai call
    response = client.chat.completions.create(
        model="gpt-4", # deployment_name, # model = "deployment_name"
        messages= messages_instruction,
        functions = functions,
        function_call= "auto",
        temperature=0.05
        # max_tokens=4096
        )
    return response.choices[0].message

# a set of functions for returning sql queries and plot data
def data1_sql_query(query):
    return query
def data2_sql_query(query):
    return query
def data3_sql_query(query):
    return query
def plot_data(query):
    return query

# extract sql query in json format from openai response object
def get_sql_query_json(response_message):
    if response_message.function_call:
        return response_message.function_call.arguments
    else:
        return "There is no query to return"

# apply an sql query in a json object to pandas dataframes with names of tables in query
def apply_query(query_json): 
        return ps.sqldf(json.loads(query_json)["query"])  


# An open ai call function determining how to format the data analysis. 
# The main decision is whether to plot data or to simply return a text 
# description of the data, which would be ther better choice if for example 
# there is only one datapoint "What is the most popular skill?"
def format_data(format_input, client):
    # Define system prompt, deciding based on data input whether to plot data or not
    system_prompt = """You are a decider, to choose based on a user message, whether to plot or simply return data. 
    The user request comes in two parts seperated by comma - the verbal user message and an input sql query. 
    
    You need to choose whether to plot the data, or to return the data based on the user question
    """

    # Define message instructions: system prompt, and the user message and sql query
    messages_instruction= [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": format_input}
    ]

    # define an openai function to say that if the data should be plotted, 
    # decide which type of plot to make and return the x and y axes
    functions= [
            {
                "name": "plot_data",
                "description": "If the user requests to plot data, determine and provide the best visualization type for a streamlit chart, the x-axis variable name, the y-axis variable name given the information provided",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to_plot": {
                            "type": "string",
                            "description": "just say True"
                        },
                        "visualization_type": {
                            "type": "string",
                            "description": "Choose between scatterplot, barplot, area chart， lineplot and table in your output. If the verbal user request contains a visualization type, use it"
                        },
                         "x": {
                            "type": "string",
                            "description": "Provide the x-axis variable name. Use the SQL query as basis for variable name."                       
                        },
                        "y": {
                            "type": "string",
                            "description": "Provide the y-axis variable name. Use the SQL query as basis for variable name."                       
                        }
                    },
                "required": [
                    "plot",
                    "visualization", 
                    "x",
                    "y"
                ]
                },
            }
        ]
    
    # Get the response of the openai call
    response = client.chat.completions.create(
        model="gpt-4", # deployment_name, # model = "deployment_name"
        messages= messages_instruction,
        functions = functions,
        function_call= "auto",
        temperature=0.05
        )
    
    return response.choices[0].message

# An openai prompt function feeding in a pandas dataframe and the initial user message. 
# This generates a text description of the dataframe, tailored to the context of the 
# initial user input
def describe_df(df, user_message, client):
    # convert dataframe to a string so it can be fed into openai prompt
    df_str = df.to_string()

    # tell the api what to do - represent df in text format
    system_prompt = """
      You take in a pandas dataframe converted to string df_str, and you develop a prompt to 
      describe this dataframe in text. This description is guided by the user message 
      which is also an argument.

      Be concise in your answer. Just provide the answer, do not give too much excess detail.
      Where possible, prioritize names over ids. For example, use role_name instead of role_id to describe a role.

    """

    # define message instructions for the model: system prompt, the user message, and the dataframe in string format
    messages_instruction= [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
        {"role": "user", "content": df_str}
    ]

    # get the model response based on the messages and dataframe provided
    response = client.chat.completions.create(
        model="gpt-4", # deployment_name, # model = "deployment_name"
        messages= messages_instruction,
        temperature=0.05
        # max_tokens=4096
        )
    
    return response.choices[0].message

# function taking information about data to plot and creating relevant streamlit charts, 
# which are built upon altair
def chart_data(df, data_format_dict):
    plot_type = data_format_dict['visualization_type']
    if plot_type == 'scatterplot':
        st.scatter_chart(data=df, x=data_format_dict['x'], y=data_format_dict['y'])
    if plot_type == 'barplot':
        st.bar_chart(data=df, x=data_format_dict['x'], y=data_format_dict['y'])
    if plot_type == 'lineplot':
        st.line_chart(data=df, x=data_format_dict['x'], y=data_format_dict['y'])
    if plot_type == 'area_chart':
        st.area_chart(data=df, x=data_format_dict['x'], y=data_format_dict['y'])
