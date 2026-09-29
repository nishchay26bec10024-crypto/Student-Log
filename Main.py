import json
import os


DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_data.json")
EXAMS = {
    "1": "Periodic Test 1",
    "2": "Periodic Test 2",
    "3": "Mid Terms",
    "4": "Finals",
}
DEFAULT_SUBJECTS = {
    "CALC": "Calculus",
    "ELEC": "Electrical",
    "SCI": "Computer Science",
}


def migrate_marks(students, subjects):
    """Convert marks saved by older versions from subject names to subject codes."""
    name_to_code = {name.lower(): code for code, name in subjects.items()}
    for student in students:
        student.setdefault("marks", {})
        for exam, marks in student["marks"].items():
            converted_marks = {}
            for subject, mark in marks.items():
                code = name_to_code.get(subject.lower(), subject.upper())
                converted_marks[code] = mark
            student["marks"][exam] = converted_marks


def load_data():
    """Load saved students and subjects, including records saved by earlier versions."""
    if not os.path.exists(DATA_FILE):
        return [], DEFAULT_SUBJECTS.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, list):  # Old format: student list only
            students = data
            subjects = DEFAULT_SUBJECTS.copy()
        elif isinstance(data, dict):
            students = data.get("students", [])
            subjects = data.get("subjects", DEFAULT_SUBJECTS.copy())
        else:
            raise ValueError("Invalid data format")
        if not isinstance(students, list) or not isinstance(subjects, dict):
            raise ValueError("Invalid data format")
        migrate_marks(students, subjects)
        return students, subjects
    except (json.JSONDecodeError, OSError, ValueError):
        print("Could not read saved data. Starting with an empty system.")
        return [], DEFAULT_SUBJECTS.copy()


