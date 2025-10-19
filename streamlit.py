# app.py
import uuid
import streamlit as st
from urllib.parse import urlencode
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from chat import graph, ChatState as State

load_dotenv()
st.set_page_config(page_title="Chat Repositori Skripsi USU", page_icon="🎓")

# --- Helpers: thread_id in URL + state ---
def get_or_create_thread_id(param_name: str = "tid") -> str:
    qp = st.query_params
    print("QUERY PARAMS:", qp)
    tid_from_url = qp.get(param_name, None)
    print("THREAD ID FROM URL:", tid_from_url)

    print("SESSION STATE BEFORE:", st.session_state)

    # if not yet in state, create one (prefer URL if present)
    if "thread_id" not in st.session_state:
        print("TEST", tid_from_url )
        st.session_state.thread_id = tid_from_url or uuid.uuid4().hex

    print("SESSION STATE AFTER:", st.session_state)
    # if URL has a different tid than state, sync it into state
    if tid_from_url and tid_from_url != st.session_state.thread_id:
        st.session_state.thread_id = tid_from_url

    return st.session_state.thread_id

def set_url_tid(tid: str, param_name: str = "tid"):
    st.query_params[param_name] = tid

# --- Initialize per-thread message store ---
tid = get_or_create_thread_id()
print("USING THREAD ID:", tid)
set_url_tid(tid)

# Keep all threads in one dict: { thread_id: [HumanMessage|AIMessage|ToolMessage, ...] }
if "threads" not in st.session_state:
    st.session_state.threads = {}

messages = st.session_state.threads.setdefault(tid, [])

# --- Sidebar controls ---
st.sidebar.header("Session")
st.sidebar.write("**Thread ID**")
st.sidebar.code(tid, language=None)

# Build a shareable URL with ?tid=...
base_url = st.request.url.split("?")[0] if hasattr(st, "request") else ""
share_url = f"{base_url}?{urlencode({'tid': tid})}" if base_url else ""
if share_url:
    st.sidebar.write("Bagikan / bookmark sesi ini:")
    st.sidebar.code(share_url, language=None)

if st.sidebar.button("➕ New chat"):
    new_tid = uuid.uuid4().hex
    st.session_state.thread_id = new_tid
    # initialize empty message list for the new thread
    st.session_state.threads.setdefault(new_tid, [])
    set_url_tid(new_tid)
    st.rerun()

if st.sidebar.button("🧹 Clear this chat only"):
    st.session_state.threads[tid] = []
    st.rerun()

# --- Main UI ---
st.title("Chat Repositori Skripsi USU")

# Render existing history for this thread
for message in messages:
    role = None
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    elif isinstance(message, ToolMessage):
        role = "assistant"  # or 'tool' if you prefer to differentiate

    if role:
        with st.chat_message(role):
            st.write(message.content)

# --- Chat input & stream ---
prompt = st.chat_input("Cari apa pun tentang skripsi dari repositori institusi USU")
if prompt:
    user_msg = HumanMessage(content=prompt)
    messages.append(user_msg)  # save into this thread's history

    # Echo user bubble immediately
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # If your graph needs prior history, pass messages=messages.
            # If it persists by thread_id internally, current user_msg alone is fine.
            # Choose one of the two lines below based on your graph design:

            # Option A: stateless graph, we supply full thread history
            state = State(messages=list(messages))

            # Option B: stateful-by-thread graph, only the latest user message is needed
            # state = State(messages=[user_msg])

            # Use the thread_id as requested
            config = {"configurable": {"thread_id": tid}}

            for chunk, metadata in graph.stream(state, config=config, stream_mode="messages"):
                # Be defensive on metadata
                tags = (metadata or {}).get("tags", [])
                if isinstance(chunk, AIMessage) and tags == ["chat"]:
                    full_response += chunk.content
                    message_placeholder.markdown(full_response + "▌")

            # Finalize streamed content
            message_placeholder.markdown(full_response)

            # Save assistant reply to THIS thread only
            messages.append(AIMessage(content=full_response))

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
