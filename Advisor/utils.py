import openpyxl
from .models import Student
from datetime import datetime

def import_students_from_excel(file_path):
    workbook = openpyxl.load_workbook(file_path)
    worksheet = workbook.active

    for row in worksheet.iter_rows(min_row=2):
        idss = row[0].value
        country = row[1].value
        registration_date_str = row[2].value 
        full_name = row[3].value
        personal_id = row[4].value
        student_status = row[5].value
        education_level = row[6].value
        study_form = row[7].value
        payment_type = row[8].value
        username = row[9].value
        phone = row[10].value
        specialty = row[11].value
        op_code = row[12].value
        gop = row[13].value
        course = row[14].value
        school = row[15].value
        study_term = row[16].value
        department = row[17].value
        gender = row[18].value

        # Проверка на student_status "Отчислен"
        if student_status.lower() == "отчислен":
            continue  # Пропускаем запись

        # Обработка строки даты и создание объекта datetime
        registration_date = None
        if registration_date_str:
            try:
                registration_date = datetime.strptime(registration_date_str, "%d/%m/%Y %H:%M")
            except ValueError:
                print(f"Ошибка при обработке даты: {registration_date_str}")

        # Создаем новый объект студента и сохраняем его
        try:
            Student.objects.create(
                idss=idss,
                country=country,
                registration_date=registration_date,
                full_name=full_name,
                personal_id=personal_id,
                student_status=student_status,
                education_level=education_level,
                study_form=study_form,
                payment_type=payment_type,
                username=username,
                phone=phone,
                specialty=specialty,
                op_code=op_code,
                gop=gop,
                course=course,
                school=school,
                study_term=study_term,
                department=department,
                gender=gender,
            )
        except Exception as e:
            print(f"Ошибка при сохранении данных: {str(e)}")

    workbook.close()
