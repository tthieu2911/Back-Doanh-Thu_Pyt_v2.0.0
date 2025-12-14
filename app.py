# app.py
import streamlit as st
import pandas as pd
import io
import uuid
import json
import copy
from datetime import date, timedelta
from pathlib import Path

st.set_page_config(layout="wide", page_title="Excel Filter & Mapping (Vietnam)")

# =========================================================
# CONSTANTS
# =========================================================
OPERATORS = [
    "=", "!=", "<", ">", "<=", ">=",
    "contains", "not contains",
    "begins with", "not begins with",
    "ends with", "not ends with"
]

DESIRED_OUTPUT_HEADERS = [
    "NGAY", "SOHD", "SERI", "MẪU SỐ", "DIENGIAI", "BOPHAN", "MA NHAP XUAT",
    "TK NO", "MADV", "TK CO", "DVT", "SOLUONG", "DONGIA", "MALOAIVAT",
    "TK CO VAT", "MAKH", "THANHTIEN", "THUEVAT", "TONGTIEN", "LOẠI TIỀN",
    "THANHTIEN NT", "THUEVAT NT", "TỶ GIÁ"
]

DEFAULT_MAPPING = [
    {"out_name": "NGAY", "mode": "fixed", "fixed_value": "last_day_of_last_month"},
    {"out_name": "SOHD", "mode": "select input", "input_col": "Số Chứng từ"},
    {"out_name": "SERI", "mode": "select input", "input_col": "Ký hiệu"},
    {"out_name": "MẪU SỐ", "mode": "select input", "input_col": "Mẫu số"},
    {"out_name": "DIENGIAI", "mode": "select input", "input_col": "Diễn giải"},
    {"out_name": "BOPHAN", "mode": "select input", "input_col": "DeptCode"},
    {"out_name": "MA NHAP XUAT", "mode": "select input", "input_col": "TransCode"},
    {"out_name": "TK NO", "mode": "fixed", "fixed_value": "1310"},
    {"out_name": "MADV", "mode": "select input", "input_col": "Vật tư"},
    {"out_name": "TK CO", "mode": "select input", "input_col": "CreditAccount2"},
    {"out_name": "DVT", "mode": "fixed", "fixed_value": "-"},
    {"out_name": "SOLUONG", "mode": "fixed", "fixed_value": "-"},
    {"out_name": "DONGIA", "mode": "fixed", "fixed_value": "-"},
    {"out_name": "MALOAIVAT", "mode": "select input", "input_col": "TaxCode"},
    {"out_name": "TK CO VAT", "mode": "select input", "input_col": "CreditAccount3"},
    {"out_name": "MAKH", "mode": "select input", "input_col": "Đối tượng"},
    {"out_name": "THANHTIEN", "mode": "select input", "input_col": "Doanh thu"},
    {"out_name": "THUEVAT", "mode": "select input", "input_col": "Tiền thuế"},
    {"out_name": "TONGTIEN", "mode": "calculate", "formula": "Doanh thu + Tiền thuế"},
    {"out_name": "LOẠI TIỀN", "mode": "currency_rule"},
    {"out_name": "THANHTIEN NT", "mode": "select input", "input_col": "Doanh thu NT"},
    {"out_name": "THUEVAT NT", "mode": "select input", "input_col": "Tiền thuế NT"},
    {"out_name": "TỶ GIÁ", "mode": "select input", "input_col": "ExchangeRate"},
]

ACCOUNTING_COLUMNS = {
    "THANHTIEN",
    "THUEVAT",
    "TONGTIEN",
    "TỶ GIÁ",
}
# =========================================================
# HELPERS
# =========================================================
PRESET_FILE = Path("mapping_presets.json")

def load_presets():
    if not PRESET_FILE.exists():
        return {}

    try:
        content = PRESET_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return {}
        return json.loads(content)
    except json.JSONDecodeError:
        PRESET_FILE.write_text("{}", encoding="utf-8")
        return {}

