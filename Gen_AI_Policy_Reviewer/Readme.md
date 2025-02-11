# **Conversational RAG AI for Policy Insights**

## **Overview**
This project implements a **Conversational Retrieval-Augmented Generation (RAG) AI** chatbot for querying and gaining insights into policy documents. It enables users to ask questions about policies, retrieve relevant sections, and engage in context-aware discussions using conversational memory.

## **Key Features**
- **PDF Document Loader**: Extracts text from uploaded policy PDFs.
- **Text Chunking**: Splits documents into manageable text chunks for efficient retrieval.
- **Vector Database (FAISS)**: Stores embedded text chunks for fast similarity searches.
- **Conversational Memory**: Retains context in multi-turn conversations.
- **Retrieval-Augmented Generation (RAG)**: Fetches relevant policy sections and passes them to an LLM (GPT-3.5/4) for responses.
- **Interactive UI (Streamlit)**: Provides a user-friendly chat interface.
- **Document Uploading**: Users can upload additional policy documents to update the knowledge base dynamically.
- **Privacy-Friendly Deployment**: Supports privately deployed LLMs like **LLaMA**, reducing privacy concerns and ensuring sensitive data stays in-house.

## **Installation & Setup**

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Set Up Environment Variables**
Create a `.env` file and add your OpenAI API key:
```ini
OPENAI_API_KEY=your-api-key-here
```

### **3. Run the Application**
```bash
streamlit run conversational_rag_ai.py
```

## **Project Structure**
```plaintext
├── conversational_rag_ai.py   # Main application script
├── requirements.txt           # Required dependencies
├── faiss_index/               # Stored FAISS vector database
├── ACL_Policy_BANK_XYZ.pdf    # Sample policy document
└── .env                       # Environment variables
```

## **Usage Guide**

### **1. Query the Policy Knowledge Base**
- Enter a question in the chat UI (e.g., *"What are the access control policies for privileged users?"*)
- The chatbot retrieves relevant policy sections and generates a detailed response.
- Sources of retrieved content are displayed for reference.

### **2. Upload New Policy Documents**
- Navigate to the *Upload Documents* tab.
- Select and upload a **PDF document** containing policy information.
- The document is processed, chunked, and embedded into the FAISS vector database.
- New knowledge is available for retrieval immediately.

## **How It Works**
### **1. Document Processing**
- The **PyPDFLoader** extracts text from PDF documents.
- Text is split into **overlapping chunks** to ensure relevant context during retrieval.
- Each chunk is converted into numerical **embeddings** using OpenAI’s embedding model.
- The embeddings are stored in **FAISS**, enabling **fast similarity search**.

### **2. Conversational Retrieval**
- When a user asks a question, the chatbot searches FAISS for the **most relevant chunks**.
- The top-matching sections are **passed to GPT-3.5/4**, along with the query.
- The LLM generates a **contextual response**, leveraging retrieved content.
- Conversational memory ensures that multi-turn exchanges retain context.

## **Code Walkthrough**
### **Loading and Chunking Policy Documents**
```python
loader = PyPDFLoader("ACL_Policy_BANK_XYZ.pdf")
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(docs)
```

### **Creating the Vector Store**
```python
embeddings = OpenAIEmbeddings()
vector_store = FAISS.from_documents(chunks, embeddings)
vector_store.save_local("faiss_index")
```

### **Building the Chatbot with Memory**
```python
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
    retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
    memory=memory,
    return_source_documents=True
)
```

### **Processing User Queries**
```python
def get_policy_answer(question: str, qa_chain=None):
    if qa_chain is None:
        qa_chain = create_qa_chain()
    response = qa_chain({"question": question})
    return {"answer": response['answer'], "sources": [doc.page_content for doc in response['source_documents']]}
```

## **Future Enhancements**
- ✅ **Deploy API via FastAPI** for external integrations.
- ✅ **Fine-tune retrieval with hybrid search (BM25 + embeddings)**.
- ✅ **Support multi-document indexing for organization-wide knowledge bases**.
- ✅ **Enable private LLM deployments (e.g., LLaMA) for enhanced privacy**.

## **Contributing**
Contributions are welcome! Feel free to submit **pull requests** or raise **issues** for enhancements.

## **License**
This project is licensed under the **MIT License**.

---

🚀 **Get Started Today! Deploy an AI-powered policy assistant for your organization with enhanced privacy controls.**
