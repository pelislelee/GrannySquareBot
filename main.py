
import streamlit as st
from PIL import Image
from io import BytesIO
from datetime import datetime
import uuid

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="GrannySquareBot",
    page_icon="🧶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>
/* General page */
.stApp {
    background-color: #ffffff;
    color: #252525;
}

header[data-testid="stHeader"] {
    background-color: #ffffff;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #f7f7f8;
    border-right: 1px solid #e5e5e5;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.2rem;
}

.brand {
    font-size: 23px;
    font-weight: 750;
    letter-spacing: -0.8px;
    color: #262626;
    margin-bottom: 4px;
}

.brand-subtitle {
    font-size: 12px;
    color: #777777;
    margin-bottom: 24px;
}

.section-label {
    font-size: 12px;
    font-weight: 600;
    color: #888888;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 20px 0 8px 4px;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid #e5e5e5;
    min-height: 42px;
    text-align: left;
    transition: background-color 0.2s ease;
}

.stButton > button:hover {
    border-color: #b7a5d8;
    color: #5e4789;
}

/* Main chat area */
.main-title {
    font-size: 25px;
    font-weight: 650;
    letter-spacing: -0.6px;
    color: #262626;
    text-align: center;
    margin-top: 55px;
    margin-bottom: 8px;
}

.main-subtitle {
    text-align: center;
    font-size: 14px;
    color: #858585;
    margin-bottom: 32px;
}

.welcome-card {
    background: #faf9fc;
    border: 1px solid #ece7f4;
    border-radius: 16px;
    padding: 22px;
    margin: 10px auto;
    max-width: 650px;
}

.welcome-card h3 {
    font-size: 17px;
    margin-bottom: 8px;
    color: #383044;
}

.welcome-card p {
    font-size: 14px;
    line-height: 1.7;
    color: #66616e;
    margin-bottom: 0;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 14px;
    padding: 14px 16px;
}

/* Chat input */
[data-testid="stChatInput"] {
    border-radius: 18px;
}

[data-testid="stChatInput"] textarea {
    font-size: 15px;
}

/* Footer */
.footer-note {
    color: #999999;
    text-align: center;
    font-size: 11px;
    margin-top: 12px;
}

/* Images */
[data-testid="stImage"] img {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

def create_chat():
    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "Obrolan baru",
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "messages": []
    }

    st.session_state.active_chat = chat_id


if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat" not in st.session_state:
    create_chat()


# =========================================================
# MODEL RESPONSE
# =========================================================

def generate_response(image_bytes, prompt):
    """
    TEMPORARY RESPONSE.

    Replace this function with your trained LLaVA inference code.

    Parameters
    ----------
    image_bytes : bytes or None
        Image uploaded by the user.
    prompt : str
        User's instruction.

    Returns
    -------
    str
        Generated crochet pattern.
    """

    if image_bytes is None:
        return (
            "Silakan unggah gambar granny square terlebih dahulu "
            "agar saya dapat membantu membuat pola rajutannya."
        )

    if not prompt.strip():
        prompt = (
            "Write the step-by-step crochet pattern instructions "
            "for this granny square."
        )

    # TODO:
    # 1. Load your trained LLaVA model and LoRA adapter.
    # 2. Process image_bytes into a PIL image.
    # 3. Pass the image and prompt to the model.
    # 4. Decode and return the generated pattern.

    return (
        "**Contoh hasil pola rajutan**\n\n"
        "Gambar berhasil diterima. Hubungkan fungsi ini dengan "
        "model LLaVA yang sudah dilatih untuk menghasilkan pola "
        "sesuai gambar.\n\n"
        "**Base:** Make a magic ring.\n\n"
        "**Round 1:** Chain 3, then work 2 double crochet stitches "
        "into the ring. Chain 2 to form a corner. Repeat the "
        "appropriate stitch sequence to form the square.\n\n"
        "*Catatan: Ini hanya contoh tampilan, bukan pola yang "
        "dihasilkan dari analisis gambar.*"
    )


