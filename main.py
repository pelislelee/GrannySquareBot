import json
from io import BytesIO
from pathlib import Path
import hashlib
import requests
import re

import streamlit as st
from PIL import Image

import database

MODEL_DIR = Path(__file__).resolve().parent / "model"
BASE_MODEL_ID = "llava-hf/llava-1.5-7b-hf"

st.set_page_config(
    page_title="GrannySquareBot",
    page_icon="🧶",
    layout="wide",
    initial_sidebar_state="expanded"
)

database.initialize_database()

@st.dialog("Sign In / Log In", width="small")
def login_dialog():
    st.write("Enter your username and password to continue.")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if username.strip() and password.strip():
                user_id = database.authenticate_or_create_user(
                    username.strip(), password
                )
                if user_id is not None:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.session_state.user = username.strip()
                    st.session_state.loaded_user_id = None
                    st.rerun()
                else:
                    st.error("Username or password is incorrect.")
            else:
                st.error("Username and password cannot be empty.")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.authenticated = False

# -----------------------------------------------------------------------------
# PALETTE STYLES & CUSTOM CSS (Using provided Blue & Brown palette)
# Chambray: #6893BC | Pale Cornflower: #90967A / #A6C8E0
# Parchment White: #F8F5F0 | Brown: #6B553D | Expresso Brown: #342B1C
# -----------------------------------------------------------------------------
st.markdown("""
<style>
/* Main App Background & Text */
.stApp { 
    background-color: #F8F5F0; 
    color: #342B1C; 
}

header[data-testid="stHeader"] { 
    background-color: #F8F5F0; 
}


/* Sidebar Styling */
section[data-testid="stSidebar"] { 
    background-color: #EFE9E0; 
    border-right: 1px solid #D6CBC1; 
}

section[data-testid="stSidebar"] > div { 
    padding-top: 1.2rem; 
}

.brand { 
    font-size: 23px; 
    font-weight: 750; 
    letter-spacing: -0.8px; 
    color: #342B1C; 
    margin-bottom: 4px; 
}

.brand-subtitle { 
    font-size: 12px; 
    color: #6B553D; 
    margin-bottom: 24px; 
}

.section-label { 
    font-size: 12px; 
    font-weight: 600; 
    color: #6B553D; 
    text-transform: uppercase; 
    letter-spacing: 1px; 
    margin: 20px 0 8px 4px; 
}

/* Primary & Sidebar Buttons */
.stButton > button { 
    border-radius: 10px; 
    border: 1px solid #D6CBC1; 
    background-color: #FFFFFF;
    color: #342B1C;
    transition: all 0.2s ease; 
}

.stButton > button:hover { 
    border-color: #6B553D; 
    color: #6B553D; 
    background-color: #F8F5F0;
}

/* Compact Sidebar Chat Items */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 8px;
    padding: 4px 8px;
    min-height: 38px;
}

/* Main Titles */
.main-title { 
    font-size: 26px; 
    font-weight: 700; 
    letter-spacing: -0.6px; 
    color: #342B1C; 
    text-align: center; 
    margin-top: 15px; 
    margin-bottom: 6px; 
}

.main-subtitle { 
    text-align: center; 
    font-size: 14px; 
    color: #6B553D; 
    margin-bottom: 24px; 
}

/* Centered image upload control */
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}

[data-testid="stFileUploaderDropzone"] button {
    width: 100% !important;
    min-height: 72px !important;
    background-color: #6893BC !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 17px !important;
    font-weight: 600 !important;
}

[data-testid="stFileUploaderDropzone"] button:hover {
    background-color: #557FA7 !important;
    color: #FFFFFF !important;
}

.upload-info {
    margin-top: 12px;
    color: #6B553D;
    font-size: 13px;
    line-height: 1.6;
    text-align: center;
}

/* Welcome Card */
.welcome-card { 
    background: #FFFFFF; 
    border: 1px solid #E5DDD3; 
    border-radius: 16px; 
    padding: 22px; 
    margin: 0 auto 24px auto; 
    max-width: 600px; 
}

.welcome-card h3 { 
    font-size: 17px; 
    margin-bottom: 8px; 
    color: #342B1C; 
}

.welcome-card p { 
    font-size: 14px; 
    line-height: 1.7; 
    color: #6B553D; 
    margin-bottom: 0; 
}

/* Chat Messages */
[data-testid="stChatMessage"] { 
    background-color: #FFFFFF;
    border: 1px solid #E8E1D7;
    border-radius: 14px; 
    padding: 14px 16px; 
    margin-bottom: 12px;
}

/* Footer */
.footer-note { 
    color: #6B553D; 
    text-align: center; 
    font-size: 11px; 
    margin-top: 30px; 
    margin-bottom: 10px;
}

[data-testid="stImage"] img { 
    border-radius: 12px; 
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.authenticated:
    login_dialog()
    st.stop()

# -----------------------------------------------------------------------------
# CHAT LOGIC & STATE
# -----------------------------------------------------------------------------
def load_user_projects(user_id):
    projects = {}
    for project_id, project_name, created_at in database.list_projects(user_id):
        messages = []
        for image_bytes, pattern in database.list_patterns(project_id):
            messages.extend([
                {
                    "role": "user",
                    "content": image_name,
                    "image_bytes": image_bytes,
                    "image_name": None,
                },
                {
                    "role": "assistant",
                    "content": pattern,
                    "image_bytes": None,
                    "image_name": None,
                },
            ])
        projects[project_id] = {
            "title": project_name,
            "created_at": created_at,
            "messages": messages,
        }
    return projects


def create_chat():
    user_id = st.session_state.user_id
    if user_id is None:
        raise RuntimeError("A logged-in user is required to create a project.")

    chat_id, created_at = database.create_project(user_id, "New Chat")
    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "created_at": created_at,
        "messages": []
    }
    st.session_state.active_chat = chat_id


def hide_chat(chat_id):
    database.hide_project(st.session_state.user_id, chat_id)
    del st.session_state.chats[chat_id]
    st.session_state.project_dialog = None
    st.session_state.project_dialog_chat_id = None

    if st.session_state.active_chat == chat_id:
        remaining_chat_ids = sorted(
            st.session_state.chats,
            key=lambda existing_chat_id: st.session_state.chats[
                existing_chat_id
            ]["created_at"],
            reverse=True,
        )
        if remaining_chat_ids:
            st.session_state.active_chat = remaining_chat_ids[0]
        else:
            create_chat()


def reset_image_uploader(chat_id):
    reset_counts = st.session_state.setdefault("uploader_reset_counts", {})
    reset_counts[chat_id] = reset_counts.get(chat_id, 0) + 1


if st.session_state.loaded_user_id != st.session_state.user_id:
    st.session_state.chats = load_user_projects(st.session_state.user_id)
    st.session_state.active_chat = None
    st.session_state.loaded_user_id = st.session_state.user_id

if "chats" not in st.session_state:
    st.session_state.chats = {}

if not st.session_state.chats:
    create_chat()
elif st.session_state.get("active_chat") not in st.session_state.chats:
    st.session_state.active_chat = next(iter(st.session_state.chats))

if "project_dialog" not in st.session_state:
    st.session_state.project_dialog = None
if "project_dialog_chat_id" not in st.session_state:
    st.session_state.project_dialog_chat_id = None


@st.dialog("Chat options", width="small", dismissible=False)
def chat_options_dialog():
    chat_id = st.session_state.project_dialog_chat_id
    if chat_id not in st.session_state.chats:
        st.session_state.project_dialog = None
        st.session_state.project_dialog_chat_id = None
        st.rerun()

    st.write(f"What would you like to do with **{st.session_state.chats[chat_id]['title']}**?")
    col_edit, col_delete, col_cancel = st.columns(3)
    with col_edit:
        if st.button("Edit", key="chat_options_edit", use_container_width=True):
            st.session_state.project_dialog = "rename"
            st.rerun()
    with col_delete:
        if st.button("Delete", key="chat_options_delete", use_container_width=True):
            st.session_state.project_dialog = "confirm_delete"
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="chat_options_cancel", use_container_width=True):
            st.session_state.project_dialog = None
            st.session_state.project_dialog_chat_id = None
            st.rerun()


@st.dialog("Rename chat", width="small", dismissible=False)
def rename_chat_dialog():
    chat_id = st.session_state.project_dialog_chat_id
    if chat_id not in st.session_state.chats:
        st.session_state.project_dialog = None
        st.session_state.project_dialog_chat_id = None
        st.rerun()

    with st.form("rename_chat_form"):
        new_title = st.text_input(
            "Chat name",
            value=st.session_state.chats[chat_id]["title"],
        )
        col_save, col_cancel = st.columns(2)
        with col_save:
            save = st.form_submit_button("Save", use_container_width=True)
        with col_cancel:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

    if save:
        if not new_title.strip():
            st.error("Chat name cannot be empty.")
            return
        database.rename_project(
            st.session_state.user_id,
            chat_id,
            new_title.strip(),
        )
        st.session_state.chats[chat_id]["title"] = new_title.strip()
        st.session_state.project_dialog = None
        st.session_state.project_dialog_chat_id = None
        st.rerun()
    if cancel:
        st.session_state.project_dialog = "options"
        st.rerun()



@st.dialog("Delete chat?", width="small", dismissible=False)
def confirm_delete_chat_dialog():
    chat_id = st.session_state.project_dialog_chat_id
    if chat_id not in st.session_state.chats:
        st.session_state.project_dialog = None
        st.session_state.project_dialog_chat_id = None
        st.rerun()

    st.write(
        f"Remove **{st.session_state.chats[chat_id]['title']}** from chat history? "
        "Its data will remain in the database."
    )
    col_delete, col_cancel = st.columns(2)
    with col_delete:
        confirm = st.button(
            "Delete",
            key="confirm_delete_chat",
            type="primary",
            use_container_width=True,
        )
    with col_cancel:
        cancel = st.button(
            "Cancel",
            key="cancel_delete_chat",
            use_container_width=True,
        )

    if confirm:
        hide_chat(chat_id)
        st.rerun()
    if cancel:
        st.session_state.project_dialog = "options"
        st.rerun()

def format_crochet_pattern(text: str) -> str:
    """Place Base, Round, and Row instructions on separate lines."""

    # Normalize existing line breaks.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Add a line break before Base, Round N, and Row N.
    text = re.sub(
        r"[ \t]*(?<!\w)(Base\s*:|Round\s+\d+\s*:|Row\s+\d+\s*:)",
        r"\n\1",
        text,
        flags=re.IGNORECASE,
    )

    # Remove excessive blank lines and trim the result.
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n\n".join(lines).strip()


def generate_response(image_bytes: bytes) -> str:
    api_url = st.secrets["GRANNYSQUARE_API_URL"].rstrip("/")
    api_key = st.secrets["GRANNYSQUARE_API_KEY"]

    try:
        response = requests.post(
            f"{api_url}/generate",
            headers={
                "Authorization": f"Bearer {api_key}",
                "ngrok-skip-browser-warning": "true",
            },
            files={
                "file": (
                    "granny_square.jpg",
                    image_bytes,
                    "image/jpeg",
                )
            },
            timeout=600,
        )

        response.raise_for_status()
        result = response.json()

        answer = result.get("answer", "").strip()
        answer = format_crochet_pattern(answer)
        if not answer:
            raise RuntimeError("The API returned an empty response.")

        return answer

    except requests.Timeout as exc:
        raise RuntimeError(
            "The model took too long to respond. "
            "Check that Colab is still running."
        ) from exc

    except requests.RequestException as exc:
        details = ""
        if exc.response is not None:
            details = f" API response: {exc.response.text[:500]}"

        raise RuntimeError(
            "Could not get a response from the Colab model API."
            + details
        ) from exc

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand">🧶 GrannySquareBot</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="brand-subtitle">Logged in as <b>{st.session_state.get("user", "User")}</b></div>',
        unsafe_allow_html=True
    )

    if st.button("＋  New Chat", use_container_width=True, type="primary"):
        create_chat()
        st.rerun()

    st.markdown('<div class="section-label">Chat History</div>', unsafe_allow_html=True)

    chat_ids = sorted(
        st.session_state.chats.keys(),
        key=lambda cid: st.session_state.chats[cid]["created_at"],
        reverse=True
    )

    if not chat_ids:
        st.caption("No chat history available.")

    for chat_id in chat_ids:
        chat = st.session_state.chats[chat_id]
        is_active = (chat_id == st.session_state.active_chat)
        prefix = "● " if is_active else " "

        col_main, col_edit = st.columns([0.84, 0.16])
        with col_main:
            if st.button(
                prefix + chat["title"],
                key=f"chat_{chat_id}",
                use_container_width=True
            ):
                st.session_state.active_chat = chat_id
                st.rerun()
        with col_edit:
            if st.button(
                "✏️",
                key=f"edit_icon_{chat_id}",
                use_container_width=True,
                help="Edit or delete chat",
            ):
                st.session_state.project_dialog_chat_id = chat_id
                st.session_state.project_dialog = "options"
                st.rerun()

    st.divider()

    if st.button("🚪 Exit / Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.loaded_user_id = None
        st.session_state.chats = {}
        st.session_state.active_chat = None
        st.session_state.project_dialog = None
        st.session_state.project_dialog_chat_id = None
        st.rerun()

    st.caption("GrannySquareBot")
    st.caption("Image-to-text crochet pattern generation")

if st.session_state.project_dialog == "options":
    chat_options_dialog()
elif st.session_state.project_dialog == "rename":
    rename_chat_dialog()
elif st.session_state.project_dialog == "confirm_delete":
    confirm_delete_chat_dialog()

# -----------------------------------------------------------------------------
# MAIN VIEW & COMPACT CENTERED FILE UPLOADER
# -----------------------------------------------------------------------------
active_chat = st.session_state.chats[st.session_state.active_chat]
messages = active_chat["messages"]

st.markdown('<div class="main-title">What would you like to crochet?</div>', unsafe_allow_html=True)

# Centered upload section
col_left, col_center, col_right = st.columns([1, 1.6, 1])

with col_center:
    uploader_reset_counts = st.session_state.setdefault(
        "uploader_reset_counts", {}
    )
    active_chat_id = st.session_state.active_chat
    uploader_key = (
        f"uploader_{active_chat_id}_"
        f"{uploader_reset_counts.get(active_chat_id, 0)}"
    )
    uploaded_file = st.file_uploader(
        "Upload your granny square image:",
        type=["png", "jpg", "jpeg", "webp"],
        key=uploader_key,
        label_visibility="collapsed"
    )
    if uploaded_file is not None:
        st.markdown(
            """
            <style>
            [data-testid="stFileUploaderDropzone"] {
                display: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        preview_col, cancel_col = st.columns([0.85, 0.15])
        with preview_col:
            st.image(
                Image.open(BytesIO(uploaded_file.getvalue())),
                caption=uploaded_file.name,
                width=220,
            )
        with cancel_col:
            st.button(
                "✕",
                key=(
                    f"cancel_upload_{active_chat_id}_"
                    f"{uploader_reset_counts.get(active_chat_id, 0)}"
                ),
                help="Cancel image upload",
                on_click=reset_image_uploader,
                args=(active_chat_id,),
                use_container_width=True,
            )
    st.markdown(
        '<div class="upload-info">Upload your granny square image to generate a pattern automatically.'
        '<br>Supported formats: PNG, JPG, JPEG, or WEBP.</div>',
        unsafe_allow_html=True
    )


if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    image_name = uploaded_file.name

    # Identify the image by its actual contents, not its filename.
    image_id = hashlib.sha256(image_bytes).hexdigest()

    processed_images = st.session_state.setdefault(
        "processed_images", set()
    )

    if image_id not in processed_images:
        if st.button(
            "Generate Crochet Pattern",
            key=f"generate_{st.session_state.active_chat}",
        ):
            try:
                with st.spinner(
                    "Analyzing image and generating crochet pattern..."
                ):
                    answer = generate_response(image_bytes)

                database.save_pattern(
                    st.session_state.user_id,
                    st.session_state.active_chat,
                    image_bytes,
                    answer,
                )

                if not messages:
                    project_name = f"Image: {image_name[:18]}"
                    active_chat["title"] = project_name
                    database.rename_project(
                        st.session_state.user_id,
                        st.session_state.active_chat,
                        project_name,
                    )

                messages.extend([
                    {
                        "role": "user",
                        "content": f"Uploaded **{image_name}**",
                        "image_bytes": image_bytes,
                        "image_name": image_name,
                    },
                    {
                        "role": "assistant",
                        "content": answer,
                        "image_bytes": None,
                        "image_name": None,
                    },
                ])

                processed_images.add(image_id)
                st.rerun()

            except Exception as e:
                st.error(f"Pattern generation failed: {e}")
                st.exception(e)

st.divider()

# Welcome Card (if empty conversation)
if not messages:
    st.markdown("""
    <div class="welcome-card">
        <h3>🧶 Crochet Pattern Generator</h3>
        <p>
            Simply upload a photo of the crochet pattern you have on the button above. The system will analyze
            the image and generate step-by-step instructions automatically.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Render generated outputs and history below the uploader
for message in messages:
    with st.chat_message(message["role"], avatar="🧶" if message["role"] == "assistant" else "👤"):
        if message.get("image_bytes"):
            st.image(
                Image.open(BytesIO(message["image_bytes"])),
                caption=message.get("image_name", "Granny Square Image"),
                width=280
            )
        if message.get("content"):
            if message["role"] == "assistant":
                st.markdown(
                    format_crochet_pattern(message["content"])
                )
            else:
                st.markdown(message["content"])

st.markdown(
    '<div class="footer-note">GrannySquareBot · AI-assisted crochet pattern generation</div>',
    unsafe_allow_html=True
)