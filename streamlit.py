# app.py
import uuid
import streamlit as st
from urllib.parse import urlencode
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from chat import graph, ChatState as State

load_dotenv()
st.set_page_config(page_title="Chat Repositori Skripsi USU", page_icon="🎓")


def get_or_create_thread_id(param_name: str = "tid") -> str:
    qp = st.query_params
    print("QUERY PARAMS:", qp)
    tid_from_url = qp.get(param_name, None)
    print("THREAD ID FROM URL:", tid_from_url)

    print("SESSION STATE BEFORE:", st.session_state)

    if "thread_id" not in st.session_state:
        print("TEST", tid_from_url)
        st.session_state.thread_id = tid_from_url or uuid.uuid4().hex

    print("SESSION STATE AFTER:", st.session_state)
    if tid_from_url and tid_from_url != st.session_state.thread_id:
        st.session_state.thread_id = tid_from_url

    return st.session_state.thread_id


def set_url_tid(tid: str, param_name: str = "tid"):
    st.query_params[param_name] = tid


tid = get_or_create_thread_id()
print("USING THREAD ID:", tid)
set_url_tid(tid)

if "threads" not in st.session_state:
    st.session_state.threads = {}

messages = st.session_state.threads.setdefault(tid, [])

st.sidebar.header("Session")
st.sidebar.write("**Thread ID**")
st.sidebar.code(tid, language=None)

base_url = st.request.url.split("?")[0] if hasattr(st, "request") else ""
share_url = f"{base_url}?{urlencode({'tid': tid})}" if base_url else ""
if share_url:
    st.sidebar.write("Bagikan / bookmark sesi ini:")
    st.sidebar.code(share_url, language=None)

if st.sidebar.button("➕ New chat"):
    new_tid = uuid.uuid4().hex
    st.session_state.thread_id = new_tid
    st.session_state.threads.setdefault(new_tid, [])
    set_url_tid(new_tid)
    st.rerun()

if st.sidebar.button("🧹 Clear this chat only"):
    st.session_state.threads[tid] = []
    st.rerun()

st.title("Chat Repositori Skripsi USU")

for message in messages:
    role = None
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    elif isinstance(message, ToolMessage):
        role = "assistant"

    if role:
        with st.chat_message(role):
            st.write(message.content)

prompt = st.chat_input("Cari apa pun tentang skripsi dari repositori institusi USU")
if prompt:
    user_msg = HumanMessage(content=prompt)
    messages.append(user_msg)

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            state = State(messages=list(messages))
            config = {"configurable": {"thread_id": tid}}

            for chunk, metadata in graph.stream(
                state, config=config, stream_mode="messages"
            ):
                tags = (metadata or {}).get("tags", [])
                if isinstance(chunk, AIMessage) and tags == ["chat"]:
                    full_response += chunk.content
                    message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
            messages.append(AIMessage(content=full_response))

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
