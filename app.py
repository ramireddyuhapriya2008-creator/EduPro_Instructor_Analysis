import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="EduPro Instructor Analytics", page_icon="🎓", layout="wide")
st.title("🎓 EduPro: Instructor Performance & Course Quality")
st.caption("Explore instructor ratings, course quality, experience, expertise, and enrollment patterns.")

# ---------- Sample data ----------
def make_sample_data():
    rng = np.random.default_rng(42)
    expertise_areas = ["AI & ML", "Web Development", "Data Science", "Cybersecurity", "Cloud Computing"]
    categories = ["Technology", "Business", "Design", "Data", "Programming"]
    levels = ["Beginner", "Intermediate", "Advanced"]
    n_teachers, n_courses, n_tx = 40, 65, 500
    teachers = pd.DataFrame({
        "TeacherID": [f"T{i:03d}" for i in range(1, n_teachers + 1)],
        "TeacherName": [f"Instructor {i}" for i in range(1, n_teachers + 1)],
        "Age": rng.integers(24, 61, n_teachers),
        "Gender": rng.choice(["Female", "Male", "Prefer not to say"], n_teachers, p=[.45, .45, .10]),
        "Expertise": rng.choice(expertise_areas, n_teachers),
        "YearsOfExperience": rng.integers(1, 26, n_teachers),
        "TeacherRating": np.round(rng.uniform(2.8, 5.0, n_teachers), 2)
    })
    courses = pd.DataFrame({
        "CourseID": [f"C{i:03d}" for i in range(1, n_courses + 1)],
        "CourseName": [f"Course {i}" for i in range(1, n_courses + 1)],
        "CourseCategory": rng.choice(categories, n_courses),
        "CourseLevel": rng.choice(levels, n_courses),
        "CourseRating": np.round(rng.uniform(2.7, 5.0, n_courses), 2)
    })
    tx = pd.DataFrame({
        "TransactionID": [f"TR{i:04d}" for i in range(1, n_tx + 1)],
        "CourseID": rng.choice(courses["CourseID"], n_tx),
        "TeacherID": rng.choice(teachers["TeacherID"], n_tx)
    })
    return teachers, courses, tx

def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_column(df, options):
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for option in options:
        if option.lower() in lookup:
            return lookup[option.lower()]
    return None

def numeric(df, col):
    if col and col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def load_uploaded_excel(file):
    xls = pd.ExcelFile(file)
    sheet_map = {s.strip().lower(): s for s in xls.sheet_names}
    def read_sheet(names):
        for name in names:
            if name in sheet_map:
                return normalize_columns(pd.read_excel(xls, sheet_name=sheet_map[name]))
        return None
    return (read_sheet(["teachers", "teacher", "teachers sheet"]),
            read_sheet(["courses", "course", "courses sheet"]),
            read_sheet(["transactions", "transaction", "transactions sheet"]))

with st.sidebar:
    st.header("📂 Data")
    uploaded = st.file_uploader("Upload Excel workbook (.xlsx)", type=["xlsx"])
    st.caption("Expected sheets: Teachers, Courses, Transactions. If no file is uploaded, sample data is used.")
    use_sample = st.checkbox("Use built-in sample data", value=True)

if uploaded is not None:
    try:
        teachers, courses, transactions = load_uploaded_excel(uploaded)
        if teachers is None or courses is None:
            st.error("Workbook must contain Teachers and Courses sheets. Transactions sheet is recommended.")
            st.stop()
        if transactions is None:
            transactions = pd.DataFrame(columns=["TransactionID", "CourseID", "TeacherID"])
            st.warning("No Transactions sheet found. Enrollment analysis will be unavailable.")
    except Exception as exc:
        st.error(f"Could not read workbook: {exc}")
        st.stop()
elif use_sample:
    teachers, courses, transactions = make_sample_data()
else:
    st.info("Upload an Excel workbook or select 'Use built-in sample data'.")
    st.stop()

teachers, courses, transactions = map(normalize_columns, [teachers, courses, transactions])

# Required-column checks
teacher_id = find_column(teachers, ["TeacherID", "Teacher Id", "InstructorID"])
teacher_name = find_column(teachers, ["TeacherName", "InstructorName", "Name"])
teacher_rating = find_column(teachers, ["TeacherRating", "InstructorRating", "Rating"])
experience = find_column(teachers, ["YearsOfExperience", "Years Experience", "Experience"])
expertise = find_column(teachers, ["Expertise", "ExpertiseArea", "Specialization"])
course_id_t = find_column(teachers, ["TeacherID", "Teacher Id", "InstructorID"])
course_id = find_column(courses, ["CourseID", "Course Id"])
course_rating = find_column(courses, ["CourseRating", "Rating"])
category = find_column(courses, ["CourseCategory", "Category"])
level = find_column(courses, ["CourseLevel", "Level"])
tx_teacher = find_column(transactions, ["TeacherID", "Teacher Id", "InstructorID"])
tx_course = find_column(transactions, ["CourseID", "Course Id"])

