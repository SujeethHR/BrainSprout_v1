import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from config import Config

logger = logging.getLogger(__name__)


def _format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


class LLMService:
    def __init__(self, vector_store):
        self.llm = ChatGroq(
            temperature=0.7,
            model_name="llama-3.3-70b-versatile",
            groq_api_key=Config.GROQ_API_KEY
        )
        self.retriever = vector_store.vector_store.as_retriever()
        self.chat_history = []

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Use the following context to answer the question:\n\n{context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{question}"),
        ])

        self.chain = (
            {
                "context": lambda x: _format_docs(self.retriever.invoke(x["question"])),
                "question": lambda x: x["question"],
                "chat_history": lambda x: x["chat_history"],
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def get_response(self, query):
        try:
            answer = self.chain.invoke({
                "question": query,
                "chat_history": self.chat_history
            })
            self.chat_history.extend([
                HumanMessage(content=query),
                AIMessage(content=answer)
            ])
            return answer
        except Exception as e:
            logger.error("llm_error", extra={"error": str(e)})
            return "I encountered an error processing your request."
