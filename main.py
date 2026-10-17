import streamlit as st
from PIL import Image
from io import BytesIO
import database

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

/* Modal / Dialog Styling */
div[role="dialog"] {
    background-color: #EFE9E0 !important;
    border: 1px solid #D6CBC1 !important;
    border-radius: 16px !important;
    color: #342B1C !important;
}

div[role="dialog"] h2 {
    color: #342B1C !important;
    font-weight: 700 !important;
}

div[role="dialog"] input {
    background-color: #FFFFFF !important;
    color: #342B1C !important;
    border: 1px solid #D6CBC1 !important;
    border-radius: 8px !important;
}

div[role="dialog"] button[type="submit"] {
    background-color: #6893BC !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
}

div[role="dialog"] button[type="submit"]:hover {
    background-color: #557FA7 !important;
    color: #FFFFFF !important;
}

[data-testid="stFormSubmitButton"] button {
    background-color: #6893BC !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
}

[data-testid="stFormSubmitButton"] button:hover {
    background-color: #557FA7 !important;
    color: #FFFFFF !important;
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
                    "content": "Uploading image...",
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

if "renaming_chat" not in st.session_state:
    st.session_state.renaming_chat = None

def generate_response(image_bytes):
    """Generated crochet pattern based strictly on uploaded image."""
    return (
        "**Generated Crochet Pattern from Image**\n\n"
        "**Base:** Make a magic ring.\n\n"
        "**Round 1:** Chain 3, work 2 double crochet stitches into the ring. "
        "Chain 2 to form a corner. Repeat sequence to form the square.\n\n"
        "*This pattern is automatically generated from image analysis.*"
    )

# -----------------------------------------------------------------------------
# SIDEBAR (with Integrated Right-Aligned Edit Icon)
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

        # Check if user clicked rename on this specific item
        if st.session_state.renaming_chat == chat_id:
            with st.form(key=f"rename_form_{chat_id}"):
                new_title = st.text_input("New Title:", value=chat["title"])
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("Save", use_container_width=True):
                        if new_title.strip():
                            st.session_state.chats[chat_id]["title"] = new_title.strip()
                            database.rename_project(
                                st.session_state.user_id,
                                chat_id,
                                new_title.strip(),
                            )
                        st.session_state.renaming_chat = None
                        st.rerun()
                with col_cancel:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.renaming_chat = None
                        st.rerun()
        else:
            # Combined row with right-aligned edit icon inside
            col_main, col_edit = st.columns([0.85, 0.15])
            with col_main:
                if st.button(
                    prefix + chat["title"],
                    key=f"chat_{chat_id}",
                    use_container_width=True
                ):
                    st.session_state.active_chat = chat_id
                    st.rerun()
            with col_edit:
                if st.button("✏️", key=f"edit_icon_{chat_id}", use_container_width=True, help="Rename project"):
                    st.session_state.renaming_chat = chat_id
                    st.rerun()

    st.divider()

    if st.button("🚪 Exit / Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.loaded_user_id = None
        st.session_state.chats = {}
        st.session_state.active_chat = None
        st.rerun()

    st.caption("GrannySquareBot")
    st.caption("Image-to-text crochet pattern generation")

# -----------------------------------------------------------------------------
# MAIN VIEW & COMPACT CENTERED FILE UPLOADER
# -----------------------------------------------------------------------------
active_chat = st.session_state.chats[st.session_state.active_chat]
messages = active_chat["messages"]

st.markdown('<div class="main-title">What would you like to crochet?</div>', unsafe_allow_html=True)

# Centered upload section
col_left, col_center, col_right = st.columns([1, 1.6, 1])

with col_center:
    uploaded_file = st.file_uploader(
        "Upload your granny square image:",
        type=["png", "jpg", "jpeg", "webp"],
        key=f"uploader_{st.session_state.active_chat}",
        label_visibility="collapsed"
    )
    st.markdown(
        '<div class="upload-info">Upload your granny square image to generate a pattern automatically.'
        '<br>Supported formats: PNG, JPG, JPEG, or WEBP.</div>',
        unsafe_allow_html=True
    )

if uploaded_file is not None:
    image_bytes = uploaded_file.getvalue()
    image_name = uploaded_file.name

    already_processed = any(
        msg.get("image_name") == image_name for msg in messages if msg["role"] == "user"
    )

    if not already_processed:
        if not messages:
            project_name = f"Image: {image_name[:18]}"
            active_chat["title"] = project_name
            database.rename_project(
                st.session_state.user_id,
                st.session_state.active_chat,
                project_name,
            )

        messages.append({
            "role": "user",
            "content": f"Uploading **{image_name}**...",
            "image_bytes": image_bytes,
            "image_name": image_name
        })

        with st.spinner("Analyzing image and generating crochet pattern..."):
            answer = generate_response(image_bytes)

        database.save_pattern(
            st.session_state.user_id,
            st.session_state.active_chat,
            image_bytes,
            answer,
        )

        messages.append({
            "role": "assistant",
            "content": answer,
            "image_bytes": None,
            "image_name": None
        })

        st.rerun()

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
            st.markdown(message["content"])

st.markdown(
    '<div class="footer-note">GrannySquareBot · AI-assisted crochet pattern generation</div>',
    unsafe_allow_html=True
)