def save_presets(presets: dict):
    tmp_file = PRESET_FILE.with_suffix(".tmp")

    try:
        tmp_file.write_text(
            json.dumps(presets, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        tmp_file.replace(PRESET_FILE)  # atomic replace
    except Exception as e:
        st.error(f"Failed to save mapping presets: {e}")

def normalize_presets(presets: dict) -> dict:
    clean = {}
    for name, mapping in presets.items():
        clean[name] = [
            {
                "out_name": m.get("out_name"),
                "mode": m.get("mode"),
                "input_col": m.get("input_col"),
                "fixed_value": m.get("fixed_value", ""),
                "formula": m.get("formula", "")
            }
            for m in mapping
        ]
    return clean
    
def new_filter(col):
    return {
        "id": str(uuid.uuid4()),
        "col": col,
        "op": "=",
        "val": ""
    }
    
def read_workbook_build_headers(file_bytes, filename):
    suffix = Path(filename).suffix.lower()
    stream = io.BytesIO(file_bytes)

    # -------- Read file --------
    if suffix == ".xlsx":
        df = pd.read_excel(stream, header=None, dtype=object, engine="openpyxl")
    elif suffix == ".xls":
        df = pd.read_excel(stream, header=None, dtype=object, engine="xlrd")
    else:
        raise ValueError("Unsupported file type")

    # -------- Ensure at least 8 rows --------
    while df.shape[0] < 8:
        df = pd.concat(
            [df, pd.DataFrame([[None] * df.shape[1]])],
            ignore_index=True
        )

    max_col = min(df.shape[1], 26)

    row7 = df.iloc[6, :max_col].fillna("").astype(str)
    row8 = df.iloc[7, :max_col].fillna("").astype(str)

    headers = []

    for i in range(max_col):
        col_letter = chr(ord("A") + i)
        a = row7.iat[i].strip()
        b = row8.iat[i].strip()

        # ---- BUSINESS RULE ----
        if col_letter in ("B", "C", "D"):
            h = f"{b} {row7.iat[1]}".strip()
        else:
            h = a

        if not h:
            h = f"Column_{i + 1}"

        headers.append(h)

    # -------- Data starts from row 9 --------
    if df.shape[0] > 8:
        data = df.iloc[8:, :max_col].reset_index(drop=True)
        data.columns = headers
    else:
        data = pd.DataFrame(columns=headers)

    return data, headers

def last_day_of_last_month():
    today = date.today()
    return date(today.year, today.month, 1) - timedelta(days=1)


def is_number_like(x):
    try:
        float(x)
        return True
    except Exception:
        return False

def try_parse_date_series(s):
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if dt.notna().sum() > 0:
        return dt
    return None


def try_parse_date_value(v):
    try:
        return pd.to_datetime(v, dayfirst=True)
    except Exception:
        return None

def apply_single_filter(df, col, op, val):
    s = df[col]

    # ---------- 1) DATE COMPARISON ----------
    if op in ("=", "!=", "<", ">", "<=", ">="):
        s_date = try_parse_date_series(s)
        v_date = try_parse_date_value(val)

        if s_date is not None and v_date is not None:
            if op == "=":  return s_date == v_date
            if op == "!=": return s_date != v_date
            if op == "<":  return s_date < v_date
            if op == ">":  return s_date > v_date
            if op == "<=": return s_date <= v_date
            if op == ">=": return s_date >= v_date

    # ---------- 2) NUMERIC COMPARISON ----------
    if op in ("=", "!=", "<", ">", "<=", ">=") and is_number_like(val):
        s_num = pd.to_numeric(s, errors="coerce")
        v = float(val)
        return {
            "=": s_num == v,
            "!=": s_num != v,
            "<": s_num < v,
            ">": s_num > v,
            "<=": s_num <= v,
            ">=": s_num >= v,
        }[op]

    # ---------- 3) STRING COMPARISON ----------
    s = s.fillna("").astype(str)
    val = str(val)

    if op == "=": return s == val
    if op == "!=": return s != val
    if op == "contains": return s.str.contains(val, case=False, na=False)
    if op == "not contains": return ~s.str.contains(val, case=False, na=False)
    if op == "begins with": return s.str.startswith(val, na=False)
    if op == "not begins with": return ~s.str.startswith(val, na=False)
    if op == "ends with": return s.str.endswith(val, na=False)
    if op == "not ends with": return ~s.str.endswith(val, na=False)

    return pd.Series(True, index=df.index)

def apply_filters(df, filters):
    mask = pd.Series(True, index=df.index)
    for f in filters:
        mask &= apply_single_filter(df, f["col"], f["op"], f["val"])
    return df[mask]


def compute_sum_formula(df, formula):
    parts = [p.strip() for p in formula.split("+")]
    res = pd.Series(0, index=df.index, dtype=float)
    for p in parts:
        if p in df.columns:
            res += pd.to_numeric(df[p], errors="coerce").fillna(0)
    return res

# =========================================================
# SESSION STATE
# =========================================================
st.session_state.setdefault("df", None)
st.session_state.setdefault("cols", [])
st.session_state.setdefault("filters", [])
st.session_state.setdefault("mappings", [
    {"out_name": h, "mode": "select input", "input_col": None,
     "fixed_value": "", "formula": ""} for h in DESIRED_OUTPUT_HEADERS
])

st.session_state.setdefault("manual_mapping_initialized", False)
st.session_state.setdefault("mapping_presets", load_presets())
st.session_state.setdefault("selected_preset", "")

st.session_state.setdefault("mapping_version", 0)

if "use_default_mapping" not in st.session_state:
    st.session_state["use_default_mapping"] = True  

# =========================================================
# UI
# =========================================================
st.title("Excel Filter & Output Mapping — Vietnam format")

left, right = st.columns([1, 2])
count = 0

# ------------------ IMPORT ------------------
with left:
    st.header("1) IMPORT")

    uploaded = st.file_uploader("Import Excel", type=["xls", "xlsx"])

    if uploaded:
        file_key = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.get("file_key") != file_key:
            df, cols = read_workbook_build_headers(uploaded.getvalue(), uploaded.name)

            st.session_state["df"] = df
            st.session_state["cols"] = cols
            
            st.session_state["manual_mapping_initialized"] = False

            # initialize default filter ONCE
            st.session_state["filters"] = [{
                "id": "default",
                "col": cols[5],
                "op": "not contains",
                "val": "TAA"
            }]
            
            st.session_state["file_key"] = file_key
    else:
        # only reset when user explicitly removes file
        pass

    if st.session_state["df"] is not None:
        st.success(f"Loaded {len(st.session_state['df'])} records")
        st.write(st.session_state["cols"])
    else:
        st.info("Upload an Excel file")

# ------------------ FILTERS ------------------
with right:
    st.header("2) Filter Conditions (AND)")

    if st.session_state["df"] is not None:
    # if st.session_state["cols"]:

        col_add, col_clear = st.columns(2)

        with col_add:
            if st.button("➕ Add filter"):
                st.session_state["filters"].append(
                    new_filter(st.session_state["cols"][0])
                )
                st.rerun()

        with col_clear:
            if st.button("Clear filters"):
                st.success("duma")
                st.session_state["filters"] = []
                st.rerun()
                st.write(st.session_state["filters"])

        # ----- render filters -----
        filters = st.session_state["filters"]
        remove_id = None

        for f in filters:
            fid = f["id"]
            c1, c2, c3, c4 = st.columns([3, 2, 3, 1])

            col_val = c1.selectbox(
                "Column",
                st.session_state["cols"],
                index=st.session_state["cols"].index(f["col"]),
                key=f"fc_{fid}"
            )

            op_val = c2.selectbox(
                "Op",
                OPERATORS,
                index=OPERATORS.index(f["op"]),
                key=f"fo_{fid}"
            )

            val_val = c3.text_input(
                "Value",
                f["val"],
                key=f"fv_{fid}"
            )

            if c4.button("❌", key=f"fr_{fid}"):
                remove_id = fid

            # update safely
            f.update({"col": col_val, "op": op_val, "val": val_val})

        if remove_id:
            st.session_state["filters"] = [
                f for f in filters if f["id"] != remove_id
            ]
            st.rerun()

# -------------------------------------------------
# SECTION #3
# -------------------------------------------------
# ------------------ MAPPING TOGGLE ------------------
if st.session_state["df"] is not None:
    st.toggle(
        "Use default mapping (recommended)",
        value=st.session_state["use_default_mapping"],
        key="use_default_mapping"
    )
    
    # ------------------ Hydrate manual mapping from default (ONCE) ------------------
    if (
        not st.session_state["use_default_mapping"]
        and not st.session_state["manual_mapping_initialized"]
    ):
        hydrated = []

        uploaded_cols = st.session_state.get("cols", [])

        for d in DEFAULT_MAPPING:
            input_col = d.get("input_col")

            # If default input_col not found, keep it as "" (visible & editable)
            if input_col not in uploaded_cols:
                input_col = ""

            hydrated.append({
                "out_name": d["out_name"],
                "mode": d.get("mode", "select input"),
                "input_col": input_col,
                "fixed_value": d.get("fixed_value", ""),
                "formula": d.get("formula", "")
            })

        st.session_state["mappings"] = hydrated
        st.session_state["manual_mapping_initialized"] = True

    # ------------------ Manual Mappings ------------------
    if not st.session_state["use_default_mapping"]:

        st.subheader("📂 Mapping Presets")

        presets = st.session_state["mapping_presets"]
        preset_names = [""] + list(presets.keys())

        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            chosen = st.selectbox(
                "Load preset",
                preset_names,
                index=preset_names.index(st.session_state["selected_preset"])
                if st.session_state["selected_preset"] in preset_names else 0
            )

        with col2:
            if st.button("Load", disabled=not chosen):
                st.session_state["mappings"] = copy.deepcopy(presets[chosen])
                st.session_state["selected_preset"] = chosen

                # 🔑 force widget reset
                st.session_state["mapping_version"] += 1

                st.rerun()

        with col3:
            if st.button("Delete", disabled=not chosen):
                del presets[chosen]
                save_presets(presets)
                st.session_state["selected_preset"] = ""
                st.rerun()
                
    if not st.session_state["use_default_mapping"]:
        st.header("3) Output Mapping (manual)")
        for i, m in enumerate(st.session_state["mappings"]):
            a, b, c = st.columns([2, 2, 4])
            v = st.session_state["mapping_version"]
            a.markdown(f"**{m['out_name']}**")
            m["mode"] = b.selectbox(
                "Mode", ["select input", "fixed", "calculate", "currency_rule"],
                index=["select input", "fixed", "calculate", "currency_rule"].index(m["mode"]),
                key=f"mm{v}_{i}"
            )
            if m["mode"] == "select input":
                options = [""] + st.session_state["cols"]

                current = m.get("input_col") or ""
                index = options.index(current) if current in options else 0

                m["input_col"] = c.selectbox(
                    "Input",
                    options,
                    index=index,
                    key=f"mi{v}_{i}"
                )
            elif m["mode"] == "fixed":
                m["fixed_value"] = c.text_input("Fixed", m["fixed_value"], key=f"mf{v}_{i}")
            elif m["mode"] == "calculate":
                m["formula"] = c.text_input("Formula", m["formula"], key=f"mc{v}_{i}")
            else:
                c.write("ExchangeRate == 1 → VND else USD")

        st.subheader("💾 Save current mapping")

        preset_name = st.text_input(
            "Preset name",
            value=st.session_state.get("selected_preset", "")
        )

        if st.button("Save mapping") and preset_name:
            st.session_state["mapping_presets"][preset_name] = copy.deepcopy(
                st.session_state["mappings"]
            )

            save_presets(normalize_presets(st.session_state["mapping_presets"]))
            st.session_state["selected_preset"] = preset_name

            # 🔑 force UI refresh so selectbox rebuilds
            
            st.success(f"Saved preset: {preset_name}")
            st.session_state["mapping_version"] += 1
            st.rerun()

st.divider()

# -------------------------
# PREVIEW & EXPORT
# -------------------------
st.header(
    "4) Preview & EXPORT" if not st.session_state["use_default_mapping"] else "3) Preview & EXPORT"
)

preview_all = st.toggle("Reveal all records", value=False)

df_src = st.session_state.get("df")

if df_src is not None:

    # Apply filters
    filtered_df = apply_filters(
        df_src,
        st.session_state.get("filters", [])
    )

    # Prepare output dataframe
    output_df = pd.DataFrame(index=filtered_df.index)

    # Choose mapping source
    active_mappings = (
        DEFAULT_MAPPING
        if st.session_state["use_default_mapping"]
        else st.session_state.get("mappings", [])
    )

    for mapping in active_mappings:
        out_col = mapping.get("out_name")
        mode = mapping.get("mode")

        # ---- SELECT INPUT COLUMN ----
        if mode == "select input":
            input_col = mapping.get("input_col")
            if input_col:
                output_df[out_col] = filtered_df.get(input_col)

        # ---- FIXED VALUE ----
        elif mode == "fixed":
            raw_val = str(mapping.get("fixed_value", "")).strip().lower()

            if raw_val in ("last_day_of_last_month", "last_day_prev_month"):
                output_df[out_col] = last_day_of_last_month().strftime("%Y-%m-%d")
            else:
                output_df[out_col] = mapping.get("fixed_value")

        # ---- CALCULATION ----
        elif mode == "calculate":
            formula = mapping.get("formula", "")
            output_df[out_col] = compute_sum_formula(filtered_df, formula)

        # ---- CURRENCY RULE ----
        elif mode == "currency_rule":
            exchange_cols = [
                c for c in filtered_df.columns
                if c.lower().replace(" ", "") in (
                    "exchangerate",
                    "tygia",
                    "tigia",
                    "tygia",
                    "tỷgiá"
                )
            ]

            if exchange_cols:
                output_df[out_col] = (
                    pd.to_numeric(
                        filtered_df[exchange_cols[0]],
                        errors="coerce"
                    )
                    .apply(lambda x: "VND" if x == 1 else "USD")
                )
            else:
                output_df[out_col] = None

    for col in ACCOUNTING_COLUMNS:
        if col in output_df.columns:
            output_df[col] = pd.to_numeric(output_df[col], errors="coerce")
            
    # ---- PREVIEW ----
    st.write(f"Output {len(output_df)} records.")

    preview_df = output_df.copy()

    for col in ACCOUNTING_COLUMNS:
        if col in preview_df.columns:
            preview_df[col] = preview_df[col].map(
                lambda x: f"{x:,.2f}" if pd.notna(x) else ""
            )
    st.dataframe(
        preview_df if preview_all else preview_df.head(10),
        use_container_width=True
    )

    # ---- EXPORT ----
    if st.button("EXPORT to Excel"):
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            output_df.to_excel(writer, index=False, sheet_name="DATA")

            ws = writer.sheets["DATA"]

            # Apply accounting format
            for col_idx, col_name in enumerate(output_df.columns, start=1):
                if col_name in ACCOUNTING_COLUMNS:
                    for row in range(2, len(output_df) + 2):
                        ws.cell(row=row, column=col_idx).number_format = "#,##0.00"

        st.download_button(
            label="Download exported file",
            data=buffer.getvalue(),
            file_name="exported.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )