import os.path as op
import uuid as uuid

from flask import redirect, url_for
from flask_login import current_user
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FileUploadField
from werkzeug.utils import secure_filename

from news import app, db
from news.models import Category, Post, Users


class AdminAccess(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_anonymous:
            return current_user.is_staff

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))


admin = Admin(app, template_mode='bootstrap4', index_view=AdminAccess())
admin.add_view(ModelView(Category, db.session))


def prefix_name(obj, file_data):
    parts = op.splitext(file_data.filename)
    return secure_filename(f'{uuid.uuid1()}_%s%s' % parts)


class PostAdmin(ModelView):
    form_columns = ['title', 'content', 'category', 'picture']
    form_extra_fields = {
        'picture': FileUploadField('picture',
                                   namegen=prefix_name,
                                   base_path='static/images')
    }


admin.add_view(PostAdmin(Post, db.session))
admin.add_view(ModelView(Users, db.session))
