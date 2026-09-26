"""
capstone_app_v6.py — Capstone Case 09 (ปรับใช้): หน้าช่วยตัดสินใจ งบครุภัณฑ์ต่อนักศึกษา รายคณะ
รุ่นนี้ใช้มุมมองเดียวทั้งหน้า: คณะที่เปรียบเทียบคือ “คณะ” เทียบกับคณะอื่นใน “กลุ่มสาขาวิชา” เดียวกัน ตัวเลขเหมือน v4–v5 ทุกอย่าง

Run (จาก root ของ repository):
    streamlit run capstone/case09_faculty/capstone_app_v6.py
ข้อมูล: data/faculty_equipment_per_student.csv (ปิดชื่อคณะ) และ data/output_summary.csv (ผลผลิต 3 ด้าน)
ถ้ามีไฟล์ private/faculty_mapping_private.csv ในเครื่อง จะเลือกแสดงชื่อคณะจริงได้ (ใช้ภายในเท่านั้น)
หลักการ: ชื่อคณะ ตัวเลข และข้อความหลักฐานคำนวณจากข้อมูลทั้งหมด ไม่พิมพ์คำตอบไว้ล่วงหน้า
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="หน้าช่วยตัดสินใจ — งบครุภัณฑ์ต่อนักศึกษา", layout="wide")
HERE = Path(__file__).parent
DATA = HERE / "data" / "faculty_equipment_per_student.csv"
PRIVATE = HERE / "private" / "faculty_mapping_private.csv"
G1, G2, G3, G4 = "ประเภท 1: ขอแล้วไม่ได้ → ให้ก่อน", "ประเภท 2: ขอน้อย → ช่วยเขียนคำขอ", "อื่น ๆ: ติดตามต่อ", "นักศึกษาน้อย: ยังไม่จัดประเภท"
COLORS = {G1: "#c0392b", G2: "#e67e22", G3: "#9aa5b1", G4: "#d5dbe0"}


@st.cache_data
def load(path):
    return pd.read_csv(path)


df = load(DATA).copy()

# ------------------------------------------------------------------ sidebar: เกณฑ์ที่ปรับได้
st.sidebar.header("ปรับเกณฑ์ (ทีมกำหนดเอง)")
thr = st.sidebar.slider("‘ได้น้อยมาก’ คือได้ไม่ถึงกี่เท่าของค่าเฉลี่ยกลุ่มสาขาวิชา (0.5 = ครึ่งหนึ่ง)", 0.2, 1.0, 0.5, 0.05)
min_n = st.sidebar.number_input("คณะต้องมีนักศึกษาอย่างน้อย (คน)", min_value=0, value=200, step=50)
frame = st.sidebar.number_input("งบคำขอครุภัณฑ์ต่อปี ใช้เทียบ (ล้านบาท)", min_value=1.0, value=300.0, step=10.0)
st.sidebar.caption("เกณฑ์ทั้งหมดทีมตั้งขึ้นเอง ไม่ใช่เกณฑ์ทางการ")
show_names = PRIVATE.exists() and st.sidebar.checkbox("แสดงชื่อคณะจริง (ใช้ภายในเท่านั้น)", value=False)
names = dict(pd.read_csv(PRIVATE)[["unit_code", "unit_name"]].values) if show_names else {}
df["label"] = df["unit_code"].map(names).fillna(df["unit_code"]) if show_names else df["unit_code"]

# ------------------------------------------------------------------ จัดกลุ่มจากข้อมูล
ok = df["students_avg"] >= min_n
g1 = ok & (df["ratio"] < 1) & (df["unmet_per_student"] >= df["cluster_unmet_rate"])
g2 = ok & ~g1 & (df["ratio"] < thr)
df["group"] = G3
df.loc[g2, "group"] = G2
df.loc[g1, "group"] = G1
df.loc[~ok, "group"] = G4
df["unmet_rel"] = df["unmet_per_student"] / df["cluster_unmet_rate"]

below = ok & (df["ratio"] < thr)
zero = ok & df["zero_5y"]
gap = ((thr * df["cluster_avg"] - df["per_student"]).clip(lower=0) * df["students_avg"])[g2].sum() / 1e6
unmet_g1 = df.loc[g1, "unmet_mb_6870"].sum()
cl = df[df["per_student"].notna()].groupby("cluster")[["normal_mb_5y", "students_avg"]].sum()
cl["per_student"] = cl["normal_mb_5y"] * 1e6 / 5 / cl["students_avg"]
rho = df.loc[ok, "per_student"].rank().corr(df.loc[ok, "per_grad"].rank())
g2_requested = int((df.loc[g2, "req_mb_6870"] > 0).sum())
lab = lambda m: ", ".join(df.loc[m].sort_values("ratio")["label"].astype(str))

# ------------------------------------------------------------------ page
st.title("หน้าช่วยตัดสินใจ — งบครุภัณฑ์ต่อนักศึกษา รายคณะ")
st.caption(f"มุมมองของหน้านี้: เปรียบเทียบ “คณะ” ({len(df)} คณะ/หน่วยงานที่มีนักศึกษา รวมวิทยาลัย สถาบัน และวิทยาเขตที่บันทึกรวม) "
           f"กับคณะอื่นใน “กลุ่มสาขาวิชา” เดียวกัน | ครุภัณฑ์งบปกติปีงบ 2566–2570 ÷ นักศึกษาเฉลี่ยปีการศึกษา 2565–2568 | ชื่อคณะแสดงเป็นรหัส")
st.subheader("สิ่งที่ต้องตัดสินใจ (Decision)")
st.markdown("**ปีหน้า ควรให้คณะไหนได้งบครุภัณฑ์ก่อน และควรช่วยคณะไหนเขียนคำขอ เพื่อให้งบสมดุลกับจำนวนนักศึกษา?**")
st.success(
    f"**ข้อเสนอ:** ให้ {int(g1.sum())} คณะได้ก่อน ({lab(g1)}) เพราะได้น้อยกว่าค่าเฉลี่ยกลุ่มสาขาวิชา และยังมีเงินที่ขอแล้วไม่ได้ "
    f"{unmet_g1:,.1f} ล้านบาท (ปี 2568 และ 2570) | ช่วย {int(g2.sum())} คณะเขียนคำขอ เพราะได้ไม่ถึง {thr:.0%} ของค่าเฉลี่ยกลุ่มสาขาวิชา "
    f"ทั้งที่ขอน้อยหรือไม่ได้ขอ ต้องใช้เงินเพิ่มราว {gap:,.1f} ล้านบาทต่อปี"
)
k1, k2, k3, k4 = st.columns(4)
k1.metric(f"นักศึกษาในคณะที่ได้ไม่ถึง {thr:.0%}", f"{df.loc[below, 'students_avg'].sum():,.0f} คน",
          f"{int(below.sum())} คณะ", delta_color="off")
k2.metric("คณะที่ไม่ได้ครุภัณฑ์งบปกติเลย 5 ปี", f"{int(zero.sum())} คณะ",
          f"{df.loc[zero, 'students_avg'].sum():,.0f} คน", delta_color="off")
k3.metric("เงินที่คณะประเภท 1 ขอแล้วไม่ได้ (2568+2570)", f"{unmet_g1:,.1f} ล้านบาท", f"{int(g1.sum())} คณะ", delta_color="off")
k4.metric(f"เงินเพิ่มต่อปีเพื่อยกคณะประเภท 2 ถึง {thr:.0%}", f"{gap:,.1f} ล้านบาท",
          f"{gap / frame:.1%} ของงบ {frame:,.0f} ล้านบาท", delta_color="off")

# ------------------------------------------------------------------ evidence visuals
st.subheader("หลักฐาน (Evidence)")
c1, c2 = st.columns(2)
bar = df[ok].sort_values("ratio")
fig_a = px.bar(bar, x="ratio", y="label", color="group", orientation="h", color_discrete_map=COLORS,
               hover_data={"cluster": True, "students_avg": ":,.0f", "per_student": ":,.0f"},
               title=f"{int(below.sum())} คณะได้งบไม่ถึง {thr:.0%} ของค่าเฉลี่ยกลุ่มสาขาวิชาเดียวกัน",
               labels={"ratio": "งบที่ได้ (% ของค่าเฉลี่ยกลุ่มสาขาวิชา)", "label": "", "group": ""},
               category_orders={"label": list(bar["label"])})
fig_a.add_vline(x=thr, line_dash="dot")
fig_a.add_vline(x=1, line_dash="dash")
fig_a.update_xaxes(tickformat=".0%")
fig_a.update_layout(height=640, legend=dict(orientation="h", y=-0.12))
c1.plotly_chart(fig_a, width="stretch")

fig_b = px.scatter(df[ok], x="ratio", y="unmet_rel", size="students_avg", color="group", color_discrete_map=COLORS,
                   hover_name="label", title="แยก 2 สาเหตุ: ขอแล้วไม่ได้ (ประเภท 1) กับขอน้อย (ประเภท 2)",
                   labels={"ratio": "งบที่ได้ (% ของค่าเฉลี่ยกลุ่มสาขาวิชา)",
                           "unmet_rel": "เงินที่ขอแล้วไม่ได้ (% ของค่าเฉลี่ยกลุ่มสาขาวิชา)", "group": ""})
fig_b.add_vline(x=1, line_dash="dash")
fig_b.add_vline(x=thr, line_dash="dot")
fig_b.add_hline(y=1, line_dash="dash")
fig_b.update_xaxes(tickformat=".0%")
fig_b.update_yaxes(tickformat=".0%")
fig_b.update_layout(height=640, legend=dict(orientation="h", y=-0.12))
c2.plotly_chart(fig_b, width="stretch")

left, right = st.columns(2)
with left:
    st.markdown("**หลักฐาน (ตรวจตัวเลขได้จากตารางด้านล่าง)**")
    st.markdown(
        "1. ค่าเฉลี่ยกลุ่มสาขาวิชา (บาทต่อนักศึกษาต่อปี): " + ", ".join(f"{i} {r.per_student:,.0f}" for i, r in cl.iterrows()) + "\n"
        f"2. {int(below.sum())} คณะได้ไม่ถึง {thr:.0%} ของค่าเฉลี่ยกลุ่มสาขาวิชา นักศึกษารวม {df.loc[below, 'students_avg'].sum():,.0f} คน\n"
        f"3. {int(zero.sum())} คณะไม่ได้ครุภัณฑ์งบปกติเลยใน 5 ปี ({df.loc[zero, 'students_avg'].sum():,.0f} คน) "
        f"และปี 2568, 2570 ขอไปรวมแค่ {df.loc[zero, 'req_mb_6870'].sum():,.2f} ล้านบาท\n"
        f"4. คณะประเภท 1 ได้ {df.loc[g1, 'ratio'].min():.0%}–{df.loc[g1, 'ratio'].max():.0%} ของค่าเฉลี่ยกลุ่มสาขาวิชา "
        f"และมีเงินที่ขอแล้วไม่ได้ {unmet_g1:,.1f} ล้านบาท\n"
        f"5. ถ้านับจากผู้สำเร็จการศึกษาแทนนักศึกษา อันดับแทบไม่เปลี่ยน (สอดคล้องกัน {rho:.2f} จากเต็ม 1, {int(ok.sum())} คณะ)"
    )
with right:
    st.markdown("**ข้อคิด (Insight)**")
    st.markdown(
        "- คณะที่ได้งบน้อยมี 2 แบบ คือ ขอแล้วไม่ได้ กับ ขอน้อยหรือไม่ได้ขอ จึงต้องแก้ต่างกัน\n"
        f"- เงินที่ต้องใช้ช่วยคณะประเภท 2 ({gap:,.1f} ล้านบาทต่อปี) เท่ากับ {gap / frame:.1%} ของงบ จึงทำได้โดยไม่กระทบภาพรวมมาก\n"
        "- **ยังต้องตรวจ (ข้อสันนิษฐาน):** คณะประเภท 2 อาจไม่ถนัดเขียนคำขอ หรืออาจไม่ต้องการครุภัณฑ์จริง ต้องถามคณะก่อน"
    )

# ------------------------------------------------------------------ recommendation + action
st.subheader("ข้อเสนอ (Recommendation)")
st.info("(1) ปีหน้า เพิ่มเกณฑ์ ‘งบต่อนักศึกษา + เงินที่ขอแล้วไม่ได้’ ในการเลือกคำขอ โดยยังคงสัดส่วนเดิม "
        "(2) ตั้งทีมช่วยคณะประเภท 2 เขียนคำขอก่อนเปิดรับ (3) ติดตามงบต่อนักศึกษาของทุกคณะทุกปี")
st.subheader("แผนลงมือ (Action Plan)")
action_plan = pd.DataFrame({
    "สิ่งที่ทำ": ["ใช้เกณฑ์ใหม่ในการเลือกคำขอ", "ทีมช่วยคณะประเภท 2 เขียนคำขอ", "ทบทวนผลแล้วตัดสินใจว่าจะใช้เกณฑ์ต่อ ปรับ หรือหยุด"],
    "ผู้รับผิดชอบ": ["คณะทำงานพิจารณาคำขอค่าครุภัณฑ์", "กองนโยบาย ยุทธศาสตร์ และแผน + คณะประเภท 2",
                     "คณะทำงานฯ + กองนโยบาย ยุทธศาสตร์ และแผน"],
    "เมื่อไร": ["รอบคำขอปีหน้า", "ก่อนเปิดรับคำขอ", "เมื่อรู้ผลจัดสรร และทุกปี"],
    "วัดด้วย": ["เงินที่คณะประเภท 1 ขอแล้วไม่ได้ ต่อปี", "จำนวนคณะประเภท 2 ที่ยื่นคำขอ", f"ทำได้ตามเป้ากี่ข้อ; คณะที่ได้ไม่ถึง {thr:.0%}"],
    "ตอนนี้": [f"{unmet_g1 / 2:,.1f} ล้านบาท (เฉลี่ยปี 2568 และ 2570)", f"{g2_requested} จาก {int(g2.sum())} คณะ",
               f"ยังไม่วัด; {int(below.sum())} คณะ"],
    "เป้าหมาย*": [f"ไม่เกิน {unmet_g1 / 4:,.1f} ล้านบาท (ลดครึ่งหนึ่ง)", f"ครบ {int(g2.sum())} คณะ",
                  f"ได้ครบ 2 ข้อ; ไม่เกิน {int(below.sum()) // 2} คณะใน 3 ปี"],
    "ผลที่คาดหวัง / แผนสำรอง": ["เงินที่ขอแล้วไม่ได้ลดลง", "คณะที่ไม่เคยขอเริ่มยื่นคำขอ",
                                  "แผนสำรอง: ถ้าไม่ได้ตามเป้า ตรวจคุณภาพคำขอของคณะประเภท 1 และถามความต้องการจริงของคณะประเภท 2 ก่อนปรับเกณฑ์"],
})
st.dataframe(action_plan, width="stretch", hide_index=True)
st.caption("*เป้าหมายเป็นค่าที่ผู้บริหารตั้ง ไม่ใช่สิ่งที่ข้อมูลรับประกันว่าทำได้")

# ------------------------------------------------------------------ มุมมองตามผลผลิต 3 ด้าน (ภาคผนวก)
# Day 4: หลักฐานที่ไม่ได้รองรับข้อเสนอโดยตรง ให้ย้ายไปภาคผนวก จึงแสดงเป็นข้อมูลเสริมใน expander
OUT = HERE / "data" / "output_summary.csv"
if OUT.exists():
    o = pd.read_csv(OUT)
    with st.expander("ดูเพิ่มเติม (ภาคผนวก): ภาพรวมตามผลผลิต 3 ด้าน"):
        o1, o2 = st.columns(2)
        share = o.melt(id_vars="output", value_vars=["share_students", "share_equipment"], var_name="type", value_name="share")
        share["type"] = share["type"].map({"share_students": "สัดส่วนนักศึกษา", "share_equipment": "สัดส่วนงบครุภัณฑ์ 5 ปี"})
        low = o.loc[(o["share_equipment"] - o["share_students"]).idxmin()]
        fig_o = px.bar(share, x="output", y="share", color="type", barmode="group",
                       title=f"ด้าน{low['output']}: นักศึกษา {low['share_students']:.0%} แต่ได้งบครุภัณฑ์ {low['share_equipment']:.0%}",
                       labels={"output": "", "share": "สัดส่วน", "type": ""})
        fig_o.update_yaxes(tickformat=".0%")
        fig_o.update_layout(legend=dict(orientation="h", y=-0.2))
        o1.plotly_chart(fig_o, width="stretch")
        trend = o.melt(id_vars="output", value_vars=[f"per_student_{y}" for y in range(2566, 2570)], var_name="year", value_name="baht")
        trend["year"] = trend["year"].str[-4:].astype(int)
        chg = o.set_index("output")["per_student_2569"] / o.set_index("output")["per_student_2566"] - 1
        fig_t = px.line(trend, x="year", y="baht", color="output", markers=True,
                        title=f"งบครุภัณฑ์ต่อนักศึกษาด้าน{chg.idxmin()} เปลี่ยน {chg.min():+.0%} (ปีงบ 2566–2569)",
                        labels={"year": "ปีงบประมาณ", "baht": "บาทต่อนักศึกษา", "output": ""})
        fig_t.update_xaxes(dtick=1)
        fig_t.update_layout(legend=dict(orientation="h", y=-0.2))
        o2.plotly_chart(fig_t, width="stretch")
        mism = df[df["output_match"] != "ตรงกัน"]
        top_unmet = o.loc[o["unmet_mb_6870"].idxmax()]
        st.markdown(
            "- งบครุภัณฑ์ต่อนักศึกษาต่อปี (รวม 5 ปี): " + ", ".join(f"{r.output} {r.per_student:,.0f} บาท" for r in o.itertuples()) + "\n"
            f"- เงินที่ขอแล้วไม่ได้ (ปี 2568 และ 2570) มากที่สุดที่ด้าน{top_unmet['output']} {top_unmet['unmet_mb_6870']:,.1f} ล้านบาท "
            f"จากที่ขอ {top_unmet['req_mb_6870']:,.1f} ล้านบาท\n"
            f"- {len(mism)} คณะมีงบอยู่คนละด้านกับนักศึกษา ({', '.join(mism['label'].astype(str))}) จึงเทียบรายคณะเป็นหลัก\n"
            "- สัดส่วนไม่จำเป็นต้องเท่ากัน เพราะเครื่องมือแต่ละด้านราคาต่างกัน ใช้ดูภาพรวมเท่านั้น ไม่ใช้จัดอันดับ"
        )

# ------------------------------------------------------------------ supporting detail
with st.expander("ตารางรายคณะ + ดาวน์โหลด"):
    table = df[["label", "cluster", "group", "students_avg", "normal_mb_5y", "per_student", "cluster_avg", "ratio",
                "unmet_mb_6870", "unmet_per_student", "per_grad"]].sort_values(["group", "ratio"])
    table.columns = ["คณะ", "กลุ่มสาขาวิชา", "ประเภท", "นักศึกษาเฉลี่ย", "งบ 5 ปี (ล้านบาท)", "งบต่อนักศึกษาต่อปี (บาท)",
                     "ค่าเฉลี่ยกลุ่มสาขาวิชา (บาท)", "% ของค่าเฉลี่ยกลุ่มสาขาวิชา", "ขอแล้วไม่ได้ 2 ปี (ล้านบาท)",
                     "ขอแล้วไม่ได้ต่อนักศึกษาต่อปี (บาท)", "งบต่อผู้สำเร็จการศึกษา (บาท)"]
    st.dataframe(table.style.format({"นักศึกษาเฉลี่ย": "{:,.0f}", "งบ 5 ปี (ล้านบาท)": "{:,.2f}", "งบต่อนักศึกษาต่อปี (บาท)": "{:,.0f}",
                                     "ค่าเฉลี่ยกลุ่มสาขาวิชา (บาท)": "{:,.0f}", "% ของค่าเฉลี่ยกลุ่มสาขาวิชา": "{:.0%}",
                                     "ขอแล้วไม่ได้ 2 ปี (ล้านบาท)": "{:,.2f}", "ขอแล้วไม่ได้ต่อนักศึกษาต่อปี (บาท)": "{:,.0f}",
                                     "งบต่อผู้สำเร็จการศึกษา (บาท)": "{:,.0f}"}, na_rep="-"),
                 width="stretch", hide_index=True)
    st.download_button("ดาวน์โหลดตาราง (CSV)", table.to_csv(index=False).encode("utf-8-sig"),
                       file_name="faculty_equipment_table.csv", mime="text/csv")
with st.expander("ข้อจำกัด"):
    st.markdown(
        "- งบต่อนักศึกษาบอกภาระการสอน ไม่ได้วัดงานวิจัยและงานบริการ และนับเฉพาะงบปกติ (ไม่นับโครงการพิเศษ)\n"
        "- ข้อมูลคำขอรายคณะมีแค่ปี 2568 และ 2570 เพราะปีอื่นนิยาม ‘คำขอ’ ไม่ตรงกัน\n"
        "- ครุภัณฑ์ห้องเรียนรวมของวิทยาเขตไม่ได้แบ่งให้คณะ และวิทยาเขตที่บันทึกรวมใช้จำนวนนักศึกษารวม\n"
        f"- คณะที่มีนักศึกษาน้อยกว่า {min_n} คนไม่ถูกจัดประเภท เพราะตัวเลขต่อหัวแกว่งง่าย\n"
        "- ตัวเลขที่ไปด้วยกันไม่ได้แปลว่าเป็นเหตุและผล และเกณฑ์ทั้งหมดทีมตั้งขึ้นเอง"
    )
