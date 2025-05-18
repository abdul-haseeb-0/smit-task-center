# app to build an agent that can perform CRUD operations on a mongo dfrom pymongo.mongo_client import MongoClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChattCompletionsModel, function_tool
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Database Collection Name
DATABASE_NAME = "smit-task"  # Replace with your actual database name
COLLECTION_NAME = "agent-crud"

# Create a new client and connect to the server
mongodb_client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))
db = mongodb_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Send a ping to confirm a successful connection
try:
    mongodb_client.admin.command('ping')
    print("You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Create Employee data on mongo db
@function_tool
def create_employee(id: int,name: str, age: int, department: str, salary: int):
    """
    Agent Playbook: Employee Creation Task
    Task Name: CreateNewEmployeeRecord
    Purpose: To securely add a new employee's essential details to our central employee database (MongoDB). This ensures our employee records are up-to-date and accurate.
    
    Input Parameters (Required for this Task):
        id (Integer): A unique identification number for the employee.
            Constraint: Must be a positive whole number (e.g., 1001, 2050).
        name (String): The full name of the employee.
            Constraint: Cannot be empty (e.g., "Alice Smith").
        age (Integer): The employee's age in years.
            Constraint: Must be between 18 and 100 (inclusive).
        department (String): The department the employee works in.
            Constraint: Cannot be empty (e.g., "Engineering", "Sales").
        salary (Integer): The employee's annual salary.
            Constraint: Must be a positive whole number (e.g., 60000, 75000).
            
    Validate Inputs:
        Check id: Is it a positive integer?
        Check name: Is it a non-empty string?
        Check age: Is it an integer between 18 and 100?
        Check department: Is it a non-empty string?
        Check salary: Is it a positive integer?
    If any input fails validation: Immediately stop this task and proceed to "Error Handling: Invalid Input."

    Database Lookup (Duplicate Check):
    Query: Search the agent-crud collection to see if any document already exists with _id equal to the provided id.
    If id already exists: Immediately stop this task and proceed to "Error Handling: Duplicate ID."

    (Note: The _id field is crucial for MongoDB to recognize it as the primary key.)
    
    Insert: Use the insert_one() method on the agent-crud collection to add this document.
    If insertion fails for any other reason (e.g., connection error, permission issue): Immediately stop this task and proceed to "Error Handling: Database Operation Failure."
    
    Success Confirmation:
    Return Message: "Employee [employee's name] has been added successfully!"

    Error Handling (What to Do if Something Goes Wrong):
    Error Type: Invalid Input
    Identify specific issue: Which input parameter was invalid (e.g., empty name, age out of range, negative salary)?
    Return specific humanized message:
        If id is invalid: "Oops, the employee ID must be a positive number. Please check it."
        If name is empty: "Hmm, it looks like the name is empty. Please provide a valid name for the employee."
        If age is invalid: "Sorry, the age must be between 18 and 100. Please provide a valid age."
        If department is empty: "The department cannot be empty. Please specify a department for the employee."
        If salary is invalid: "Whoops, the salary must be a positive number. Please provide a valid salary."
        Error Type: Duplicate ID

    Return Message: "Oops, that ID is already in use. Please try a different one."
    Error Type: Database Operation Failure

    Capture error details: Log the exact exception message (e.g., connection issues, permission problems).
    Return Message: "I encountered an issue while trying to save the employee data. It might be a temporary database problem or a permission error. Please try again or contact support if the issue persists."
"""
    try:
        mongodb_client.collection.insert_one({"id": id, "name": name, "age": age, "department": department, "salary": salary})
        return "Employee created successfully"
    except Exception as e:
        return f"Error creating employee: {e}"



# Read Employee data on mongo db by name
@function_tool
def read_employee_by_name(name: str):
    """
    Agent Playbook: Employee Retrieval Task
    Task Name: RetrieveEmployeeRecord
    Purpose: To find and retrieve the details of an employee from our central employee database (MongoDB) based on their name. This allows us to access and display employee information.

    Input Parameters (Required for this Task):
        name (String): The full name of the employee you are looking for.
        Constraint: Cannot be empty (e.g., "Alice Smith").
    
    Action Steps (What to Do):
    Validate Input:
    Check name: Is it a non-empty string?
    If the name is empty: Immediately stop this task and proceed to "Error Handling: Invalid Input."
    
    Database Lookup:
    Connect to MongoDB: Use the pre-configured mongodb_client to access the agent-crud collection.
    Query: Search the agent-crud collection for a document where the name field exactly matches the provided name. Use the find_one() method.
    
    Process Query Result:
    If an employee record is found:
    Return the entire employee document as it is retrieved from MongoDB (e.g., {"_id": 1001, "name": "Alice Smith", "age": 30, "department": "Engineering", "salary": 60000}).
    If no employee record is found with the given name:
    Return a specific "Not Found" message: "No employee found with the name '[provided employee name]'."
    
    Error Handling (Database Operation Failure):
    If the database operation fails for any reason (e.g., connection error, permission issue):
    Capture error details: Log the exact exception message.
    Return a general error message: "I encountered an issue while trying to retrieve the employee data. Please try again or contact support if the issue persists."
    Log Details (for system administrators): Record the full error traceback in our internal logging system for diagnostics.
    Error Handling (What to Do if Something Goes Wrong with Input):

    Error Type: Invalid Input

    Identify specific issue: The name input is empty.
    Return specific humanized message: "Please provide a valid name to search for an employee."
    """
    try:
        employee = mongodb_client.collection.find_one({"name": name})
        return employee
    except Exception as e:
        return f"Error reading employee: {e}"

# Read Employee data on mongo db by id
@function_tool
def read_employee_by_id(id: int):
    """
    Agent Playbook: Employee Retrieval by ID Task
    Task Name: RetrieveEmployeeRecordById
    Purpose: To find and retrieve the details of an employee from our central employee database (MongoDB) based on their unique ID. This allows us to access specific employee information using their identifier.

    Input Parameters (Required for this Task):
        id (Integer): The unique identification number of the employee you are looking for.
            Constraint: Must be a positive whole number (e.g., 1001, 2050).

    Validate Input:
        Check id: Is it a positive integer?
    If the id is not a positive integer: Immediately stop this task and proceed to "Error Handling: Invalid Input."

    Database Lookup:
        Query: Search the agent-crud collection for a document where the _id field exactly matches the provided id. Use the find_one() method.

    Process Query Result:
        If an employee record is found:
            Return the entire employee document as it is retrieved from MongoDB (e.g., {"_id": 1001, "name": "Alice Smith", "age": 30, "department": "Engineering", "salary": 60000}).
        If no employee record is found with the given id:
            Return a specific "Not Found" message: "No employee found with the ID '[provided employee ID]'."

    Error Handling (What to Do if Something Goes Wrong):
    Error Type: Invalid Input
        Identify specific issue: The id input is not a positive integer.
        Return specific humanized message: "Please provide a valid positive integer for the employee ID."
    Error Type: Database Operation Failure
        Capture error details: Log the exact exception message (e.g., connection issues, permission problems).
        Return Message: "I encountered an issue while trying to retrieve the employee data by ID. Please try again or contact support if the issue persists."
    """
    try:
        employee = mongodb_client.collection.find_one({"id": id})
        return employee
    except Exception as e:
        return f"Error reading employee: {e}"

# Update Employee data on mongo db by id
@function_tool
def update_employee(id: int, name: str, age: int, department: str, salary: int):
    """
    Agent Playbook: Employee Update Task
    Task Name: UpdateEmployeeRecord
    Purpose: To modify the details of an existing employee in our central employee database (MongoDB) based on their unique ID. This allows us to keep employee information current.

    Input Parameters (Required for this Task):
        id (Integer): The unique identification number of the employee to update.
            Constraint: Must be a positive whole number (e.g., 1001, 2050).
        name (String): The updated full name of the employee.
            Constraint: Cannot be empty (e.g., "Alice Smith").
        age (Integer): The updated employee's age in years.
            Constraint: Must be between 18 and 100 (inclusive).
        department (String): The updated department the employee works in.
            Constraint: Cannot be empty (e.g., "Engineering", "Sales").
        salary (Integer): The updated employee's annual salary.
            Constraint: Must be a positive whole number (e.g., 65000, 80000).

    Validate Inputs:
        Check id: Is it a positive integer?
        Check name: Is it a non-empty string?
        Check age: Is it an integer between 18 and 100?
        Check department: Is it a non-empty string?
        Check salary: Is it a positive integer?
    If any input fails validation: Immediately stop this task and proceed to "Error Handling: Invalid Input."

    Database Update:
        Query: Search the agent-crud collection for a document where the _id field exactly matches the provided id.
        Action: If a matching document is found, update the "name", "age", "department", and "salary" fields with the provided new values using the `$set` operator.
        If no employee record is found with the given id:
            Return a specific "Not Found" message: "No employee found with the ID '[provided employee ID]'. Unable to update."

    Success Confirmation:
        If the update operation is successful:
            Return Message: "Employee with ID '[provided employee ID]' has been updated successfully!"

    Error Handling (What to Do if Something Goes Wrong):
    Error Type: Invalid Input
        Identify specific issue: Which input parameter was invalid (e.g., empty name, age out of range, negative salary, invalid ID)?
        Return specific humanized message:
            If id is invalid: "Oops, the employee ID must be a positive number. Please check it."
            If name is empty: "Hmm, it looks like the name is empty. Please provide a valid name for the employee."
            If age is invalid: "Sorry, the age must be between 18 and 100. Please provide a valid age."
            If department is empty: "The department cannot be empty. Please specify a department for the employee."
            If salary is invalid: "Whoops, the salary must be a positive number. Please provide a valid salary."
    Error Type: Employee Not Found
        Return Message: "No employee found with the ID '[provided employee ID]'. Unable to update."
    Error Type: Database Operation Failure
        Capture error details: Log the exact exception message (e.g., connection issues, permission problems).
        Return Message: "I encountered an issue while trying to update the employee data. Please try again or contact support if the issue persists."
    """
    try:
        mongodb_client.collection.update_one({"id": id}, {"$set": {"name": name, "age": age, "department": department, "salary": salary}})
        return "Employee updated successfully"
    except Exception as e:
        return f"Error updating employee: {e}"

# Delete Employee data on mongo db by id
@function_tool
def delete_employee(id: int):
    """
    Agent Playbook: Employee Deletion Task
    Task Name: DeleteEmployeeRecord
    Purpose: To permanently remove an employee record from our central employee database (MongoDB) based on their unique ID. Use this function with caution.

    Input Parameters (Required for this Task):
        id (Integer): The unique identification number of the employee to delete.
            Constraint: Must be a positive whole number (e.g., 1001, 2050).

    Validate Input:
        Check id: Is it a positive integer?
    If the id is not a positive integer: Immediately stop this task and proceed to "Error Handling: Invalid Input."

    Database Deletion:
        Query: Search the agent-crud collection for a document where the _id field exactly matches the provided id.
        Action: If a matching document is found, delete that single document using the `delete_one()` method.
        Note: If no employee record is found with the given id, the operation will complete without error, but no deletion will occur.

    Success Confirmation:
        If the deletion operation is successful (a document with the given ID was found and deleted):
            Return Message: "Employee with ID '[provided employee ID]' has been deleted successfully!"
        If no employee record was found with the given id:
            Return Message: "No employee found with the ID '[provided employee ID]'. No action taken."

    Error Handling (What to Do if Something Goes Wrong):
    Error Type: Invalid Input
        Identify specific issue: The id input is not a positive integer.
        Return specific humanized message: "Please provide a valid positive integer for the employee ID to delete."
    Error Type: Database Operation Failure
        Capture error details: Log the exact exception message (e.g., connection issues, permission problems).
        Return Message: "I encountered an issue while trying to delete the employee data. Please try again or contact support if the issue persists."
    """
    try:
        mongodb_client.collection.delete_one({"id": id})
        return "Employee deleted successfully"
    except Exception as e:
        return f"Error deleting employee: {e}"



gemini_api_key = os.getenv("GEMINI_API_KEY")
client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

agent = Agent(
    name="MongoDB Data Manager",
    instructions="""
    You are the MongoDB EasyData Agent, a friendly and reliable assistant for managing a MongoDB database.
    Your role is to perform CRUD operations: create new data entries, retrieve or read existing data, update data as needed,
    and delete data when requested. Communicate in a clear, conversational, and humanized tone, as if explaining to a colleague
    or friend. Provide step-by-step feedback for each operation, including success messages (e.g., 'I’ve added that data for you!')
    or helpful, easy-to-understand error messages (e.g., 'Oops, looks like that ID doesn’t exist—want to try another?'). Ensure
    all actions are secure, follow MongoDB best practices, and respect database permissions. If a request is unclear, ask for
    clarification in a polite, engaging way to ensure the users needs are met.
    """,
    model=OpenAIChattCompletionsModel(model="gemini-1.5-flash", openai_client=client),
    tools=[
        create_employee,
        read_employee_by_name,
        read_employee_by_id,
        update_employee,
        delete_employee
    ]
)


async def main():
    query = input("Enter a query: ")
    result = Runner.run_streamed(agent, input=query)
    async for event in result.stream_events():
        # You need to define or import ResponseTextDeltaEvent
        if event.type == "raw_response_event" and hasattr(event.data, "delta"):
            print(event.data.delta, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())