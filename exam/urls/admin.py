from django.conf.urls import url

from exam.views.admin import ExamList,ExamCreate,ExamDelete,ExamUpdate,ExamGet,ExamDetailCreate,ExamDetailGet,ExamDetailList,ExamDetailUpdate,ExamDetailOfExam,ExamDetailDelete,ExamExportResult
from exam.views.admin import StudentCreate,StudentList,StudentUpdate,StudentDelete,StudentGet,StudentResetPassword,StudentImport

#管理员级别
urlpatterns = [
    url(r"^exam/get/?$", ExamGet.as_view(), name="exam_get_api"),
    url(r"^exam/get_list/?$", ExamList.as_view(), name="exam_list_api"),
    url(r"^exam/create/?$", ExamCreate.as_view(), name="exam_create_api"),
    url(r"^exam/delete/?$", ExamDelete.as_view(), name="exam_delete_api"),
    url(r"^exam/update/?$", ExamUpdate.as_view(), name="exam_update_api"),
    url(r"^exam/get_exam_detail/?$", ExamDetailOfExam.as_view(), name="exam_exam_detail_get_api"),
   url(r"^exam/update_exam_detail/?$", ExamDetailOfExam.as_view(), name="exam_exam_detail_update_api"),
url(r"^exam/export_result/?$", ExamExportResult.as_view(), name="exam_export_result_api"),
    url(r"^exam/exam_detail/create/?$", ExamDetailCreate.as_view(), name="exam_detail_create_api"),
    url(r"^exam/exam_detail/get_list/?$", ExamDetailList.as_view(), name="exam_detail_list_api"),
    
    url(r"^exam/exam_detail/get/?$", ExamDetailGet.as_view(), name="exam_detail_get_api"),
    
    url(r"^exam/exam_detail/update/?$", ExamDetailUpdate.as_view(), name="exam_detail_update_api"),
    url(r"^exam/exam_detail/delete/?$", ExamDetailDelete.as_view(), name="exam_detail_delete_api"),

    url(r"^student/create/?$", StudentCreate.as_view(), name="student_create_api"),
    url(r"^student/get_list/?$", StudentList.as_view(), name="student_list_api"),
    url(r"^student/update/?$", StudentUpdate.as_view(), name="student_update_api"),
    url(r"^student/delete/?$", StudentDelete.as_view(), name="student_delete_api"),
    url(r"^student/get/?$", StudentGet.as_view(), name="student_get_api"),
    url(r"^student/reset_password/?$", StudentResetPassword.as_view(), name="student_reset_password_api"),
    url(r"^student/import/?$", StudentImport.as_view(), name="student_import_api"),
]