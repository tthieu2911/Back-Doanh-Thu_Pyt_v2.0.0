import streamlit as st
import pandas as pd
import io
from datetime import date, timedelta

st.set_page_config(layout="wide", page_title="Excel Filter & Mapping (Enhanced)")

OPERATORS = ["=", "!=", "<", ">", "<=", ">=", "contains", "begins with", "ends with"]

# -------------------------
# User-provided desired output header names (from your message)
# -------------------------
DESIRED_OUTPUT_HEADERS = [
    "NGAY", "SOHD", "SERI", "MẪU SỐ", "DIENGIAI", "BOPHAN", "MA NHAP XUAT",
    "TK NO", "MADV", "TK CO", "DVT", "SOLUONG", "DONGIA", "MALOAIVAT",
    "TK CO VAT", "MAKH", "THANHTIEN", "THUEVAT", "TONGTIEN", "LOẠI TIỀN",
    "THANHTIEN NT", "THUEVAT NT", "TỶ GIÁ"
]

# -------------------------
# Helpers
# -------------------------
def read_workbook_build_headers(file_bytes):
    wb = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, header=None, dtype=object)
    # ensure at least 8 rows
    while wb.shape[0] < 8:
        wb = wb.append(pd.Series([None]*wb.shape[1]), ignore_index=True)
    max_col = min(wb.shape[1], 26)
    row7 = wb.iloc[6, :max_col].fillna("").astype(str)
    row8 = wb.iloc[7, :max_col].fillna("").astype(str)
    headers = []
    for i in range(max_col):
        a = row7.iat[i].strip()
        b = row8.iat[i].strip()
        if a and b:
            hh = f"{a} {b}".strip()
        elif a:
            hh = a
        elif b:
            hh = b
        else:
            hh = f"Column_{i+1}"
        headers.append(hh)
    # data starts row 9 => index 8
    if wb.shape[0] > 8:
        data = wb.iloc[8:, :max_col].reset_index(drop=True)
        data.columns = headers
    else:
        data = pd.DataFrame(columns=headers)
    return data, headers

def is_number_like(x):
    try:
        float(x)
        return True
    except:
        return False

def apply_single_filter(df, column, op, cond):
    if column not in df.columns:
        return pd.Series([False]*len(df), index=df.index)
    series = df[column]
    if op in ("=", "!=", "<", ">", "<=", ">="):
        if is_number_like(cond):
            cond_val = float(cond)
            ser_num = pd.to_numeric(series, errors='coerce')
            if op == "=": return ser_num == cond_val
            if op == "!=": return ser_num != cond_val
            if op == "<": return ser_num < cond_val
            if op == ">": return ser_num > cond_val
            if op == "<=": return ser_num <= cond_val
            if op == ">=": return ser_num >= cond_val
        else:
            s = series.fillna("").astype(str)
            if op == "=": return s == str(cond)
            if op == "!=": return s != str(cond)
            if op == "<": return s < str(cond)
            if op == ">": return s > str(cond)
            if op == "<=": return s <= str(cond)
            if op == ">=": return s >= str(cond)
    if op == "contains":
        return series.fillna("").astype(str).str.contains(str(cond), case=False, na=False)
    if op == "begins with":
        return series.fillna("").astype(str).str.startswith(str(cond), na=False)
    if op == "ends with":
        return series.fillna("").astype(str).str.endswith(str(cond), na=False)
    return pd.Series([False]*len(df), index=df.index)

def apply_filters(df, filters):
    if df is None or df.empty:
        return df
    mask = pd.Series([True]*len(df), index=df.index)
    for f in filters:
        if not f.get("col"): continue
        mask = mask & apply_single_filter(df, f["col"], f["op"], f["val"])
    return df[mask]

def compute_sum_formula(df, formula_str):
    """ parse 'A + B + 100' where tokens either column names or numeric literals """
    tokens = [t.strip() for t in formula_str.split("+") if t.strip()]
    if not tokens:
        return pd.Series([None]*len(df), index=df.index)
    parts = []
    for t in tokens:
        if t in df.columns:
            parts.append(pd.to_numeric(df[t], errors='coerce').fillna(0))
        else:
            try:
                num = float(t)
                parts.append(pd.Series([num]*len(df), index=df.index))
            except:
                # unknown token -> NaN series
                return pd.Series([None]*len(df), index=df.index)
    s = parts[0]
    for p in parts[1:]:
        s = s + p
    return s

