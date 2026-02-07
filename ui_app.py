import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Voucher Portal Demo", layout="wide")

# ---------- HTTP helpers ----------
def api_post(path: str, json: dict, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(f"{API_BASE}{path}", json=json, headers=headers, timeout=30)

def api_get(path: str, token: str | None = None, params: dict | None = None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.get(f"{API_BASE}{path}", headers=headers, params=params, timeout=30)

def api_post_multipart(path: str, data: dict, files: dict, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.post(
        f"{API_BASE}{path}",
        data=data,
        files=files,
        headers=headers,
        timeout=60,
    )

def logout():
    for k in ["token", "me"]:
        st.session_state.pop(k, None)
    st.success("Logged out.")
    st.rerun()

def ensure_me():
    token = st.session_state.get("token")
    if not token:
        return None
    me = st.session_state.get("me")
    if me:
        return me
    r = api_get("/auth/me", token=token)
    if r.status_code == 200:
        st.session_state["me"] = r.json()
        return st.session_state["me"]
    return None

# ---------- UI ----------
st.title("Voucher Portal — Demo UI")

with st.expander("API status", expanded=False):
    try:
        r = api_get("/health")
        st.code(r.json())
    except Exception as e:
        st.error(f"API not reachable: {e}")

token = st.session_state.get("token")
me = ensure_me()

# ---------- Login block ----------
if not token:
    st.subheader("Login")

    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Email", value="admin@cadsk.local")
    with col2:
        password = st.text_input("Password", type="password", value="admin123")

    if st.button("Login", type="primary"):
        r = api_post("/auth/login", {"email": email, "password": password})
        if r.status_code != 200:
            st.error(f"Login failed ({r.status_code}): {r.text}")
        else:
            st.session_state["token"] = r.json()["access_token"]
            # load me
            ensure_me()
            st.success("Login successful.")
            st.rerun()

    st.info("Tip: If login fails after DB reset, run seed again: `python -m app.db.seed_admin`")
    st.stop()

# ---------- Logged in ----------
st.subheader("Session")
c1, c2 = st.columns([3, 1])
with c1:
    st.code(me if me else {"note": "Could not load /auth/me"})
with c2:
    if st.button("Logout"):
        logout()

st.divider()

role = (me or {}).get("role")

# Tabs: Admin Setup / Client Portal / Admin View
tabs = st.tabs(["🏢 Admin Setup", "👤 Client Portal", "📂 Admin View"])

# ---------- Tab 1: Admin Setup ----------
with tabs[0]:
    st.header("Admin Setup (create firm, client, client user)")

    if role not in ("CA_ADMIN", "ADMIN", "CA"):
        st.warning("Login as admin (seeded user) to use setup.")
    else:
        st.subheader("1) Create Firm")
        with st.form("create_firm_form"):
            firm_name = st.text_input("Firm Name", value="Demo CA Firm")
            submitted = st.form_submit_button("Create Firm")
            if submitted:
                r = api_post("/firm", {"name": firm_name}, token=st.session_state["token"])
                if r.status_code == 200:
                    st.success(f"Firm created ✅ {r.json()}")
                else:
                    st.error(r.text)

        st.subheader("2) List Firm")
        if st.button("Refresh Firm Info"):
            r = api_get("/firm", token=st.session_state["token"])
            if r.status_code == 200:
                st.code(r.json())
            else:
                st.error(r.text)

        st.subheader("3) Create Client")
        with st.form("create_client_form"):
            client_name = st.text_input("Client Name", value="Ravi Traders")
            client_code = st.text_input("Client Code", value="RAVI")
            submitted = st.form_submit_button("Create Client")
            if submitted:
                r = api_post(
                    "/firm/clients",
                    {"name": client_name, "code": client_code},
                    token=st.session_state["token"],
                )
                if r.status_code == 200:
                    st.success(f"Client created ✅ {r.json()}")
                else:
                    st.error(r.text)

        st.subheader("4) Create Client User (login user for client)")
        with st.form("create_client_user_form"):
            client_id = st.number_input("Client ID", min_value=1, step=1, value=1)
            cu_email = st.text_input("Client User Email", value="client1@test.com")
            cu_name = st.text_input("Client User Full Name", value="Ravi (Client)")
            cu_password = st.text_input("Client User Password", type="password", value="client123")
            submitted = st.form_submit_button("Create Client User")
            if submitted:
                r = api_post(
                    "/users/create-client-user",
                    {
                        "client_id": int(client_id),
                        "email": cu_email,
                        "full_name": cu_name,
                        "password": cu_password,
                    },
                    token=st.session_state["token"],
                )
                if r.status_code == 200:
                    st.success(f"Client user created ✅ {r.json()}")
                else:
                    st.error(r.text)

        st.info("After creating client user, go to Client Portal tab and login with that email/password.")

# ---------- Tab 2: Client Portal ----------
with tabs[1]:
    st.header("Client Portal (upload + list + stats)")

    if role != "CLIENT":
        st.warning("Login as CLIENT user to upload vouchers. Use Admin Setup tab to create a client user.")
    else:
        st.subheader("📤 Upload Voucher")

        with st.form("upload_form", clear_on_submit=True):
            fy = st.selectbox("Financial Year", ["2024-25", "2025-26"], index=1)
            month = st.selectbox("Month", ["2026-01", "2026-02", "2026-03"], index=1)
            vtype = st.selectbox("Voucher Type", ["PURCHASE", "SALES", "EXPENSE", "BANK"], index=0)
            file = st.file_uploader("Voucher file (PDF/image)", type=["pdf", "png", "jpg", "jpeg"])
            submitted = st.form_submit_button("Upload", type="primary")

            if submitted:
                if not file:
                    st.error("Please select a file")
                else:
                    with st.spinner("Uploading..."):
                        r = api_post_multipart(
                            "/vouchers/upload",
                            data={"fy": fy, "month": month, "vtype": vtype},
                            files={"file": (file.name, file.getvalue())},
                            token=st.session_state["token"],
                        )
                    if r.status_code == 200:
                        st.success(f"Uploaded ✅ {r.json()}")
                    else:
                        st.error(f"Upload failed ({r.status_code}): {r.text}")

        st.subheader("📂 My Vouchers")
        fy_filter = st.selectbox("Filter FY", ["All", "2024-25", "2025-26"], index=0, key="c_fy")
        month_filter = st.selectbox("Filter Month", ["All", "2026-01", "2026-02", "2026-03"], index=0, key="c_month")

        params = {}
        if fy_filter != "All":
            params["fy"] = fy_filter
        if month_filter != "All":
            params["month"] = month_filter

        r = api_get("/vouchers", token=st.session_state["token"], params=params)
        if r.status_code != 200:
            st.error(r.text)
        else:
            vouchers = r.json().get("vouchers", [])
            st.dataframe(vouchers, use_container_width=True)

        st.subheader("📊 My Voucher Summary")
        r = api_get("/vouchers/stats", token=st.session_state["token"], params=params)
        if r.status_code != 200:
            st.error(r.text)
        else:
            summary = r.json().get("summary", [])
            if not summary:
                st.info("No data")
            else:
                cols = st.columns(4)
                for i, row in enumerate(summary):
                    cols[i % 4].metric(row["vtype"], row["total"])

# ---------- Tab 3: Admin View ----------
with tabs[2]:
    st.header("Admin View (list vouchers + stats per client)")

    if role not in ("CA_ADMIN", "ADMIN", "CA"):
        st.warning("Login as admin to view all firm vouchers.")
    else:
        st.subheader("Filters")
        fy_filter = st.selectbox("FY", ["All", "2024-25", "2025-26"], index=0, key="a_fy")
        month_filter = st.selectbox("Month", ["All", "2026-01", "2026-02", "2026-03"], index=0, key="a_month")
        client_id = st.number_input("Client ID (optional)", min_value=0, step=1, value=0)

        params = {}
        if fy_filter != "All":
            params["fy"] = fy_filter
        if month_filter != "All":
            params["month"] = month_filter
        if client_id > 0:
            params["client_id"] = int(client_id)

        st.subheader("📂 Vouchers")
        r = api_get("/vouchers", token=st.session_state["token"], params=params)
        if r.status_code != 200:
            st.error(r.text)
        else:
            vouchers = r.json().get("vouchers", [])
            st.dataframe(vouchers, use_container_width=True)

        st.subheader("📊 Voucher Summary")
        r = api_get("/vouchers/stats", token=st.session_state["token"], params=params)
        if r.status_code != 200:
            st.error(r.text)
        else:
            summary = r.json().get("summary", [])
            if not summary:
                st.info("No data")
            else:
                cols = st.columns(4)
                for i, row in enumerate(summary):
                    cols[i % 4].metric(row["vtype"], row["total"])
