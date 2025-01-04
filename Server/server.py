import os
import re
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
            temperature=1.6,
            openai_api_key=openai_api_key or os.getenv('OPENAI_API_KEY')
        )
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"  # which output to store in memory
        )
        
        # Create retrieval chain
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            ),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"output_key": "answer"}  # ensure consistent output key
        )

    def extract_year_and_type(self, text: str):
        """
        Extracts year and type (recall/complaint) from text.
        """
        # Extract year
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        year = year_match.group(0) if year_match else None

        # Determine type based on query keywords
        if "recall" in text.lower():
            query_type = "recall"
        elif "complaint" in text.lower():
            query_type = "complaint"
        else:
            query_type = None

        return {
            "year": year,
            "type": query_type
        }

    def find_year_in_history(self, chat_history):
        """
        Look for a year in reversed chat history. 
        Returns the first year found or None.
        """
        for msg in reversed(chat_history):
            # msg is typically {'role': 'user'/'assistant', 'content': 'some text'}
            year_match = re.search(r"\b(19|20)\d{2}\b", msg.content)
            if year_match:
                return year_match.group(0)
        return None

    def find_type_in_history(self, chat_history):
        """
        Optionally, look for 'recall' or 'complaint' if needed.
        """
        for msg in reversed(chat_history):
            if "recall" in msg.content.lower():
                return "recall"
            elif "complaint" in msg.content.lower():
                return "complaint"
        return None
    
    def query(self, question: str) -> dict:
        try:
            # Retrieve conversation history from memory
            chat_history = self.memory.load_memory_variables({}).get("chat_history", [])
            
            # Extract from current user question
            metadata = self.extract_year_and_type(question)
            print(f"Extracted Metadata: {metadata}")

            # If no year in the user question, attempt to parse from history
            if not metadata["year"]:
                historical_year = self.find_year_in_history(chat_history)
                if historical_year:
                    metadata["year"] = historical_year

            # If still no year, ask user
            if not metadata["year"]:
                return {
                    "answer": "I need more information to answer your question. Could you specify the year?",
                    "sources": []
                }

            # Configure filters
            filters = {"ModelYear": metadata["year"]}
            if metadata["type"]:
                filters["type"] = metadata["type"]

            print(f"Filters used: {filters}")

            # Retrieve documents
            filtered_retriever = self.vectorstore.as_retriever(
                search_kwargs={
                    "k": 3,
                    "filter": filters
                }
            )

            # Override the chain's retriever
            self.chain.retriever = filtered_retriever

            # Query the chain
            response = self.chain.invoke({"question": question, "chat_history": chat_history})
            # print(f"Chain response: {response}")

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
    
    load_dotenv()
    
    # Initialize the RAG chain
    rag = RAGChain(
        pinecone_api_key=os.getenv('PINECONE_API_KEY'),
        pinecone_env=os.getenv('PINECONE_ENVIRONMENT'),
        index_name=os.getenv('PINECONE_INDEX_NAME'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    print("Chatbot is ready! Type your questions below (type 'exit' to quit).")
    while True:
        question = input("\nYou: ")
        if question.lower() == 'exit':
            print("Goodbye!")
            break
        response = rag.query(question)
        print(f"\nChatbot: {response['answer']}")
        print("\nSources:")
        for i, source in enumerate(response['sources'], 1):
            print(f"{i}. {source[:200]}...")