if teacher_id is None or teacher_rating is None:
    st.error("Teachers sheet must include TeacherID and TeacherRating columns.")
    st.stop()
if course_id is None or course_rating is None:
    st.error("Courses sheet must include CourseID and CourseRating columns.")
    st.stop()

teachers = numeric(teachers, teacher_rating)
if experience:
    teachers = numeric(teachers, experience)
courses = numeric(courses, course_rating)
teachers = teachers.dropna(subset=[teacher_id])
courses = courses.dropna(subset=[course_id])
teachers[teacher_rating] = teachers[teacher_rating].clip(0, 5)
courses[course_rating] = courses[course_rating].clip(0, 5)

# Filter controls
with st.sidebar:
    st.header("🔎 Filters")
    if expertise:
        expert_options = sorted(teachers[expertise].dropna().astype(str).unique().tolist())
        selected_expertise = st.multiselect("Instructor expertise", expert_options, default=expert_options)
    else:
        selected_expertise = []
    if category:
        category_options = sorted(courses[category].dropna().astype(str).unique().tolist())
        selected_categories = st.multiselect("Course category", category_options, default=category_options)
    else:
        selected_categories = []
    if level:
        level_options = sorted(courses[level].dropna().astype(str).unique().tolist())
        selected_levels = st.multiselect("Course level", level_options, default=level_options)
    else:
        selected_levels = []
    min_rating, max_rating = st.slider("Course rating range", 0.0, 5.0, (0.0, 5.0), 0.1)

filtered_teachers = teachers.copy()
filtered_courses = courses.copy()
if expertise:
    filtered_teachers = filtered_teachers[filtered_teachers[expertise].astype(str).isin(selected_expertise)]
if category:
    filtered_courses = filtered_courses[filtered_courses[category].astype(str).isin(selected_categories)]
if level:
    filtered_courses = filtered_courses[filtered_courses[level].astype(str).isin(selected_levels)]
filtered_courses = filtered_courses[filtered_courses[course_rating].between(min_rating, max_rating)]

# Enrollment counts by teacher, using the transactions table
if tx_teacher and not transactions.empty:
    enrollments = transactions.groupby(tx_teacher).size().rename("EnrollmentCount").reset_index()
    enrollments = enrollments.rename(columns={tx_teacher: teacher_id})
    filtered_teachers = filtered_teachers.merge(enrollments, on=teacher_id, how="left")
    filtered_teachers["EnrollmentCount"] = filtered_teachers["EnrollmentCount"].fillna(0).astype(int)
else:
    filtered_teachers["EnrollmentCount"] = np.nan

# Map teacher IDs onto courses through transactions, where possible
if tx_teacher and tx_course and not transactions.empty:
    tx_join = transactions[[tx_teacher, tx_course]].dropna().drop_duplicates()
    tx_join = tx_join.rename(columns={tx_teacher: teacher_id, tx_course: course_id})
    course_teacher = tx_join.merge(filtered_teachers[[teacher_id] + ([teacher_name] if teacher_name else [])],
                                   on=teacher_id, how="inner")
    course_teacher = course_teacher.merge(filtered_courses, on=course_id, how="inner", suffixes=("_teacher", "_course"))
else:
    course_teacher = pd.DataFrame()

# KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Average teacher rating", f"{filtered_teachers[teacher_rating].mean():.2f}" if not filtered_teachers.empty else "N/A")
c2.metric("Average course rating", f"{filtered_courses[course_rating].mean():.2f}" if not filtered_courses.empty else "N/A")
c3.metric("Instructors", f"{len(filtered_teachers):,}")
c4.metric("Courses", f"{len(filtered_courses):,}")
c5.metric("Enrollment records", f"{len(transactions):,}" if tx_teacher else "N/A")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👩‍🏫 Instructor leaderboard", "📚 Course quality", "📁 Data & insights"])

