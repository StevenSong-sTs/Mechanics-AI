import os
import re
from dotenv import load_dotenv

########################
# Imports for LangChain 0.3.14
########################
# (Install from "langchain-community", "langchain-huggingface", "langchain-pinecone")

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import Pinecone
from langchain_community.chat_models import ChatOpenAI

from langchain.chains import ConversationalRetrievalChain
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

########################
# Pinecone - new usage
########################
from pinecone import Pinecone as PineconeClient


########################
# Custom Prompt for "Stuff" QA
########################
CUSTOM_PROMPT_TEMPLATE = """
You are an AI assistant (an experienced mechanic) that helps users with car-related questions.
We have a set of potentially relevant documents, but they might not directly answer the user.
If you are not certain about the correct answer, say so.

However, you must:
1. Provide a disclaimer that the info may not address the exact issue.
2. Summarize any relevant details from the documents below if they could help.

Documents:
{context}

Question: {question}

Please provide your best-effort answer, referencing the documents if needed.
"""

CUSTOM_PROMPT = PromptTemplate(
    template=CUSTOM_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)


def build_custom_combine_chain(llm):
    """Create a QA chain using the 'stuff' approach plus our custom prompt."""
    return load_qa_chain(
        llm=llm,
        chain_type="stuff",
        prompt=CUSTOM_PROMPT
    )


class RAGChain:
    def __init__(
        self,
        pinecone_api_key: str,
        pinecone_env: str,
        index_name: str,
        openai_api_key: str = None,
        model_name: str = "gpt-3.5-turbo"
    ):
        """
        RAGChain constructor:
          - Sets up Pinecone using the modern approach (PineconeClient).
          - Creates a HuggingFaceEmbeddings and a Pinecone vector store.
          - Uses ChatOpenAI from langchain_community.
          - Builds a custom chain for combining documents with the user's question.
          - Wraps everything in a ConversationalRetrievalChain with memory.
        """

        # 1) Initialize Pinecone client (no pinecone.init())
        pc = PineconeClient(
            api_key=pinecone_api_key,
            environment=pinecone_env
        )

        # 2) Reference an existing Pinecone index
        self.index = pc.Index(index_name)

        # 3) Hugging Face embeddings from the new package
        self.embeddings = HuggingFaceEmbeddings(
            model_name="paraphrase-MiniLM-L6-v2"
        )

        # 4) Build a Pinecone vector store from the new package
        #    Use `embedding=...`, not `embedding_function=...`
        self.vectorstore = Pinecone(
            index=self.index,
            embedding=self.embeddings,
            text_key="description"
        )

        # 5) Create an LLM (ChatOpenAI) from langchain_community
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=1.0,
            openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )

        # 6) Build a custom chain that uses a "stuff" prompt
        self.combine_docs_chain = build_custom_combine_chain(self.llm)

        # 7) Conversation buffer memory (stores the chat)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # 8) Create the ConversationalRetrievalChain
        #    - We pass `chain_type=None` so it doesn't auto-create a combine chain
        #    - Then we pass our own `combine_docs_chain`
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=self.memory,
            return_source_documents=True,
            chain_type=None,
            combine_docs_chain=self.combine_docs_chain
        )

    def extract_year_and_type(self, text: str):
        """Extracts a year (e.g. 2020) and type ('recall', 'complaint') from the text."""
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        year = year_match.group(0) if year_match else None

        txt_lower = text.lower()
        if "recall" in txt_lower:
            q_type = "recall"
        elif "complaint" in txt_lower:
            q_type = "complaint"
        else:
            q_type = None

        return {"year": year, "type": q_type}

    def find_year_in_history(self, chat_history):
        """Look for a 4-digit year in reversed chat history."""
        for msg in reversed(chat_history):
            yr_match = re.search(r"\b(19|20)\d{2}\b", msg.content)
            if yr_match:
                return yr_match.group(0)
        return None

    def find_type_in_history(self, chat_history):
        """Look for 'recall' or 'complaint' in reversed chat history."""
        for msg in reversed(chat_history):
            lower_msg = msg.content.lower()
            if "recall" in lower_msg:
                return "recall"
            elif "complaint" in lower_msg:
                return "complaint"
        return None

    def query(self, question: str) -> dict:
        try:
            # Retrieve stored conversation from memory
            chat_history = self.memory.load_memory_variables({}).get("chat_history", [])

            # Extract metadata from the current user question
            meta = self.extract_year_and_type(question)
            year = meta["year"]
            q_type = meta["type"]

            # If year isn't mentioned now, try from conversation history
            if not year:
                year = self.find_year_in_history(chat_history)
            if not year:
                return {
                    "answer": "Could you let me know the year of the vehicle?",
                    "sources": []
                }

            # If type isn't mentioned, try from history
            if not q_type:
                q_type = self.find_type_in_history(chat_history)

            # Build Pinecone filter
            filters = {"ModelYear": year}
            if q_type:
                filters["type"] = q_type

            print(f"[DEBUG] Using filters: {filters}")

            # Override the chain's retriever to use the new filters
            self.chain.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 3, "filter": filters}
            )

            # Ask the chain
            result = self.chain({"question": question, "chat_history": chat_history})
            answer = result["answer"]
            source_docs = result["source_documents"]

            return {
                "answer": answer,
                "sources": [doc.page_content for doc in source_docs]
            }

        except Exception as e:
            print(f"Error during query: {e}")
            return {
                "answer": "Sorry, an error occurred while processing your question.",
                "sources": []
            }


###################
# Main Interactive Loop
###################
if __name__ == "__main__":
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    load_dotenv()  # Load .env if needed

    # Initialize your RAG chain
    rag = RAGChain(
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        pinecone_env=os.getenv("PINECONE_ENVIRONMENT"),
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-3.5-turbo"
    )

    print("Chatbot is ready! Type your questions below (type 'exit' to quit).")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        resp = rag.query(user_input)
        print(f"\nChatbot: {resp['answer']}\n")

        # Show truncated sources
        print("Sources:")
        for i, src in enumerate(resp["sources"], 1):
            print(f"{i}. {src[:200]}...")

