# EduPro Instructor Performance & Course Quality Dashboard

A beginner-friendly Streamlit analytics project matching the Unified Mentor brief.

## Features
- Instructor performance leaderboard
- Teacher and course rating KPIs
- Experience vs. rating scatter plot and correlation
- Course quality by category and level
- Expertise, category, level, and rating filters
- Enrollment counts from Transactions
- Data-quality checks and CSV export
- Built-in synthetic sample data, so the app can run before you receive the official dataset
- Excel upload support

## 1. Open Terminal and enter the project folder
```bash
cd ~/Downloads/EduPro_Instructor_Analytics
```
If you extracted it somewhere else, use that folder's actual path.

## 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```
If the first command says venv is missing on Ubuntu:
```bash
sudo apt update
sudo apt install python3-venv python3-pip
```
Then repeat the virtual-environment commands.

## 3. Install packages
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Start the dashboard
```bash
streamlit run app.py
```
Streamlit prints a local URL, usually `http://localhost:8501`. Open it in your browser.

## Excel workbook format
Upload an `.xlsx` workbook with these sheets:
- `Teachers`: `TeacherID`, `TeacherName`, `Age`, `Gender`, `Expertise`, `YearsOfExperience`, `TeacherRating`
- `Courses`: `CourseID`, `CourseName`, `CourseCategory`, `CourseLevel`, `CourseRating`
- `Transactions`: `TransactionID`, `CourseID`, `TeacherID`

The app accepts capitalization differences in sheet names and common column-name variants. TeacherID and TeacherRating are required in Teachers; CourseID and CourseRating are required in Courses. Transactions is recommended for enrollment analysis.

## Important
The built-in data is synthetic. Use the official dataset for your final analysis and clearly label any sample-data screenshots. Ratings are assumed to be on a 0–5 scale.
