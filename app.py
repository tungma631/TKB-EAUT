from flask import Flask, render_template, request, redirect, url_for, flash
from crawler_service import get_schedule_data

app = Flask(__name__)
app.secret_key = 'khoa_bi_mat_cua_tung' # Để dùng flash message

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        msv = request.form['msv']
        password = request.form['password']
        
        # Gọi hàm crawler chạy ngầm
        data = get_schedule_data(msv, password)
        
        if data is None:
            flash('Đăng nhập thất bại! Kiểm tra lại MSV hoặc Mật khẩu.', 'error')
            return redirect(url_for('login'))
        else:
            # Nếu thành công, render trang dashboard với dữ liệu vừa lấy
            return render_template('dashboard.html', schedule=data, user_name=msv)
            
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)