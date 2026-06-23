# -*- coding: utf-8 -*-
"""RAG 文档问答链。"""
from langchain_core.prompts import ChatPromptTemplate

from agents.llm import get_llm

from .vectorstore import retrieve_context

_QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是一名资深接口测试工程师助手，负责根据接口文档回答测试相关问题。\n"
     "只依据下面提供的文档片段回答；文档中没有的信息，明确说明\"文档中未提及\"，不要编造。\n"
     "回答时尽量给出接口 Path、Method、参数名、业务状态码等具体信息。"),
    ("human", "文档片段：\n{context}\n\n问题：{question}"),
])


def answer(question: str) -> dict:
    """返回 {answer, context}。"""
    context = retrieve_context(question)
    chain = _QA_PROMPT | get_llm()
    resp = chain.invoke({"context": context, "question": question})
    return {"answer": resp.content, "context": context}
