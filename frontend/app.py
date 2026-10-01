"""
SecureRAG Streamlit Frontend Dashboard.

Provides interactive UI for tenant user switching, document uploading,
permission-aware RAG question answering, and source citation inspection.
"""

import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="SecureRAG - Permission-Aware Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern executive aesthetic
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .user-badge {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 20px;
        font-weight: 500;
    }
    .source-box {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 8px 12px;
        margin-top: 8px;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to fetch demo users from backend
@st.cache_data(ttl=60)
def fetch_demo_users():
    try:
        res = requests.get(f"{API_BASE_URL}/users", timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    # Local fallback if API loading
    return [
        {"user_id": "rahul", "name": "Rahul (HR)", "tenant_id": "company_a", "role": "HR"},
        {"user_id": "amit", "name": "Amit (Engineering)", "tenant_id": "company_a", "role": "ENGINEERING"},
        {"user_id": "admin_a", "name": "Admin A (System Admin)", "tenant_id": "company_a", "role": "ADMIN"},
        {"user_id": "neha", "name": "Neha (HR)", "tenant_id": "company_b", "role": "HR"},
        {"user_id": "admin_b", "name": "Admin B (System Admin)", "tenant_id": "company_b", "role": "ADMIN"}
    ]

demo_users = fetch_demo_users()

# SIDEBAR: User Identity & Document Upload
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shield-together.png", width=64)
    st.title("User Context")

    user_names = [u["name"] for u in demo_users]
    selected_name = st.selectbox("Select User Identity:", user_names, index=0)

    # Resolve active user dict
    current_user = next(u for u in demo_users if u["name"] == selected_name)

    st.markdown("---")
    st.markdown("### Active Context Details")
    st.markdown(f"**User ID:** `{current_user['user_id']}`")
    st.markdown(f"**Tenant:** `{current_user['tenant_id'].upper()}`")
    st.markdown(f"**Role:** `{current_user['role']}`")
    st.markdown("---")

    st.subheader("Upload PDF Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    dept = st.selectbox("Document Department", ["HR", "ENGINEERING", "FINANCE", "GENERAL"])
    roles_options = ["HR", "ENGINEERING", "FINANCE", "ADMIN"]
    selected_roles = st.multiselect("Allowed Roles", roles_options, default=[current_user["role"], "ADMIN"])

    if st.button("Upload & Index Document", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please select a PDF file to upload.")
        else:
            with st.spinner("Processing PDF, generating embeddings, and indexing FAISS..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                data = {
                    "user_id": current_user["user_id"],
                    "tenant_id": current_user["tenant_id"],
                    "role": current_user["role"],
                    "department": dept,
                    "allowed_roles": ",".join(selected_roles) if selected_roles else "ADMIN"
                }

                try:
                    res = requests.post(f"{API_BASE_URL}/documents/upload", files=files, data=data, timeout=60)
                    if res.status_code == 200:
                        out = res.json()
                        st.success(f"Indexed **{out['document_name']}**! ({out['chunks_count']} chunks)")
                    else:
                        st.error(f"Upload failed: {res.json().get('detail', res.text)}")
                except Exception as err:
                    st.error(f"Could not connect to backend server: {err}")

# MAIN AREA
st.markdown("<div class='main-title'>🛡️ SecureRAG Intelligence Platform</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Permission-Aware Multi-Tenant Document Retrieval & Generation</div>", unsafe_allow_html=True)

# User Identity Banner
st.markdown(f"""
<div class='user-badge'>
    Logged in as <b>{current_user['name']}</b> | Tenant ID: <b>{current_user['tenant_id']}</b> | Role: <b>{current_user['role']}</b>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💬 Query & Chat", "📄 Accessible Documents Catalog"])

with tab1:
    st.markdown("#### Ask a Question About Authorized Documents")
    
    question = st.text_input(
        "Enter your query:",
        placeholder="e.g. What is the annual paid leave policy?",
        key="user_query"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        top_k = st.number_input("Top Chunks (k)", min_value=1, max_value=10, value=4)

    if st.button("Submit Question", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Performing permission-filtered retrieval & Groq LLM reasoning..."):
                payload = {
                    "user_id": current_user["user_id"],
                    "tenant_id": current_user["tenant_id"],
                    "role": current_user["role"],
                    "question": question,
                    "top_k": top_k
                }

                try:
                    res = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=30)
                    if res.status_code == 200:
                        response_data = res.json()
                        answer = response_data.get("answer", "")
                        sources = response_data.get("sources", [])
                        chunks = response_data.get("chunks", [])

                        st.markdown("---")
                        st.markdown("### Answer")
                        st.write(answer)

                        # Display Sources
                        st.markdown("### 📌 Source Citations")
                        if sources:
                            for s in sources:
                                st.markdown(f"""
                                <div class='source-box'>
                                    📄 <b>{s['document_name']}</b> — Page {s['page']} (Dept: {s.get('department', 'N/A')})
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No sources retrieved or authorized for this query.")

                        # Debug / Preview retrieved chunks
                        with st.expander("🔍 Preview Retrieved Authorized Chunks (Debug / Inspection)"):
                            st.write(f"Total Authorized Chunks Retrieved: **{len(chunks)}**")
                            for idx, c in enumerate(chunks, 1):
                                st.markdown(f"**Chunk #{idx}** (Tenant: `{c['metadata'].get('tenant_id')}`, Allowed Roles: `{c['metadata'].get('allowed_roles')}`)")
                                st.code(c['content'], language="text")

                    else:
                        st.error(f"Error ({res.status_code}): {res.json().get('detail', res.text)}")
                except Exception as e:
                    st.error(f"Failed to communicate with backend API: {e}")

with tab2:
    st.markdown("#### Documents Accessible to Your Role in This Tenant")
    if st.button("Refresh Catalog"):
        st.cache_data.clear()

    try:
        res = requests.get(
            f"{API_BASE_URL}/documents",
            params={"tenant_id": current_user["tenant_id"], "user_id": current_user["user_id"], "role": current_user["role"]},
            timeout=5
        )
        if res.status_code == 200:
            docs = res.json()
            if docs:
                st.dataframe(docs, use_container_width=True)
            else:
                st.info("No documents uploaded yet for this tenant/role.")
        else:
            st.error("Failed to load document catalog.")
    except Exception as e:
        st.error(f"Could not reach backend API: {e}")
