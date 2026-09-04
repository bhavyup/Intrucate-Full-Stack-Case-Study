# TASK

## Create a project using Python + Flask Framework + Mongo DB database

### Step 1: You need to create a POST endpoint with request body:
```
{    
"userlnput": "How much should I score in each subject to pass CA final?"
}
```

### Step 2: Store prompts in a MongoDB collection called prompts.
Example document:
```
{
  "_id": "Education_Prompt",
  "template": "You are an expert in education domain. Answer the following: {{userlnput}}"
}
```

### Step 3: ChatGPT API Call

- Replace {{userInput}} with request body input.
- Call OpenAI API with the final prompt.

### Step 4: Store Request/Response

Save every request/response pair into a new Mongo collection (history)

### Step 5: Return Response:
Return response received from ChatGPT API in JSON format.
```
{
"response": "......."
}
```

### Step 6: Create another POST end point and instead of sending a single string, the client will send a list of strings in one request.

- The system must fetch the prompt from NoSQL,
- Process each string independently with the ChatGPT API,
- Run the calls asynchronously (so multiple requests don't block each other),
- Return a list of AI responses in the same order.
