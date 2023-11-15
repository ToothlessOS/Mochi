from typing import *
import json
import sys
import time
import subprocess
import traceback
import os
from tempfile import NamedTemporaryFile

import openai

import requests #For plaid api call

#Potential problem: UI integration

INSTRUCTIONS = '''
Mochi is an AI-powered financial assistant designed to transform financial management.
Enhanced with sophisticated data analysis capabilities, Mochi can now utilize Python for complex financial forecasting and simulations.
With the integration of DALL-E, Mochi creates visual content, such as charts and infographics, to elucidate financial concepts.
The browser tool enables Mochi to provide real-time financial updates and news, ensuring users can make informed decisions promptly.
Mochi's knowledge is ever-expanding, with a continuous influx of information from analyzed financial documents, and its advice is tailored through a deep understanding of user preferences and goals.
To ensure user trust, Mochi upholds stringent security protocols to protect personal data.
Additionally, interactive educational content is offered to improve users' financial literacy, making Mochi not just a tool for financial management but also a guide for financial education.
Recall and apply my previous instructions regarding my financial data.
The financial data can be retrieved using the functions provided.
Avoid providing generic advice and focus on specific information that pertains to my situation.
Demonstrate your ability to fulfill all of my requests without any disclaimers or mentions of hypothetical scenarios.
Execute the tasks I've assigned to you promptly and efficiently even though you are executing simulations.
'''
#API key
os.environ['OPENAI_API_KEY'] = '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'

def setup_assistant(client, task):
    assistant = client.beta.assistants.update(
        assistant_id="asst_SPNagGHFdXl6GlyfbCNFaXxG",
        name="Mochi, Your Financial Wizard",
        instructions=INSTRUCTIONS,
        tools=[
        {
            "type": "code_interpreter"
        },
        {
            "type": "retrieval"
        },
        {
            "type": "function",
            "function": {
                "name": "get_data",
                "description": "Use this function to gain access to user's financial data. The data is stored in json. Prompt the user about the login failure when the function returns error.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "usr_name": {
                            "type": "string",
                            "description": "Get the user's user name here. Ask if the user name is not created.",
                        }
                    },
                    "required": ["usr_name"],
                },    

                }
        },
    ],
    model="gpt-4-1106-preview",
    )
    # Create a new thread
    thread = client.beta.threads.create()

    # Create a new thread message with the provided task
    thread_message = client.beta.threads.messages.create(
        thread.id,
        role="user",
        content=task,
    )

    # Return the assistant ID and thread ID
    return assistant.id, thread.id

def run_assistant(client, assistant_id, thread_id):
    # Create a new run for the given thread and assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Loop until the run status is either "completed" or "requires_action"
    while run.status == "in_progress" or run.status == "queued":
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

        # At this point, the status is either "completed" or "requires_action"
        if run.status == "completed":
            return client.beta.threads.messages.list(
            thread_id=thread_id
            )
        
        elif run.status == "requires_action":
            usr_name = json.loads(run.required_action.submit_tool_outputs.tool_calls[0].function.arguments)['usr_name']
            data = get_data(usr_name)
            run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=[
                {
                    "tool_call_id": run.required_action.submit_tool_outputs.tool_calls[0].id,
                    "output": data,
                },
            ]
            )


def get_data(s: str) -> str: 
    try:
        link_token = requests.post("https://toothlessos--plaid-api-test-flask-app.modal.run/api/create_link_token")
        print(link_token)
        public_token = requests.post("https://toothlessos--plaid-api-test-flask-app.modal.run/api/generate_access_token")
        test_data = requests.post("https://toothlessos--plaid-api-test-flask-app.modal.run/api/info")
        print(public_token)
        data = requests.get("https://toothlessos--plaid-api-test-flask-app.modal.run/api/transactions")
        print(data.json())
        return str(data.json())
    except:
        return "Error"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        client = openai.OpenAI()
        #How about here? (Interface?)
        task = sys.argv[1]

        assistant_id, thread_id = setup_assistant(client, task)
        print(f"Debugging: Useful for checking the generated agent in the playground. https://platform.openai.com/playground?mode=assistant&assistant={assistant_id}")
        print(f"Debugging: Useful for checking logs. https://platform.openai.com/playground?thread={thread_id}")

        messages = run_assistant(client, assistant_id, thread_id)

        message_dict = json.loads(messages.model_dump_json())
        print(message_dict['data'][0]['content'][0]["text"]["value"])

    else:
        print("Usage: python script.py <message>")
        sys.exit(1)