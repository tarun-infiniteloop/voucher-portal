import streamlit as st
import requests
import pandas as pd  # add at top once
import base64

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Voucher Portal Demo", layout="wide")

# ---------- HTTP helpers ----------
STATUS_LABEL = {
    "RECEIVED": "Pending Review",
    "QUERY": "Client Clarification",
    "POSTED": "Posted",
}

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

def api_get_bytes(path: str, token: str, params: dict | None = None):
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(f"{API_BASE}{path}", headers=headers, params=params, timeout=120)

def fetch_clients(token: str):
    r = api_get("/firm/clients", token=token)
    if r.status_code != 200:
        return []
    return r.json().get("clients", [])

def api_get_file_bytes(voucher_id: int, token: str):
    return api_get_bytes(f"/vouchers/{voucher_id}/file", token=token, params=None)

def api_patch(path: str, json: dict, token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    return requests.patch(f"{API_BASE}{path}", json=json, headers=headers, timeout=30)

# ---------- UI ----------
st.title("Client Voucher Upload & CA Review Portal")
st.caption("Collect vouchers from clients, raise queries, and export month-wise ZIP for Tally/Busy.")


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
st.subheader("Logged-in User")
c1, c2 = st.columns([4, 1])

with c1:
    if me:
        name = me.get("full_name", "-")
        email = me.get("email", "-")
        role = me.get("role", "-")
        st.markdown(f"**Logged in as:** {name}  \n**Email:** {email}  \n**Role:** `{role}`")
        with st.expander("Show raw session JSON", expanded=False):
            st.json(me)
    else:
        st.warning("Could not load /auth/me")

with c2:
    if st.button("Logout"):
        logout()

st.divider()

role = (me or {}).get("role")

# Tabs: Admin Setup / Client Portal / Admin View
if role == "CLIENT":
    tabs = st.tabs(["👤 Upload Vouchers"])
elif role in ("CA_ADMIN", "ADMIN", "CA"):
    tabs = st.tabs(["🏢 Firm Setup", "📂 Review & Export"])
else:
    tabs = st.tabs([])

# ---------- Tab 1: Admin Setup ----------
if role in ("CA_ADMIN", "ADMIN", "CA"):
    with tabs[0]:
        st.header("Firm Setup")
        st.caption("Create firm, add clients, and create client logins.")

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
if role == "CLIENT":
    with tabs[0]:
        st.header("Upload Vouchers")
        st.caption("Upload purchase/sales/expense/bank vouchers for the selected month.")

        if role != "CLIENT":
            st.warning("Login as CLIENT user to upload vouchers. Use Admin Setup tab to create a client user.")
        else:
            st.subheader("📤 Upload Accounting Vouchers")
            st.caption("Upload bills, invoices, or bank statements for bookkeeping.")

            with st.form("upload_form", clear_on_submit=True):
                fy = st.selectbox("Financial Year", ["2024-25", "2025-26"], index=1)
                # month = st.selectbox("Month", ["2026-01", "2026-02", "2026-03"], index=1)
                month = st.selectbox(
                    "Month",
                    [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 13)],
                    index=0,
                    key="c_upload_month",
                )
                vtype = st.selectbox(
                    "Voucher Category",
                    ["PURCHASE", "SALES", "EXPENSE", "BANK"],
                    index=0
                )
                file = st.file_uploader(
                    "Upload bill / invoice / statement (PDF or image)",
                    type=["pdf", "png", "jpg", "jpeg"]
                )

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

            st.subheader("📂 Uploaded Vouchers")
            st.caption("All vouchers you have uploaded for the selected period.")

            fy_filter = st.selectbox("Filter FY", ["All", "2024-25", "2025-26"], index=0, key="c_fy")
            month_filter = st.selectbox(
                "Filter Month",
                ["All"] + [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 13)],
                index=0,
                key="c_month",
            )


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
                for v in vouchers:
                    v["status_label"] = STATUS_LABEL.get(v.get("status"), v.get("status"))

                if vouchers:
                    total = len(vouchers)
                    pending = sum(1 for v in vouchers if v.get("status") == "RECEIVED")
                    in_query = sum(1 for v in vouchers if v.get("status") == "QUERY")
                    posted = sum(1 for v in vouchers if v.get("status") == "POSTED")

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total", total)
                    m2.metric("Pending review", pending)
                    m3.metric("Need my reply", in_query)
                    m4.metric("Posted", posted)

                st.dataframe(vouchers, use_container_width=True)

            st.subheader("📊 My Voucher Summary")
            r = api_get("/reports/stats", token=st.session_state["token"], params=params)
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
if role in ("CA_ADMIN", "ADMIN", "CA"):
    with tabs[1]:
        st.header("Review & Export")
        st.caption("Review client uploads, raise queries, mark posted, and export month ZIP.")

        if role not in ("CA_ADMIN", "ADMIN", "CA"):
            st.warning("Login as admin to view all firm vouchers.")
        else:
            st.subheader("Filters")
            fy_filter = st.selectbox("FY", ["All", "2024-25", "2025-26"], index=0, key="a_fy")
            month_filter = st.selectbox(
                "Month",
                ["All"] + [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 13)],
                index=0,
                key="a_month"
            )

            clients = fetch_clients(st.session_state["token"])

            client_options = [("All clients", 0)]
            for c in clients:
                label = f'{c["name"]} ({c["code"]})'
                client_options.append((label, c["id"]))

            selected_label = st.selectbox(
                "Client",
                options=[x[0] for x in client_options],
                index=0,
            )

            client_id = dict(client_options).get(selected_label, 0)

            params = {}
            if fy_filter != "All":
                params["fy"] = fy_filter
            if month_filter != "All":
                params["month"] = month_filter
            if client_id > 0:
                params["client_id"] = int(client_id)

            st.subheader("📂 Client Voucher Inbox")
            st.caption("Vouchers uploaded by clients, pending review or posting.")

            r = api_get("/vouchers", token=st.session_state["token"], params=params)
            if r.status_code != 200:
                st.error(r.text)
            else:
                vouchers = r.json().get("vouchers", [])
                # --- Quick Overview metrics ---
                if vouchers:
                    total = len(vouchers)
                    received = sum(1 for v in vouchers if v.get("status") == "RECEIVED")
                    query = sum(1 for v in vouchers if v.get("status") == "QUERY")
                    posted = sum(1 for v in vouchers if v.get("status") == "POSTED")

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total vouchers", total)
                    m2.metric("Received", received)
                    m3.metric("In query", query)
                    m4.metric("Posted", posted)
                else:
                    st.info("No vouchers for selected filters.")

                for v in vouchers:
                    v["status_label"] = STATUS_LABEL.get(v.get("status"), v.get("status"))

                df = pd.DataFrame(vouchers)
                preferred_cols = [c for c in ["id", "client_id", "fy", "month", "vtype", "status_label", "original_filename", "uploaded_at"] if c in df.columns]
                st.dataframe(df[preferred_cols] if preferred_cols else df, use_container_width=True)

                st.divider()
                st.subheader("🧾 Review selected voucher")

                if df.empty:
                    st.info("No vouchers to review.")
                else:
                    # pick a voucher to review
                    selected_vid = st.selectbox(
                        "Select Voucher ID",
                        options=df["id"].tolist(),
                        format_func=lambda x: f"Voucher #{x}",
                        key="review_voucher_id",
                    )

                    # Fetch voucher detail + comments
                    detail = api_get(f"/vouchers/by-id/{int(selected_vid)}", token=st.session_state["token"])
                    if detail.status_code != 200:
                        st.error(f"Could not load voucher detail: {detail.text}")
                    else:
                        payload = detail.json()
                        v = payload["voucher"]
                        comments = payload.get("comments", [])

                        c1, c2 = st.columns([2, 1])

                        with c1:
                            st.markdown(
                                f"""
                                **Voucher ID:** {v["id"]}  
                                **Client ID:** {v["client_id"]}  
                                **FY / Month:** {v["fy"]} / {v["month"]}  
                                **Type:** {v["vtype"]}  
                                **Status:** `{v["status"]}`  
                                **File:** {v["original_filename"]}
                                """
                            )

                        with c2:
                            # Download file
                            file_resp = api_get_file_bytes(int(v["id"]), token=st.session_state["token"])
                            if file_resp.status_code == 200:
                                st.download_button(
                                    "⬇️ Download voucher file",
                                    data=file_resp.content,
                                    file_name=v["original_filename"] or f"voucher_{v['id']}",
                                    mime="application/octet-stream",
                                    use_container_width=True,
                                )
                                show_preview = st.checkbox("👁️ Preview in browser", value=True, key=f"prev_{v['id']}")

                                if show_preview:
                                    ext = (v.get("original_filename") or "").lower()

                                    # Images
                                    if ext.endswith((".png", ".jpg", ".jpeg")):
                                        st.image(file_resp.content, caption=v.get("original_filename"), use_container_width=True)

                                    # PDF (inline iframe)
                                    elif ext.endswith(".pdf"):
                                        b64_pdf = base64.b64encode(file_resp.content).decode("utf-8")
                                        pdf_html = f"""
                                        <iframe
                                            src="data:application/pdf;base64,{b64_pdf}"
                                            width="100%"
                                            height="650px"
                                            style="border:1px solid #ddd; border-radius:8px;"
                                        ></iframe>
                                        """
                                        st.markdown(pdf_html, unsafe_allow_html=True)

                                    else:
                                        st.info("Preview supported only for PDF/JPG/PNG. Use download for other files.")

                            else:
                                st.warning("File not downloadable (missing or access issue).")

                        st.markdown("### 💬 Comments / Clarifications")
                        if comments:
                            for c in comments:
                                st.markdown(f"- **User {c['user_id']}**: {c['message']}  \n  _{c['created_at']}_")
                        else:
                            st.info("No comments yet.")

                        st.markdown("### ✅ CA Actions")

                        colA, colB = st.columns(2)

                        with colA:
                            with st.form("ca_add_comment_form"):
                                msg = st.text_area("Write a comment to client (puts voucher in QUERY automatically)", height=80)
                                submit_comment = st.form_submit_button("Send comment", type="primary")
                                if submit_comment:
                                    r = api_post(
                                        f"/vouchers/{int(v['id'])}/comment",
                                        {"message": msg},
                                        token=st.session_state["token"],
                                    )
                                    if r.status_code == 200:
                                        st.success("Comment added ✅")
                                        st.rerun()
                                    else:
                                        st.error(r.text)

                        with colB:
                            st.caption("Explicit status update (CA only)")
                            new_status = st.selectbox("Set status", ["RECEIVED", "QUERY", "POSTED"], index=2)
                            if st.button("Update status", use_container_width=True):
                                r = api_patch(
                                    f"/vouchers/{int(v['id'])}/status",
                                    {"status": new_status},
                                    token=st.session_state["token"],
                                )
                                if r.status_code == 200:
                                    st.success(f"Updated ✅ {r.json()}")
                                    st.rerun()
                                else:
                                    st.error(r.text)

            st.subheader("🧾 Review Selected Voucher")

            # pick voucher id from the list
            voucher_ids = [v["id"] for v in vouchers] if vouchers else []
            selected_vid = st.selectbox("Select Voucher ID", options=voucher_ids)

            if selected_vid:
                detail = api_get(f"/vouchers/by-id/{selected_vid}", token=st.session_state["token"])
                if detail.status_code != 200:
                    st.error(detail.text)
                else:
                    payload = detail.json()
                    v = payload.get("voucher", {})
                    comments = payload.get("comments", [])

                    st.markdown(f"**File:** {v.get('original_filename')}")
                    st.markdown(f"**Status:** `{v.get('status')}` → {STATUS_LABEL.get(v.get('status'), v.get('status'))}")
                    st.markdown(f"**Stored path:** `{v.get('stored_path')}`")

                    st.write("### Comments")
                    if comments:
                        st.dataframe(comments, use_container_width=True)
                    else:
                        st.info("No comments yet.")

                    st.write("### Actions")

                    colA, colB = st.columns(2)

                    with colA:
                        msg = st.text_area("Ask client / comment", placeholder="E.g., Please upload GST invoice, this is proforma.")
                        if st.button("Send Query to Client (sets status QUERY)"):
                            r = api_post(f"/vouchers/{selected_vid}/comment", {"message": msg}, token=st.session_state["token"])
                            if r.status_code == 200:
                                st.success("Query sent ✅")
                                st.rerun()
                            else:
                                st.error(r.text)

                    with colB:
                        if st.button("Mark as POSTED"):
                            r = requests.patch(
                                f"{API_BASE}/vouchers/{selected_vid}/status",
                                json={"status": "POSTED"},
                                headers={"Authorization": f"Bearer {st.session_state['token']}"},
                                timeout=30,
                            )
                            if r.status_code == 200:
                                st.success("Marked POSTED ✅")
                                st.rerun()
                            else:
                                st.error(r.text)

            st.subheader("⬇️ Export for Accounting (ZIP)")
            st.caption("Download all vouchers for selected client, month, and FY.")

            if client_id <= 0:
                st.info("Select a client to enable export.")
            elif fy_filter == "All" or month_filter == "All":
                st.info("Select FY and Month to enable export.")
            else:
                if st.button("Prepare Month-wise ZIP", type="primary"):
                    r = api_get_bytes("/reports/vouchers-zip", token=st.session_state["token"], params=params)
                    if r.status_code != 200:
                        st.error(f"Export failed ({r.status_code}): {r.text}")
                    else:
                        filename = f"vouchers_client{int(client_id)}_{fy_filter}_{month_filter}.zip"
                        st.download_button(
                            "Download ZIP",
                            data=r.content,
                            file_name=filename,
                            mime="application/zip",
                        )

            st.subheader("📊 Voucher Summary")
            r = api_get("/reports/stats", token=st.session_state["token"], params=params)
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