def last_day_of_last_month():
    today = date.today()
    first_of_current = date(today.year, today.month, 1)
    last_of_prev = first_of_current - timedelta(days=1)
    return last_of_prev

# -------------------------
# Session state init
# -------------------------
if "bytes" not in st.session_state: st.session_state["bytes"] = None
if "df" not in st.session_state: st.session_state["df"] = None
if "cols" not in st.session_state: st.session_state["cols"] = []
if "filters" not in st.session_state: st.session_state["filters"] = []
if "mappings" not in st.session_state:
    # initialize mapping entries with default mode 'select input' empty
    st.session_state["mappings"] = [{
        "out_name": name,
        "mode": "select input",   # select input | fixed | calculate | currency_rule
        "input_col": None,
        "fixed_value": "",
        "formula": ""
    } for name in DESIRED_OUTPUT_HEADERS]

# -------------------------
# UI
# -------------------------
st.title("Excel Filter & Output Mapping — Vietnam format")

left, right = st.columns([1, 2])

with left:
    st.header("1) IMPORT")
    uploaded = st.file_uploader("Upload Excel (A7:Z8 will be used to build headers)", type=["xlsx","xls","xlsm"])
    if uploaded:
        st.session_state["bytes"] = uploaded.read()
        st.success("File loaded")
        df, cols = read_workbook_build_headers(st.session_state["bytes"])
        st.session_state["df"] = df
        st.session_state["cols"] = cols

    if st.session_state["df"] is not None:
        st.write("Detected input columns:")
        st.write(st.session_state["cols"])
    else:
        st.info("Please upload file to continue")

with right:
    st.header("2) Filter Conditions (AND)")
    if st.session_state["cols"]:
        if st.button("➕ Add filter"):
            st.session_state["filters"].append({"col": st.session_state["cols"][0], "op": "=", "val": ""})
        if st.button("Clear filters"):
            st.session_state["filters"] = []

        for i, f in enumerate(st.session_state["filters"]):
            c1, c2, c3, c4 = st.columns([3,2,3,1])
            with c1:
                sel = st.selectbox(f"Column {i+1}", st.session_state["cols"], index=st.session_state["cols"].index(f["col"]) if f["col"] in st.session_state["cols"] else 0, key=f"fil_col_{i}")
                st.session_state["filters"][i]["col"] = sel
            with c2:
                opc = st.selectbox(f"Op {i+1}", OPERATORS, index=OPERATORS.index(f["op"]) if f["op"] in OPERATORS else 0, key=f"fil_op_{i}")
                st.session_state["filters"][i]["op"] = opc
            with c3:
                v = st.text_input(f"Val {i+1}", value=f.get("val",""), key=f"fil_val_{i}")
                st.session_state["filters"][i]["val"] = v
            with c4:
                if st.button("Remove", key=f"fil_rm_{i}"):
                    st.session_state["filters"].pop(i)
                    st.experimental_rerun()
    else:
        st.info("Upload file to create filters")

st.markdown("---")
st.header("3) Output Mapping (choose input / fixed / calculation)")

st.write("For each desired output header (pre-filled), choose an input column, or Fixed value, or Calculate (SUM), or Currency rule")
st.write("Currency rule will produce 'VND' when ExchangeRate == 1, else 'USD'.")

