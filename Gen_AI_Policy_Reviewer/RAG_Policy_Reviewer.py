from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import streamlit as st
import tempfile

# Load environment variables
load_dotenv()

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_dir, "ACL_Policy_BANK_XYZ.pdf")

def load_and_chunk_pdf(pdf_path):
    """Load and chunk the PDF document"""
    # Load the PDF file
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  
        chunk_overlap=200  
    )

    # Split into chunks
    return text_splitter.split_documents(docs)

def create_vector_store(chunks):
    """Create FAISS vector store from document chunks"""
    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings()
    
    # Create vector store
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    # Save the vector store locally
    vector_store.save_local("faiss_index")
    
    return vector_store

def load_vector_store():
    """Load the saved FAISS vector store"""
    embeddings = OpenAIEmbeddings()
    if os.path.exists("faiss_index"):
        return FAISS.load_local("faiss_index", embeddings)
    else:
        chunks = load_and_chunk_pdf(pdf_path)
        return create_vector_store(chunks)

def create_qa_chain():
    """Create a conversational QA chain with memory"""
    # Load the vector store
    vector_store = load_vector_store()
    
    # Initialize the LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0
    )
    
    # Initialize conversation memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key='answer'
    )
    
    # Create the conversational chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        return_source_documents=True,
        return_generated_question=True
    )
    
    return qa_chain

def get_policy_answer(question: str, qa_chain=None):
    """Get answer for a policy-related question"""
    if qa_chain is None:
        qa_chain = create_qa_chain()
    
    response = qa_chain({"question": question})
    
    return {
        "answer": response['answer'],
        "sources": [doc.page_content for doc in response['source_documents']],
        "chain": qa_chain  # Return the chain to maintain conversation history
    }

def process_uploaded_file(uploaded_file):
    """Process an uploaded PDF file and add it to the vector store"""
    try:
        # Create a temporary file to store the upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Load and chunk the new document
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        # Load existing vector store or create new one
        embeddings = OpenAIEmbeddings()
        if os.path.exists("faiss_index"):
            vector_store = FAISS.load_local("faiss_index", embeddings)
            # Add new documents to existing index
            vector_store.add_documents(chunks)
        else:
            vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save updated vector store
        vector_store.save_local("faiss_index")
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        return True, "Document successfully processed and added to knowledge base."
    except Exception as e:
        return False, f"Error processing document: {str(e)}"

def main():
    st.set_page_config(
        page_title="Policy Chatbot",
        page_icon="📚",
        layout="wide"
    )
    
    st.header("🤖 Bank XYZ Policy Assistant")
    
    # Add tabs for chat and document upload
    tab1, tab2 = st.tabs(["Chat", "Upload Documents"])
    
    with tab1:
        st.markdown("""
        Ask any questions about Bank XYZ's policies and procedures. 
        I'll help you find the relevant information from our policy documents.
        """)
        
        # Initialize chat history and QA chain in session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "qa_chain" not in st.session_state:
            st.session_state.qa_chain = create_qa_chain()

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sources" in message and message["sources"]:
                    with st.expander("View Sources"):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"**Source {i}:**\n{source[:200]}...")

        # Chat input
        if prompt := st.chat_input("Ask about our policies..."):
            # Display user message
            st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Get chatbot response
            with st.chat_message("assistant"):
                with st.spinner("Searching policies..."):
                    response = get_policy_answer(
                        prompt, 
                        qa_chain=st.session_state.qa_chain
                    )
                    st.markdown(response["answer"])
                    
                    with st.expander("View Sources"):
                        for i, source in enumerate(response["sources"], 1):
                            st.markdown(f"**Source {i}:**\n{source[:200]}...")
            
            # Save assistant response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["sources"]
            })
    
    with tab2:
        st.markdown("### Upload New Policy Documents")
        st.markdown("""
        Upload PDF documents to add to the knowledge base. 
        The chatbot will be able to reference these documents in future responses.
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf",
            help="Upload a PDF document containing policy information"
        )
        
        if uploaded_file is not None:
            with st.spinner("Processing document..."):
                success, message = process_uploaded_file(uploaded_file)
                
                if success:
                    st.success(message)
                    # Reset the QA chain to include new documents
                    st.session_state.qa_chain = create_qa_chain()
                else:
                    st.error(message)

if __name__ == "__main__":
    main()