def save_data():
    """Save every change automatically in a JSON file."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump({"students": students, "subjects": subjects}, file, indent=4)
    except OSError as error:
        print("Could not save data:", error)


def find_student(roll):
    return next((student for student in students if student["roll"] == roll), None)


def get_mark(subject_code, subject_name):
    while True:
        try:
            mark = float(input(f"  {subject_code} ({subject_name}): "))
            if 0 <= mark <= 100:
                return mark
            print("  Marks must be between 0 and 100.")
        except ValueError:
            print("  Enter a valid number, for example: 78.5")


def choose_exam():
    print("\nChoose an exam:")
    for number, exam in EXAMS.items():
        print(f"  {number}. {exam}")
    exam = EXAMS.get(input("Exam number: ").strip())
    if not exam:
        print("Invalid exam selection.")
    return exam


def add_student():
    global menu_notice
    print("\n--- Add Student ---")
    roll = input("Roll number: ").strip()
    if not roll:
        print("Roll number cannot be empty.")
        return
    if find_student(roll):
        menu_notice = "This roll number already exists. Use option 2 to add or update marks."
        return

    name = input("Student name: ").strip()
    if not name:
        print("Student name cannot be empty.")
        return
    students.append({"roll": roll, "name": name, "marks": {}})
    save_data()
    print(f"{name} was added successfully. Your change has been saved.")


def add_exam_marks():
    print("\n--- Add or Update Marks ---")
    student = find_student(input("Student roll number: ").strip())
    if not student:
        print("Student not found. Add the student first using option 1.")
        return
    if not subjects:
        print("No subjects are available. Add a subject using option 5 first.")
        return

    exam = choose_exam()
    if not exam:
        return
    print(f"\nEnter or update marks for {student['name']} — {exam}.")
    print("Choose a subject code, enter its mark out of 100, then choose another code or type DONE.")
    view_subjects()
    marks = student["marks"].setdefault(exam, {})
    marks_changed = False
    while True:
        code = input("\nSubject code (or DONE): ").strip().upper()
        if code == "DONE":
            break
        if code not in subjects:
            print("Subject code not found. Choose a code from the list above.")
            continue
        marks[code] = get_mark(code, subjects[code])
        marks_changed = True
        print(f"Saved in this session: {code} — {subjects[code]}")

    if not marks_changed:
        if not marks:
            del student["marks"][exam]
        print("No marks were changed.")
        return
    save_data()
    print(f"{exam} marks saved for {student['name']}.")


def view_students():
    print("\n--- Student List ---")
    if not students:
        print("No students found.")
        return
    print(f"{'Roll Number':<15} Name")
    print("-" * 42)
    for student in students:
        print(f"{student['roll']:<15} {student['name']}")


def print_student_record(student):
    print(f"\n--- Student Record ---\nRoll Number: {student['roll']}\nName: {student['name']}")
    if not student["marks"]:
        print("No exam marks recorded yet.")
        return

    for exam, marks in student["marks"].items():
        total = sum(marks.values())
        percentage = total / len(marks) if marks else 0
        result = "PASS" if percentage >= 33 else "FAIL"
        print(f"\n{exam}")
        print(f"{'Code':<10} {'Subject':<25} {'Marks':>8}")
        print("-" * 47)
        for code, mark in marks.items():
            subject_name = subjects.get(code, "Removed subject")
            print(f"{code:<10} {subject_name:<25} {mark:>7.1f}")
        print("-" * 47)
        print(f"{'Total':<36} {total:>7.1f}")
        print(f"{'Percentage':<35} {percentage:>6.2f}%")
        print(f"{'Result':<36} {result}")


def view_student_record():
    print_student = find_student(input("\nStudent roll number: ").strip())
    if print_student:
        print_student_record(print_student)
    else:
        print("Student not found.")


def add_subject():
    print("\n--- Add Subject ---")
    code = input("Subject code (for example, ENG): ").strip().upper()
    if not code or not code.replace("_", "").isalnum():
        print("Use a non-empty code containing letters, numbers, or underscores only.")
        return
    if code in subjects:
        print("That subject code already exists.")
        return
    name = input("Subject name (for example, English): ").strip()
    if not name:
        print("Subject name cannot be empty.")
        return
    subjects[code] = name
    save_data()
    print(f"{code} — {name} was added and saved.")


def remove_subject():
    print("\n--- Remove Subject ---")
    if not subjects:
        print("There are no subjects to remove.")
        return
    view_subjects()
    code = input("Subject code to remove: ").strip().upper()
    if code not in subjects:
        print("Subject code not found.")
        return
    name = subjects[code]
    confirmation = input(f"Remove {code} ({name}) from future mark entry? [y/N]: ").strip().lower()
    if confirmation != "y":
        print("No subject was removed.")
        return
    del subjects[code]
    save_data()
    print(f"{code} was removed. Existing historical marks have been kept in student records.")


def view_subjects():
    print("\n--- Subject Codes ---")
    if not subjects:
        print("No subjects found.")
        return
    for code, name in subjects.items():
        print(f"{code}: {name}")


students, subjects = load_data()
menu_notice = ""
pending_action = None

while True:
    print("\nSTUDENT MARKS MANAGEMENT")
    print("========================")
    print("1. Add Student")
    print("2. Add or Update Marks")
    print("3. Student List")
    print("4. View Student Record")
    print("5. Add Subject")
    print("6. Remove Subject")
    print("7. View Subject Codes")
    print("E. Exit")
    if menu_notice:
        print(f"\n{menu_notice}")
        menu_notice = ""

    actions = {
        "1": add_student,
        "2": add_exam_marks,
        "3": view_students,
        "4": view_student_record,
        "5": add_subject,
        "6": remove_subject,
        "7": view_subjects,
    }
    if pending_action:
        action = actions[pending_action]
        pending_action = None
        action()

    choice = input("\nEnter your choice: ").strip()
    if choice in actions:
        pending_action = choice
    elif choice.lower() == "e":
        print("Thank you!")
        break
    else:
        print("Invalid choice. Please choose 1–7 or E.")
