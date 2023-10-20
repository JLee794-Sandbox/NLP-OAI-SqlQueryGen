import os
import re
import logging
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion
from myPlugins.ttsPlugin.ttsPlugin import TTSPlugin
from myPlugins.sttPlugin.sttPlugin import STTPlugin
from dotenv import load_dotenv
import pyodbc
import time


# Configure logging
logging.basicConfig(filename='nlp_sql.log', level=logging.DEBUG)

# Native functions are used to call the native skills
# 1. Create speech from the textill 
# 2. Create text from user's voice through microphone
def nativeFunctions(kernel, context, plugin_class,skill_name, function_name):
    native_plugin = kernel.import_skill(plugin_class, skill_name)
    function = native_plugin[function_name]    
    result = function.invoke(context=context)
    return result["result"]

# Create speech from the text
def speak_out_response(kernel, context, content):
    context["content"] = content
    context["speech_key"] = os.getenv("speech_key")
    context["speech_region"] = os.getenv("speech_region")
    nativeFunctions(kernel, context, TTSPlugin(),"ttsPlugin","speak_out_response")

# Create text from user's voice through microphone
def recognize_from_microphone(kernel, context):
    context["speech_key"] = os.getenv("speech_key")
    context["speech_region"] = os.getenv("speech_region")
    return nativeFunctions(kernel, context, STTPlugin(),"sttPlugin","recognize_from_microphone")    

# Semantic functions are used to call the semantic skills
# 1. nlp_sql: Create SQL query from the user's query
def semanticFunctions(kernel, skills_directory, skill_name,input):
    functions = kernel.import_semantic_skill_from_directory(skills_directory, "myPlugins")
    summarizeFunction = functions[skill_name]
    
    return summarizeFunction(input)

# Function to get the result from the database
def get_result_from_database(sql_query):
    server_name = os.getenv("server_name")
    database_name = os.getenv("database_name")
    username = os.environ.get("SQLADMIN_USER")
    password = os.getenv("SQL_PASSWORD")
    
    conn_str = 'DRIVER={driver};SERVER={server_name};DATABASE={database_name};UID={username};PWD={password}'.format(driver="ODBC Driver 18 for SQL Server",server_name=server_name, database_name=database_name, username=username, password=password)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        result = cursor.fetchone()
    except:
        return "No Result Found"
    cursor.close()
    conn.close()
    return result[0]

def main():

    #Load environment variables from .env file
    load_dotenv()

    # Create a new kernel
    kernel = sk.Kernel()
    context = kernel.create_new_context()
    context['result'] = ""

    # Prompt the user to select the mode
    mode = input("Select mode:\n[1] Voice\n[2] Terminal\nEnter choice: ")    
    use_voice = mode.lower() == "1" or mode.lower() == "voice"
    context["use_voice"] = use_voice
    
    # Configure AI service used by the kernel
    deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

    # Add the AI service to the kernel
    kernel.add_text_completion_service("dv", AzureTextCompletion(deployment, endpoint, api_key))

    if use_voice:
        # Starting the Conversation
        speak_out_response(kernel,context,"....Welcome to the Kiosk Bot!! I am here to help you with your queries. I am still learning. So, please bear with me.")
    
    repeat = True
    while(repeat):
        query = ''
        if use_voice:
            speak_out_response(kernel,context,"Please ask your query through the Microphone:")
            print("Listening:")
            query = recognize_from_microphone(kernel, context)
        else:
            query = input("What would you like to see retrieved from the db?: ")

        # Taking Input from the user through the Microphone
        print("Processing........")
        print("The query is: {}".format(query))
        
        # Processing the query
        # Generating summary
        skills_directory = os.path.dirname(os.path.abspath(__file__))
        sql_query = semanticFunctions(kernel, skills_directory,"nlpToSqlPlugin",query).result.split(';')[0]
        fmt_sql_query = "SELECT {}".format(sql_query)
        
        logging.debug("Full SQL Query: {}".format(sql_query))
        # Regex pattern to extract the first SQL query
        pattern = r"(?s)^(.*?)\n\n###"

        # Find the first SQL query using the regex pattern
        match = re.search(pattern, fmt_sql_query)

        if match:
            # Extract the first SQL query
            fmt_sql_query = match.group(1).strip()
            print("The SQL query is: {}".format(fmt_sql_query))
        else:
            print("No SQL query found")
        
        # print("The SQL query is: {}".format(fmt_sql_query))

        # Use the query to call the database and get the output
        result = get_result_from_database(fmt_sql_query)
        # Speak out the result to the user
        
        if use_voice:
            # Taking Input from the user
            speak_out_response(kernel,context,"The result of your query is: {}".format(result))
            speak_out_response(kernel,context,"Do you have any other query? Say Yes to Continue")
            print("Listening:")
            user_input = recognize_from_microphone(kernel, context)
        else:
            print("The result of your query is: {}".format(result))
            user_input = input("Do you have any other query? Say Yes to Continue: ")
        if user_input == 'Yes':
            repeat = True
        else:
            repeat = False
            if use_voice:
                speak_out_response(kernel,context,"Thank you for using the Kiosk Bot. Have a nice day.")
            else:
                print("Result: %s", result)
                print("Thank you for using the Kiosk Bot. Have a nice day.")


if __name__ == "__main__":
    start = time.time()
    main()
    print("Time taken Overall(mins): ", (time.time() - start)/60)