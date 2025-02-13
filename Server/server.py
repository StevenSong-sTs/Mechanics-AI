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
from langchain.chains.llm import LLMChain

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

Documents:{context}

Question: {question}

Please provide your best-effort answer, referencing the documents if needed.
"""

CUSTOM_PROMPT = PromptTemplate(
    template=CUSTOM_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)


def build_custom_combine_chain(llm):
    """Create a QA chain using the 'stuff' approach with our custom prompt."""
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
        model_name: str = "gpt-4o-mini"
    ):
        """
        RAGChain constructor:
          - Initializes Pinecone and references an index.
          - Sets up HuggingFaceEmbeddings and vector store.
          - Creates a ChatOpenAI LLM.
          - Sets up a custom chain for document-combination using our custom prompt.
          - Builds a question generator chain for follow-up questions.
          - Instantiates the ConversationalRetrievalChain with a conversation memory.
        """
        # Initialize Pinecone client and obtain the index
        pc = PineconeClient(api_key=pinecone_api_key, environment=pinecone_env)
        self.index = pc.Index(index_name)

        # Set up embeddings and vector store
        self.embeddings = HuggingFaceEmbeddings(model_name="paraphrase-MiniLM-L6-v2")
        self.vectorstore = Pinecone(
            index=self.index,
            embedding=self.embeddings,
            text_key="description"
        )

        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=1.0,
            openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )

        # Build custom combine_docs chain using our custom prompt
        self.combine_docs_chain = build_custom_combine_chain(self.llm)

        # Conversation memory for chat history
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        # Build question generator chain to turn follow-up questions into standalone ones.
        question_generator_template = """
Given the following conversation history and a follow-up question, rephrase the question to be standalone.
Chat History: {chat_history}
Follow Up Question: {question}
Standalone Question:"""
        question_generator_prompt = PromptTemplate(
            template=question_generator_template,
            input_variables=["chat_history", "question"]
        )
        question_generator_chain = LLMChain(
            llm=self.llm,
            prompt=question_generator_prompt
        )

        # Construct the ConversationalRetrievalChain directly.
        self.chain = ConversationalRetrievalChain(
            question_generator=question_generator_chain,
            combine_docs_chain=self.combine_docs_chain,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=self.memory,
            return_source_documents=True,
            verbose=False
        )

    def extract_year_and_type(self, text: str):
        """Extract a year (e.g. 2020) and the type ('recall', 'complaint') from text."""
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
        """Search the chat history for a 4-digit year."""
        for msg in reversed(chat_history):
            yr_match = re.search(r"\b(19|20)\d{2}\b", msg.content)
            if yr_match:
                return yr_match.group(0)
        return None

    def find_type_in_history(self, chat_history):
        """Search the chat history for 'recall' or 'complaint'."""
        for msg in reversed(chat_history):
            lower_msg = msg.content.lower()
            if "recall" in lower_msg:
                return "recall"
            elif "complaint" in lower_msg:
                return "complaint"
        return None

    def query(self, question: str) -> dict:
        try:
            # Load conversation history.
            chat_history = self.memory.load_memory_variables({}).get("chat_history", [])

            # Extract metadata from current question and, if missing, fill from history.
            meta = self.extract_year_and_type(question)
            year = meta["year"] or self.find_year_in_history(chat_history)
            if not year:
                return {
                    "answer": "Could you let me know the year of the vehicle?",
                    "sources": []
                }
            q_type = meta["type"] or self.find_type_in_history(chat_history)

            # Build and update filters for the retriever.
            filters = {"ModelYear": year}
            if q_type:
                filters["type"] = q_type

            print(f"[DEBUG] Using filters: {filters}")
            self.chain.retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 3, "filter": filters}
            )

            result = self.chain({
                "question": question,
                "chat_history": chat_history
            })
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
        model_name="gpt-4o-mini"
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

