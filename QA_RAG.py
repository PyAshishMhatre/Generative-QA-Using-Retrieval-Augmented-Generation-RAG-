import streamlit as st
import pandas as pd
import pinecone
import openai

#########################  Open AI Setup #################################

openai.api_key = st.secrets['openai_api']
embed_model = "text-embedding-ada-002"

def complete(prompt):
    # query text-davinci-003
    res = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        temperature=0,
        max_tokens=400,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return res['choices'][0]['text'].strip()

def retrieve(query):
    limit = 3750
    res = openai.Embedding.create(
        input=[query],
        engine=embed_model
    )

    # retrieve from Pinecone
    xq = res['data'][0]['embedding']

    # get relevant contexts
    res = index.query(xq, top_k=4, include_metadata=True)
    contexts = [x['metadata']['text'] for x in res['matches']]


    # build our prompt with the retrieved contexts included
    prompt_start = (
        "Answer the question based on the context below.\n\n"+
        "Context:\n"
    )
    prompt_end = (
        f"\n\nQuestion: {query}\nAnswer:"
    )
    # append contexts until hitting limit
    for i in range(1, len(contexts)):
        if len("\n\n---\n\n".join(contexts[:i])) >= limit:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts[:i-1]) +
                prompt_end
            )
            break
        elif i == len(contexts)-1:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts) +
                prompt_end
            )
    return prompt

##########################################################################

############### PineCone Setup ###########################################

index_name = 'openai-youtube-transcriptions'

# initialize connection to pinecone (get API key at app.pinecone.io)
pinecone.init(api_key=st.secrets['pinecone_api'],
              environment="northamerica-northeast1-gcp"  # may be different, check at app.pinecone.io
             )

index = pinecone.Index(index_name)

#########################################################################

# Define the app's interface
st.title("MyProtein Q&A")
st.header("Ask any doubts related to world's favourite protein brand")

# Take the user's input query
query = st.text_input("Enter your question?")

run = st.button('Search')
# Process the user's query and display the results
if query and run:
    query_with_contexts = retrieve(query)
    
    st.markdown('Query reformatted as -')
    
    st.write(query_with_contexts)
    
    answer = complete(query_with_contexts)
    
    st.write(f'**:green[{answer}]**')