# mapping UI
for idx, m in enumerate(st.session_state["mappings"]):
    cols_ui = st.columns([2, 2, 2, 2, 2])
    with cols_ui[0]:
        st.markdown(f"**{m['out_name']}**")
    with cols_ui[1]:
        mode = st.selectbox(f"Mode_{idx}", ["select input", "fixed", "calculate", "currency_rule"], index=["select input","fixed","calculate","currency_rule"].index(m.get("mode","select input")), key=f"map_mode_{idx}")
        st.session_state["mappings"][idx]["mode"] = mode
    with cols_ui[2]:
        if mode == "select input":
            input_choice = st.selectbox(f"Input col_{idx}", ["(none)"] + st.session_state["cols"], index=(["(none)"] + st.session_state["cols"]).index(m.get("input_col") if m.get("input_col") else "(none)"), key=f"map_in_{idx}")
            st.session_state["mappings"][idx]["input_col"] = input_choice if input_choice != "(none)" else None
        elif mode == "fixed":
            fx = st.text_input(f"Fixed value_{idx}", value=m.get("fixed_value",""), key=f"map_fix_{idx}")
            st.session_state["mappings"][idx]["fixed_value"] = fx
        elif mode == "calculate":
            ph = "e.g. Doanh thu + Tiền thuế  OR  100 + ColA"
            form = st.text_input(f"SUM formula_{idx}", value=m.get("formula",""), placeholder=ph, key=f"map_form_{idx}")
            st.session_state["mappings"][idx]["formula"] = form
        elif mode == "currency_rule":
            st.write("Currency rule: ExchangeRate == 1 -> 'VND' else 'USD'")

st.markdown("---")
st.header("4) Preview & EXPORT")

if st.session_state["df"] is None:
    st.info("Upload file first")
else:
    df0 = st.session_state["df"]
    st.subheader("Raw preview (first 10 rows)")
    st.dataframe(df0.head(10))

    st.subheader("Filtered preview")
    filtered = apply_filters(df0, st.session_state["filters"])
    st.write(f"Rows after filter: {len(filtered)} / {len(df0)}")
    st.dataframe(filtered.head(10))

    # Build output according to mappings
    out_df = pd.DataFrame(index=filtered.index)
    for m in st.session_state["mappings"]:
        name = m["out_name"]
        mode = m["mode"]
        if mode == "select input":
            incol = m.get("input_col")
            if incol and incol in filtered.columns:
                out_df[name] = filtered[incol]
            else:
                out_df[name] = pd.Series([None]*len(filtered), index=filtered.index)
        elif mode == "fixed":
            val = m.get("fixed_value","")
            # special fixed value token 'LAST_DAY_PREV_MONTH' if user types that or we provide button later
            if val.strip().lower() == "last_day_prev_month" or val.strip().lower() == "last_day_of_last_month":
                out_df[name] = pd.Series([last_day_of_last_month().strftime("%Y-%m-%d")] * len(filtered), index=filtered.index)
            else:
                out_df[name] = pd.Series([val]*len(filtered), index=filtered.index)
        elif mode == "calculate":
            formula = m.get("formula","")
            out_df[name] = compute_sum_formula(filtered, formula)
        elif mode == "currency_rule":
            # uses ExchangeRate column if present; default column name guessed earlier is 'ExchangeRate'
            ex_col_candidates = [c for c in filtered.columns if c.lower().replace(" ", "") in ("exchangerate","tygia","tỷgia","tigia")]
            ex_col = ex_col_candidates[0] if ex_col_candidates else None
            if ex_col:
                ex_ser = pd.to_numeric(filtered[ex_col], errors='coerce').fillna(0)
                out_df[name] = ex_ser.apply(lambda x: "VND" if x == 1 else "USD")
            else:
                # if no exchange column, fill blank
                out_df[name] = pd.Series([None]*len(filtered), index=filtered.index)

    st.subheader("Output preview (first 10 rows)")
    st.dataframe(out_df.head(10))

    # EXPORT
    if st.button("EXPORT to Excel"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            out_df.to_excel(writer, index=False, sheet_name="Export")
        st.session_state["export_bytes"] = buffer.getvalue()
        st.success("Export ready — click download button below")

    if st.session_state.get("export_bytes", None):
        st.download_button("Download exported file", data=st.session_state["export_bytes"], file_name="exported.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("----")
st.caption("Notes: For a fixed column that should be 'last day of last month' type 'last_day_of_last_month' as the fixed value (the app will format it). For calculate mode use '+' only. Currency rule uses ExchangeRate-like column if detected.")