# =========================================================
# LEFT SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="brand">🧶 GrannySquareBot</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="brand-subtitle">'
        'Your AI crochet pattern assistant'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "＋  Obrolan Baru",
        use_container_width=True,
        type="primary"
    ):
        create_chat()
        st.rerun()

    st.markdown(
        '<div class="section-label">Riwayat Obrolan</div>',
        unsafe_allow_html=True
    )

    # Newest chats first
    chat_ids = sorted(
        st.session_state.chats.keys(),
        key=lambda cid: st.session_state.chats[cid]["created_at"],
        reverse=True
    )

    if not chat_ids:
        st.caption("Belum ada riwayat obrolan.")

    for chat_id in chat_ids:
        chat = st.session_state.chats[chat_id]

        # Highlight active conversation
        prefix = "● " if chat_id == st.session_state.active_chat else "　"

        if st.button(
            prefix + chat["title"],
            key=f"chat_{chat_id}",
            use_container_width=True
        ):
            st.session_state.active_chat = chat_id
            st.rerun()

    st.divider()

    st.caption("GrannySquareBot")
    st.caption("Image-to-text crochet pattern generation")


# =========================================================
# ACTIVE CHAT
# =========================================================

active_chat = st.session_state.chats[
    st.session_state.active_chat
]

messages = active_chat["messages"]


# =========================================================
# WELCOME SCREEN
# =========================================================

if not messages:

    st.markdown(
        '<div class="main-title">Apa yang ingin kamu rajut?</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Unggah gambar granny square dan buat pola rajutan '
        'langkah demi langkah.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="welcome-card">
        <h3>🧶 Crochet Pattern Generator</h3>
        <p>
            Kirim gambar motif rajutan yang ingin kamu buat.
            GrannySquareBot dirancang untuk membantu menyusun
            instruksi rajutan berdasarkan gambar, mulai dari
            bagian dasar hingga setiap putaran.
        </p>
    </div>
    """, unsafe_allow_html=True)

else:

    # =====================================================
    # DISPLAY CHAT HISTORY
    # =====================================================

    for message in messages:

        with st.chat_message(
            message["role"],
            avatar="🧶" if message["role"] == "assistant" else "👤"
        ):

            if message.get("content"):
                st.markdown(message["content"])

            if message.get("image_bytes"):
                st.image(
                    Image.open(BytesIO(message["image_bytes"])),
                    caption=message.get("image_name", "Uploaded image"),
                    width=320
                )


# =========================================================
# CHAT INPUT WITH IMAGE UPLOAD
# =========================================================

chat_input = st.chat_input(
    "Ketik pesan atau unggah gambar granny square...",
    accept_file="multiple",
    file_type=["png", "jpg", "jpeg", "webp"],
    key="chat_composer"
)


# =========================================================
# HANDLE USER MESSAGE
# =========================================================

if chat_input is not None:

    prompt = (chat_input.text or "").strip()
    uploaded_files = list(chat_input.files or [])

    # Allow text-only messages or image uploads
    if prompt or uploaded_files:

        # For this example, process the first uploaded image
        uploaded_file = uploaded_files[0] if uploaded_files else None

        image_bytes = (
            uploaded_file.getvalue()
            if uploaded_file is not None
            else None
        )

        image_name = (
            uploaded_file.name
            if uploaded_file is not None
            else None
        )

        # Set conversation title from first message
        if not messages:
            if prompt:
                active_chat["title"] = prompt[:32]
            elif image_name:
                active_chat["title"] = f"Gambar: {image_name[:24]}"

        # Save user message
        user_message = {
            "role": "user",
            "content": prompt,
            "image_bytes": image_bytes,
            "image_name": image_name
        }

        messages.append(user_message)

        # Generate assistant response
        with st.spinner("Menyiapkan pola rajutan..."):
            answer = generate_response(image_bytes, prompt)

        messages.append({
            "role": "assistant",
            "content": answer,
            "image_bytes": None,
            "image_name": None
        })

        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    '<div class="footer-note">'
    'GrannySquareBot · AI-assisted crochet pattern generation'
    '</div>',
    unsafe_allow_html=True
)
