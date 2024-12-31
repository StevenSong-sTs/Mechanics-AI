import os
from typing import List
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import Pinecone
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from pinecone import Pinecone as PineconeClient
from dotenv import load_dotenv

class RAGChain:
    def __init__(
        self,
        pinecone_api_key: str,
        pinecone_env: str,
        index_name: str,
        openai_api_key: str = None,
        model_name: str = "gpt-4o-mini"
    ):
        # Initialize Pinecone client
        pc = PineconeClient(api_key=pinecone_api_key)
        
        # Initialize components
        self.embeddings = HuggingFaceEmbeddings(model_name='paraphrase-MiniLM-L6-v2')
        self.index = pc.Index(index_name)
        
        # Create vector store
        self.vectorstore = Pinecone.from_existing_index(
            index_name=index_name,
            embedding=self.embeddings,
            text_key="description"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=0.0,
            openai_api_key=openai_api_key or os.getenv('OPENAI_API_KEY')
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"  # Specify which output to store in memory
        )
        
        # Create retrieval chain
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            ),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"output_key": "answer"}  # Ensure consistent output key
        )
    
    def query(self, question: str) -> dict:
        """
        Process a question and return both the answer and source documents
        """
        try:
            response = self.chain.invoke({"question": question})  # Use invoke instead of __call__
            return {
                "answer": response["answer"],
                "sources": [doc.page_content for doc in response["source_documents"]]
            }
        except Exception as e:
            print(f"Error during query: {str(e)}")
            return {
                "answer": "Sorry, I encountered an error processing your question.",
                "sources": []
            }

# Usage example
if __name__ == "__main__":
    # Set environment variable to avoid tokenizer warning
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # Need to load environment variables first
    load_dotenv()
    
    # Initialize the RAG chain
    rag = RAGChain(
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_env=os.getenv('PINECONE_ENVIRONMENT'),
        index_name=os.getenv('PINECONE_INDEX_NAME'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Example conversation
    questions = [
        "Why my 2020 Jeep Wrangler is making a loud noise while braking?",
        "I plan to buy a 2018 Jeep Wrangler, what are some common issues I should be aware of?",
        "The check engine light is on for my 2020 Jeep wrnagler, it has 30,000 miles on it, what are some possible causes?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        response = rag.query(question)
        print(f"Answer: {response['answer']}")
        print("\nSources:")
        for i, source in enumerate(response['sources'], 1):
            print(f"{i}. {source[:200]}...")