with tab1:
    left, right = st.columns(2)
    with left:
        st.subheader("Instructor rating distribution")
        if not filtered_teachers.empty:
            st.plotly_chart(px.histogram(filtered_teachers, x=teacher_rating, nbins=10, title="Teacher ratings",
                                         labels={teacher_rating: "Teacher rating"}), use_container_width=True)
        else:
            st.info("No instructors match the current filters.")
    with right:
        st.subheader("Experience vs rating")
        if experience and not filtered_teachers.empty:
            st.plotly_chart(px.scatter(filtered_teachers, x=experience, y=teacher_rating,
                                       hover_name=teacher_name if teacher_name else None,
                                       title="Does experience relate to ratings?",
                                       labels={experience: "Years of experience", teacher_rating: "Teacher rating"}),
                            use_container_width=True)
        else:
            st.info("Add a YearsOfExperience column to view this chart.")
    left, right = st.columns(2)
    with left:
        st.subheader("Course ratings by category")
        if category and not filtered_courses.empty:
            st.plotly_chart(px.box(filtered_courses, x=category, y=course_rating, title="Course quality by category",
                                   labels={category: "Category", course_rating: "Course rating"}),
                            use_container_width=True)
        else:
            st.info("Category data is unavailable.")
    with right:
        st.subheader("Experience and performance correlation")
        if experience and len(filtered_teachers) > 1:
            corr = filtered_teachers[[experience, teacher_rating]].corr(numeric_only=True).iloc[0, 1]
            st.metric("Correlation coefficient", f"{corr:.3f}" if pd.notna(corr) else "N/A")
            st.caption("Correlation ranges from -1 to +1. Correlation does not prove causation.")
        else:
            st.info("More experience/rating data is needed.")

with tab2:
    st.subheader("Instructor performance leaderboard")
    leaderboard = filtered_teachers.copy()
    if teacher_name is None:
        leaderboard["Instructor"] = leaderboard[teacher_id].astype(str)
        name_col = "Instructor"
    else:
        name_col = teacher_name
    show_cols = [teacher_id, name_col]
    if expertise: show_cols.append(expertise)
    if experience: show_cols.append(experience)
    show_cols += [teacher_rating, "EnrollmentCount"]
    leaderboard = leaderboard.sort_values(teacher_rating, ascending=False)
    st.dataframe(leaderboard[show_cols], use_container_width=True, hide_index=True)
    st.download_button("Download leaderboard CSV", leaderboard[show_cols].to_csv(index=False).encode("utf-8"),
                       "instructor_leaderboard.csv", "text/csv")

with tab3:
    st.subheader("Course quality analysis")
    if not filtered_courses.empty:
        if category:
            category_summary = filtered_courses.groupby(category, dropna=False)[course_rating].agg(["mean", "count"]).reset_index()
            category_summary.columns = [category, "Average rating", "Number of courses"]
            st.dataframe(category_summary.sort_values("Average rating", ascending=False), use_container_width=True, hide_index=True)
            st.plotly_chart(px.bar(category_summary, x=category, y="Average rating", title="Average rating by category"),
                            use_container_width=True)
        if level:
            level_summary = filtered_courses.groupby(level, dropna=False)[course_rating].mean().reset_index()
            level_summary.columns = [level, "Average rating"]
            st.plotly_chart(px.bar(level_summary, x=level, y="Average rating", title="Average rating by course level"),
                            use_container_width=True)
        st.dataframe(filtered_courses, use_container_width=True, hide_index=True)
    else:
        st.info("No courses match the current filters.")

with tab4:
    st.subheader("Data quality checks")
    d1, d2, d3 = st.columns(3)
    d1.metric("Missing teacher ratings", int(teachers[teacher_rating].isna().sum()))
    d2.metric("Missing course ratings", int(courses[course_rating].isna().sum()))
    d3.metric("Duplicate teacher IDs", int(teachers[teacher_id].duplicated().sum()))
    st.subheader("Key findings (based on current filters)")
    if not filtered_teachers.empty:
        best = filtered_teachers.sort_values(teacher_rating, ascending=False).iloc[0]
        st.write(f"**Highest-rated instructor:** {best[teacher_name] if teacher_name else best[teacher_id]} "
                 f"({best[teacher_rating]:.2f}/5).")
        if experience:
            corr = filtered_teachers[[experience, teacher_rating]].corr(numeric_only=True).iloc[0, 1]
            if pd.notna(corr):
                st.write(f"**Experience-rating correlation:** {corr:.2f}. Treat this as an association, not proof of cause.")
    if not filtered_courses.empty and category:
        means = filtered_courses.groupby(category)[course_rating].mean().sort_values(ascending=False)
        if len(means):
            st.write(f"**Highest-rated category:** {means.index[0]} ({means.iloc[0]:.2f}/5).")
    st.subheader("Dataset preview")
    with st.expander("Teachers"):
        st.dataframe(teachers, use_container_width=True, hide_index=True)
    with st.expander("Courses"):
        st.dataframe(courses, use_container_width=True, hide_index=True)
    with st.expander("Transactions"):
        st.dataframe(transactions, use_container_width=True, hide_index=True)

st.divider()
st.caption("Note: Built-in sample data is synthetic for demonstration. Replace it with the official project dataset before reporting real conclusions.")
