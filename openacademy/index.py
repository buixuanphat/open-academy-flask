from flask import render_template, request, redirect, url_for
from flask_login import login_user

from openacademy import app, utils, models, login
import cloudinary.uploader
from openacademy.utils import add_lecturer, add_student


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/lecturer-register', methods=['GET', 'POST'])
def lecturer_register():
    err_msg = ""
    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        bio = request.form.get('bio')

        if password != confirm_password:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            try:
                avatar_file = request.files.get('avatar')
                avatar_url = None
                if avatar_file:
                    res_avatar = cloudinary.uploader.upload(avatar_file)
                    avatar_url = res_avatar.get('secure_url')

                degree_files = request.files.getlist('degree_files[]')
                degree_names = request.form.getlist('degree_names[]')
                degrees_data = []

                for i in range(len(degree_files)):
                    file = degree_files[i]
                    if file and file.filename != '':
                        res_degree = cloudinary.uploader.upload(file)

                        name_val = degree_names[i].strip() if i < len(degree_names) else file.filename
                        if not name_val:
                            name_val = file.filename

                        degrees_data.append({
                            'name': name_val,
                            'url': res_degree.get('secure_url')
                        })

                new_lecturer = add_lecturer(
                    last_name=last_name,
                    first_name=first_name,
                    email=email,
                    password=password,
                    avatar=avatar_url,
                    bio=bio,
                    degrees=degrees_data
                )

                if new_lecturer:
                    return redirect(url_for('home'))
                else:
                    err_msg = "Có lỗi xảy ra"

            except Exception as e:
                err_msg = f"Lỗi hệ thống: {str(e)}"

    return render_template('lecturer_register.html', err_msg=err_msg)


@app.route('/student-register', methods=['GET', 'POST'])
def student_register():
    err_msg = ""
    if request.method == 'POST':
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        goal = request.form.get('goal')
        level = request.form.get('level')

        if password != confirm_password:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            try:
                avatar_file = request.files.get('avatar')
                avatar_url = None
                if avatar_file:
                    res_avatar = cloudinary.uploader.upload(avatar_file)
                    avatar_url = res_avatar.get('secure_url')

                new_student = add_student(
                    last_name=last_name,
                    first_name=first_name,
                    email=email,
                    password=password,
                    avatar=avatar_url,
                    goal=goal,
                    level=level
                )

                if new_student:
                    return redirect(url_for('home'))
                else:
                    err_msg = "Có lỗi xảy ra"

            except Exception as e:
                err_msg = f"Lỗi hệ thống: {str(e)}"
    return render_template('student_register.html', goals=models.StudyGoal, levels=models.StudentLevel, err_msg=err_msg)


@login.user_loader
def user_load(user_id):
    return utils.get_user_by_id(user_id=user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    err_msg = ''
    if request.method.__eq__('POST'):
        username = request.form.get('username')
        password = request.form.get('password')

        user = utils.check_login(username=username, password=password)
        if user:
            login_user(user=user)
            return redirect(url_for('index'))
        else:
            err_msg = 'Username hoac password KHONG chinh xac!!!'

    return render_template('login.html', err_msg=err_msg)


if __name__ == '__main__':
    app.run(debug=True)
