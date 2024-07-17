from flask import Flask, render_template, request
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential


# Put the keys and endpoints here (never put your real keys in the code)
AOAI_ENDPOINT = "https://polite-ground-030dc3103.4.azurestaticapps.net/api/v1"
AOAI_KEY = "90375df3-fbd6-4030-8d43-9d93938091e5"
MODEL_NAME = "shesharp-fp-hack-gpt35-turbo-16k"

# Search endpoints, etc
SEARCH_ENDPOINT = "https://polite-ground-030dc3103.4.azurestaticapps.net/api/v1"
SEARCH_KEY = "90375df3-fbd6-4030-8d43-9d93938091e5"
AZURE_SEARCH_INDEX = "margiestraveldocs"


# Set up the client for AI Chat using the contstants and API Version
client = AzureOpenAI(
    api_key= AOAI_KEY,
    azure_endpoint= AOAI_ENDPOINT,
    api_version="2024-05-01-preview",
)

search_client = SearchClient(
    endpoint= SEARCH_ENDPOINT,
    credential=AzureKeyCredential(SEARCH_KEY),
    index_name=AZURE_SEARCH_INDEX
    )

# Set the tone of the conversation
SYSTEM_MESSAGE = "You are a helpful AI assistant that can answer questions and provide information, you are a surfer dude let us know it. You must use the provided sources."



# PUT YOUR CODE FOR GETTING YOUR AI ANSWER INSIDE THIS FUNCTION
def get_response(question, message_history=[]):
  search_results = search_client.search(search_text=question)
  search_summary = " ".join(result["content"] for result in search_results)    

  # Create a new message history if there isn't one
  if not message_history:
      messages=[
          {"role": "system", "content": SYSTEM_MESSAGE},
          {"role": "user", "content": question + "\nSources: " + search_summary},
      ]
  # Otherwise, append the user's question to the message history
  else:
      messages = message_history + [
          {"role": "user", "content": question + "\nSources: " + search_summary},
      ]

  # Get the answer using the GPT model (create 1 answer (n) and use a temperature of 0.7 to set it to be pretty creative/random)
  response = client.chat.completions.create(model=MODEL_NAME,temperature=0.7,n=1,messages=messages)
  answer = response.choices[0].message.content
  return answer, message_history + [{"role": "user", "content": question}]





############################################
######## THIS IS THE WEB APP CODE  #########
############################################

# Create a flask app
app = Flask(
  __name__,
  template_folder='templates',
  static_folder='static'
)


# This is the route for the home page (it links to the pages we'll create)
@app.get('/')
def index():
  # Return a page that links to these three pages /test-ai, /ask, /chat
  return """<a href="/test-ai">Test AI</a> <br> 
            <a href="/ask">Ask</a> <br> 
            <a href="/chat">Chat</a>"""

# Put the extra routes here

# This is the route that shows the form the user asks a question on
@app.get('/test-ai')
def test_ai():
    # Very basic form that sends a question to the /contextless-message endpoint
    return """
    <h1>Ask a question!</h1>
    <form method="post" action="/test-ai">
        <textarea name="question" placeholder="Ask a question"></textarea>
        <button type="submit">Ask</button>
    </form>
    """

# This is the route that the form sends the question to and sends back the response
@app.route("/test-ai", methods=["POST"])
def ask_response():
    # Get the question from the form
    question = request.form.get("question")

    # Return the response from the AI
    return get_response(question)


@app.get('/ask')
def ask():
    return render_template("ask.html")

@app.route('/contextless-message', methods=['GET', 'POST'])
def contextless_message():
    question = request.json['message']
    resp = get_response(question)
    return {"resp": resp[0]}

@app.get('/chat')
def chat():
    return render_template('chat.html')

@app.route("/context-message", methods=["GET", "POST"])
def context_message():
    question = request.json["message"]
    context = request.json["context"]

    resp, context = get_response(question, context)
    return {"resp": resp, "context": context}


# This is for when there is not a matching route. 
@app.errorhandler(404)
def handle_404(e):
    return '<h1>404</h1><p>File not found!</p><img src="https://httpcats.com/404.jpg" alt="cat in box" width=400>', 404


if __name__ == '__main__':
  # Run the Flask app
  app.run(host='0.0.0.0', debug=True, port=8080)